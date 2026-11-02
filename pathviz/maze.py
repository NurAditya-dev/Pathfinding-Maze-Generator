"""Maze generation with iterative recursive backtracking (explicit stack)."""
from __future__ import annotations

import random
from typing import Iterator, Optional

from .grid import DIRECTIONS, EMPTY, WALL, Grid, Node


def recursive_backtracker(
    grid: Grid, rng: Optional[random.Random] = None, loops: float = 0.08
) -> Iterator[Node]:
    """Fill `grid` with walls, then carve a maze starting at (1, 1).

    Returns a generator that carves one cell per step and yields it, so a UI can
    animate the process. A pure backtracker makes a "perfect" maze with a single
    route; `loops` is the fraction of leftover inner walls knocked down afterwards
    so that alternative routes exist and the algorithms behave differently.

    The grid needs odd dimensions (>= 5) so rooms sit on odd coordinates.
    """
    if grid.rows < 5 or grid.cols < 5 or grid.rows % 2 == 0 or grid.cols % 2 == 0:
        raise ValueError("maze needs odd grid dimensions of at least 5")
    rng = rng or random.Random()
    grid.fill(WALL)
    return _carve(grid, rng, loops)


def _carve(grid: Grid, rng: random.Random, loops: float) -> Iterator[Node]:
    rows, cols = grid.rows, grid.cols
    origin = (1, 1)
    grid.set(origin, EMPTY)
    seen = {origin}
    stack = [origin]
    yield origin

    while stack:
        r, c = stack[-1]
        options = [
            (dr, dc)
            for dr, dc in DIRECTIONS
            if 0 < r + 2 * dr < rows - 1
            and 0 < c + 2 * dc < cols - 1
            and (r + 2 * dr, c + 2 * dc) not in seen
        ]
        if not options:
            stack.pop()  # dead end: backtrack
            continue
        dr, dc = rng.choice(options)
        gap = (r + dr, c + dc)
        room = (r + 2 * dr, c + 2 * dc)
        grid.set(gap, EMPTY)
        yield gap
        grid.set(room, EMPTY)
        yield room
        seen.add(room)
        stack.append(room)

    # Walls that separate two open rooms: removing one creates a loop.
    candidates = []
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if grid.get((r, c)) != WALL:
                continue
            if r % 2 == 1 and c % 2 == 0:
                sides = ((r, c - 1), (r, c + 1))
            elif r % 2 == 0 and c % 2 == 1:
                sides = ((r - 1, c), (r + 1, c))
            else:
                continue
            if all(grid.get(side) == EMPTY for side in sides):
                candidates.append((r, c))
    rng.shuffle(candidates)
    for node in candidates[: int(len(candidates) * loops)]:
        grid.set(node, EMPTY)
        yield node
