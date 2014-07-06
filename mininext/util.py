"""
Additional utilities and patches for MiniNExT.
"""

from os.path import isdir
import os
import pwd
import grp
import shutil

from mininet.util import quietRun
from mininext.mount import ObjectPermissions

# Patches #


def isShellBuiltin(cmd):
    """Override to replace MiniNExT's existing isShellBuiltin() function,
       which is partially broken. Function should return true if
       cmd issued is a bash builtin."""
    # Original version would return true if container name was 'a'
    # or similar), as the letter 'a' exists within the output of
    # 'bash -c enable'. Prevented below at minimal cost"""
    if isShellBuiltin.builtIns is None:
        # get shell builtin functions, split at newlines
        rawBuiltIns = quietRun('bash -c enable')

        # parse the raw collected builtIns, add to a set
        isShellBuiltin.builtIns = set()
        for rawBuiltIn in rawBuiltIns.split('\n'):
            # keep only the part of the string after 'enable' and add to set
            isShellBuiltin.builtIns.add(rawBuiltIn.partition(' ')[2])
    space = cmd.find(' ')
    if space > 0:
        cmd = cmd[:space]
    return cmd in isShellBuiltin.builtIns

isShellBuiltin.builtIns = None

# Mount support / permissions management #

# Check directory/file state and permissions


def checkIsDir(path):
    "Raises exception if path is not valid directory"
    if quietCheckIsDir(path) is False:
        raise Exception("Path [%s] is not a valid directory" % (path))


def quietCheckIsDir(path):
    "Return if path is a valid directory"
    return isdir(path)


def checkPath(path):
    "Raises exception if path is not valid"
    if quietCheckPath(path) is False:
        raise Exception("Path [%s] is not valid" % (path))


def quietCheckPath(path):
    "Return if path is valid"
    return os.path.exists(path)


def createDirIfNeeded(path, perms=None, recursive=False):
    "Create a dir with specified permissions if it does not already exist"

    # Set function based on recursive parameter
    f = os.mkdir
    if recursive is True:
        f = os.makedirs

    # Check if directory or object at path already exists
    if os.path.isdir(path):
        return
    if not os.path.isdir(path) and os.path.exists(path):
        raise Exception("Cannot create directory, object at path %s" % (path))

    if perms is None:
        f(path)

    else:
        # Set the UID / GID in perms if username / groupname
        # passed instead of IDs
        setUIDGID(perms)

        oldumask = os.umask(0)

        # Create the directory
        if perms.mode is not None:
            f(path, perms.mode)
        else:
            f(path)

        # Set uid and gid
        uid = perms.uid
        gid = perms.gid
        if uid is None:
            uid = -1
        if gid is None:
            gid = -1
        os.chown(path, uid, gid)
        os.umask(oldumask)  # revert back to previous umask


def deleteDirIfExists(path):
    "Delete a directory if it exists (no error if it does not exist)"
    if quietCheckIsDir(path):
        shutil.rmtree(path)


def getUIDGID(username=None, groupname=None):
    "Get the UID and GID corresponding with a username and/or groupname"
    uid = None
    if username is not None:
        try:
            uid = pwd.getpwnam(username).pw_uid
        except KeyError:
            raise Exception("Expected user %s does not exist" % (username))
    gid = None
    if groupname is not None:
        try:
            gid = grp.getgrnam(groupname).gr_gid
        except KeyError:
            raise Exception("Expected group %s does not exist" % (groupname))
    return uid, gid


def setUIDGID(perms):
    "Set perms.uid and .gid only if perms.username / .groupname set"
    uid, gid = getUIDGID(perms.username, perms.groupname)
    perms.uid = uid
    perms.gid = gid


def doDirPermsEqual(path, perms):
    "Ask below if the perms are equal, raise exception if they are not..."
    if quietDoDirPermsEqual(path, perms) is False:
        raise Exception("Insufficient or unexpected permissions for %s "
                        "or a subdirectory / file\n"
                        "Expected user = %s, group = %s, (minimum) mode = %s"
                        % (path, perms.username,
                            perms.groupname, oct(perms.mode)))


def quietDoDirPermsEqual(path, perms):
    "Check if a dir's permissions are equal to the specified values"

    # Parent directory first...
    if doObjectPermsEqual(path, perms) is False:
        return False

    # Then recursively checksubdirectories...
    if perms.enforceRecursive is True:
        for root, dirs, files in os.walk(path):
            for momo in dirs:
                if doObjectPermsEqual(
                        os.path.join(
                            root,
                            momo),
                        perms) is False:
                    return False
            for momo in files:
                if doObjectPermsEqual(
                        os.path.join(
                            root,
                            momo),
                        perms) is False:
                    return False
    return True


def doObjectPermsEqual(objectToCheck, perms):
    "Compare object's (file / dir) permissions to specified values (with IDs)"

    # Set the UID / GID in perms if username / groupname passed instead of IDs
    setUIDGID(perms)

    # Perform the comparison operation
    permsEqual = True
    objectStat = os.stat(objectToCheck)
    if perms.uid is not None:
        permsEqual &= (objectStat.st_uid == perms.uid)
    if perms.gid is not None:
        permsEqual &= (objectStat.st_gid == perms.gid)
    if perms.mode is not None:
        if perms.strictMode is None or True:
            permsEqual &= (((objectStat.st_mode & 0o777) ^ perms.mode)
                           & perms.mode) == 0
        else:
            permsEqual &= (objectStat.st_mode & 0o777) == perms.mode
    return permsEqual


