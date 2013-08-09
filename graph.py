#!/usr/bin/python
"""
DES-CHAN: A Framework for Channel Assignment Algorithms for Testbeds

This module provides a class to represent network graphs and conflict graphs.

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

import re
import sys


class Graph:

    def __init__(self, vertices=[]):
        # initialize internal data structures
        self.values = dict()
        self.distances = dict()
        # set vertex names and distances
        for vertex in vertices:
            self.add_vertex(vertex)


    def add_vertex(self, new_vertex):
        """Adds the given vertex to the graph.

        """
        # do nothing if vertex already exists
        if new_vertex in self.get_vertices():
            return
        # otherwise set up data structures for new vertex
        self.values[new_vertex] = dict()
        self.distances[new_vertex] = dict()
        for old_vertex in self.get_vertices():
            self.set_edge_value((old_vertex, new_vertex), None, False)
            self.set_distance(old_vertex, new_vertex, sys.maxint)
        # distance to itself is 0
        self.set_distance(new_vertex, new_vertex, 0)


    def remove_vertex(self, vertex):
        """Removes the given vertex from the graph.

        """
        del self.values[vertex]
        del self.distances[vertex]
        for v in self.get_vertices():
            del self.values[v][vertex]
            del self.distances[v][vertex]


    def get_vertices(self):
        """Returns a list that contains all vertices of the graph.

        """
        return set(self.values.keys())


    def set_edge_value(self, edge, value, update=True):
        """Sets the value of the given edge. The edge is represented by a tuple
        of two vertices.

        """
        v1, v2 = edge
        self.values[v1][v2] = value
        # we implement an undirected graph
        self.values[v2][v1] = value
        # update distance information
        # None, "", False, and 0 correspond to no edge
        if value:
            self.set_distance(v1, v2, 1)
            # other shortest paths may have changed
            if update:
                self.update_distances()


    def set_distance(self, v1, v2, d):
        """Sets the distance between the two vertices.

        """
        self.distances[v1][v2] = d
        # we implement an undirected graph
        self.distances[v2][v1] = d


    def get_edge_value(self, edge):
        """Returns the value of the given edge. The edge is represented by a tuple
        of two vertices.

        """
        v1, v2 = edge
        return self.values[v1][v2]


    def get_distance(self, v1, v2):
        """Returns the distance between v1 and v2.

        """
        return self.distances[v1][v2]


    def get_edges(self, get_all=False):
        """Returns a dictionary that contains all edges as keys and the
        corresponding edge values as values. Only edges that have a value are
        returned. By default the graph is assumed to be undirected. If the
        optional parameter get_all is True, all vertices are returned.

        """
        edges = dict()
        remaining_vertices = self.get_vertices()
        for v1 in self.get_vertices():
            for v2 in remaining_vertices:
                value = self.get_edge_value((v1, v2))
                # None, "", False, and 0 correspond to no edge
                if value:
                    edges[(v1, v2)] = value
            # graph is assumed to be undirected, therefore discard
            # duplicate edges if not explicitly requested
            if not get_all:
                remaining_vertices.remove(v1)
        return edges


    def merge(self, graph):
        """Merges the current graph with the specified graph. The new graph
        contains the union of both vertex sets and the corresponding edge
        values.

        """
        # add missing vertices
        for vertex in graph.get_vertices() - self.get_vertices():
            self.add_vertex(vertex)
        # set edge values
        for edge, edge_value in graph.get_edges().items():
            self.set_edge_value(edge, edge_value, False)
        self.update_distances()


    def get_adjacency_matrix(self):
        """Returns the graph's adjacency matrix as a formatted string.

        """
        vertices = self.values.keys()
        maxlen = 4
        # get maximum length of vertex names for proper layout
        for vertex in vertices:
            if len(str(vertex)) > maxlen:
                maxlen = len(str(vertex))
        # print column heads
        matrix = "".rjust(maxlen) + " |"
        for vertex in vertices:
            matrix += " " + str(vertex).rjust(maxlen) + " |"
        # print without trailing |
        matrix = matrix[:-1] + "\n"
        # generate row separator
        matrix += "-" * maxlen + "-+"
        for i in range(len(vertices)):
            matrix += "-" + "-" * maxlen + "-+"
        # print without trailing +
        matrix = matrix[:-1] + "\n"
        # print rows
        for v1 in vertices:
            matrix += str(v1).ljust(maxlen) + " |"
            for v2 in vertices:
                matrix += " " + self._get_edge_value_as_text((v1, v2)).rjust(maxlen) + " |"
            # print without trailing |
            matrix = matrix[:-1] + "\n"
        return matrix
    

    def get_graphviz(self, label=""):
        """Returns a string representation of the graph in the dot language from
        the graphviz project.

        """
        left_vertices = set(self.values.keys())
        graph = "Graph G {\n"
        if label != "":
            graph += "\tgraph [label = \"%s\", labelloc=t]\n" % label
        for v1 in self.values.keys():
            for v2 in left_vertices:
                if self.get_edge_value((v1, v2)):
                    graph += "\t\"" + str(v1) + "\" -- \"" + str(v2) + "\" "
                    graph += "[label = \"" + str(self.get_edge_value((v1, v2))) + "\"]\n"
            # undirected graph, therefore discard double connections
            left_vertices.remove(v1)
        graph += "}\n"
        return graph


    def write_to_file(self, file_name, use_graphviz=False):
        """Writes a textual representation of the graph to the specified file.
        If the optional parameter use_graphviz is True, the graph is represented
        in the dot language from the graphviz project.

        """
        file = open(file_name, 'w')
        if use_graphviz:
            file.write(self.get_graphviz())
        else:
            file.write(self.get_adjacency_matrix())
        file.close()


    def read_from_dotfile(self, file_name):
        """Reads the graph from a graphviz dot file.

        """
        file = open(file_name, 'r')
        # clear current data
        self.__init__()
        # match following lines
        # "t9-035" -- "t9-146" [label = "1"]
        edge_re = re.compile('\s*"(.+)" -- "(.+)" \[label = "(.+)"\]')
        for line in file:
            edge_ma = edge_re.match(line)
            if edge_ma:
                v1 = edge_ma.group(1)
                v2 = edge_ma.group(2)
                value = edge_ma.group(3)
                self.add_vertex(v1)
                self.add_vertex(v2)
                self.set_edge_value((v1, v2), value, False)
        file.close()
        self.update_distances()


    def read_from_file(self, file_name):
        """Reads the graph from a file containing an adjacency matrix as
        generated by get_adjacency_matrix() or write_to_file(). The dot format
        is not supported.

        """
        file = open(file_name, 'r')
        # line counter
        i = 0;
        vertices = list()
        for line in file:
            i += 1
            # first line contains the vertex names
            if i == 1:
                # first element is empty, therefore discard it
                for vertex in line.split("|")[1:]:
                    vertices.append(vertex.strip())
                # clear current data and set new vertices
                self.__init__(vertices)
            if i > 2:
                row = line.split("|")
                # first element is the vertex name
                v1 = row[0].strip()
                # remaining elements are edge values
                row = row[1:]
                for v2 in vertices:
                    value = row[vertices.index(v2)].strip()
                    if value == '':
                        value = None
                    self.set_edge_value((v1, v2), value, False)
        file.close()
        self.update_distances()


    def update_distances(self):
        """Updates the distance matrix with the number of hops between all
        vertex pairs.

        """
        # Floyd Warshall algorithm
        # calculate all shortest paths
        for k in self.get_vertices():
            remaining_vertices = self.get_vertices()
            for v1 in self.get_vertices():
                for v2 in remaining_vertices:
                    d = min(self.get_distance(v1, v2), 
                            self.get_distance(v1, k) + self.get_distance(k, v2))
                    self.set_distance(v1, v2, d)
                remaining_vertices.remove(v1)


    def get_neighbors(self, vertex):
        """Returns a set that contains all direct neighbors of the given vertex.

        """
        neighbors = set()
        for v1, v2 in self.get_edges().keys():
            if v1 == vertex:
                neighbors.add(v2)
            elif v2 == vertex:
                neighbors.add(v1)
        return neighbors


    def copy(self):
        """Returns a new Graph object that contains the same vertices and edges.

        """
        remaining_vertices = self.get_vertices()
        g = Graph(list(remaining_vertices))
        for v1 in self.get_vertices():
            for v2 in remaining_vertices:
                g.set_edge_value((v1, v2), self.get_edge_value((v1, v2)))
                g.set_distance(v1, v2, self.get_distance(v1, v2))
            remaining_vertices.remove(v1)
        return g


    def copy_fast(self):
        """Returns a new Graph object that contains the same vertices and edges.

        """
        remaining_vertices = self.get_vertices()
        g = Graph(list(remaining_vertices))
        e = self.get_edges()
        for (v1, v2), chans in self.get_edges().iteritems():
            g.set_edge_value((v1,v2), self.get_edge_value((v1, v2)), update=False)
            g.set_distance(v1, v2, self.get_distance(v1, v2))
        return g


    def _get_edge_value_as_text(self, edge):
        """Returns a textual representation of the value of the given edge. The
        edge is represented by a tuple of two vertices.

        """
        v1, v2 = edge
        if not self.values[v1][v2]:
            return ""
        else:
            return str(self.values[v1][v2])


class ConflictGraphVertex:
    
    def __init__(self, conflict_graph, nw_graph_edge):
        self.conflict_graph = conflict_graph
        self.nw_graph_edge = nw_graph_edge
        self.channels = None


    def __str__(self):
        return "%s_%s" % (self.nw_graph_edge)


    def get_channel(self):
        """Returns the channel of the link in the network graph that corresponds
        to this vertex.

        """
        return int(self.conflict_graph.network_graph.get_edge_value(self.nw_graph_edge))


    def set_channel(self, channel):
        """Sets the channel in the network graph and computes the resulting
        conflict graph.

        """
        # update network graph
        self.conflict_graph.network_graph.set_edge_value(self.nw_graph_edge,
                                                         str(channel))
        # update conflict graph
		# NOTE the change: We do not have to recalculate ALL edges, just the onces
        # adjacent to the changed one are enough! gives us O(n) instead of O(n*n)
        self.conflict_graph.update_edge(self)
        # self.conflict_graph.update_edges()


    def get_nw_graph_neighbor(self, node_name):
        """Returns the neigbor in the network graph corresponding to the link.

        """
        if node_name not in self.nw_graph_edge:
            return None
        if self.nw_graph_edge[0] == node_name:
            return self.nw_graph_edge[1]
        else:
            return self.nw_graph_edge[0]


class ConflictGraph(Graph):

    def __init__(self, network_graph, interference_model):
        # store the original network graph for later reference
        self.network_graph = network_graph
        self.interference_model = interference_model
        vertices = set()
        # each edge in the network graph corresponds to a vertex in the conflict
        # graph
        for edge in network_graph.get_edges().keys():
            vertices.add(ConflictGraphVertex(self, edge))
        # call constructor of the super-class with new vertex set
        Graph.__init__(self, vertices)
        # set edges according to interference model
        self.update_edges()


    def update_edges(self):
        """Updates all edges of the ConflictGraph regarding the current channel
        assignment and the applied interference model.

        """
        remaining_vertices = self.get_vertices()
        for v1 in self.get_vertices():
            for v2 in remaining_vertices:
                # get edge value according to the interference model
                value = self.interference_model.get_interference(self.network_graph,
                                                                 v1.nw_graph_edge,
                                                                 v2.nw_graph_edge)
                self.set_edge_value((v1, v2), value, False)
            # graph is undirected
            remaining_vertices.remove(v1)


    def update_edge(self, cg_vertex):
        """Updates all edges that are adjacent to the supplied cg_vertex.

        """
        remaining_vertices = self.get_vertices()
        for v2 in self.get_vertices():
            # get edge value according to the interference model
            value = self.interference_model.get_interference(self.network_graph,
                                                                 cg_vertex.nw_graph_edge,
                                                                 v2.nw_graph_edge)
            self.set_edge_value((cg_vertex, v2), value, False)


    def get_vertices_for_node(self, node_name):
        """Returns a set containing all vertices that correspond to links that
        are incident to the given node.

        """
        vertices = set()
        for vertex in self.get_vertices():
            if vertex.nw_graph_edge[0] == node_name or \
               vertex.nw_graph_edge[1] == node_name:
                vertices.add(vertex)
        return vertices


    def get_vertex(self, node1, node2):
        """Returns the vertex that corresponds to the link between the two given
        node names, or None, if such vertex does not exist.

        """
        for vertex in self.get_vertices():
            if (vertex.nw_graph_edge[0] == node1 and \
                vertex.nw_graph_edge[1] == node2) or \
               (vertex.nw_graph_edge[0] == node2 and \
                vertex.nw_graph_edge[1] == node1):
                return vertex
        return None


    def get_interference_sum(self):
        """Returns the overall interference which is calculated by summing up
        all edge values.

        """
        sum = 0
        for value in self.get_edges().values():
            sum += value
        return sum
    
    
    def get_vertex_names(self):
        vertex_names = set()
        for vertex in self.get_vertices():
            vertex_names.add(str(vertex))
        return vertex_names

    
    def update(self, network_graph):
        old_edges = self.network_graph.get_edges()
        new_edges = network_graph.get_edges()
        # do nothing if graphs are equal
        if new_edges == old_edges:
            return
        old_edges_keys = set(old_edges.keys())
        new_edges_keys = set(new_edges.keys())
        # assign new network graph
        self.network_graph = network_graph
        # update conflict graph
        for new_edge in new_edges_keys - old_edges_keys:
            # create a new conflict graph vertex for each new network graph edge
            self.add_vertex(ConflictGraphVertex(self, new_edge))
        for obsolete_edge in old_edges_keys - new_edges_keys:
            # remove conflict graph vertices for obsolete edges
            self.remove_vertex(self.get_vertex(obsolete_edge[0],
                                               obsolete_edge[1]))
        self.update_edges()


# this only runs if the module was *not* imported
if __name__ == '__main__':
    g = Graph(["a", "b", "c", "d", "e"])
    g.set_edge_value(("a", "b"), 40)
    g.set_edge_value(("b", "c"), 40)
    g.set_edge_value(("c", "d"), 40)
    g.set_edge_value(("d", "e"), 40)
    print g.get_adjacency_matrix()

