#!/usr/bin/env python

"Setuptools params for MiniNExT"

from setuptools import setup

modname = distname = 'mininext'

setup(
    name=distname,
    version=1.10,
    description='Extensions to Mininet (MiniNExT)',
    author='Brandon Schlinker',
    author_email='bschlink@usc.edu',
    packages=[ 'mininext', 'mininext.services' ],
    long_description="""
        MiniNExT (MiniNet ExTended) is a layer of extensions
        on top of the existing Mininet software package. We are working
        to upstream some of these extensions into mainline Mininet.
        MiniNExT is part of the PEERING project at USC, which combines
        multiple technologies (MiniNExT, BGPMux, Transit Portal, TP at Scale)
        to lower the barriers to Internet routing research.
        """,
    classifiers=[
          "License :: OSI Approved :: BSD License",
          "Programming Language :: Python",
          "Development Status :: 5 - Production/Stable",
          "Intended Audience :: Developers",
          "Topic :: System :: Emulators",
    ],
    keywords='networking emulator protocol Internet OpenFlow SDN BGP Quagga containers',
    license='BSD',
    install_requires=[
        'setuptools',
        'mininet',
    ],
)
