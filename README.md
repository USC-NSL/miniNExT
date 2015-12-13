miniNExT
==============

MiniNExT (_Mininet ExTended_) is an extension layer that makes it easier to build complex networks in [Mininet](http://www.mininet.org).

**MiniNExT does not currently support the latest version of Mininet -- you must use version 2.1.0**

MiniNExT includes building blocks that are used in many experimental networks, including:

* Routing engines (Quagga and BIRD)
* Servers (BIND and Apache)
* Connectivity components (OpenVPN, etc.)
* NAT and Network Management components (DHCP, etc.)

In addition, MiniNExT hosts / containers can provide greater isolation, including:

* PID namespaces - isolates each container's processes, improving application support and analysis
* UTS namespaces - each host can have its own hostname, simplifying debugging and analysis
* Improved mount namespaces - makes it possible to override each host's view of their local filesystem 
* Log and runtime isolation - each host can have its own /var/log and /run with one line

We also make it easier to express common configurations with:

* Service helpers - makes it easier to run and manage the services in your hosts
* Network helpers - makes it easier to configure loopback interfaces and NAT networks
* Mount management - makes it easier to provide hosts with individual application configurations

We hope to upstream some of these extensions (such as support for PID and UTS namespaces, easier mount management, etc.) into mainline Mininet.

## Project Details

MiniNExT was developed by Brandon Schlinker at [The University of Southern California](http://www.usc.edu) in collaboration with Kyriakos Zarifis (USC), Italo Cunha (UFMG), Nick Feamster (GaTech), Ethan Katz-Bassett (USC), and Minlan Yu (USC).

MiniNExT is part of the PEERING project at USC, which combines Transit Portal and MiniNExT. Combined, these tools enable researchers to build realistic AS topologies that can exchange BGP routes and traffic with _real_ ISPs around the world. The PEERING tools played a role in evaluating [Software Defined Internet Exchanges](http://noise-lab.net/projects/software-defined-networking/sdx/) by making it possible to build a virtual IXP fabric composed of _real_ ISP peers.

For problems with the code base, please use the GitHub issue tracker. All other queries, please email bschlink@usc.edu

## Getting Started

### Installing Mininet

MiniNExT depends on the Mininet software package, and thus you must have Mininet installed.

**MiniNExT does not currently support the latest version of Mininet -- you must use version 2.1.0**

You can check if you already have Mininet installed and its version by executing `mn --version`

You can install Mininet version 2.1.0 on Ubuntu by executing:
```
$ sudo apt-get install mininet=2.1.0-0ubuntu1
```

If the above fails, you may need to uninstall your current version of Mininet:
```
$ sudo apt-get purge mininet
```

You can also check if your package manager has Mininet version 2.1.0:
```
$ sudo apt-cache madison ^mininet
```

Alternatively, Mininet can be installed from source by following the instructions on the [Mininet website](http://www.mininet.org)

### Downloading MiniNExT

MiniNExT sources are available [here](http://mininext.uscnsl.net). The easiest option is to download a `.zip` or `.tar.gz` source archive. Download and extract the archive to a location in your home directory.

You may also prefer to use `git` to `clone` the MiniNExT repository to make upgrading easier.

### Installing MiniNExT Dependencies

MiniNExT depends on a packages that may not be installed by default with Mininet.

To list these dependencies, execute the following in the directoy where you _extracted_ MiniNExT:
```
$ make deps
```

These dependencies can be installed on Debian/Ubuntu by executing:
```
$ sudo apt-get install `make deps`
```

### Installing MiniNExT

To install MiniNExT, execute the following in the directoy where you _extracted_ MiniNExT:
```
$ sudo make install
```

### Uninstalling MiniNExT

To uninstall MiniNExT, execute the following in the directoy where you _extracted_ MiniNExT:
```
$ sudo make uninstall
```

Note that the `pip` package must be installed for this to work.

### Developer Installation

If you're extending or debugging MiniNExT, you likely do _not_ want to install to the system's Python library. 

Instead, you can run the following command to install MiniNExT in developer mode:
```
$ sudo make develop
```

This triggers the [development mode](https://pythonhosted.org/setuptools/setuptools.html#development-mode) that is provided by the `setuptools` package, which then creates a link instead of performing a complete installation. However, note that the `mxexec` and supporting help files are still installed into their respective system paths.

To remove, run:
```
$ sudo make undevelop
```


**Note:** MiniNExT no longer _forks_ Mininet<br>
Previously MiniNExT functionality was built by forking and modifying the original Mininet source code. However, this created conflicts with existing Mininet installations and made it difficult to merge in upstream changes. MiniNExT has been redesigned to _extend_ Mininet, and does _not_ impact default Mininet execution.
