#!/usr/bin/python -t
"""
DES-CHAN: A Framework for Channel Assignment Algorithms for Testbeds

This module implements the two-hop heuristic, which states that any two links
that are separated by less than two other links interfere.  

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

from des_chan.error import CHANError

def get_interference(graph, e1, e2):
    """Returns the interference value for the given edges according to the
    two-hop heuristic. The value can either be 0 (edges do not interfere), or 1
    (edges do interfere), since the interference model is only binary. However,
    other interference models that implement this function may return any value
    between 0 and 1.
    
    2-hop heuristic: two links interfere, if they are separated by less
    than two hops and share the same channel

    """
    # a link does not interfere with itself
    if e1 == e2:
        return 0

    # a Graph object may take variables of any type as edge value, try to
    # convert it to integer 
    try:
        channel1 = int(graph.get_edges()[e1])
    except TypeError:
        raise CHANError("Unable to calculate interference! Invalid channel %s for edge %s" % (graph.get_edges()[e1], e1))
    try:
        channel2 = int(graph.get_edges()[e2])
    except TypeError:
        raise CHANError("Unable to calculate interference! Invalid channel %s for edge %s" % (graph.get_edges()[e2], e2))

    # Distinct channels do not interfere.
    # Note, we assume the algorithms work with orthogonal channels only.
    if channel1 != channel2:
        return 0

    # distance of two edges is defined by the minimum distance of the
    # corresponding vertices
    hop_counts = list()
    hop_counts.append(graph.get_distance(e1[0], e2[0]))
    hop_counts.append(graph.get_distance(e1[0], e2[1]))
    hop_counts.append(graph.get_distance(e1[1], e2[0]))
    hop_counts.append(graph.get_distance(e1[1], e2[1]))
    
    if min(hop_counts) < 2:
        return 1
    else:
        return 0



