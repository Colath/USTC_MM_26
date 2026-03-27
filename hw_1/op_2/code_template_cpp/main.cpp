// Copyright 2026, Yumeng Liu @ USTC
// op_2: Metro Shortest Path — Student Template
//
// Deps  : OpenCV, STL
// Usage : ./op2_template [data_dir] [city]
//         data_dir defaults to ../../data (from build/)
//         city: name (e.g. Barcelona) or index (0,1,...), defaults to first
//
// TODO: Implement in metro_algorithm.cpp:
//   [1/3] Graph::addEdge(u, v, w)  — add undirected edge
//   [2/3] Graph::numEdges()        — return edge count
//   [3/3] dijkstra(G, src, dst)   — shortest path
//
// GUI: Left-click (src/dst/reset), Space (find path), r (reset), q (quit)

#include "metro_gui.h"

int main(int argc, char* argv[]) {
    MetroGui gui;
    return gui.run(argc, argv);
}
