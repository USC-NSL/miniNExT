"""
Example service that manages Quagga routers
"""

from mininext.mount import MountProperties, ObjectPermissions, PathProperties
from mininext.moduledeps import serviceCheck
from mininext.service import Service


class QuaggaService(Service):

    "Manages Quagga Software Router Service"

    def __init__(self, name="Quagga", **params):
        """Initializes a QuaggaService instance with a set of global parameters

        Args:
            name (str): Service name (derived class may wish to override)
            params: Arbitrary length list of global properties for this service

        """

        # Verify that Quagga is installed"
        serviceCheck('quagga', moduleName='Quagga (nongnu.org/quagga/)')

        # Call service initialization (will set defaultGlobalParams)
        Service.__init__(self, name=name, **params)

        self.getDefaultGlobalMounts()

    def verifyNodeMeetsServiceRequirements(self, node):
        """Verifies that a specified node is configured to support Quagga

        Overrides the :class:`.Service` default verification method to conduct
            checks specific to Quagga. This includes checking that the node
            has a private log space, a private run space, and is in a PID
            namespace

        Args:
            node: Node to inspect

        """

        if node.inPIDNamespace is False:
            raise Exception("Quagga service requires PID namespace (node %s)\n"
                            % (node))

        if node.hasPrivateLogs is False:
            raise Exception("Quagga service requires private logs (node %s)\n"
                            % (node))

        if node.hasPrivateRun is False:
            raise Exception("Quagga service requires private /run (node %s)\n"
                            % (node))

    def setupNodeForService(self, node):
        """After mounts and other operations taken care of by Service Helper,
           we perform a few last minute tasks here"""

        # Initialize log directory
        _, err, ret = node.pexec("mkdir /var/log/quagga")
        _, err, ret = node.pexec("chown quagga:quagga /var/log/quagga")

    def getDefaultGlobalParams(self):
        "Returns the default parameters for this service"
        defaults = {'startCmd': '/etc/init.d/quagga start',
                    'stopCmd': '/etc/init.d/quagga stop',
                    'autoStart': True,
                    'autoStop': True,
                    'configPath': None}
        return defaults

    def getDefaultGlobalMounts(self):
        "Service-wide default mounts for the Quagga service"

        mounts = []
        mountConfigPairs = {}

        # quagga configuration paths
        quaggaConfigPerms = ObjectPermissions(username='quagga',
                                              groupname='quaggavty',
                                              mode=0o775,
                                              strictMode=False,
                                              enforceRecursive=True)
        quaggaConfigPath = PathProperties(path=None,
                                          perms=quaggaConfigPerms,
                                          create=True,
                                          createRecursive=True,
                                          setPerms=True,
                                          checkPerms=True)
        quaggaConfigMount = MountProperties(target='/etc/quagga',
                                            source=quaggaConfigPath)
        mounts.append(quaggaConfigMount)
        mountConfigPairs['quaggaConfigPath'] = quaggaConfigMount

        return mounts, mountConfigPairs
