// Copyright 2026, Yumeng Liu @ USTC
// op_2: Metro Shortest Path — GUI implementation (provided)

#include "metro_gui.h"
#include "metro_algorithm.h"
#include <opencv2/opencv.hpp>
#include <algorithm>
#include <cctype>
#include <cmath>
#include <filesystem>
#include <map>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

static bool findDataRoot(const std::string& root, std::vector<std::string>& out_cities) {
    out_cities.clear();
    std::error_code ec;
    fs::path root_path(root);
    if (!fs::exists(root_path, ec) || !fs::is_directory(root_path, ec)) return false;
    for (const auto& entry : fs::directory_iterator(root_path, ec)) {
        if (ec || !entry.is_directory()) continue;
        for (const auto& f : fs::directory_iterator(entry.path(), ec)) {
            if (ec) continue;
            std::string name = f.path().filename().string();
            if (name.find("adjacency-distance.csv") != std::string::npos) {
                out_cities.push_back(entry.path().filename().string());
                break;
            }
        }
    }
    return !out_cities.empty();
}

static std::map<int, std::string> loadStationMap(const std::string& path) {
    std::map<int, std::string> stations;
    std::ifstream f(path);
    if (!f) return stations;
    std::string line;
    std::getline(f, line);  // skip header
    while (std::getline(f, line)) {
        std::istringstream ss(line);
        std::string id_s, name;
        if (!std::getline(ss, id_s, '\t')) continue;
        if (!std::getline(ss, name, '\t')) continue;
        stations[std::stoi(id_s)] = name;
    }
    return stations;
}

static Graph loadGraph(const std::string& csv_path, const std::vector<std::string>& names) {
    Graph G(names);
    int n = (int)names.size();
    std::ifstream f(csv_path);
    if (!f) return G;
    for (int i = 0; i < n; i++) {
        std::string line;
        if (!std::getline(f, line)) break;
        std::istringstream ss(line);
        std::string tok;
        int j = 0;
        while (std::getline(ss, tok, ',') && j < n) {
            try {
                double val = std::stod(tok);
                if (j > i && val > 0.0)
                    G.addEdge(i, j, val);
            } catch (...) {}
            j++;
        }
    }
    return G;
}

static const int GRAPH_W = 900;
static const int GRAPH_H = 700;
static const int PANEL_W = 320;
static const int WIN_H = GRAPH_H;
static const int WIN_W = GRAPH_W + PANEL_W;

static cv::Point toPixel(float gx, float gy) {
    return {int(gx * GRAPH_W), int(gy * GRAPH_H)};
}

static std::vector<std::pair<float, float>> springLayout(const Graph* G,
                                                        unsigned seed = 42,
                                                        int iters = 60) {
    int n = G->numNodes();
    if (n <= 0) return {};
    std::vector<float> px(n), py(n);
    unsigned rng = seed;
    auto rand01 = [&]() -> float {
        rng = rng * 1664525u + 1013904223u;
        return (rng & 0x7FFFFFFFu) / float(0x7FFFFFFFu);
    };
    for (int i = 0; i < n; i++) { px[i] = rand01(); py[i] = rand01(); }

    float k = std::sqrt(1.0f / std::max(n, 1));
    float temp = 1.0f;

    for (int it = 0; it < iters; it++) {
        std::vector<float> dx(n, 0.f), dy(n, 0.f);
        for (int u = 0; u < n; u++) {
            for (int v = u + 1; v < n; v++) {
                float ex = px[u] - px[v], ey = py[u] - py[v];
                float d = std::max(std::hypot(ex, ey), 0.001f);
                float f = k * k / d;
                dx[u] += ex / d * f; dy[u] += ey / d * f;
                dx[v] -= ex / d * f; dy[v] -= ey / d * f;
            }
        }
        for (int u = 0; u < n; u++) {
            for (const Edge& e : G->neighbors(u)) {
                int v = e.to;
                if (v <= u) continue;
                float ex = px[u] - px[v], ey = py[u] - py[v];
                float d = std::max(std::hypot(ex, ey), 0.001f);
                float f = d * d / k;
                dx[u] -= ex / d * f; dy[u] -= ey / d * f;
                dx[v] += ex / d * f; dy[v] += ey / d * f;
            }
        }
        for (int u = 0; u < n; u++) {
            float mag = std::max(std::hypot(dx[u], dy[u]), 0.001f);
            float s = std::min(temp, mag) / mag;
            px[u] += dx[u] * s; py[u] += dy[u] * s;
        }
        temp *= 0.92f;
    }

    float xmin = *std::min_element(px.begin(), px.end());
    float xmax = *std::max_element(px.begin(), px.end());
    float ymin = *std::min_element(py.begin(), py.end());
    float ymax = *std::max_element(py.begin(), py.end());
    float xs = std::max(xmax - xmin, 1e-6f);
    float ys = std::max(ymax - ymin, 1e-6f);

    std::vector<std::pair<float, float>> pos(n);
    for (int i = 0; i < n; i++)
        pos[i] = {(px[i] - xmin) / xs * 0.9f + 0.05f,
                  (py[i] - ymin) / ys * 0.9f + 0.05f};
    return pos;
}