def getObjectPerms(objectToInspect):
    "Returns an object's (file / dir) permissions"
    objectStat = os.stat(objectToInspect)

    uid = objectStat.st_uid
    gid = objectStat.st_gid
    mode = objectStat.st_mode & 0o777

    return ObjectPermissions(uid=uid, gid=gid, mode=mode)

# Create & modify directory/file state and permissions


def setDirPerms(path, perms):
    "Set a path's permissions to the specified values"

    # Parent directory first...
    setObjectPerms(path, perms)

    # Then, if requested, recursively update subdirectories and files
    if perms.enforceRecursive is True:
        for root, dirs, files in os.walk(path):
            for momo in dirs:
                setObjectPerms(os.path.join(root, momo), perms)
            for momo in files:
                setObjectPerms(os.path.join(root, momo), perms)


def setObjectPerms(objectPath, perms):
    "Set an object's permissions to the specified values"

    # Set the UID / GID in perms if username / groupname passed instead of IDs
    setUIDGID(perms)

    # Set an objects's permissions to the specified values (with IDs)
    uid = perms.uid
    gid = perms.gid
    if uid is None:
        uid = -1
    if gid is None:
        gid = -1
    os.chown(objectPath, uid, gid)

    # Update the mode if needed
    if perms.mode is not None:
        objectStat = os.stat(objectPath)

        # Determine if an update is required
        modeOK = False
        if perms.strictMode is None or True:
            modeOK = (
                ((objectStat.st_mode & 0o777) ^ perms.mode) & perms.mode) == 0
        else:
            modeOK = (objectStat.st_mode & 0o777) == perms.mode

        # If update required, proceed
        if modeOK is False:
            os.chmod(objectPath, perms.mode)


def copyTreeToExistingDir(src, dst, symlinks=False, ignore=None):
    "Copy the contents of one directory into another (existing) directory"
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

# Simple Objects #

# Parameter management for global and node specific parameters


class ParamContainer(object):

    """Basic parameter management object that can be used by many nodes.
       Used to store configuration for services, where a global service
       config exists that can vary on a per node basis..."""

    def __init__(self, name, **params):
        """name: name of parameter container
           params: parameters to be used for global params"""
        self.name = name
        self.globalParams = {}  # global parameters
        self.nodeParams = {}  # dict of nodes and their associated parameters

        # update global parameters with defaults, then passed parameters
        defaultGlobalParams = self.getDefaultGlobalParams()
        if defaultGlobalParams is not None:
            self.updateGlobalParams(**defaultGlobalParams)
        self.updateGlobalParams(**params)

    # Handlers for global parameters

    def getDefaultGlobalParams(self):
        "This is filled in by derived class with default parameters"
        return None

    def updateGlobalParams(self, **kwargs):
        "Update the parameters shared by all nodes (the global parameters)"
        self.globalParams.update(kwargs)

    def getGlobalParam(self, param, **kwargs):
        "Get a service wide default parameter"
        if 'defaultValue' in kwargs:
            # Return the specified defaultValue if param not set
            # kwargs is used as defaultValue could be 'None'
            return self.globalParams.get(param, kwargs['defaultValue'])
        else:
            # Any KeyError exception will need to be handled upstream
            return self.globalParams.get(param)

    def getGlobalParams(self):
        "Get service wide default parameters"
        return self.globalParams

    # Handlers for node specific parameters

    def storeNodeParams(self, node, params, copyDefaults=False):
        """Stores or updates node specific service parameters
           If requested, merge the default config with the node's config,
           with the node's service config taking priority"""
        nodeServiceParams = {}
        if copyDefaults is True:
            nodeServiceParams = self.globalParams.copy()
        if params is not None:
            nodeServiceParams.update(params)

        # Store parameters structure for future use (uncouples from node)
        self.nodeParams[node] = nodeServiceParams

    def hasNodeParam(self, node, param):
        "Checks whether we have a parameter for a specific node"
        return param in self.getNodeParams(node)

    def hasNodeParams(self, node):
        "Checks whether we have received parameters for a specific node"
        return node in self.nodeParams

    def getNodeParam(self, node, param, **kwargs):
        "Returns a specific parameter from node's parameters for this service"
        if 'defaultValue' in kwargs:
            # Return the specified defaultValue if param not set
            # kwargs is used as defaultValue could be 'None'
            return self.getNodeParams(node, kwargs).get(param,
                                                        kwargs['defaultValue'])
        else:
            # Any KeyError exception will need to be handled upstream
            return self.getNodeParams(node, kwargs).get(param)

    def getNodeParams(self, node, includeGlobals=True, **kwargs):
        "Returns structure containing a node's parameters for this service"
        if includeGlobals is False and node not in self.nodeParams\
                and 'defaultValue' not in kwargs:
            raise Exception('ParamContainer %s doesn\'t have params for '
                            'node %s' % (self.name, node))

        nodeServiceParams = {}
        if includeGlobals is True:
            nodeServiceParams.update(self.globalParams)
        if node in self.nodeParams:
            nodeServiceParams.update(self.nodeParams[node])
        return nodeServiceParams
