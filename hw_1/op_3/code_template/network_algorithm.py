# Copyright 2026, Yumeng Liu @ USTC
"""
社交网络算法模块 —— 图构建、中心性计算、SIR 传播模拟
"""

import random
import re
from collections import deque


# ============================================================
# Graph 数据结构
# ============================================================


class Graph:
    """
    简单的无向无权图。

    需要实现的接口
    -------------
    - add_node(node_id)      : 添加节点
    - add_edge(u, v)         : 添加无向边
    - neighbors(node_id)     : 返回邻居（可迭代对象）
    - degree(node_id)        : 返回节点度数
    - number_of_edges()      : 返回边数

    属性
    ----
    nodes : set[int] 或其他可迭代容器
        存储所有节点 id。算法函数和 GUI 都会通过
        ``for v in G.nodes`` 和 ``len(G.nodes)`` 来访问，
        请确保它支持迭代和 len()。

    提示
    ----
    你可以自由选择底层数据结构（邻接表、邻接矩阵、边列表等）。
    """

    def __init__(self):
        self.nodes = set()
        # TODO: 初始化你的数据结构

    def add_node(self, node_id: int):
        """添加节点。"""
        # TODO: 将 node_id 加入图中
        pass

    def add_edge(self, u: int, v: int):
        """添加无向边 (u, v)。"""
        # TODO: 在数据结构中记录无向边
        pass

    def neighbors(self, node_id: int):
        """
        返回 node_id 的邻居（可迭代对象）。

        若节点不存在或无邻居，返回空集合/列表。
        """
        # TODO: 返回邻居
        return set()

    def degree(self, node_id: int) -> int:
        """返回 node_id 的度数。"""
        # TODO
        return 0

    def number_of_edges(self) -> int:
        """返回图中边的数量（每条无向边只计一次）。"""
        # TODO
        return 0


# ============================================================
# 图构建
# ============================================================


def build_graph(data: str) -> Graph:
    """
    解析边列表数据，构建无向无权图。

    数据格式：每条边以 ``[u v]`` 表示，节点编号从 1 开始。
    节点集合自动从边中推断。
    """
    G = Graph()
    for u_s, v_s in re.findall(r"\[(\d+)\s+(\d+)\]", data):
        G.add_edge(int(u_s), int(v_s))
    return G


# ============================================================
# BFS 工具函数
# ============================================================


def bfs_shortest_paths(
    G: Graph, source: int
) -> tuple[dict[int, int], dict[int, int], dict[int, list[int]], list[int]]:
    """
    从 source 出发执行 BFS，返回：
      - dist:  {node: 最短距离}
      - sigma: {node: 从 source 到 node 的最短路径条数}
      - pred:  {node: [最短路径上的前驱节点列表]}
      - order: BFS 遍历序列

    这是实现 Closeness / Betweenness 中心性的核心工具函数。

    提示
    ----
    - 使用 collections.deque 作为 BFS 队列
    - G.neighbors(v) 返回节点 v 的邻居集合
    - G.nodes 返回图中所有节点的集合
    - 当发现新节点时更新 dist, sigma, pred
    - 当发现到已知节点的另一条最短路径时（dist 相等），更新 sigma 和 pred
    """
    dist = {source: 0}
    sigma: dict[int, int] = {v: 0 for v in G.nodes}
    sigma[source] = 1
    pred: dict[int, list[int]] = {v: [] for v in G.nodes}
    order: list[int] = [source]

    # TODO: 请实现 BFS 算法
    # 1. 创建 BFS 队列 (deque)，初始放入 source
    # 2. 循环取出队首节点 u，遍历其邻居 v：
    #    - 若 v 未被访问（不在 dist 中），设置 dist[v]，入队
    #    - 若 dist[v] == dist[u] + 1，更新 sigma[v] 和 pred[v]
    # 3. 记录遍历顺序到 order

    return dist, sigma, pred, order


# ============================================================
# 中心性指标计算
# ============================================================


def degree_centrality(G: Graph) -> dict[int, float]:
    """
    度中心性：C_D(v) = deg(v) / (n - 1)

    Parameters
    ----------
    G : Graph
        无向图。

    Returns
    -------
    dict[int, float]
        每个节点的度中心性。

    提示
    ----
    - G.degree(v) 返回节点 v 的度数
    - n = len(G.nodes)
    """
    # TODO: 请实现度中心性计算
    return {v: 0.0 for v in G.nodes}


