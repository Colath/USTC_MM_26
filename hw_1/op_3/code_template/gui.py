# Copyright 2026, Yumeng Liu @ USTC
"""
社交网络关键节点识别 —— 交互式 GUI 模块

基于 Tkinter + Matplotlib，提供：
  - 中心性可视化：节点大小/颜色编码中心性，top-k 高亮
  - 节点检查器：点击节点查看所有中心性得分
  - SIR 传播对比：影响力最大 vs 最小节点的逐步传播动画
"""

import math
import random
import tkinter as tk
from tkinter import ttk

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.figure import Figure
from matplotlib.patches import Patch

from network_algorithm import (
    Graph,
    betweenness_centrality,
    closeness_centrality,
    degree_centrality,
    pagerank,
    sir_simulation,
)

matplotlib.use("TkAgg")


# ============================================================
# 布局算法
# ============================================================


def spring_layout(
    G: Graph, iterations: int = 50, seed: int = 42
) -> dict[int, tuple[float, float]]:
    """Fruchterman-Reingold 力导向布局算法。"""
    rng = random.Random(seed)
    nodes = sorted(G.nodes)
    n = len(nodes)
    if n == 0:
        return {}

    pos = {v: (rng.uniform(-1, 1), rng.uniform(-1, 1)) for v in nodes}

    area = 4.0
    k = math.sqrt(area / n)
    t = 1.0
    dt = t / (iterations + 1)

    for _ in range(iterations):
        disp = {v: [0.0, 0.0] for v in nodes}

        for i, u in enumerate(nodes):
            for j in range(i + 1, n):
                v = nodes[j]
                dx = pos[u][0] - pos[v][0]
                dy = pos[u][1] - pos[v][1]
                dist = max(math.hypot(dx, dy), 0.01)
                f = k * k / dist
                fx, fy = f * dx / dist, f * dy / dist
                disp[u][0] += fx
                disp[u][1] += fy
                disp[v][0] -= fx
                disp[v][1] -= fy

        for u in nodes:
            for v in G.neighbors(u):
                if u < v:
                    dx = pos[u][0] - pos[v][0]
                    dy = pos[u][1] - pos[v][1]
                    dist = max(math.hypot(dx, dy), 0.01)
                    f = dist * dist / k
                    fx, fy = f * dx / dist, f * dy / dist
                    disp[u][0] -= fx
                    disp[u][1] -= fy
                    disp[v][0] += fx
                    disp[v][1] += fy

        for v in nodes:
            dx, dy = disp[v]
            dist = max(math.hypot(dx, dy), 0.01)
            scale = min(dist, t) / dist
            pos[v] = (pos[v][0] + dx * scale, pos[v][1] + dy * scale)

        t -= dt

    xs = [pos[v][0] for v in nodes]
    ys = [pos[v][1] for v in nodes]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_rng = x_max - x_min if x_max > x_min else 1.0
    y_rng = y_max - y_min if y_max > y_min else 1.0

    return {
        v: (2 * (pos[v][0] - x_min) / x_rng - 1,
            2 * (pos[v][1] - y_min) / y_rng - 1)
        for v in nodes
    }


# ============================================================
# GUI 主类
# ============================================================


