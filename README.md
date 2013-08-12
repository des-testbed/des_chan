des_chan
========

DES-Chan is a framework to develop distributed channel assignment algorithms in testbed environments. It has been initially developed for the [DES-Testbed](http://www.des-testbed.net), a wireless testbed with about 130 multi-radio network nodes.

The framework provides basic services that are useful for a wide variety of different channel assignment algorithms. For instance, a neighbor discovery service is provided based on the ETX link metric (see [http://github.com/des-testbed/etxd](http://github.com/des-testbed/etxd)). Additionally, functions to set the wireless network interface parameters are provided and basic data structures to model the network graph and conflict graphs. The framework currently provides the 2-hop interference model and the Channel Occupancy Interference Model (COIM). Messages can be exchanged among the nodes based on Python Twisted.

An overview and documentation about the framework is available in these two publications:

1. Juraschek, F., M. Günes, and B. Blywis, [A Framework for External Interference-Aware Distributed Channel Assignment](http://des-testbed.net/content/framework-external-interference-aware-distributed-channel-assignment), International Journal of Wireless Networks and Broadband Technologies (IJWNBT), vol. 1, no. 4, pp. 40-54, 2012.

2. Juraschek, F., M. Günes, M. Philipp, B. Blywis, and O. Hahm, [DES-Chan: A Framework for Distributed Channel Assignment in Wireless Mesh Networks](http://des-testbed.net/content/des-chan-framework-distributed-channel-assignment-wireless-mesh-networks), Proceedings of the Australasian Telecommunication Networks And Applications Conference (ATNAC 2011), November, 2011 


Installation from git
---------------------
1. Clone the repository:
    
        git clone git://github.com/des-testbed/des_chan.git
    
    
2. Please make sure you have the following Python modules installed:

        - twisted
        - netifaces
        - pythonwifi
        - pgsql


Example algorithms based on des_chan
------------------------------------
to be commited soon
