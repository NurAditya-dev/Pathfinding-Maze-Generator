"""Pygame front-end for the pathfinding visualizer."""
from __future__ import annotations

import random
from typing import Optional

import pygame

from . import theme
from .algorithms import ALGORITHM_INFO, ALGORITHMS, FRONTIER, VISIT, Searcher, Result
from .grid import EMPTY, MUD, WALL, Grid, Node, line_cells
from .maze import recursive_backtracker
from .widgets import Button, Slider, draw_text, font, mix

ROWS, COLS, CELL = 31, 41, 20  # odd sizes so the maze generator fits exactly
MARGIN = 20
PANEL_W = 280
PAD = 16

GRID_X, GRID_Y = MARGIN, MARGIN
GRID_W, GRID_H = COLS * CELL, ROWS * CELL
PANEL_X = GRID_X + GRID_W + MARGIN
WIN_W = PANEL_X + PANEL_W + MARGIN
WIN_H = GRID_H + 2 * MARGIN + 30

INNER_X = PANEL_X + PAD
INNER_W = PANEL_W - 2 * PAD

POP_SECONDS = 0.35  # how long a freshly visited cell glows
PATH_SPEED = 90  # path cells revealed per second
MAZE_STEPS = 8  # carve steps per frame
WALL_DENSITY = 0.28
ALGO_ORDER = list(ALGORITHMS)


def wrap(text: str, size: int, width: int) -> list[str]:
    f = font(size)
    lines: list[str] = []
    line = ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if f.size(trial)[0] <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


