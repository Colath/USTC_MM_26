// Copyright 2026, Yumeng Liu @ USTC
// op_2: Metro Shortest Path — TODO: implement addEdge, numEdges, dijkstra

#include "metro_algorithm.h"
#include <algorithm>
#include <limits>
#include <queue>

// Empty graph: 0 nodes, no slots needed
Graph::Graph() : n_(0), nodes_(0) {}

// n = names.size(), nodes_[i].name = names[i]
Graph::Graph(const std::vector<std::string>& names) : n_((int)names.size()), nodes_(names.size()) {
    for (size_t i = 0; i < names.size(); i++)
        nodes_[i].name = names[i];
}

Graph::~Graph() {}

// TODO [1/3]: Add an undirected weighted edge between u and v.
void Graph::addEdge(int u, int v, double w) {
    (void)u; (void)v; (void)w;
    // TODO: implement
}

// TODO [2/3]: Return the total number of undirected edges.
int Graph::numEdges() const {
    // TODO: implement
    return 0;
}

// TODO [3/3]: Dijkstra shortest path from src to dst.
Path dijkstra(const Graph* G, int src, int dst) {
    (void)G; (void)src; (void)dst;
    // TODO: implement
    return {std::numeric_limits<double>::infinity(), {}};
}
