"""
Service Helper for MiniNExT.
"""

import copy
from mininext.mount import MountProperties
from mininext.util import ParamContainer


class Service(ParamContainer):

    "Basic service object that can be used by many nodes."

    def __init__(self, name, **kwargs):
        """Initializes a new service helper object
           name: service name (e.g. OpenVPN, Quagga, etc.)
           kwargs: arguments that override service default configuration
           """
        ParamContainer.__init__(self, name=name, **kwargs)

    # Checks to determine the current state of nodes #

    def nodeIsSubscribed(self, node):
        """Checks if a node is subscribed by looking for its parameter entry
           Even if a node had no params to pass, there will
           still be an entry for the node"""
        return self.hasNodeParams(node)

    def errIfNodeNotSubscribed(self, node):
        "Raises an exception if node is not subscribed"
        if self.nodeIsSubscribed(node) is False:
            raise Exception("Service %s has not been setup for node %s\n"
                            % (self.name, node))

    # Setup handlers for each node subscribed to the service #

    def setupNode(self, node, nodeServiceParams, includeDefaults=True):
        "Setup a node to support the service and record node subscription"

        # Check if node already setup
        if self.nodeIsSubscribed(node):
            raise Exception("Service %s has already been setup for node %s\n"
                            "Update node config with storeParamsForNode()\n"
                            % (self.name, node))

        # Make sure the node meets the service's requirements
        self.verifyNodeMeetsServiceRequirements(node)

        # Setup the node's service parameters
        self.storeNodeParams(node, nodeServiceParams, includeDefaults)

        # Setup the node's mounts
        self.setupNodeMounts(node)

        # Pass control to a function which services may override easily
        self.setupNodeForService(node)

    def verifyNodeMeetsServiceRequirements(self, node):
        """Subclasses can to verify that a node meets it's requirements
           by inspecting the node's attributes (inPIDNamespace, etc.),
           parameters (node.params), and by inspecting hasPrivateMount()"""
        pass

    def setupNodeForService(self, node):
        "Subclasses can use this to perform detailed setup (as needed)"
        pass

    def setupNodeMounts(self, node):
        "Get the service mounts for a specific node"
        nodeServiceMounts = self.getMountsForNode(node)
        for mountPoint in nodeServiceMounts:
            if mountPoint.source is not None and \
                    mountPoint.source.path is not None and \
                    mountPoint.target is not None:
                node.setupMountPoint(mountPoint)

    # Start / stop service management #

    def autoStart(self, node):
        "Auto-start nodes that have requested it"
        if self.getNodeParam(node, 'autoStart', defaultValue=None) is True:
            return self.start(node)
        return None

    def autoStop(self, node):
        "Auto-stop nodes that have requested it"
        if self.getNodeParam(node, 'autoStop', defaultValue=None) is True:
            return self.stop(node)
        return None

    def start(self, node):
        "Start the service for a specific node"

        # sanity check, then grab the startCmd
        self.errIfNodeNotSubscribed(node)
        startCmd = self.getNodeParam(node, 'startCmd', defaultValue=None)
        if startCmd is None:
            raise Exception("Cannot start service %s, startCmd not defined\n"
                            % (self.name))

        # attempt to start the service
        _, err, ret = node.pexec(startCmd)
        if ret != 0 and self.getNodeParam(
                node,
                'exceptionOnStartFail') is True:
            raise Exception("Error starting %s service\n"
                            "Error = %s" % (self.name, err))
        return {'err': err, 'ret': ret}

    def stop(self, node):
        "Stop the service for a specific node"

        # sanity check, then grab the stopCmd and try to stop
        self.errIfNodeNotSubscribed(node)
        stopCmd = self.getNodeParam(node, 'stopCmd', defaultValue=None)
        if stopCmd is None:
            raise Exception("Cannot stop service %s, stopCmd not defined\n"
                            % (self.name))

        _, err, ret = node.pexec(stopCmd)
        return {'err': err, 'ret': ret}

    # Service / parameter handling #

    def getDefaultGlobalParams(self):
        "An individual service fills this in with it's default parameters"
        return None

    # Mount management #

    def getDefaultGlobalMounts(self):
        "Returns service-wide default mounts and mount config pairs"
        mounts = []
        mountConfigPairs = {}

        return mounts, mountConfigPairs

    def getMountsForNode(self, node):
        "Returns a structure with the node's service mounts"

        # sanity check then grab the node's parameters
        self.errIfNodeNotSubscribed(node)
        if self.hasNodeParam(node, 'mounts') is True:
            # If a mounts parameter was passed for the node's config,
            # we override all other mounts and just use those in mounts
            return self.getNodeParam(node, 'mounts')

        # allow overrides via defined configuration strings
        nodeMounts = []
        _, mountConfigPairs = self.getDefaultGlobalMounts()
        for mountName, mountProperties in mountConfigPairs.iteritems():
            # do a deep copy so we don't impact other nodes
            mountProperties = copy.deepcopy(mountProperties)

            # does the node have a serviceParam equal to this mountName?
            nodeMountOptions = self.getNodeParam(node, mountName,
                                                 defaultValue=None)
            if nodeMountOptions is None:
                # The node does not wish to override this default mount
                continue

            # Handle update depending on what is passed
            if isinstance(nodeMountOptions, basestring):
                # Node passed a string, indicates override source
                mountProperties.source.path = nodeMountOptions
            elif isinstance(nodeMountOptions, MountProperties):
                # Node passed a node properties object, replace object
                mountProperties = nodeMountOptions
            else:
                raise Exception("getMountsForNode does not support this "
                                "object type\n")

            # add the mount to the nodeMount list
            nodeMounts.append(mountProperties)

        return nodeMounts

    # Service representation #

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)

    def __str__(self):
        return self.name

    def __hash__(self):
        """Hashes any object of a service to the same value
           Thus, an attempt to use two instances of the same service
           in a single node will result in a collision"""
        return hash(self.name)
