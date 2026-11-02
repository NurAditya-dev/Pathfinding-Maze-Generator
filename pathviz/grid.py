"""Grid model: a 2D matrix of terrain values."""
from __future__ import annotations

import random
from typing import Iterable, Iterator

Node = tuple[int, int]  # (row, col)

EMPTY, WALL, MUD = 0, 1, 2
MUD_COST = 5
DIRECTIONS = ((-1, 0), (0, 1), (1, 0), (0, -1))  # up, right, down, left


class Grid:
    def __init__(self, rows: int, cols: int) -> None:
        self.rows = rows
        self.cols = cols
        self.cells = [[EMPTY] * cols for _ in range(rows)]

    def get(self, node: Node) -> int:
        return self.cells[node[0]][node[1]]

    def set(self, node: Node, value: int) -> None:
        self.cells[node[0]][node[1]] = value

    def in_bounds(self, node: Node) -> bool:
        return 0 <= node[0] < self.rows and 0 <= node[1] < self.cols

    def passable(self, node: Node) -> bool:
        return self.in_bounds(node) and self.get(node) != WALL

    def cost(self, node: Node) -> int:
        """Cost of stepping onto `node`."""
        return MUD_COST if self.get(node) == MUD else 1

    def neighbors(self, node: Node) -> Iterator[Node]:
        r, c = node
        for dr, dc in DIRECTIONS:
            nxt = (r + dr, c + dc)
            if self.passable(nxt):
                yield nxt

    def fill(self, value: int) -> None:
        for row in self.cells:
            row[:] = [value] * self.cols

    def clear(self) -> None:
        self.fill(EMPTY)

    def scatter_walls(
        self, density: float, rng: random.Random, keep: Iterable[Node] = ()
    ) -> None:
        """Turn roughly `density` of the cells into walls, except those in `keep`."""
        protected = set(keep)
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) not in protected and rng.random() < density:
                    self.cells[r][c] = WALL


def line_cells(a: Node, b: Node) -> Iterator[Node]:
    """Cells on the straight line from a to b (Bresenham), both ends included."""
    r0, c0 = a
    r1, c1 = b
    dc, dr = abs(c1 - c0), -abs(r1 - r0)
    sc = 1 if c0 < c1 else -1
    sr = 1 if r0 < r1 else -1
    err = dc + dr
    while True:
        yield (r0, c0)
        if (r0, c0) == (r1, c1):
            return
        e2 = 2 * err
        if e2 >= dr:
            err += dr
            c0 += sc
        if e2 <= dc:
            err += dc
            r0 += sr
