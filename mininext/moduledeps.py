"""
Extended moduledeps object for MiniNExT.
"""

from mininet.log import error
from mininet.util import errRun


def serviceCheck(*args, **kwargs):
    "Make sure each service in *args can be found in /etc/init.d/."
    moduleName = kwargs.get('moduleName', 'it')
    for arg in args:
        _, _, ret = errRun('test -x /etc/init.d/' + arg)
        if ret != 0:
            error('Cannot find required service %s in /etc/init.d/.\n' % arg +
                  'Please make sure that %s is installed ' % moduleName)
            exit(1)
