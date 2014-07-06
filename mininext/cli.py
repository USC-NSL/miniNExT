"""
Extended CLI object for MiniNExT.
"""
from mininet.cli import CLI as BaseCLI


class CLI(BaseCLI):

    "Simple command-line interface to talk to nodes."

    prompt = 'mininext> '
