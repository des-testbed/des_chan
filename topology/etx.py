#!/usr/bin/python -t
"""
DES-CHAN: A Framework for Channel Assignment Algorithms for Testbeds

This module retrieves the local network topology via inter process communication
from the ETX daemon.

etxd is available here: git clone git://github.com/des-testbed/etxd.git

Authors:    Matthias Philipp <mphilipp@inf.fu-berlin.de>,
            Felix Juraschek <fjuraschek@gmail.com>

Copyright 2008-2013, Freie Universitaet Berlin (FUB). All rights reserved.

These sources were developed at the Freie Universitaet Berlin, 
Computer Systems and Telematics / Distributed, embedded Systems (DES) group 
(http://cst.mi.fu-berlin.de, http://www.des-testbed.net)
-------------------------------------------------------------------------------
This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see http://www.gnu.org/licenses/ .
--------------------------------------------------------------------------------
For further information and questions please use the web site
       http://www.des-testbed.net
       
"""


from twisted.internet import reactor, defer
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineOnlyReceiver

from des_chan.graph import Graph
from des_chan import util

import socket

TIMEOUT = 5 
DEBUG = False


class EtxIpcProtocol(LineOnlyReceiver):
    
    delimiter = '\n'

    def connectionMade(self):
        """Send the request for all links meeting the quality threshold.

        """
        self.factory.timeout.cancel()
        self.sendLine("CHAFT %.1f" % self.factory.quality)

    
    def lineReceived(self, line):
        """Receive and parse the result for the local network topology.
        If recursive is set, send requests to our neighbors which eventually will 
        deliver the 2-hop neighborhood.

        """
        # split line in vertex names
        neighbor_ip, channel = line.split(":")
        channel = int(channel)
        # try to resolve the name of the corresponding nodes
        node1 = util.resolve_node_name(self.factory.host)
        node2 = util.resolve_node_name(neighbor_ip)
        if not node1 or not node2:
            return
        # add vertices to graph
        self.factory.graph.add_vertex(node1)
        self.factory.graph.add_vertex(node2)
        # set channel as edge value
        edge_value = self.factory.graph.get_edge_value((node1, node2))
        if not edge_value:
            edge_value = set()
        edge_value.add(channel)
        self.factory.graph.set_edge_value((node1, node2), edge_value)
        if self.factory.recursive:
            # get two-hop neighbors and stop recursion
            reactor.callWhenRunning(_query_host, neighbor_ip,
                                    self.factory.graph, self.factory.deferred)
        

class EtxIpcFactory(ClientFactory):

    conn_cnt = 0

    def __init__(self, host, graph, deferred, recursive,quality):
        self.protocol = EtxIpcProtocol
        self.host = host
        self.graph = graph
        self.deferred = deferred
        self.recursive = recursive
        self.quality=quality

    def startedConnecting(self, connector):
        if DEBUG: print "Connecting to %s" % (connector.getDestination().host)
        EtxIpcFactory.conn_cnt += 1
        if DEBUG: print "num connections %d" % EtxIpcFactory.conn_cnt

    def clientConnectionFailed(self, connector, reason):
        print "des_chan.topology.etx: Connection to %s failed: %s" % (connector.getDestination().host,
                                               reason.getErrorMessage())
        self.finished()
    
    def clientConnectionLost(self, connector, reason):
        if DEBUG: print "Connection to %s lost" % (connector.getDestination().host)
        self.finished()
    
    def finished(self):
        EtxIpcFactory.conn_cnt -= 1
        if DEBUG: print "num connections %d" % EtxIpcFactory.conn_cnt
        # if all connections have been closed, i.e. all neighbors have been
        # queried for their neighbors
        if EtxIpcFactory.conn_cnt == 0:
            # fire the callback
            self.deferred.callback(self.graph)


def _timed_out(port):
    if DEBUG: print "connection timed out"
    port.disconnect()


def _query_host(host, graph, deferred, recursive=False,quality=0.6):
    """Query one of our neighbors for its neighbors, so we can determine our 2-hop neighborhood.

    """
    ipc_factory = EtxIpcFactory(host, graph, deferred, recursive, quality)
    port = reactor.connectTCP(host, 9157, ipc_factory)
    # schedule timeout function that stops the connection if it takes too long
    ipc_factory.timeout = reactor.callLater(TIMEOUT, _timed_out, port)


def get_network_graph(quality=0.6):
    """Retrieve the 2-hop neighborhood.

    """
    deferred = defer.Deferred()
    graph = Graph()
    # at first get the one-hop neighbors of this node, afterwards recursively
    # get the two-hop neighbors by querying the one-hop neighbors
    reactor.callWhenRunning(_query_host, "localhost", graph, deferred, True, quality)
    return deferred

