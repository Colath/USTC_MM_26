// Copyright 2026, Yumeng Liu @ USTC
// op_2: Metro Shortest Path — Algorithm module (TODO: implement in metro_algorithm.cpp)
// No OpenCV dependency.

#ifndef METRO_ALGORITHM_H
#define METRO_ALGORITHM_H

#include <stdexcept>
#include <string>
#include <vector>

struct Edge {
    int to;
    double weight;
};

struct Node {
    std::string name;  // station name
    std::vector<Edge> edges;
};

struct Path {
    double total_cost;
    std::vector<int> node_ids;
};

class Graph {
public:
    Graph();  // empty graph
    Graph(const std::vector<std::string>& names);  // n = names.size()
    ~Graph();
    void addEdge(int u, int v, double w);
    int numEdges() const;
    int numNodes() const { return n_; }
    const std::vector<Edge>& neighbors(int u) const {
        if (u < 0 || u >= n_ || (size_t)u >= nodes_.size())
            throw std::out_of_range("neighbors: node index out of range");
        return nodes_[u].edges;
    }
    const std::string& nodeName(int u) const {
        if (u < 0 || u >= n_ || (size_t)u >= nodes_.size())
            throw std::out_of_range("nodeName: index out of range");
        return nodes_[u].name;
    }

private:
    int n_;
    std::vector<Node> nodes_;
};

Path dijkstra(const Graph* G, int src, int dst);

#endif