static MetroGui* g_gui = nullptr;

void onMouse(int event, int x, int y, int, void* ud) {
    if (event != cv::EVENT_LBUTTONDOWN) return;
    MetroGui* gui = reinterpret_cast<MetroGui*>(ud);
    if (x >= GRAPH_W || y >= GRAPH_H) return;

    int id = gui->nearestNode(x, y);
    if (id < 0) return;

    gui->onMouseSelect(id);
}

// MetroGui 实现

MetroGui::MetroGui() : graph_(nullptr) {}

MetroGui::~MetroGui() {
    delete graph_;
    graph_ = nullptr;
}

int MetroGui::nearestNode(int px, int py) const {
    if (pos_.empty() || !graph_ || graph_->numNodes() == 0) return -1;
    float gx = px / float(GRAPH_W);
    float gy = py / float(GRAPH_H);
    int best = -1;
    float best_d = 1e9f;
    for (int i = 0; i < graph_->numNodes(); i++) {
        float dx = pos_[i].first - gx;
        float dy = pos_[i].second - gy;
        float d = dx * dx + dy * dy;
        if (d < best_d) { best_d = d; best = i; }
    }
    return best;
}

void MetroGui::onMouseSelect(int id) {
    int mode = click_cnt_ % 3;
    if (mode == 0) {
        src_id_ = id;
        path_ = Path{};
        std::cout << "Source: " << graph_->nodeName(id) << "\n";
    } else if (mode == 1) {
        dst_id_ = id;
        path_ = Path{};
        std::cout << "Dest  : " << graph_->nodeName(id) << "\n";
    } else {
        src_id_ = dst_id_ = -1;
        path_ = Path{};
        click_cnt_ = -1;
    }
    click_cnt_++;
}

void MetroGui::loadCity(int idx) {
    if (idx < 0 || idx >= (int)cities_.size()) return;
    city_idx_ = idx;
    src_id_ = dst_id_ = -1;
    click_cnt_ = 0;
    path_ = Path{};

    std::string dir = data_root_ + "/" + cities_[idx];
    std::vector<cv::String> tsvs, csvs;
    cv::glob(dir + "/*station-id-map.tsv", tsvs, false);
    cv::glob(dir + "/*adjacency-distance.csv", csvs, false);
    if (tsvs.empty() || csvs.empty()) {
        std::cerr << "Data files not found in " << dir << "\n";
        return;
    }

    auto stations = loadStationMap(tsvs[0]);
    int n = (int)stations.size();
    std::vector<std::string> names(n);
    for (auto& [id, name] : stations) {
        if (id >= 1 && id <= n) names[id - 1] = name;
    }
    delete graph_;
    graph_ = new Graph(loadGraph(csvs[0], names));

    std::cout << "Loaded " << cities_[idx] << ": "
              << n << " stations, " << graph_->numEdges()
              << " edges. Computing layout...\n" << std::flush;
    pos_ = springLayout(graph_);
    std::cout << "Layout done.\n";
}

void MetroGui::findPath() {
    if (!graph_ || src_id_ < 0 || dst_id_ < 0 || src_id_ == dst_id_) return;
    path_ = dijkstra(graph_, src_id_, dst_id_);
    if (path_.node_ids.empty()) {
        std::cout << "No path found.\n";
    } else {
        std::cout << "Path: " << graph_->nodeName(src_id_) << " -> " << graph_->nodeName(dst_id_)
                  << "  dist=" << path_.total_cost << " km  stops=" << path_.node_ids.size() << "\n";
    }
}