class App:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Pathfinding Visualizer")
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        self.clock = pygame.time.Clock()
        self.now = pygame.time.get_ticks() / 1000
        self.quit = False
        self.rng = random.Random()

        self.grid = Grid(ROWS, COLS)
        self.start: Node = (ROWS // 2, COLS // 4)
        self.goal: Node = (ROWS // 2, 3 * COLS // 4)

        self.algo = "A*"
        self.tool = WALL
        self.slider = Slider((INNER_X, 306, INNER_W, 16), 0.45)

        # search state
        self.searcher: Optional[Searcher] = None
        self.running = False
        self.acc = 0.0
        self.visited: dict[Node, float] = {}
        self.frontier: set[Node] = set()
        self.path: Optional[list[Node]] = None
        self.path_progress = 0.0
        self.results: dict[str, Result] = {}

        # maze animation
        self.maze_gen = None
        self.maze_head: Optional[Node] = None

        # mouse editing
        self.drag: Optional[str] = None
        self.paint_value = WALL
        self.last_cell: Optional[Node] = None

        self.buttons = self._build_buttons()

    # ------------------------------------------------------------------ UI
    def _build_buttons(self) -> list[Button]:
        half = (INNER_W - 6) // 2
        third = (INNER_W - 12) // 3
        buttons: list[Button] = []

        for i, name in enumerate(ALGO_ORDER):
            x = INNER_X + (i % 2) * (half + 6)
            y = 112 + (i // 2) * 34
            buttons.append(Button((x, y, half, 28), name,
                                  lambda n=name: self.select_algo(n),
                                  active=lambda n=name: self.algo == n))

        tools = (("Dinding", WALL), ("Lumpur", MUD), ("Hapus", EMPTY))
        for i, (label, value) in enumerate(tools):
            x = INNER_X + i * (third + 6)
            buttons.append(Button((x, 244, third, 28), label,
                                  lambda v=value: setattr(self, "tool", v),
                                  active=lambda v=value: self.tool == v))

        buttons.append(Button((INNER_X, 332, INNER_W, 36), self.run_label,
                              self.toggle_run, primary=True))
        rows = (
            (("Langkah", self.step), ("Reset", self.reset_search)),
            (("Buat Labirin", self.make_maze), ("Dinding Acak", self.random_walls)),
            (("Bersihkan", self.clear), ("Bandingkan", self.run_all)),
        )
        for r, row in enumerate(rows):
            for c, (label, action) in enumerate(row):
                buttons.append(Button((INNER_X + c * (half + 6), 376 + r * 34, half, 28),
                                      label, action))
        return buttons

    def run_label(self) -> str:
        if self.searcher is None:
            return "Mulai"
        if self.searcher.done:
            return "Ulangi"
        return "Jeda" if self.running else "Lanjut"

    def speed(self) -> float:
        """Nodes expanded per second."""
        return 10 ** (0.5 + 3.3 * self.slider.value)

    # ------------------------------------------------------------ actions
    def invalidate(self) -> None:
        """The grid changed: drop the search and any stored results."""
        self.reset_search()
        self.results.clear()

    def reset_search(self) -> None:
        self.searcher = None
        self.running = False
        self.acc = 0.0
        self.visited.clear()
        self.frontier.clear()
        self.path = None
        self.path_progress = 0.0

    def select_algo(self, name: str) -> None:
        self.algo = name
        self.reset_search()

    def toggle_run(self) -> None:
        if self.searcher is None or self.searcher.done:
            self.reset_search()
            self.searcher = Searcher(self.algo, self.grid, self.start, self.goal)
            self.running = True
        else:
            self.running = not self.running

    def step(self) -> None:
        if self.searcher is None or self.searcher.done:
            self.reset_search()
            self.searcher = Searcher(self.algo, self.grid, self.start, self.goal)
        self.running = False
        self._advance(1)

    def clear(self) -> None:
        self.invalidate()
        self.grid.clear()

    def random_walls(self) -> None:
        self.invalidate()
        self.grid.clear()
        self.grid.scatter_walls(WALL_DENSITY, self.rng, keep=(self.start, self.goal))

    def make_maze(self) -> None:
        self.invalidate()
        self.start = (1, 1)
        self.goal = (ROWS - 2, COLS - 2)
        self.maze_gen = recursive_backtracker(self.grid, self.rng)

    def run_all(self) -> None:
        """Run every algorithm instantly, fill the comparison table, show the selected one."""
        self.reset_search()
        shown: Optional[Searcher] = None
        shown_events = []
        for name in ALGO_ORDER:
            searcher = Searcher(name, self.grid, self.start, self.goal)
            events = searcher.advance(10 ** 9)
            self.results[name] = searcher.result()
            if name == self.algo:
                shown, shown_events = searcher, events
        assert shown is not None
        self._apply(shown_events, stamp=self.now - 10)
        self.searcher = shown
        self._finish()
        self.path_progress = float(len(self.path or ()))

    # ---------------------------------------------------------- simulation
    def _apply(self, events, stamp: Optional[float] = None) -> None:
        stamp = self.now if stamp is None else stamp
        for kind, node in events:
            if kind == VISIT:
                self.frontier.discard(node)
                self.visited[node] = stamp
            elif kind == FRONTIER:
                self.frontier.add(node)

    def _advance(self, visits: int) -> None:
        assert self.searcher is not None
        self._apply(self.searcher.advance(visits))
        if self.searcher.done:
            self._finish()

    def _finish(self) -> None:
        assert self.searcher is not None
        self.results[self.searcher.name] = self.searcher.result()
        self.path = self.searcher.path
        self.path_progress = 0.0
        self.running = False

    def tick(self, dt: float) -> None:
        if self.maze_gen is not None:
            for _ in range(MAZE_STEPS):
                try:
                    self.maze_head = next(self.maze_gen)
                except StopIteration:
                    self.maze_gen = None
                    self.maze_head = None
                    break
            return
        if self.running and self.searcher is not None:
            self.acc += dt * self.speed()
            count = int(self.acc)
            self.acc -= count
            if count:
                self._advance(count)
        if self.path and self.path_progress < len(self.path):
            self.path_progress = min(len(self.path), self.path_progress + dt * PATH_SPEED)

    # --------------------------------------------------------------- input
    def cell_at(self, pos) -> Optional[Node]:
        x, y = pos[0] - GRID_X, pos[1] - GRID_Y
        if 0 <= x < GRID_W and 0 <= y < GRID_H:
            return (y // CELL, x // CELL)
        return None

    def handle(self, event) -> None:
        if event.type == pygame.QUIT:
            self.quit = True
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.quit = True
            elif self.maze_gen is None:
                self._on_key(event.key)
            return
        if self.maze_gen is not None:  # ignore the mouse while the maze is being carved
            return
        for button in self.buttons:
            if button.handle(event):
                return
        if self.slider.handle(event):
            return
        self._on_grid_mouse(event)

    def _on_key(self, key: int) -> None:
        actions = {
            pygame.K_SPACE: self.toggle_run,
            pygame.K_s: self.step,
            pygame.K_r: self.reset_search,
            pygame.K_c: self.clear,
            pygame.K_m: self.make_maze,
        }
        if key in actions:
            actions[key]()
        elif pygame.K_1 <= key < pygame.K_1 + len(ALGO_ORDER):
            self.select_algo(ALGO_ORDER[key - pygame.K_1])

    def _on_grid_mouse(self, event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
            cell = self.cell_at(event.pos)
            if cell is None:
                return
            self.last_cell = cell
            if event.button == 1 and cell == self.start:
                self.drag = "start"
            elif event.button == 1 and cell == self.goal:
                self.drag = "goal"
            else:
                value = self.tool if event.button == 1 else EMPTY
                if self.grid.get(cell) == value:
                    value = EMPTY  # clicking an already painted cell erases it
                self.drag, self.paint_value = "paint", value
                self._paint(cell)
        elif event.type == pygame.MOUSEMOTION and self.drag:
            cell = self.cell_at(event.pos)
            if cell is None or self.last_cell is None or cell == self.last_cell:
                return
            if self.drag == "paint":
                for node in line_cells(self.last_cell, cell):
                    self._paint(node)
            else:
                self._move_marker(self.drag, cell)
            self.last_cell = cell
        elif event.type == pygame.MOUSEBUTTONUP and event.button in (1, 3):
            self.drag = None

    def _paint(self, node: Node) -> None:
        if node in (self.start, self.goal) or self.grid.get(node) == self.paint_value:
            return
        self.grid.set(node, self.paint_value)
        self.invalidate()

    def _move_marker(self, which: str, node: Node) -> None:
        other = self.goal if which == "start" else self.start
        if node == other:
            return
        self.grid.set(node, EMPTY)
        if which == "start":
            self.start = node
        else:
            self.goal = node
        self.invalidate()

    # ------------------------------------------------------------- drawing
    def status(self) -> tuple[str, tuple[int, int, int]]:
        if self.maze_gen is not None:
            return "Membuat labirin...", theme.MUTED
        s = self.searcher
        if s is None:
            return "Gambar rintangan, lalu tekan Mulai", theme.MUTED
        if s.done:
            result = self.results[s.name]
            if result.steps is None:
                return "Tidak ada jalur", theme.END
            return f"Jalur ditemukan: {result.steps} langkah", theme.PATH
        label = "Mencari" if self.running else "Dijeda"
        return f"{label} - {s.visited} sel dikunjungi", theme.MUTED

    def draw(self) -> None:
        self.screen.fill(theme.BG)
        self._draw_grid()
        self._draw_panel()
        self._draw_footer()

    def _draw_grid(self) -> None:
        s = self.screen
        pygame.draw.rect(s, theme.LINE, (GRID_X, GRID_Y, GRID_W, GRID_H))
        cells = self.grid.cells
        for r in range(ROWS):
            y = GRID_Y + r * CELL
            for c in range(COLS):
                x = GRID_X + c * CELL
                terrain = cells[r][c]
                if terrain == WALL:
                    pygame.draw.rect(s, theme.WALL, (x, y, CELL, CELL))
                    continue
                node = (r, c)
                color = theme.MUD if terrain == MUD else theme.CELL
                stamp = self.visited.get(node)
                if node == self.maze_head:
                    color = theme.PATH
                elif stamp is not None:
                    base = theme.VISITED if terrain == EMPTY else mix(theme.VISITED, theme.MUD, 0.35)
                    age = self.now - stamp
                    color = mix(theme.POP, base, age / POP_SECONDS) if age < POP_SECONDS else base
                elif node in self.frontier:
                    color = theme.FRONTIER
                pygame.draw.rect(s, color, (x, y, CELL - 1, CELL - 1), border_radius=3)

        if self.path and self.path_progress >= 1:
            count = min(int(self.path_progress) + 1, len(self.path))
            points = [self._center(n) for n in self.path[:count]]
            pygame.draw.lines(s, theme.PATH, False, points, 5)
            for p in points:
                pygame.draw.circle(s, theme.PATH, p, 2)

        if self.maze_gen is None:
            sx, sy = self._center(self.start)
            pygame.draw.circle(s, theme.START, (sx, sy), 8)
            gx, gy = self._center(self.goal)
            pygame.draw.circle(s, theme.END, (gx, gy), 8)
            pygame.draw.circle(s, theme.BG, (gx, gy), 3)

    @staticmethod
    def _center(node: Node) -> tuple[int, int]:
        return (GRID_X + node[1] * CELL + CELL // 2 - 1,
                GRID_Y + node[0] * CELL + CELL // 2 - 1)

    def _draw_panel(self) -> None:
        s = self.screen
        mouse = pygame.mouse.get_pos()
        panel = pygame.Rect(PANEL_X, GRID_Y, PANEL_W, GRID_H)
        pygame.draw.rect(s, theme.PANEL, panel, border_radius=10)
        pygame.draw.rect(s, theme.LINE, panel, 1, border_radius=10)

        draw_text(s, "Pathfinding", (INNER_X, 34), 22, bold=True)
        text, color = self.status()
        draw_text(s, text, (INNER_X, 66), 13, color)

        def label(text: str, y: int) -> None:
            draw_text(s, text, (INNER_X, y), 11, theme.MUTED, bold=True)

        label("ALGORITMA", 94)
        label("ALAT GAMBAR", 226)
        label("KECEPATAN", 284)

        for i, line in enumerate(wrap(ALGORITHM_INFO[self.algo], 13, INNER_W)):
            draw_text(s, line, (INNER_X, 182 + i * 17), 13, theme.MUTED)

        draw_text(s, f"{int(self.speed())} sel/dtk", (INNER_X + INNER_W, 283), 12,
                  theme.MUTED, align="right")
        self.slider.draw(s)
        for button in self.buttons:
            button.draw(s, mouse)
        self._draw_table()

    def _draw_table(self) -> None:
        s = self.screen
        draw_text(s, "PERBANDINGAN", (INNER_X, 486), 11, theme.MUTED, bold=True)
        cols = {"sel": 118, "langkah": 170, "biaya": 210, "ms": INNER_W}
        y = 506
        draw_text(s, "Algoritma", (INNER_X, y), 11, theme.MUTED)
        for key, title in (("sel", "Sel"), ("langkah", "Langkah"), ("biaya", "Biaya"), ("ms", "ms")):
            draw_text(s, title, (INNER_X + cols[key], y), 11, theme.MUTED, align="right")

        # Highlight the cheapest search, but only among algorithms that found the best path.
        costs = [r.cost for r in self.results.values() if r.cost is not None]
        best = [r.visited for r in self.results.values()
                if r.cost is not None and r.cost == min(costs)]
        fewest = min(best) if len(self.results) > 1 and best else None
        dash = "-"
        for i, name in enumerate(ALGO_ORDER):
            row_y = 524 + i * 22
            active = name == self.algo
            if active:
                pygame.draw.rect(s, theme.ROW_ACTIVE,
                                 (INNER_X - 8, row_y - 3, INNER_W + 16, 22), border_radius=5)
            draw_text(s, name, (INNER_X, row_y), 13, theme.TEXT if active else theme.MUTED, bold=active)
            r = self.results.get(name)
            values = {
                "sel": (str(r.visited) if r else dash,
                        theme.START if r and r.cost is not None and r.visited == fewest
                        else theme.TEXT),
                "langkah": (str(r.steps) if r and r.steps is not None else dash, theme.TEXT),
                "biaya": (str(r.cost) if r and r.cost is not None else dash, theme.TEXT),
                "ms": (f"{r.ms:.1f}" if r else dash, theme.TEXT),
            }
            for key, (value, col) in values.items():
                draw_text(s, value, (INNER_X + cols[key], row_y), 13,
                          col if r else theme.MUTED, align="right")

    def _draw_footer(self) -> None:
        s = self.screen
        y = GRID_Y + GRID_H + 14
        x = GRID_X
        items = (("Start", theme.START), ("Tujuan", theme.END), ("Dinding", theme.WALL),
                 ("Lumpur (biaya 5)", theme.MUD), ("Frontier", theme.FRONTIER),
                 ("Dikunjungi", theme.VISITED), ("Jalur", theme.PATH))
        for name, color in items:
            pygame.draw.rect(s, color, (x, y + 2, 12, 12), border_radius=3)
            rect = draw_text(s, name, (x + 18, y), 12, theme.MUTED)
            x = rect.right + 22
        draw_text(s, "Spasi: mulai/jeda   S: langkah   M: labirin   1-4: algoritma   klik kanan: hapus",
                  (PANEL_X + PANEL_W, y), 12, theme.MUTED, align="right")

    # ----------------------------------------------------------------- run
    def run(self) -> None:
        while not self.quit:
            dt = min(self.clock.tick(60) / 1000, 0.05)
            self.now = pygame.time.get_ticks() / 1000
            for event in pygame.event.get():
                self.handle(event)
            self.tick(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()
