"""Pathfinding algorithms written as generators so a UI can animate them.

Every algorithm yields events `(kind, node)`:
  * FRONTIER - the node was discovered and queued
  * VISIT    - the node was taken out of the queue and expanded
and *returns* the path as a list of nodes (or None when the goal is unreachable).
"""
from __future__ import annotations

import heapq
import math
from collections import deque
from dataclasses import dataclass
from itertools import count
from time import perf_counter
from typing import Callable, Generator, Optional

from .grid import Grid, Node

VISIT = "visit"
FRONTIER = "frontier"

Event = tuple[str, Node]
Path = Optional[list[Node]]
Search = Generator[Event, None, Path]


def manhattan(a: Node, b: Node) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _trace(came_from: dict[Node, Optional[Node]], end: Node) -> list[Node]:
    path: list[Node] = []
    node: Optional[Node] = end
    while node is not None:
        path.append(node)
        node = came_from[node]
    path.reverse()
    return path


def bfs(grid: Grid, start: Node, goal: Node) -> Search:
    """Queue (FIFO). Shortest path in number of steps; ignores terrain cost."""
    came_from: dict[Node, Optional[Node]] = {start: None}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        yield VISIT, current
        if current == goal:
            return _trace(came_from, current)
        for nxt in grid.neighbors(current):
            if nxt not in came_from:
                came_from[nxt] = current
                queue.append(nxt)
                yield FRONTIER, nxt
    return None


def dfs(grid: Grid, start: Node, goal: Node) -> Search:
    """Stack (LIFO). Finds *a* path, usually a long and winding one."""
    came_from: dict[Node, Optional[Node]] = {}
    stack: list[tuple[Node, Optional[Node]]] = [(start, None)]
    while stack:
        current, parent = stack.pop()
        if current in came_from:
            continue
        came_from[current] = parent
        yield VISIT, current
        if current == goal:
            return _trace(came_from, current)
        # Reversed so the first direction in DIRECTIONS is explored first.
        for nxt in reversed(list(grid.neighbors(current))):
            if nxt not in came_from:
                stack.append((nxt, current))
                yield FRONTIER, nxt
    return None


def dijkstra(grid: Grid, start: Node, goal: Node) -> Search:
    """Priority queue ordered by cost so far. Optimal with terrain costs."""
    tie = count()
    dist = {start: 0}
    came_from: dict[Node, Optional[Node]] = {start: None}
    closed: set[Node] = set()
    heap = [(0, next(tie), start)]
    while heap:
        d, _, current = heapq.heappop(heap)
        if current in closed:
            continue  # stale heap entry
        closed.add(current)
        yield VISIT, current
        if current == goal:
            return _trace(came_from, current)
        for nxt in grid.neighbors(current):
            nd = d + grid.cost(nxt)
            if nxt not in closed and nd < dist.get(nxt, math.inf):
                dist[nxt] = nd
                came_from[nxt] = current
                heapq.heappush(heap, (nd, next(tie), nxt))
                yield FRONTIER, nxt
    return None


def astar(grid: Grid, start: Node, goal: Node) -> Search:
    """Dijkstra guided by a Manhattan-distance heuristic (admissible: min cost is 1)."""
    tie = count()
    g = {start: 0}
    came_from: dict[Node, Optional[Node]] = {start: None}
    closed: set[Node] = set()
    heap = [(manhattan(start, goal), manhattan(start, goal), next(tie), start)]
    while heap:
        _, _, _, current = heapq.heappop(heap)
        if current in closed:
            continue
        closed.add(current)
        yield VISIT, current
        if current == goal:
            return _trace(came_from, current)
        for nxt in grid.neighbors(current):
            ng = g[current] + grid.cost(nxt)
            if nxt not in closed and ng < g.get(nxt, math.inf):
                g[nxt] = ng
                came_from[nxt] = current
                h = manhattan(nxt, goal)
                # Ties on f are broken by smaller h, which drives straight to the goal.
                heapq.heappush(heap, (ng + h, h, next(tie), nxt))
                yield FRONTIER, nxt
    return None


ALGORITHMS: dict[str, Callable[[Grid, Node, Node], Search]] = {
    "BFS": bfs,
    "DFS": dfs,
    "Dijkstra": dijkstra,
    "A*": astar,
}

ALGORITHM_INFO = {
    "BFS": "BFS: melebar merata, jalur terpendek (abaikan lumpur)",
    "DFS": "DFS: menyelam sedalam mungkin, jalur belum tentu terpendek",
    "Dijkstra": "Dijkstra: perluas biaya terkecil, optimal dengan lumpur",
    "A*": "A*: Dijkstra + heuristik Manhattan, mengarah ke tujuan",
}


@dataclass(frozen=True)
class Result:
    name: str
    visited: int
    steps: Optional[int]  # moves along the path, None if unreachable
    cost: Optional[int]
    ms: float


class Searcher:
    """Drives one algorithm and measures it."""

    def __init__(self, name: str, grid: Grid, start: Node, goal: Node) -> None:
        self.name = name
        self.grid = grid
        self.path: Path = None
        self.done = False
        self.visited = 0
        self.elapsed = 0.0
        self._gen = ALGORITHMS[name](grid, start, goal)

    def advance(self, visits: int) -> list[Event]:
        """Run until `visits` more nodes were expanded (or the search ends)."""
        events: list[Event] = []
        remaining = visits
        started = perf_counter()
        while remaining > 0 and not self.done:
            try:
                event = next(self._gen)
            except StopIteration as stop:
                self.path = stop.value
                self.done = True
                break
            events.append(event)
            if event[0] == VISIT:
                self.visited += 1
                remaining -= 1
        self.elapsed += perf_counter() - started
        return events

    def result(self) -> Result:
        steps = cost = None
        if self.path:
            steps = len(self.path) - 1
            cost = sum(self.grid.cost(node) for node in self.path[1:])
        return Result(self.name, self.visited, steps, cost, self.elapsed * 1000)