void MetroGui::redraw() {
    cv::Mat area = canvas_(cv::Rect(0, 0, GRAPH_W, GRAPH_H));
    area.setTo(cv::Scalar(245, 245, 245));

    if (!graph_ || graph_->numNodes() == 0 || pos_.empty()) {
        cv::putText(area, "Usage: ./op2_template [data_dir] [city]",
                    cv::Point(GRAPH_W / 2 - 200, GRAPH_H / 2),
                    cv::FONT_HERSHEY_SIMPLEX, 0.6,
                    cv::Scalar(120, 120, 120), 1, cv::LINE_AA);
    } else {
        cv::putText(area, cities_[city_idx_] + " Metro Network",
                    cv::Point(8, 22), cv::FONT_HERSHEY_SIMPLEX, 0.65,
                    cv::Scalar(60, 60, 60), 1, cv::LINE_AA);

        for (int u = 0; u < graph_->numNodes(); u++) {
            for (const Edge& e : graph_->neighbors(u)) {
                int v = e.to;
                if (v <= u) continue;
                cv::line(area, toPixel(pos_[u].first, pos_[u].second),
                               toPixel(pos_[v].first, pos_[v].second),
                         cv::Scalar(185, 185, 185), 1, cv::LINE_AA);
            }
        }

        if (path_.node_ids.size() > 1) {
            for (int i = 0; i + 1 < (int)path_.node_ids.size(); i++) {
                int u = path_.node_ids[i], v = path_.node_ids[i + 1];
                cv::line(area, toPixel(pos_[u].first, pos_[u].second),
                               toPixel(pos_[v].first, pos_[v].second),
                         cv::Scalar(50, 50, 220), 3, cv::LINE_AA);
            }
        }

        for (int i = 0; i < graph_->numNodes(); i++) {
            cv::Point p = toPixel(pos_[i].first, pos_[i].second);
            cv::circle(area, p, 4, cv::Scalar(144, 198, 248), cv::FILLED, cv::LINE_AA);
            cv::circle(area, p, 4, cv::Scalar(21, 101, 192), 1, cv::LINE_AA);
        }

        if (!path_.node_ids.empty()) {
            for (int id : path_.node_ids) {
                cv::Point p = toPixel(pos_[id].first, pos_[id].second);
                cv::circle(area, p, 5, cv::Scalar(200, 200, 255), cv::FILLED, cv::LINE_AA);
                cv::circle(area, p, 5, cv::Scalar(30, 30, 180), 1, cv::LINE_AA);
                std::string nm = graph_->nodeName(id);
                if (nm.size() > 14) nm = nm.substr(0, 12) + "..";
                cv::putText(area, nm, p + cv::Point(7, -4),
                            cv::FONT_HERSHEY_SIMPLEX, 0.3,
                            cv::Scalar(40, 40, 160), 1, cv::LINE_AA);
            }
        }

        auto marker = [&](int id, cv::Scalar fill, cv::Scalar border, const char* lbl) {
            if (id < 0 || id >= graph_->numNodes()) return;
            cv::Point p = toPixel(pos_[id].first, pos_[id].second);
            cv::circle(area, p, 9, fill, cv::FILLED, cv::LINE_AA);
            cv::circle(area, p, 9, border, 2, cv::LINE_AA);
            cv::putText(area, lbl, p + cv::Point(-5, 5),
                        cv::FONT_HERSHEY_SIMPLEX, 0.4,
                        cv::Scalar(255, 255, 255), 1, cv::LINE_AA);
        };
        marker(src_id_, cv::Scalar(46, 139, 46), cv::Scalar(0, 80, 0), "S");
        marker(dst_id_, cv::Scalar(40, 100, 230), cv::Scalar(0, 40, 180), "D");
    }

    cv::Mat panel = canvas_(cv::Rect(GRAPH_W, 0, PANEL_W, WIN_H));
    panel.setTo(cv::Scalar(30, 30, 30));

    auto text = [&](const std::string& t, int y,
                    cv::Scalar col = cv::Scalar(200, 200, 200), double sc = 0.48) {
        cv::putText(panel, t, cv::Point(10, y), cv::FONT_HERSHEY_SIMPLEX,
                    sc, col, 1, cv::LINE_AA);
    };

    int y = 28;
    text("Metro Planner", y, cv::Scalar(100, 220, 100), 0.60); y += 34;

    if (!cities_.empty() && graph_) {
        text("City: " + cities_[city_idx_], y, cv::Scalar(180, 220, 255), 0.52); y += 22;
        text("Stations: " + std::to_string(graph_->numNodes()), y); y += 20;
        text("Edges   : " + std::to_string(graph_->numEdges()), y); y += 32;
    }

    text("[ Selection ]", y, cv::Scalar(160, 160, 100)); y += 22;
    std::string src_nm = (src_id_ >= 0 && graph_) ? graph_->nodeName(src_id_) : "(click to set)";
    std::string dst_nm = (dst_id_ >= 0 && graph_) ? graph_->nodeName(dst_id_) : "(click to set)";
    if (src_nm.size() > 24) src_nm = src_nm.substr(0, 22) + "..";
    if (dst_nm.size() > 24) dst_nm = dst_nm.substr(0, 22) + "..";
    text("From: " + src_nm, y, cv::Scalar(80, 200, 80)); y += 20;
    text("  To: " + dst_nm, y, cv::Scalar(80, 140, 255)); y += 32;

    if (!path_.node_ids.empty()) {
        char buf[32];
        snprintf(buf, sizeof(buf), "%.3f", path_.total_cost);
        text("[ Result ]", y, cv::Scalar(160, 160, 100)); y += 22;
        text(std::string("Dist : ") + buf + " km", y, cv::Scalar(255, 120, 80)); y += 20;
        text("Stops: " + std::to_string((int)path_.node_ids.size()), y); y += 22;
        text("Route:", y); y += 18;
        for (int id : path_.node_ids) {
            std::string nm = graph_->nodeName(id);
            if (nm.size() > 26) nm = nm.substr(0, 24) + "..";
            text("  " + nm, y, cv::Scalar(200, 180, 150), 0.42); y += 16;
            if (y > WIN_H - 90) { text("  (more...)", y); break; }
        }
    }

    y = WIN_H - 105;
    text("[ Keys ]", y, cv::Scalar(110, 110, 110)); y += 18;
    text("Click: set src / dst", y, cv::Scalar(130, 130, 130), 0.42); y += 15;
    text("3rd click: reset", y, cv::Scalar(130, 130, 130), 0.42); y += 15;
    text("Space/Enter: find", y, cv::Scalar(130, 130, 130), 0.42); y += 15;
    text("r: reset  q: quit", y, cv::Scalar(130, 130, 130), 0.42);

    cv::imshow("Metro Planner", canvas_);
}

