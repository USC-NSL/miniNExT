"""
Extended "link" module for MiniNExT.
"""

from mininet.link import Intf


class LoopbackIntf(Intf):

    "A special interface object that handles a loopback interface for a node"

    def __init__(self, node, loNum=None, **params):
        """node: owning node (where this loopback intf is being created)
           loNum: the loopback number (lo:X)
           other arguments are passed to Intf.config"""
        self.node = node
        self.loNum = loNum
        self.mac, self.ip, self.prefixLen = None, None, None
        self.params = params

        # determine the loopback number and name
        if self.loNum is None:
            self.loNum = node.nextLoopbackIntf()
        self.name = ("lo:%d" % self.loNum)

        # update the node's config
        node.addNodeLoopbackIntf(loIntf=self, loNum=self.loNum)

        # we don't actually need to instantiate the lo:X intf, just config it
        self.config(**params)

    # block out those interface operations that don't make sense here...
    def rename(self, newname):
        pass

    def delete(self):
        pass
