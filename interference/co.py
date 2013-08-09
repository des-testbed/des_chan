#!/usr/bin/python -t
"""
DES-CHAN: A Framework for Channel Assignment Algorithms for Testbeds

This module implements the Channel Occupancy Interference Model (COIM). The 
measurements must have been already performed, so this modules retrieves 
the measurement results from the database and checks for interference
relationships. The database can be stored directly on the nodes or on the 
testbed server for convenience.  

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

# from syslog import *
from datetime import datetime

from des_chan.error import CHANError
from des_chan import des_db

# Threshold for the sensed channel occupancy (in percent)
CO_THRESHOLD = 2.0

node_id = dict()
cot_max = dict()


def init():
    """Caches the CO measurement results into a data structure, so we can look up
    interference relationships faster without accessing the database.
    
    """
	# get all nodes 
    res_db = des_db._raw_query("SELECT id, name FROM \"Node\" WHERE  type = 0")
    for res in res_db:
        node_id[res.get('id')] = res.get('name')

    # get the CO measurement results
    res_db = des_db._raw_query("SELECT id_listener, id_sender, cot_max FROM \"CORResultsKernel\"")
    for res in res_db:
        cot_max[node_id[res.get('id_listener')] + '-' + node_id[res.get('id_sender')]] = res.get('cot_max')


def get_interference_by_node(node_sender, node_listener):
    """Returns if node_sender is an interferer for node_listener
    
    """
    
    # get node IDs
    dict_name_id = dict()
    res_db = des_db._raw_query("SELECT id, name FROM \"Node\" WHERE name = '" + str(node_sender) + "' OR name = '" + str(node_listener) + "'")
    for res in res_db:
        dict_name_id[res.get('name')] = res.get('id')

    res_db = des_db._raw_query("SELECT cot_max FROM \"CORResultsKernel\" WHERE id_sender = " \
        + str(dict_name_id[node_sender]) + " AND id_listener = " + str(dict_name_id[node_listener]))

    cot_m = 0

    for res in res_db:
        cot_m = res.get('cot_max')

    if cot_m > CO_THRESHOLD:
        return 1
    else:
        return 0


def get_interference(graph, e1, e2):
    """Returns the interference value for the given edges according to the
    channel occupancy measurement approach. The value can either be 0 (edges 
    do not interfere), or 1 (edges do interfere), since the interference model
    is only binary.
    
    """
    # if this is the first call, retrieve all CO measurements from the database
    # syslog(LOG_DEBUG, str(datetime.now()) + "### interference check")
    if len(node_id) == 0:
        # syslog(LOG_DEBUG, str(datetime.now()) + "### start co caching")
        init()
        # syslog(LOG_DEBUG, str(datetime.now()) + "### end co caching")

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
    # Note, we assume here that all channels are orthogonal
    if channel1 != channel2:
        return 0

    # co_values are taken from the CO matrix
    co_values = list()
    co_values.append(cot_max[e1[0] + '-' + e2[0]])
    co_values.append(cot_max[e1[0] + '-' + e2[1]])
    co_values.append(cot_max[e1[1] + '-' + e2[0]])
    co_values.append(cot_max[e1[1] + '-' + e2[1]])

    # syslog(LOG_DEBUG, "CO values: %s" % str(co_values))

    # if one of the values is above the threshold, the two edges potentially 
    # interfere with each other
    if max(co_values) > CO_THRESHOLD:
        return 1
    else:
        return 0