class SocialNetworkApp:
    """基于 Tkinter 的社交网络关键节点分析交互界面。"""

    BG = "#f0f2f5"
    EDGE_CLR = "#c0c0c0"
    CMAP_NAME = "YlOrRd"
    SIR_CLR = {"S": "#42a5f5", "I": "#ef5350", "R": "#bdbdbd"}
    SIDEBAR_W = 350

    def __init__(self, graph: Graph):
        self.graph = graph
        self.pos = spring_layout(self.graph)

        self.centralities = {
            "Degree": degree_centrality(self.graph),
            "Closeness": closeness_centrality(self.graph),
            "Betweenness": betweenness_centrality(self.graph),
            "PageRank": pagerank(self.graph),
        }

        self.selected_node: int | None = None

        self._comp_best_hist: list[dict[int, str]] = []
        self._comp_worst_hist: list[dict[int, str]] = []
        self._comp_best_seed: int = 0
        self._comp_worst_seed: int = 0
        self._comp_metric: str = ""
        self._comp_avg_best: np.ndarray = np.array([])
        self._comp_avg_worst: np.ndarray = np.array([])
        self._anim_timer: str | None = None

        self._build_ui()
        self._draw_centrality()

    # ================================================================
    # UI 构建
    # ================================================================

    def _build_ui(self):
        self.root = tk.Tk()
        self.root.title("Social Network — Key Node Identification")
        self.root.configure(bg=self.BG)
        self.root.geometry("1500x900")

        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=0, minsize=self.SIDEBAR_W)
        self.root.rowconfigure(0, weight=1)

        canvas_frame = ttk.Frame(self.root)
        canvas_frame.grid(row=0, column=0, sticky="nsew")
        self.fig = Figure(figsize=(10, 8), dpi=100, facecolor=self.BG)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.mpl_connect("button_press_event", self._on_canvas_click)

        sidebar = ttk.Frame(self.root, width=self.SIDEBAR_W)
        sidebar.grid(row=0, column=1, sticky="nsew", padx=(0, 5), pady=5)
        sidebar.grid_propagate(False)

        self.notebook = ttk.Notebook(sidebar)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._build_centrality_tab()
        self._build_propagation_tab()
        self._build_inspector_tab()

    def _build_centrality_tab(self):
        tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab, text="  Centrality  ")

        ttk.Label(tab, text="Metric:", font=("", 11, "bold")).pack(anchor=tk.W)
        self.metric_var = tk.StringVar(value="Degree")
        cb = ttk.Combobox(
            tab,
            textvariable=self.metric_var,
            values=list(self.centralities.keys()),
            state="readonly",
        )
        cb.pack(fill=tk.X, pady=(0, 10))
        cb.bind("<<ComboboxSelected>>", lambda _: self._draw_centrality())

        ttk.Label(tab, text="Top-k:", font=("", 11, "bold")).pack(anchor=tk.W)
        self.topk_var = tk.IntVar(value=5)
        tk.Scale(
            tab,
            from_=1,
            to=15,
            orient=tk.HORIZONTAL,
            variable=self.topk_var,
            command=lambda _: self._draw_centrality(),
            bg=self.BG,
            highlightthickness=0,
        ).pack(fill=tk.X, pady=(0, 6))

        ttk.Label(tab, text="Rankings:", font=("", 11, "bold")).pack(
            anchor=tk.W, pady=(5, 2)
        )
        rf = ttk.Frame(tab)
        rf.pack(fill=tk.BOTH, expand=True)

        cols = ("rank", "node", "score")
        self.rank_tree = ttk.Treeview(rf, columns=cols, show="headings", height=20)
        self.rank_tree.heading("rank", text="#")
        self.rank_tree.heading("node", text="Node")
        self.rank_tree.heading("score", text="Score")
        self.rank_tree.column("rank", width=30, anchor=tk.CENTER)
        self.rank_tree.column("node", width=75, anchor=tk.CENTER)
        self.rank_tree.column("score", width=105, anchor=tk.CENTER)
        sb = ttk.Scrollbar(rf, orient=tk.VERTICAL, command=self.rank_tree.yview)
        self.rank_tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.rank_tree.pack(fill=tk.BOTH, expand=True)

    def _build_propagation_tab(self):
        tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab, text="  Propagation  ")

        ttk.Label(
            tab,
            text="Compare the highest vs lowest PageRank\n"
            "node as infection seed, step by step.",
            wraplength=300,
            font=("", 10),
        ).pack(anchor=tk.W, pady=(0, 10))

        pf = ttk.LabelFrame(tab, text="SIR Parameters", padding=6)
        pf.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(pf, text="β (infection rate):").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.beta_var = tk.DoubleVar(value=0.3)
        ttk.Entry(pf, textvariable=self.beta_var, width=8).grid(
            row=0, column=1, padx=5, pady=2
        )

        ttk.Label(pf, text="γ (recovery rate):").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        self.gamma_var = tk.DoubleVar(value=0.1)
        ttk.Entry(pf, textvariable=self.gamma_var, width=8).grid(
            row=1, column=1, padx=5, pady=2
        )

        ttk.Label(pf, text="Steps:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.steps_var = tk.IntVar(value=5)
        ttk.Entry(pf, textvariable=self.steps_var, width=8).grid(
            row=2, column=1, padx=5, pady=2
        )

        ttk.Button(
            tab, text="Run Comparison", command=self._run_comparison
        ).pack(fill=tk.X, pady=(4, 8))

        ctrl = ttk.LabelFrame(tab, text="Playback", padding=6)
        ctrl.pack(fill=tk.X, pady=(0, 8))

        self.step_slider_var = tk.IntVar(value=0)
        self.step_slider = tk.Scale(
            ctrl,
            from_=0,
            to=0,
            orient=tk.HORIZONTAL,
            variable=self.step_slider_var,
            command=lambda _: self._on_step_changed(),
            bg=self.BG,
            highlightthickness=0,
            state=tk.DISABLED,
        )
        self.step_slider.pack(fill=tk.X)

        btn_row = ttk.Frame(ctrl)
        btn_row.pack(fill=tk.X, pady=(4, 0))
        self.play_btn = ttk.Button(
            btn_row, text="▶  Play", command=self._play_animation, state=tk.DISABLED
        )
        self.play_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        self.stop_btn = ttk.Button(
            btn_row, text="■  Stop", command=self._stop_animation, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(4, 0))

        self.prop_text = tk.Text(
            tab,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#fafafa",
            relief=tk.FLAT,
            padx=8,
            pady=6,
        )
        self.prop_text.pack(fill=tk.BOTH, expand=True)

    def _build_inspector_tab(self):
        tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab, text="  Inspector  ")

        ttk.Label(
            tab, text="Click a node on the graph to inspect.", font=("", 10)
        ).pack(anchor=tk.W, pady=(0, 8))
        self.insp_text = tk.Text(
            tab,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#fafafa",
            relief=tk.FLAT,
            padx=8,
            pady=6,
        )
        self.insp_text.pack(fill=tk.BOTH, expand=True)

    # ================================================================
    # 中心性可视化  ← 需要你来实现！
    # ================================================================

    def _draw_centrality(self):
        """
        绘制社交网络图，节点大小/颜色编码中心性，高亮 top-k 节点。

        TODO: 请完成此方法中的可视化部分（标记 TODO 处）。
        """
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(self.BG)

        metric = self.metric_var.get()
        top_k = self.topk_var.get()
        scores = self.centralities[metric]

        vals = np.array([scores[n] for n in self.graph.nodes])
        if vals.size == 0:
            self.ax.set_title("Graph is empty — complete the TODO in network_algorithm.py",
                              fontsize=11, color="#999")
            self.ax.set_xticks([]); self.ax.set_yticks([])
            self.canvas.draw_idle()
            return
        vmin, vmax = vals.min(), vals.max()
        rng = vmax - vmin if vmax > vmin else 1.0

        sorted_nodes = sorted(scores, key=scores.get, reverse=True)
        top_set = set(sorted_nodes[:top_k])

        # --- 更新侧边栏排名表（已实现，无需修改） ---
        for item in self.rank_tree.get_children():
            self.rank_tree.delete(item)
        for i, n in enumerate(sorted_nodes):
            tag = "top" if i < top_k else ""
            self.rank_tree.insert(
                "",
                tk.END,
                values=(i + 1, f"Node {n}", f"{scores[n]:.4f}"),
                tags=(tag,),
            )
        self.rank_tree.tag_configure("top", background="#fff9c4")

        # ===================== TODO =====================
        # 请在下方完成两部分可视化：
        #
        # 1. 绘制图的所有边
        #    提示：遍历 self.graph.nodes 和 self.graph.neighbors(u)
        #          获取每条边的两个端点，用 self.pos 查坐标，
        #          用 ax.plot([x0, x1], [y0, y1], ...) 绘制线段
        #          注意避免重复绘制（u < v）
        #
        # 2. 绘制所有节点，节点大小和颜色应反映其中心性得分
        #    提示：
        #    - 使用 matplotlib colormap 将得分映射为颜色
        #        cmap = plt.get_cmap("YlOrRd")  # 或其他 colormap
        #        norm = Normalize(vmin=vmin, vmax=vmax)
        #        colors = [cmap(norm(scores[n])) for n in self.graph.nodes]
        #    - 节点大小按线性映射：
        #        sizes = [base + scale * (scores[n] - vmin) / rng ...]
        #    - 使用 ax.scatter(xs, ys, s=sizes, c=colors, ...) 绘制节点
        #
        # 可用变量：
        #   self.graph - 自定义 Graph 对象（self.graph.nodes / neighbors）
        #   self.pos   - 节点布局 {node_id: (x, y)}
        #   scores     - 当前中心性得分 {node_id: float}
        #   vmin, vmax - 得分的最小/最大值
        #   rng        - 得分范围 (vmax - vmin)
        #
        # 请将你计算的 cmap 和 norm 保存到局部变量，
        # 下方的 top-k 高亮、标签、colorbar 代码会用到它们。
        # ================================================

        cmap = plt.get_cmap(self.CMAP_NAME)
        norm = Normalize(vmin=vmin, vmax=vmax)

        # --- 以下为已实现部分，无需修改 ---

        # Top-k 高亮（红色粗边框）
        tk_list = sorted_nodes[:top_k]
        tk_sizes = [120 + 600 * (scores[n] - vmin) / rng for n in tk_list]
        tk_colors = [cmap(norm(scores[n])) for n in tk_list]
        tk_xy = np.array([self.pos[n] for n in tk_list])
        if len(tk_xy):
            self.ax.scatter(
                tk_xy[:, 0], tk_xy[:, 1], s=tk_sizes, c=tk_colors,
                edgecolors="#d32f2f", linewidths=2.5, zorder=4,
            )

        # 节点标签
        for n in self.graph.nodes:
            x, y = self.pos[n]
            if n in top_set:
                self.ax.text(
                    x, y, str(n), fontsize=10, fontweight="bold",
                    color="#1a237e", ha="center", va="center", zorder=5,
                )
            else:
                self.ax.text(
                    x, y, str(n), fontsize=7,
                    color="#666", ha="center", va="center", zorder=5,
                )

        # 选中节点高亮圈
        if self.selected_node is not None:
            x, y = self.pos[self.selected_node]
            self.ax.scatter(
                x, y, s=450, facecolors="none",
                edgecolors="#1565c0", linewidths=3, zorder=5,
            )

        # Colorbar
        sm = ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        self.fig.colorbar(sm, ax=self.ax, shrink=0.6, pad=0.02, label=metric)

        self.ax.set_title(
            f"Zachary's Karate Club — {metric} Centrality\n"
            f"Top-{top_k} nodes highlighted (red border)",
            fontsize=13, fontweight="bold",
        )
        self.ax.axis("off")
        self.fig.tight_layout()
        self.canvas.draw_idle()

    # ================================================================
    # 点击节点 → 检查器
    # ================================================================

    def _on_canvas_click(self, event):
        if event.inaxes != self.ax:
            return
        best, best_d = None, float("inf")
        for n, (x, y) in self.pos.items():
            d = (event.xdata - x) ** 2 + (event.ydata - y) ** 2
            if d < best_d:
                best, best_d = n, d
        if best is not None and best_d < 0.003:
            self.selected_node = best
            self._show_inspector(best)
            self._draw_centrality()

    def _show_inspector(self, node: int):
        self.notebook.select(2)
        self.insp_text.delete("1.0", tk.END)

        lines = [
            f"═══ Node {node} ═══",
            "",
            f"Degree    : {self.graph.degree(node)}",
            f"Neighbors : {sorted(self.graph.neighbors(node))}",
            "",
            "Centrality Scores:",
            "─" * 35,
        ]
        for m, sc in self.centralities.items():
            rank = sorted(sc.values(), reverse=True)
            r = rank.index(sc[node]) + 1
            lines.append(f"  {m:15s}: {sc[node]:.4f}  (#{r})")
        self.insp_text.insert(tk.END, "\n".join(lines))

    # ================================================================
    # SIR 传播对比
    # ================================================================

    def _run_comparison(self):
        self._stop_animation()

        scores = self.centralities["PageRank"]
        sorted_nodes = sorted(scores, key=scores.get, reverse=True)
        if not sorted_nodes:
            return
        best_seed, worst_seed = sorted_nodes[0], sorted_nodes[-1]

        steps = self.steps_var.get()
        beta = self.beta_var.get()
        gamma = self.gamma_var.get()
        n_runs = 30

        random.seed(0)
        self._comp_best_hist = sir_simulation(self.graph, [best_seed], beta, gamma, steps)
        random.seed(0)
        self._comp_worst_hist = sir_simulation(self.graph, [worst_seed], beta, gamma, steps)

        for hist in (self._comp_best_hist, self._comp_worst_hist):
            while len(hist) <= steps:
                hist.append(dict(hist[-1]))

        self._comp_best_seed = best_seed
        self._comp_worst_seed = worst_seed
        self._comp_metric = "PageRank"

        best_matrix: list[list[int]] = []
        worst_matrix: list[list[int]] = []
        for run_id in range(n_runs):
            random.seed(run_id)
            h = sir_simulation(self.graph, [best_seed], beta, gamma, steps)
            while len(h) <= steps:
                h.append(dict(h[-1]))
            best_matrix.append(
                [sum(1 for v in h[t].values() if v in ("I", "R")) for t in range(steps + 1)]
            )

            random.seed(run_id)
            h = sir_simulation(self.graph, [worst_seed], beta, gamma, steps)
            while len(h) <= steps:
                h.append(dict(h[-1]))
            worst_matrix.append(
                [sum(1 for v in h[t].values() if v in ("I", "R")) for t in range(steps + 1)]
            )

        self._comp_avg_best = np.mean(best_matrix, axis=0)
        self._comp_avg_worst = np.mean(worst_matrix, axis=0)

        self.step_slider.config(to=steps, state=tk.NORMAL)
        self.step_slider_var.set(0)
        self.play_btn.config(state=tk.NORMAL)

        self._draw_step(0)

    def _on_step_changed(self):
        if not self._comp_best_hist:
            return
        self._draw_step(self.step_slider_var.get())

    def _play_animation(self):
        self.play_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self._tick_animation()

    def _stop_animation(self):
        if self._anim_timer:
            self.root.after_cancel(self._anim_timer)
            self._anim_timer = None
        self.play_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def _tick_animation(self):
        cur = self.step_slider_var.get()
        max_step = int(self.step_slider.cget("to"))
        if cur >= max_step:
            self._stop_animation()
            return
        self.step_slider_var.set(cur + 1)
        self._draw_step(cur + 1)
        self._anim_timer = self.root.after(500, self._tick_animation)

    def _draw_step(self, step: int):
        n = len(self.graph.nodes)
        state_b = self._comp_best_hist[step]
        state_w = self._comp_worst_hist[step]

        reach_b = sum(1 for v in state_b.values() if v in ("I", "R"))
        reach_w = sum(1 for v in state_w.values() if v in ("I", "R"))

        self.fig.clear()
        ax_l = self.fig.add_subplot(121)
        ax_r = self.fig.add_subplot(122)

        self._draw_sir_state(
            ax_l, state_b, self._comp_best_seed,
            f"Highest {self._comp_metric}: Node {self._comp_best_seed}\n"
            f"Step {step}: {reach_b}/{n} reached ({reach_b / n * 100:.0f}%)",
        )
        self._draw_sir_state(
            ax_r, state_w, self._comp_worst_seed,
            f"Lowest {self._comp_metric}: Node {self._comp_worst_seed}\n"
            f"Step {step}: {reach_w}/{n} reached ({reach_w / n * 100:.0f}%)",
        )

        legend = [
            Patch(fc=self.SIR_CLR["S"], ec="#333", label="Susceptible"),
            Patch(fc=self.SIR_CLR["I"], ec="#333", label="Infected"),
            Patch(fc=self.SIR_CLR["R"], ec="#333", label="Recovered"),
            Patch(fc="gold", ec="#333", label="Seed node"),
        ]
        ax_r.legend(handles=legend, loc="lower right", fontsize=9)

        beta, gamma = self.beta_var.get(), self.gamma_var.get()
        max_step = int(self.step_slider.cget("to"))
        self.fig.suptitle(
            f"SIR Propagation Comparison  (β={beta}, γ={gamma})",
            fontsize=14, fontweight="bold", y=0.98,
        )
        self.fig.tight_layout(rect=[0, 0, 1, 0.95])
        self.canvas.draw_idle()

        avg_b = self._comp_avg_best[step]
        avg_w = self._comp_avg_worst[step]
        self.prop_text.delete("1.0", tk.END)
        self.prop_text.insert(
            tk.END,
            f"Step {step} / {max_step}\n"
            f"{'═' * 32}\n\n"
            f"Node {self._comp_best_seed:>2d} (highest {self._comp_metric})\n"
            f"  This run : {reach_b:>2d}/{n} reached\n"
            f"  Avg (30r): {avg_b:.1f}/{n} ({avg_b / n * 100:.1f}%)\n\n"
            f"Node {self._comp_worst_seed:>2d} (lowest {self._comp_metric})\n"
            f"  This run : {reach_w:>2d}/{n} reached\n"
            f"  Avg (30r): {avg_w:.1f}/{n} ({avg_w / n * 100:.1f}%)\n\n"
            f"{'─' * 32}\n"
            f"Difference : {avg_b - avg_w:+.1f} nodes (avg)\n",
        )

    def _draw_edges(self, ax):
        """绘制所有边。"""
        for u in self.graph.nodes:
            for v in self.graph.neighbors(u):
                if u < v:
                    x0, y0 = self.pos[u]
                    x1, y1 = self.pos[v]
                    ax.plot(
                        [x0, x1], [y0, y1],
                        color=self.EDGE_CLR, linewidth=0.8, alpha=0.5, zorder=1,
                    )

    def _draw_sir_state(
        self, ax, state: dict[int, str], seed: int, title: str
    ):
        """在给定 axes 上绘制一个 SIR 快照，高亮种子节点。"""
        ax.set_facecolor(self.BG)

        self._draw_edges(ax)

        for s, clr in self.SIR_CLR.items():
            nodelist = [n for n, st in state.items() if st == s]
            if nodelist:
                xy = np.array([self.pos[n] for n in nodelist])
                ax.scatter(
                    xy[:, 0], xy[:, 1], s=200, c=clr,
                    edgecolors="#333", linewidths=0.8, zorder=3,
                )

        x, y = self.pos[seed]
        ax.scatter(
            x, y, s=420, marker="*", c="gold",
            edgecolors="#333", linewidths=1.2, zorder=6,
        )

        for n in self.graph.nodes:
            x, y = self.pos[n]
            ax.text(
                x, y, str(n), fontsize=7, fontweight="bold",
                color="white", ha="center", va="center", zorder=4,
            )

        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.axis("off")

    # ================================================================
    # 启动
    # ================================================================

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = SocialNetworkApp()
    app.run()