// Resolve city idx from argv: "Barcelona" -> index, or "0" -> 0
static int resolveCityIdx(const std::vector<std::string>& cities, const char* arg) {
    if (!arg || !*arg) return 0;
    if (cities.empty()) return 0;
    try {
        int idx = std::stoi(arg);
        if (idx >= 0 && idx < (int)cities.size()) return idx;
    } catch (...) {}
    std::string want(arg);
    for (size_t i = 0; i < want.size(); i++)
        want[i] = (char)std::tolower((unsigned char)want[i]);
    for (size_t i = 0; i < cities.size(); i++) {
        std::string c = cities[i];
        for (size_t j = 0; j < c.size(); j++)
            c[j] = (char)std::tolower((unsigned char)c[j]);
        if (c == want) return (int)i;
    }
    return 0;
}

int MetroGui::run(int argc, char* argv[]) {
    const char* data_arg = nullptr;
    const char* city_arg = nullptr;
    if (argc > 1) {
        std::error_code ec;
        if (fs::exists(argv[1], ec) && fs::is_directory(argv[1], ec))
            data_arg = argv[1];
        else
            city_arg = argv[1];
    }
    if (argc > 2) {
        data_arg = argv[1];
        city_arg = argv[2];
    }

    if (data_arg && data_arg[0]) {
        data_root_ = data_arg;
    } else {
        for (const char* root : {"../../data", "../data", "data"}) {
            if (findDataRoot(root, cities_)) {
                data_root_ = root;
                break;
            }
        }
        if (data_root_.empty()) {
            std::cerr << "No city data found. Usage: ./op2_template [data_dir] [city]\n"
                      << "  city: name (e.g. Barcelona) or index (0,1,...)\n";
            return 1;
        }
    }
    g_gui = this;

    if (cities_.empty()) {
        if (!findDataRoot(data_root_, cities_)) {
            std::cerr << "No city data found in " << data_root_ << "\n";
            return 1;
        }
    }
    std::sort(cities_.begin(), cities_.end());
    cities_.erase(std::unique(cities_.begin(), cities_.end()), cities_.end());
    std::cout << "Found " << cities_.size() << " cities.\n";

    city_idx_ = resolveCityIdx(cities_, city_arg);
    std::cout << "Selected city: " << cities_[city_idx_] << " (index " << city_idx_ << ")\n";

    canvas_ = cv::Mat(WIN_H, WIN_W, CV_8UC3);

    cv::namedWindow("Metro Planner", cv::WINDOW_AUTOSIZE);
    cv::setMouseCallback("Metro Planner", onMouse, this);

    loadCity(city_idx_);
    redraw();

    while (true) {
        int key = cv::waitKey(30) & 0xFF;
        if (key == 27 || key == 'q') break;
        if (key == ' ' || key == '\r' || key == '\n') {
            findPath();
            redraw();
        }
        if (key == 'r') {
            src_id_ = dst_id_ = -1;
            click_cnt_ = 0;
            path_ = Path{};
            redraw();
        }
    }
    g_gui = nullptr;
    return 0;
}
