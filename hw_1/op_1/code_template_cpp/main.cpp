// Copyright 2026, Yumeng Liu @ USTC
// op_1: Seam Carving — Student Template
//
// Deps  : OpenCV, STL
// Usage : ./op1_template [image_path]
//
// TODO: Implement seamCarveImage() below.

#include <opencv2/opencv.hpp>
#include <algorithm>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

// ============================================================
// TODO: Implement seamCarveImage
// ============================================================
//
// Seam carving to resize img to (target_rows, target_cols).
//
// You may define any helper functions above this function.
//
// Args:
//   img         — input BGR image (CV_8UC3)
//   target_rows — target height in pixels
//   target_cols — target width  in pixels
//
// Returns: resized image of size (target_rows, target_cols)
cv::Mat seamCarveImage(cv::Mat img, int target_rows, int target_cols) {
    // TODO: replace with your implementation
    (void)target_rows; (void)target_cols;
    return img;
}

// ============================================================
// GUI
// ============================================================

static cv::Mat g_src, g_dst;
static int g_col_pct = 100, g_row_pct = 100;

static void refresh() {
    const int PAD = 20, HDR = 36;
    int h = g_src.rows + HDR;
    int w = g_src.cols;
    if (!g_dst.empty()) {
        h = std::max(g_src.rows, g_dst.rows) + HDR;
        w = g_src.cols + g_dst.cols + PAD;
    }

    cv::Mat canvas(h, w, CV_8UC3, cv::Scalar(45, 45, 45));
    g_src.copyTo(canvas(cv::Rect(0, HDR, g_src.cols, g_src.rows)));
    cv::putText(canvas,
        "Input [" + std::to_string(g_src.cols) + " x " + std::to_string(g_src.rows) + "]",
        cv::Point(4, HDR - 10), cv::FONT_HERSHEY_SIMPLEX, 0.55,
        cv::Scalar(210, 210, 210), 1, cv::LINE_AA);

    if (!g_dst.empty()) {
        int xoff = g_src.cols + PAD;
        g_dst.copyTo(canvas(cv::Rect(xoff, HDR, g_dst.cols, g_dst.rows)));
        cv::putText(canvas,
            "Result [" + std::to_string(g_dst.cols) + " x " + std::to_string(g_dst.rows) + "]",
            cv::Point(xoff + 4, HDR - 10), cv::FONT_HERSHEY_SIMPLEX, 0.55,
            cv::Scalar(210, 210, 210), 1, cv::LINE_AA);
    } else {
        cv::putText(canvas, "Adjust sliders then press [Space]",
            cv::Point(10, h / 2 + 10), cv::FONT_HERSHEY_SIMPLEX, 0.65,
            cv::Scalar(80, 220, 80), 2, cv::LINE_AA);
    }
    cv::imshow("Seam Carving", canvas);
}

int main(int argc, char* argv[]) {
    std::string path;
    if (argc > 1) {
        path = argv[1];
        g_src = cv::imread(path, cv::IMREAD_COLOR);
    } else {
        for (const char* p : {"../figs/original.png", "../../figs/original.png"}) {
            g_src = cv::imread(p, cv::IMREAD_COLOR);
            if (!g_src.empty()) { path = p; break; }
        }
        if (g_src.empty()) path = "../figs/original.png";
    }
    if (g_src.empty()) {
        std::cerr << "Cannot open image: " << path << "\n"
                  << "Usage: op1_template [image_path]\n";
        return 1;
    }

    std::cout << "Image: " << g_src.cols << " x " << g_src.rows << " px\n"
              << "Keys : [Space] run  [s] save  [r] reset  [q/Esc] quit\n";

    cv::namedWindow("Seam Carving", cv::WINDOW_NORMAL);
    int win_w = std::min(g_src.cols * 2 + 140, 1600);
    cv::resizeWindow("Seam Carving", win_w, g_src.rows + 120);

    cv::createTrackbar("Col %", "Seam Carving", &g_col_pct, 200);
    cv::createTrackbar("Row %", "Seam Carving", &g_row_pct, 200);
    cv::setTrackbarPos("Col %", "Seam Carving", 100);
    cv::setTrackbarPos("Row %", "Seam Carving", 100);

    refresh();

    while (true) {
        int key = cv::waitKey(30) & 0xFF;
        if (key == 27 || key == 'q') break;

        if (key == ' ') {
            int col_pct = std::max(10, g_col_pct);
            int row_pct = std::max(10, g_row_pct);
            int tgt_w   = std::max(1, g_src.cols * col_pct / 100);
            int tgt_h   = std::max(1, g_src.rows * row_pct / 100);
            std::cout << "Running: " << g_src.cols << "x" << g_src.rows
                      << " -> " << tgt_w << "x" << tgt_h << " ...\n";
            g_dst = seamCarveImage(g_src.clone(), tgt_h, tgt_w);
            std::cout << "Done.\n";
            refresh();
        }

        if (key == 'r') {
            g_dst = cv::Mat();
            cv::setTrackbarPos("Col %", "Seam Carving", 100);
            cv::setTrackbarPos("Row %", "Seam Carving", 100);
            refresh();
        }

        if (key == 's' && !g_dst.empty()) {
            cv::imwrite("result.png", g_dst);
            std::cout << "Saved result.png\n";
        }
    }
    return 0;
}
