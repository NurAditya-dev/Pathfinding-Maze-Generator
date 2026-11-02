import random
import unittest
from collections import deque

from pathviz.algorithms import ALGORITHMS, Searcher
from pathviz.grid import EMPTY, MUD, WALL, Grid
from pathviz.maze import recursive_backtracker


def solve(name, grid, start, goal):
    searcher = Searcher(name, grid, start, goal)
    searcher.advance(10 ** 9)
    return searcher


def random_grid(rng, rows=15, cols=15, walls=0.25, mud=0.15):
    grid = Grid(rows, cols)
    for r in range(rows):
        for c in range(cols):
            x = rng.random()
            grid.cells[r][c] = WALL if x < walls else MUD if x < walls + mud else EMPTY
    start, goal = (0, 0), (rows - 1, cols - 1)
    grid.set(start, EMPTY)
    grid.set(goal, EMPTY)
    return grid, start, goal


def valid_path(grid, path, start, goal):
    return (
        path[0] == start
        and path[-1] == goal
        and all(grid.passable(n) for n in path)
        and all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 for a, b in zip(path, path[1:]))
    )


class PathfindingTests(unittest.TestCase):
    def test_open_grid_shortest_is_manhattan(self):
        grid = Grid(10, 10)
        for name in ("BFS", "Dijkstra", "A*"):
            s = solve(name, grid, (0, 0), (9, 9))
            self.assertEqual(len(s.path) - 1, 18, name)

    def test_unreachable_returns_none(self):
        grid = Grid(5, 5)
        for r in range(5):
            grid.set((r, 2), WALL)
        for name in ALGORITHMS:
            s = solve(name, grid, (0, 0), (4, 4))
            self.assertTrue(s.done)
            self.assertIsNone(s.path, name)

    def test_start_equals_goal(self):
        for name in ALGORITHMS:
            self.assertEqual(solve(name, Grid(3, 3), (1, 1), (1, 1)).path, [(1, 1)])

    def test_all_paths_valid_and_optimal_algorithms_agree(self):
        rng = random.Random(7)
        for _ in range(150):
            grid, start, goal = random_grid(rng)
            runs = {n: solve(n, grid, start, goal) for n in ALGORITHMS}
            reachable = runs["Dijkstra"].path is not None
            for name, s in runs.items():
                self.assertEqual(s.path is not None, reachable, name)
                if s.path:
                    self.assertTrue(valid_path(grid, s.path, start, goal), name)
            if reachable:
                cost = lambda n: runs[n].result().cost
                self.assertEqual(cost("A*"), cost("Dijkstra"))
                self.assertLessEqual(cost("Dijkstra"), cost("BFS"))
                self.assertLessEqual(cost("Dijkstra"), cost("DFS"))
                # BFS is optimal in steps
                self.assertEqual(len(runs["BFS"].path), min(len(r.path) for r in runs.values()))

    def test_astar_explores_less_than_bfs_on_open_grid(self):
        grid = Grid(31, 41)
        a = solve("A*", grid, (15, 10), (15, 30))
        b = solve("BFS", grid, (15, 10), (15, 30))
        self.assertLess(a.visited, b.visited // 4)


class MazeTests(unittest.TestCase):
    def test_maze_is_fully_connected_and_bordered(self):
        for seed in range(10):
            grid = Grid(31, 41)
            for _ in recursive_backtracker(grid, random.Random(seed)):
                pass
            open_cells = {(r, c) for r in range(31) for c in range(41) if grid.get((r, c)) == EMPTY}
            self.assertIn((1, 1), open_cells)
            self.assertIn((29, 39), open_cells)
            seen, queue = {(1, 1)}, deque([(1, 1)])
            while queue:
                for n in grid.neighbors(queue.popleft()):
                    if n not in seen:
                        seen.add(n)
                        queue.append(n)
            self.assertEqual(seen, open_cells)
            self.assertTrue(all(grid.get((0, c)) == WALL and grid.get((30, c)) == WALL for c in range(41)))
            self.assertTrue(all(grid.get((r, 0)) == WALL and grid.get((r, 40)) == WALL for r in range(31)))

    def test_rejects_even_size(self):
        with self.assertRaises(ValueError):
            recursive_backtracker(Grid(10, 10))


if __name__ == "__main__":
    unittest.main()
