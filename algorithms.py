from __future__ import annotations

from collections import deque
import heapq
from itertools import count
from time import perf_counter

try:
    from search.node import Node
except (ModuleNotFoundError, ImportError):
    from node import Node  # type: ignore


def greedy_search(initial_state, is_goal, successors, heuristic, time_limit_ms=None, max_nodes=5_000_000):
    deadline = None if time_limit_ms is None else perf_counter() + (time_limit_ms / 1000.0)
    root = Node(state=initial_state, g=0.0, h=heuristic(initial_state))
    if is_goal(initial_state):
        return root

    frontier = []
    tie = count()
    heapq.heappush(frontier, (root.h, root.g, next(tie), root))
    best_g = {initial_state: 0.0}
    expanded = 0

    while frontier:
        if deadline is not None and perf_counter() > deadline:
            return None
        if expanded >= max_nodes:
            return None

        _, _, _, node = heapq.heappop(frontier)
        if node.g > best_g.get(node.state, float('inf')):
            continue
        if is_goal(node.state):
            return node

        expanded += 1
        for action, next_state, step_cost in successors(node.state):
            ng = node.g + step_cost
            if ng >= best_g.get(next_state, float('inf')):
                continue
            best_g[next_state] = ng
            child = Node(state=next_state, parent=node, action=action, g=ng, h=heuristic(next_state))
            heapq.heappush(frontier, (child.h, child.g, next(tie), child))

    return None


def astar(initial_state, is_goal, successors, heuristic, time_limit_ms=None, max_nodes=1_000_000):
    deadline = None if time_limit_ms is None else perf_counter() + (time_limit_ms / 1000.0)
    root = Node(state=initial_state, g=0.0, h=heuristic(initial_state))
    if is_goal(initial_state):
        return root

    frontier = []
    tie = count()
    heapq.heappush(frontier, (root.g + root.h, root.h, root.g, next(tie), root))
    best_g = {initial_state: 0.0}
    expanded = 0

    while frontier:
        if deadline is not None and perf_counter() > deadline:
            return None
        if expanded >= max_nodes:
            return None

        _, _, _, _, node = heapq.heappop(frontier)
        if node.g > best_g.get(node.state, float('inf')):
            continue
        if is_goal(node.state):
            return node

        expanded += 1
        for action, next_state, step_cost in successors(node.state):
            ng = node.g + step_cost
            if ng >= best_g.get(next_state, float('inf')):
                continue
            best_g[next_state] = ng
            child = Node(state=next_state, parent=node, action=action, g=ng, h=heuristic(next_state))
            heapq.heappush(frontier, (child.g + child.h, child.h, child.g, next(tie), child))

    return None


def bfs(initial_state, is_goal, successors, time_limit_ms=None):
    deadline = None if time_limit_ms is None else perf_counter() + (time_limit_ms / 1000.0)
    root = Node(state=initial_state, g=0.0, h=0.0)
    if is_goal(initial_state):
        return root

    frontier = deque([root])
    visited = {initial_state}

    while frontier:
        if deadline is not None and perf_counter() > deadline:
            return None
        node = frontier.popleft()
        if is_goal(node.state):
            return node
        for action, next_state in successors(node.state):
            if next_state in visited:
                continue
            visited.add(next_state)
            frontier.append(Node(state=next_state, parent=node, action=action, g=node.g + 1, h=0.0))
    return None
