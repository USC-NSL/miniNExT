"""
Extended node object for MiniNExT.
"""

import signal
import select
import shutil
import tempfile
from subprocess import Popen, PIPE, STDOUT

from mininet.node import Node as BaseNode
from mininet.log import error, debug

from mininext.link import LoopbackIntf
from mininext.util import (checkPath, getObjectPerms, createDirIfNeeded,
                           setDirPerms, doDirPermsEqual)
from mininext.mount import MountProperties, PathProperties


class Node(BaseNode):

    """A Mininet node with various extensions and enhancements."""

    def __init__(self, name, inMountNamespace=False, inPIDNamespace=False,
                 inUTSNamespace=False, **params):
        """name: name of node
           inNamespace: in network namespace?
           inMountNamespace: has private mountspace?
           inPIDNamespace: has private PID namespace?
           params: Node parameters (see config() for details)"""

        # PID and Mount Namespace handling
        self.inPIDNamespace = inPIDNamespace
        self.inUTSNamespace = inUTSNamespace
        self.inMountNamespace = inMountNamespace

        # Private config monitoring
        self.hasPrivateLogs = False
        self.hasPrivateRun = False

        # Sanity check on namespace config
        if self.inPIDNamespace is True and self.inMountNamespace is False:
            raise Exception('PID namespaces require mount namespace for /proc')

        # Stash extended configuration information
        self.services = {}  # dict of services and parameters for this node
        self.privateMounts = {}  # dict of private mounts for this node

        # Network information
        self.loIntfs = {}

        # Request initialization of the BaseNode
        BaseNode.__init__(self, name, **params)

    # Overrides to support additional extensions #

    # Override on startShell() to support PID and mount namespaces
    def startShell(self):
        """Overrides the default shell start process to handle
           the addition of PID, UTS, and mount namespaces."""
        if self.shell:
            error("%s: shell is already running")
            return
        # mnexec: (c)lose descriptors, (d)etach from tty,
        # (p)rint pid, and run in (n)etwork namespace,
        # (m)ount namespace, p(i)d namespace, mount proc(f)s
        opts = '-cdp'
        if self.inNamespace:
            opts += 'n'
        if self.inMountNamespace:
            opts += 'm'
        if self.inPIDNamespace:
            opts += 'if'
        if self.inUTSNamespace:
            opts += 'u'
        # bash -m: enable job control
        # -s: pass $* to shell, and make process easy to find in ps
        cmd = ['mxexec', opts, 'bash', '-ms', 'mininet:' + self.name]
        self.shell = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT,
                           close_fds=True)
        self.stdin = self.shell.stdin
        self.stdout = self.shell.stdout
        self.pid = self.shell.pid
        self.pollOut = select.poll()
        self.pollOut.register(self.stdout)
        # Maintain mapping between file descriptors and nodes
        # This is useful for monitoring multiple nodes
        # using select.poll()
        self.outToNode[self.stdout.fileno()] = self
        self.inToNode[self.stdin.fileno()] = self
        self.execed = False
        self.lastCmd = None
        self.lastPid = None
        self.readbuf = ''
        self.waiting = False

        # If this node has a private PID space, grab the PID to attach to
        # Otherwise, we use the same PID as the shell's PID
        if self.inPIDNamespace:
            # monitor() will grab shell's true PID and put in self.lastPid
            self.monitor()
            if self.lastPid is None:
                raise Exception('Unable to determine shell\'s PID')
            self.pid = self.lastPid
            self.lastPid = None

    # Override on popen() to support mount and PID namespaces
    def popen(self, *args, **kwargs):
        """Return Popen() object in proper PID, UTS, mount, network namespaces
           args: Popen() args, single list, or string
           kwargs: Popen() keyword args"""
        opts = []
        opts.append('mxexec')
        opts.append('-d')
        if self.inNamespace:
            opts.append('-a')
            opts.append(str(self.pid))
        if self.inMountNamespace:
            opts.append('-b')
            opts.append(str(self.pid))
        if self.inPIDNamespace:
            opts.append('-k')
            opts.append(str(self.pid))
        if self.inUTSNamespace:
            opts.append('-j')
            opts.append(str(self.pid))
        defaults = {'stdout': PIPE, 'stderr': PIPE,
                    'mncmd': opts}
        defaults.update(kwargs)
        if len(args) == 1:
            if isinstance(args[0], list):
                # popen([cmd, arg1, arg2...])
                cmd = args[0]
            elif isinstance(args[0], str):
                # popen("cmd arg1 arg2...")
                cmd = args[0].split()
            else:
                raise Exception('popen() requires a string or list')
        elif len(args) > 0:
            # popen( cmd, arg1, arg2... )
            cmd = list(args)
        # Form the command to hand off
        mncmd = defaults['mncmd']
        del defaults['mncmd']
        cmd = mncmd + cmd
        # Shell requires a string, not a list!
        if defaults.get('shell', False):
            cmd = ' '.join(cmd)
        return Popen(cmd, **defaults)

    # Override on sendInt() to handle PID namespaces
    def sendInt(self, sig=signal.SIGINT):
        """Interrupt running command."""
        if self.lastPid and self.inPIDNamespace:
            # Cannot kill via os.kill (wrong PID namespace)
            # Instead, we kill by running 'kill -SIGNAL pid
            # inside of the namespace itself....
            killStr = "kill -%d %d" % (sig, self.lastPid)
            self.pexec(killStr)
        else:
            BaseNode.sendInt(self)

    # Override on setParam() to handle passing dicts with non-string keywords
    def setParam(self, results, method, **param):
        """Internal method: configure a *single* parameter
           results: dict of results to update
           method: config method name
           param: arg=value (ignore if value=None)
           value may also be list or dict"""
        name, value = param.items()[0]
        f = getattr(self, method, None)
        if not f or value is None:
            return
        if isinstance(value, list):
            result = f(*value)
        elif isinstance(value, dict):
            # In some cases, we're passing a dict with non-string keywords,
            # and thus must pass f( value ) instead of f( **value ).

            # Python 2x prohibits passing dicts with non-string keywords
            # (see Python/getargs.c for additional details)

            # To determine when we need to do this, we iterate through all
            # dict keys to discover non-string keys. We could also use a
            # flag or catch an exception, but these may have side-effects
            if all(isinstance(k, basestring) for k in value):
                result = f(**value)
            else:
                result = f(value)
        else:
            result = f(value)
        results[name] = result
        return result

    # Override on config() to support extended parameters
    def config(self, privateLogDir=None, privateRunDir=None,
               privateMounts=None, services=None, hostname=None,
               loIntfs=None, **_params):
        """Configure Node according to (optional) parameters:
           mac: MAC address for default interface
           ip: IP address for default interface
           defaultRoute: default route for all traffic
           privateLogDir = boolean or path to dir to bind over /var/log
           privateRunDir = boolean or path to dir to bind over /run
           privateMounts = mount / path properties objects
           loopbackIntfs = list of loopback interfaces and parameters
           services = service objects for service manager"""

        r = BaseNode.config(self, **_params)
        # Process private mounts and services in this order:
        # (1) - privateLogDir (/var/log), privateRunDir (/run) if requested
        # (2) - user private mounts
        # (3) - services and service mounts
        # (4) - setup hostname, loopback adapters, and other network components
        self.setParam(r, 'setupPrivateLogs', privateLogDir=privateLogDir)
        self.setParam(r, 'setupPrivateRun', privateRunDir=privateRunDir)
        self.setParam(r, 'setupPrivateMounts', privateMounts=privateMounts)
        self.setParam(r, 'setupServices', services=services)
        self.setParam(r, 'setupHostname', hostname=hostname)
        self.setParam(r, 'setupLoopbacks', loIntfs=loIntfs)
        return r

    # Additional extensions #

    # Network Handlers #
    def setupHostname(self, hostname):
        "Handles the setup of a hostname for the node"
        # Checks if the node has UTS namespace AND mount namespace
        if self.inMountNamespace is False or self.inUTSNamespace is False:
            raise Exception("Hostname for node %s cannot be set\n"
                            "Node must be in a mount and UTS namespaces\n"
                            % (self))

        # Update /etc/hostname...
        # Create a new temporary file, then write the hostname to the file
        # then mount over /etc/hostname with the new file
        hnTmp = tempfile.NamedTemporaryFile(prefix=("mx-hostname-%s" % (self)),
                                            delete=False)
        hnTmp.write(hostname)
        self.bindObject(hnTmp.name, "/etc/hostname")

        # Update /etc/hosts...
        # Create a new temporary file, then write the hostname to the file
        # then mount over /etc/hosts with the new file
        hostsTmp = tempfile.NamedTemporaryFile(prefix=("mx-hosts-%s" % (self)),
                                               delete=False)

        # copy the existing hosts file
        shutil.copyfile("/etc/hosts", hostsTmp.name)

        # seek to the end of the file and append our hostname, then bind
        hostsTmp.seek(0, 2)
        hostsTmp.write("\n# MiniNExT Container Hostname\n")
        hostsTmp.write("127.0.1.1\t%s\n\n" % (self))
        self.bindObject(hostsTmp.name, "/etc/hosts")

        # Call hostname inside of the node as well
        self.cmd("hostname %s" % (self.name))

    def setupLoopbacks(self, *loIntfs):
        "Handles the setup of a list of loopback configs"
        for loIntf in loIntfs:
            # create loopback interface object which will then update node
            LoopbackIntf(node=self, **loIntf)

    def addNodeLoopbackIntf(self, loIntf, loNum):
        """Adds a loopback interface (called on instantiation an interface).
           loIntf: loopback interface."""
        self.nameToIntf[loIntf.name] = loIntf
        self.loIntfs[loIntf.name] = loNum
        debug('\n')
        debug('added intf %s to node %s\n' % (loIntf, self.name))

    def nextLoopbackIntf(self):
        "Returns the index of the next loopback interface that is free"
        if len(self.loIntfs) > 0:
            return max(self.loIntfs.values()) + 1
        return 0

    # Service handlers #
    def setupServices(self, services=None):
        "Sets up services in the passed list for this node"

        # Make sure we were passed a dict of services
        if services is None:
            raise Exception("Passed empty services parameter\n")

        # Check if an identical service already exists
        if any(True for k in services if k in self.services):
            raise Exception("Cannot setup same service twice\n")

        # Update our list of services, perform the setup on the node
        self.services.update(services)
        for service, serviceProperties in services.items():
            service.setupNode(self, serviceProperties)

    def autoStartServices(self):
        "Starts services w/ autoStart=True that are configured for this node"
        returnCodes = {}
        for service in self.services.keys():
            serviceReturnCode = service.autoStart(self)
            if serviceReturnCode:
                returnCodes[service] = serviceReturnCode

        if len(returnCodes):
            return returnCodes
        return None

    def autoStopServices(self):
        "Stops services w/ autoStop=True that are configured for this node"
        returnCodes = {}
        for service in self.services.keys():
            serviceReturnCode = service.autoStop(self)
            if serviceReturnCode:
                returnCodes[service] = serviceReturnCode

        if len(returnCodes):
            return returnCodes
        return None

    # Mount / private directory management #
    # bindObject() for a simple mount -B operation with no checking, etc.
    # setupMountPoint() for complex operations (perms, tmps, creation, etc.)
    def setupPrivateLogs(self, privateLogDir):
        """Sets up a private /var/log directory for the node
           privateLogDir: None/True for default source, else path for source"""

        # Handle the input provided (either a bool or a path)
        if isinstance(privateLogDir, bool):
            if privateLogDir is False:
                return
            privateLogDir = '/var/log/mininext/%s' % (self.name)
        elif not isinstance(privateLogDir, basestring):
            raise Exception("Invalid parameter for privateLogDir\n")

        # Create the PathProperties and MountProperties objects
        logPathProperties = PathProperties(path=privateLogDir,
                                           perms=getObjectPerms('/var/log'),
                                           create=True,
                                           createRecursive=True,
                                           setPerms=False)
        logMount = MountProperties(target='/var/log', source=logPathProperties)

        # Pass the created mountPoint off...
        self.setupMountPoint(logMount)

        # Mark the node as having private run space
        self.hasPrivateLogs = True

    def setupPrivateRun(self, privateRunDir):
        """Sets up a private /run (& /var/run) directory for the node
           privateRunDir: None/True for default source, else path for source"""

        # Handle the input provided (either a bool or a path)
        if isinstance(privateRunDir, bool):
            if privateRunDir is False:
                return
            privateRunDir = '/run/mininext/%s' % (self.name)
        elif not isinstance(privateRunDir, basestring):
            raise Exception("Invalid parameter for privateRunDir\n")

        # Create the PathProperties and MountProperties objects
        logPathProperties = PathProperties(path=privateRunDir,
                                           perms=getObjectPerms('/run'),
                                           create=True,
                                           createRecursive=True,
                                           setPerms=False)
        logMount = MountProperties(target='/run', source=logPathProperties)

        # Pass the created mountPoint off...
        self.setupMountPoint(logMount)

        # Mark the node as having private run space
        self.hasPrivateRun = True

    def setupMountPoint(self, mountPoint):
        """Handle mountPoint source and target as PathProperties or strings
           Assume source/target strings first, then handle PathProperties"""
        sourcePath = mountPoint.source
        if isinstance(mountPoint.source, PathProperties):
            self.setupPath(mountPoint.source)
            sourcePath = mountPoint.source.path

        targetPath = mountPoint.target
        if isinstance(mountPoint.target, PathProperties):
            self.setupPath(mountPoint.target)
            sourcePath = mountPoint.target.path

        # Path setup (if requested) is complete -- proceed to bind!
        self.bindObject(sourcePath, targetPath)

    def setupMountPoints(self, mounts):
        "Handles PathProperties objects then binds"
        for mountPoint in mounts:
            self.setupMountPoint(mountPoint)

    def setupPath(self, pathProperties):
        "Sets up a path / directory based on a PathProperties object"
        if pathProperties.create is True:
            createDirIfNeeded(path=pathProperties.path,
                              perms=pathProperties.perms,
                              recursive=pathProperties.createRecursive)
        if pathProperties.setPerms is True:
            setDirPerms(path=pathProperties.path,
                        perms=pathProperties.perms)
        if pathProperties.checkPerms is True:
            doDirPermsEqual(path=pathProperties.path,
                            perms=pathProperties.perms)

    def setupPaths(self, paths):
        "Sets up a paths / directories based on PathProperties objects"
        for path in paths:
            self.setupPath(path)

    def bindObject(self, source, target):
        """Bind (mount -B) source to target, update records of existing binds
           source: path being attached (/home/user/privatedir)
           target: attachment / overlay point (/etc/app/config)"""

        # Verify that this node has a private mount namespace...
        if self.inMountNamespace is False:
            raise Exception("Refusing to bind directory %s to %s\n"
                            "Node %s is not in a private mount namespace\n"
                            % (source, target, self.name))

        # Perform the bind...
        checkPath(source)
        checkPath(target)
        _, err, ret = self.pexec('mount -n -B %s %s' % (source, target))
        if ret != 0:
            raise Exception("Unable to bind source object %s to target %s\n"
                            "Error = %s"
                            % (source, target, err))
        self.privateMounts[target] = source

    def hasPrivateMount(self, target):
        "Returns if the node has a private mount for a specific target"
        return target in self.privateMounts


class Host(Node):

    "MiniNExT enabled host"
    pass
