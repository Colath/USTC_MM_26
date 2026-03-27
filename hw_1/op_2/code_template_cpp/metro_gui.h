// Copyright 2026, Yumeng Liu @ USTC
// op_2: Metro Shortest Path — GUI module
// Deps: OpenCV, metro_algorithm.h

#ifndef METRO_GUI_H
#define METRO_GUI_H

#include "metro_algorithm.h"
#include <string>
#include <vector>
#include <opencv2/core.hpp>

class MetroGui {
public:
    MetroGui();
    ~MetroGui();

    int run(int argc, char* argv[]);

private:
    Graph* graph_;  // 私有指针，由本类负责 new/delete

    std::string data_root_;
    std::vector<std::string> cities_;
    int city_idx_ = 0;
    std::vector<std::pair<float, float>> pos_;
    int src_id_ = -1, dst_id_ = -1;
    int click_cnt_ = 0;
    Path path_;
    cv::Mat canvas_;

    void loadCity(int idx);
    void redraw();
    void findPath();
    int nearestNode(int px, int py) const;
    void onMouseSelect(int id);

    friend void onMouse(int event, int x, int y, int, void*);
};

#endif
