"""
Extended "net" module for MiniNExT.
"""

from mininet.log import info
from mininet.net import Mininet


class MiniNExT(Mininet):

    """Override on the default Mininet class to enable use of MiniNExT enabled
       hosts"""

    def __init__(self, *args, **kwargs):
        info("** Using Mininet Extended (MiniNExT) Handler\n")
        Mininet.__init__(self, *args, **kwargs)

    def configHosts(self):
        "Configure the networks hosts."

        # Let Mininet handle the baseline initialization
        Mininet.configHosts(self)

        info('*** Starting host services\n')
        for host in self.hosts:
            returnCodes = host.autoStartServices()
            if returnCodes:
                # print detailed information on the started services
                statusStr = "%s: " % (host)
                for service, returnCode in returnCodes.iteritems():
                    if returnCode['ret'] == 0:
                        result = 'OK'
                    else:
                        result = 'FAIL'
                    statusStr += "%s (%s) " % (service, result)
                info(statusStr + '\n')

    def stop(self):
        "Stop the controller(s), switches and hosts"

        # First, stop all services in the network
        info('*** Stopping host services\n')
        for host in self.hosts:
            returnCodes = host.autoStopServices()
            if returnCodes:
                # print detailed information on the stopped services
                statusStr = "%s: " % (host)
                for service, returnCode in returnCodes.iteritems():
                    if returnCode['ret'] == 0:
                        result = 'OK'
                    else:
                        result = 'FAIL'
                    statusStr += "%s (%s) " % (service, result)
                info(statusStr + '\n')

        # Then, let Mininet take over and stop everything
        Mininet.stop(self)
