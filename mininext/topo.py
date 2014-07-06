"""
Extended "topo" module for MiniNExT.
"""

from mininet.topo import Topo as BaseTopo
from mininext.node import Host


class Topo(BaseTopo):

    "Extended topology object to support MiniNExT customizations"

    def __init__(self, nopts=None, **opts):
        """Extended Topo object:
           nopts: default NAT options"""
        self.nopts = {} if nopts is None else nopts
        BaseTopo.__init__(self, **opts)

    # Override addHost so that constructor defaults to MiniNExT host
    def addHost(self, name, cls=Host, **opts):
        """Adds a host using the MiniNExT host constructor.
           name: host name
           cls: host constructor
           opts: host options
           returns: host name"""
        if not opts and self.hopts:
            opts = self.hopts
        return BaseTopo.addNode(self, name, cls=cls, **opts)

    # Configure a loopback interface
    def addNodeLoopbackIntf(self, node, ip, loNum=None, **opts):
        """Adds a loopback interface to a specified host.
           node: host node
           ip: the IP address that will be assigned to the lo interface
           loNum: loopback interface number (lo:X)
           opts: loopback interface options"""

        # grab the node from our list
        nodeParams = self.nodeInfo(node)

        # craft the dictionary entry to contain the lo interface info
        loIntf = {"ip": ip, "loNum": loNum}
        loIntf.update(opts)

        # grab any existing interfaces and append to them
        loIntfs = []
        if "loIntfs" in nodeParams:
            loIntfs = nodeParams['loIntfs']
        loIntfs.append(loIntf)
        nodeParams['loIntfs'] = loIntfs

    # Configure a service for a node
    def addNodeService(self, node, service, nodeConfig):
        """Adds a loopback interface to a specified host.
           node: host node
           service: service object
           nodeConfig: a specific node's override's on service configuration
           returns: success or failure"""

        # grab the node from our list
        nodeParams = self.nodeInfo(node)

        # grab any existing interfaces and append to them
        services = {}
        if "services" in nodeParams:
            services = nodeParams['services']
        services[service] = nodeConfig
        nodeParams['services'] = services
