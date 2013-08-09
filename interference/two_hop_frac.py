#!/usr/bin/python -t
"""
DES-CHAN: A Framework for Channel Assignment Algorithms for Testbeds

This module implements the two-hop heuristic, which states that any two links
that are separated by less than two other links interfere.  Additionally, 
overlapping channels have to be used on the links so that there are
interference effects.

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

frequencies = {}
# 2.4 GHz band
for i in range(14):
    frequencies[i + 1] = 2412 + i * 5
# lower 5GHz band
for i in range(36, 68, 4):
    frequencies[i] = 5180 + 20 * ((i - 36) / 4)
# middle 5GHz band
for i in range(100, 144, 4):
    frequencies[i] = 5500 + 20 * ((i - 100) / 4)
# upper 5GHz band
for i in range(149, 169, 4):
    frequencies[i] = 5745 + 20 * ((i - 149) / 4)

MIN_FREQ_DIFF = 60


def get_interference(graph, e1, e2):
    """Returns the interference value for the given edges according to the
    two-hop heuristic. The value will be between 0 (edges do not interfere), and
    1 (edges do interfere), depending on the spectral difference of the
    channels. If the two edges are separated by more than two hops, the
    interference value is 0 regardless of the channel difference. If the edges
    are within two hops of each other and the center frequences of the channels
    are separated by more than 60 MHz, the interference value is also 0.

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
    
    # calculate the interference level
    diff = abs(frequencies[channel1] - frequencies[channel2])
    # experiments showed that a channel separation of 60 MHz does not interfere
    # on the DES-Testbed
    # this corresponds to 3 channels in the 5GHz band and 12 channels in the
    # 2.4GHz band
    if diff >= MIN_FREQ_DIFF:
        return 0

    interf = -1.0/MIN_FREQ_DIFF * diff + 1
    
    # distance of two edges is defined by the minimum distance of the
    # corresponding vertices
    hop_counts = list()
    hop_counts.append(graph.get_distance(e1[0], e2[0]))
    hop_counts.append(graph.get_distance(e1[0], e2[1]))
    hop_counts.append(graph.get_distance(e1[1], e2[0]))
    hop_counts.append(graph.get_distance(e1[1], e2[1]))
    
    # if the links are spacially close and use overlapping channels,
    # return the interference level
    if min(hop_counts) < 2:
        return interf
    else:
        return 0