def closeness_centrality(G: Graph) -> dict[int, float]:
    """
    接近中心性：C_C(v) = (n - 1) / Σ_{u≠v} d(v, u)

    Parameters
    ----------
    G : Graph
        无向图。

    Returns
    -------
    dict[int, float]
        每个节点的接近中心性。

    提示
    ----
    - 对每个节点 v 调用 bfs_shortest_paths(G, v) 获取最短距离
    - 将所有距离求和作为分母
    """
    # TODO: 请实现接近中心性计算
    return {v: 0.0 for v in G.nodes}


def betweenness_centrality(G: Graph) -> dict[int, float]:
    """
    中介中心性（Brandes 算法）：
      C_B(v) = Σ_{s≠v≠t} σ_st(v) / σ_st

    归一化：除以 (n-1)(n-2)（无向图）

    Parameters
    ----------
    G : Graph
        无向图。

    Returns
    -------
    dict[int, float]
        每个节点的中介中心性（归一化后）。

    提示
    ----
    Brandes 算法核心步骤：
    1. 对每个源节点 s，调用 bfs_shortest_paths 获取 dist, sigma, pred, order
    2. 反向累积（从 order 末尾向前）：
       - 对 w 的每个前驱 v ∈ pred[w]：
         delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
       - 若 w ≠ s：bc[w] += delta[w]
    3. 最终归一化：bc[v] /= (n-1)(n-2)
    """
    # TODO: 请实现 Brandes 算法计算中介中心性
    return {v: 0.0 for v in G.nodes}


def pagerank(
    G: Graph, alpha: float = 0.85, max_iter: int = 100, tol: float = 1e-6
) -> dict[int, float]:
    """
    PageRank：PR(v) = (1-α)/n + α × Σ_{u→v} PR(u) / deg(u)

    Parameters
    ----------
    G : Graph
        无向图。
    alpha : float
        阻尼系数，默认 0.85。
    max_iter : int
        最大迭代次数。
    tol : float
        收敛阈值。

    Returns
    -------
    dict[int, float]
        每个节点的 PageRank 值。

    提示
    ----
    - 初始化所有节点 PR 为 1/n
    - 每次迭代：对每个节点 v，累加邻居贡献 PR(u)/deg(u)
    - 当所有节点 PR 变化量之和 < tol 时停止
    """
    nodes = list(G.nodes)
    n = len(nodes)

    # TODO [Optional]: 请实现 PageRank 算法
    return {v: 1.0 / n for v in nodes}


# ============================================================
# SIR 传播模拟
# ============================================================


def sir_simulation(
    G: Graph,
    seeds: list[int],
    beta: float = 0.3,
    gamma: float = 0.1,
    max_steps: int = 5,
) -> list[dict[int, str]]:
    """
    SIR 传播模型。每一步：
      - 感染节点以概率 β 传染给相邻的易感节点
      - 感染节点以概率 γ 恢复

    Parameters
    ----------
    G : Graph
        无向图。
    seeds : list[int]
        初始感染节点列表。
    beta : float
        感染概率（每条边每步）。
    gamma : float
        恢复概率（每个感染者每步）。
    max_steps : int
        最大模拟步数。

    Returns
    -------
    list[dict[int, str]]
        长度为 steps+1 的列表，history[t] 记录第 t 步每个节点的状态
        （'S'=易感, 'I'=感染, 'R'=恢复）。

    提示
    ----
    1. 初始化所有节点为 'S'，将 seeds 中的节点设为 'I'
    2. 每一步创建 state 的副本 new_state：
       - 遍历所有状态为 'I' 的节点 v
       - 对 v 的每个邻居 u：若 u 为 'S'，以概率 beta 将 new_state[u] 设为 'I'
       - 以概率 gamma 将 new_state[v] 设为 'R'
    3. 用 new_state 替换 state，记录到 history
    4. 若没有 'I' 状态节点，提前终止
    5. 使用 random.random() < beta 判断是否感染
    """
    # TODO [Optional]: 请实现 SIR 传播模拟
    state = {v: "S" for v in G.nodes}
    for s in seeds:
        state[s] = "I"
    history = [dict(state)]
    return history
