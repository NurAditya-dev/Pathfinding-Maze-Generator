"""Render docs/prd.png and docs/erd.png using pygame only.

Run from the project root:  python docs/generate_diagrams.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pathviz import theme  # noqa: E402  (reuse the app palette)

pygame.init()
pygame.display.set_mode((1, 1))

_fonts: dict = {}


def font(size: int, bold: bool = False) -> pygame.font.Font:
    if (size, bold) not in _fonts:
        _fonts[(size, bold)] = pygame.font.SysFont("segoeui,arial", size, bold=bold)
    return _fonts[(size, bold)]


def text(s, msg, pos, size=14, color=theme.TEXT, bold=False, align="left"):
    img = font(size, bold).render(msg, True, color)
    rect = img.get_rect()
    setattr(rect, {"left": "topleft", "right": "topright", "center": "center"}[align], pos)
    s.blit(img, rect)
    return rect


def wrap(msg: str, size: int, width: int, bold: bool = False) -> list[str]:
    f = font(size, bold)
    lines, line = [], ""
    for word in msg.split():
        trial = f"{line} {word}".strip()
        if f.size(trial)[0] <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


# ---------------------------------------------------------------------- PRD
PRIORITY_COLOR = {"P0": theme.END, "P1": theme.PATH, "P2": theme.ACCENT}

LEFT_CARDS = [
    ("Latar belakang & masalah", [
        ("p", "Algoritma pencarian rute sulit dipahami hanya dari kode atau teori. Penonton dan "
              "mahasiswa perlu melihat sendiri bagaimana tiap algoritma menjelajah grid, dan "
              "mengapa hasilnya berbeda."),
    ]),
    ("Tujuan produk", [
        ("b", "Menampilkan BFS, DFS, Dijkstra, dan A* langkah demi langkah secara real-time."),
        ("b", "Pengguna bisa menggambar rintangan sendiri atau membuat labirin otomatis."),
        ("b", "Membandingkan efisiensi algoritma pada grid yang sama dengan angka terukur."),
        ("b", "Murni Python, tampilan sederhana dan tidak berantakan."),
    ]),
    ("Target pengguna", [
        ("p", "Mahasiswa Algoritma & Pemrograman, dosen dan penonton demo, serta pemula yang "
              "belajar struktur data (queue, stack, heap)."),
    ]),
    ("User stories", [
        ("b", "Sebagai pengguna, saya ingin menggambar dinding agar bisa menguji rintangan versi saya."),
        ("b", "Saya ingin memindahkan titik start dan tujuan untuk mencoba berbagai skenario."),
        ("b", "Saya ingin membuat labirin acak dengan satu klik tanpa menggambar manual."),
        ("b", "Saya ingin mengatur kecepatan dan melangkah satu per satu untuk mengikuti logikanya."),
        ("b", "Saya ingin membandingkan BFS dan A* pada grid yang sama untuk melihat selisih "
              "sel yang dijelajahi."),
    ]),
    ("Metrik keberhasilan", [
        ("b", "Jalur Dijkstra dan A* selalu sama optimal (diverifikasi unit test pada 150 grid acak)."),
        ("b", "Pada grid kosong, A* menjelajah jauh lebih sedikit sel daripada BFS (contoh 67 vs 1267)."),
        ("b", "Kasus tanpa jalur ditangani dengan pesan yang jelas, bukan crash."),
        ("b", "Target animasi 60 FPS pada grid 41 x 31."),
    ]),
]

RIGHT_CARDS = [
    ("Alur pengguna", [
        ("step", "Siapkan grid: gambar dinding, buat labirin, atau dinding acak."),
        ("step", "Atur titik start dan tujuan dengan menyeretnya."),
        ("step", "Pilih algoritma: BFS, DFS, Dijkstra, atau A*."),
        ("step", "Tekan Mulai dan amati sel frontier serta sel yang dikunjungi."),
        ("step", "Jalur terpendek muncul, statistik tercatat di tabel."),
        ("step", "Tekan Bandingkan untuk menjalankan keempat algoritma sekaligus."),
    ]),
    ("Fitur & prioritas", [
        ("tag", "P0", "Grid 41 x 31, gambar dinding, start dan tujuan dapat diseret."),
        ("tag", "P0", "BFS, DFS, Dijkstra, A* dengan animasi."),
        ("tag", "P0", "Kontrol Mulai, Jeda, Langkah, Reset, dan slider kecepatan."),
        ("tag", "P1", "Labirin Recursive Backtracking yang dianimasikan."),
        ("tag", "P1", "Lumpur (biaya 5) agar algoritma berbobot terlihat bedanya."),
        ("tag", "P1", "Tabel perbandingan: sel, langkah, biaya, waktu (ms)."),
        ("tag", "P2", "Dinding acak dan pintasan keyboard."),
    ]),
    ("Kebutuhan non-fungsional", [
        ("b", "Hanya Python 3 dan pygame."),
        ("b", "Algoritma berupa generator, terpisah dari UI sehingga mudah diuji."),
        ("b", "Tanpa database: seluruh state disimpan di memori."),
    ]),
    ("Di luar cakupan", [
        ("b", "Gerak diagonal dan ukuran grid dinamis."),
        ("b", "Simpan dan muat peta."),
        ("b", "Algoritma lain (Greedy Best-First, JPS) serta versi web atau mobile."),
    ]),
]


def render_items(s, x, y, w, items) -> int:
    """Draw card body items; returns the y just below the last one."""
    step_no = 0
    for item in items:
        kind = item[0]
        if kind == "p":
            for line in wrap(item[1], 14, w):
                text(s, line, (x, y), 14, theme.TEXT)
                y += 21
            y += 4
        elif kind == "b":
            lines = wrap(item[1], 14, w - 18)
            pygame.draw.circle(s, theme.ACCENT, (x + 4, y + 10), 3)
            for line in lines:
                text(s, line, (x + 18, y), 14, theme.TEXT)
                y += 21
            y += 5
        elif kind == "step":
            step_no += 1
            lines = wrap(item[1], 14, w - 40)
            pygame.draw.circle(s, theme.ACCENT, (x + 11, y + 11), 11)
            text(s, str(step_no), (x + 11, y + 11), 13, theme.ACCENT_TEXT, True, "center")
            for line in lines:
                text(s, line, (x + 34, y + 1), 14, theme.TEXT)
                y += 21
            y += 8
        elif kind == "tag":
            lines = wrap(item[2], 14, w - 46)
            pill = pygame.Rect(x, y + 1, 32, 20)
            pygame.draw.rect(s, PRIORITY_COLOR[item[1]], pill, border_radius=10)
            text(s, item[1], pill.center, 12, theme.ACCENT_TEXT, True, "center")
            for line in lines:
                text(s, line, (x + 44, y), 14, theme.TEXT)
                y += 21
            y += 5
    return y


def draw_card(s, x, y, w, title, items) -> int:
    pad = 20
    scratch = pygame.Surface((10, 10))
    body_h = render_items(scratch, 0, 0, w - 2 * pad, items)
    h = 56 + body_h + pad - 6
    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(s, theme.PANEL, rect, border_radius=12)
    pygame.draw.rect(s, theme.LINE, rect, 1, border_radius=12)
    text(s, title.upper(), (x + pad, y + 18), 13, theme.ACCENT, True)
    render_items(s, x + pad, y + 48, w - 2 * pad, items)
    return y + h


def make_prd(path: Path) -> None:
    W, margin, gap = 1560, 40, 24
    col_w = (W - 2 * margin - gap) // 2
    s = pygame.Surface((W, 3000))
    s.fill(theme.BG)

    text(s, "PRODUCT REQUIREMENTS DOCUMENT", (margin, 36), 13, theme.ACCENT, True)
    text(s, "Pathfinding Visualizer & Maze Generator", (margin, 58), 34, theme.TEXT, True)
    text(s, "Versi 1.0   |   Aplikasi desktop   |   Python 3 + pygame", (margin, 106), 15, theme.MUTED)

    ends = []
    for x, cards in ((margin, LEFT_CARDS), (margin + col_w + gap, RIGHT_CARDS)):
        y = 150
        for title, items in cards:
            y = draw_card(s, x, y, col_w, title, items) + gap
        ends.append(y)
    height = max(ends) + margin - gap
    pygame.image.save(s.subsurface((0, 0, W, height)), str(path))


# ---------------------------------------------------------------------- ERD
ENTITY_W = 330
HEAD_H = 38
ROW_H = 28

# name -> (accent colour, attributes as (keys, name, type))
ENTITIES = {
    "MAZE_GENERATOR": (theme.START, [
        ("PK", "generator_id", "int"),
        ("", "method", "text"),
        ("", "loops", "float"),
        ("", "seed", "int"),
    ]),
    "GRID": (theme.ACCENT, [
        ("PK", "grid_id", "int"),
        ("", "rows", "int"),
        ("", "cols", "int"),
        ("FK", "generator_id", "int, null"),
    ]),
    "SEARCH_RUN": (theme.FRONTIER, [
        ("PK", "run_id", "int"),
        ("FK", "grid_id", "int"),
        ("FK", "algorithm", "text"),
        ("", "visited_count", "int"),
        ("", "elapsed_ms", "float"),
        ("", "done", "bool"),
        ("", "path", "list of cell"),
    ]),
    "ALGORITHM": (theme.PATH, [
        ("PK", "name", "BFS | DFS | Dijkstra | A*"),
        ("", "data_structure", "text"),
        ("", "uses_cost", "bool"),
        ("", "uses_heuristic", "bool"),
        ("", "optimal_path", "bool"),
    ]),
    "MARKER": (theme.ACCENT, [
        ("PK,FK", "grid_id", "int"),
        ("PK", "kind", "START | GOAL"),
        ("FK", "row", "int"),
        ("FK", "col", "int"),
    ]),
    "CELL": (theme.ACCENT, [
        ("PK,FK", "grid_id", "int"),
        ("PK", "row", "int"),
        ("PK", "col", "int"),
        ("", "terrain", "EMPTY | WALL | MUD"),
        ("", "cost", "1 | 5 (turunan)"),
    ]),
    "SEARCH_EVENT": (theme.FRONTIER, [
        ("PK,FK", "run_id", "int"),
        ("PK", "seq", "int"),
        ("", "kind", "VISIT | FRONTIER"),
        ("FK", "row", "int"),
        ("FK", "col", "int"),
    ]),
    "RESULT": (theme.FRONTIER, [
        ("PK,FK", "run_id", "int"),
        ("", "visited_count", "int"),
        ("", "steps", "int, null"),
        ("", "cost", "int, null"),
        ("", "elapsed_ms", "float"),
    ]),
}

COLS_X = [50, 500, 950, 1400]
ROW_Y = [100, 450]
POSITION = {
    "MAZE_GENERATOR": (0, 0), "GRID": (1, 0), "SEARCH_RUN": (2, 0), "ALGORITHM": (3, 0),
    "MARKER": (0, 1), "CELL": (1, 1), "SEARCH_EVENT": (2, 1), "RESULT": (3, 1),
}


def entity_rect(name: str) -> pygame.Rect:
    col, row = POSITION[name]
    n = len(ENTITIES[name][1])
    return pygame.Rect(COLS_X[col], ROW_Y[row], ENTITY_W, HEAD_H + n * ROW_H + 10)


def draw_entity(s, name: str) -> None:
    color, attrs = ENTITIES[name]
    r = entity_rect(name)
    pygame.draw.rect(s, theme.PANEL, r, border_radius=10)
    pygame.draw.rect(s, theme.LINE, r, 1, border_radius=10)
    head = pygame.Rect(r.x, r.y, r.w, HEAD_H)
    pygame.draw.rect(s, color, head, border_top_left_radius=10, border_top_right_radius=10)
    text(s, name, head.center, 16, theme.ACCENT_TEXT, True, "center")
    for i, (keys, attr, typ) in enumerate(attrs):
        y = r.y + HEAD_H + 8 + i * ROW_H
        bx = r.x + 12
        for key in keys.split(",") if keys else []:
            badge = pygame.Rect(bx, y + 2, 24, 17)
            pygame.draw.rect(s, theme.PATH if key == "PK" else theme.ACCENT, badge, border_radius=4)
            text(s, key, badge.center, 11, theme.ACCENT_TEXT, True, "center")
            bx += 28
        text(s, attr, (r.x + 68, y), 14, theme.TEXT, bold=bool(keys))
        text(s, typ, (r.right - 12, y + 1), 12, theme.MUTED, align="right")


def line(s, pts) -> None:
    pygame.draw.lines(s, theme.MUTED, False, pts, 2)


def h_edge(s, left: str, right: str, card_l: str, card_r: str, verb: str) -> None:
    a, b = entity_rect(left), entity_rect(right)
    y = a.y + HEAD_H // 2
    line(s, [(a.right, y), (b.left, y)])
    text(s, card_l, (a.right + 8, y - 22), 14, theme.TEXT, True)
    text(s, card_r, (b.left - 8, y - 22), 14, theme.TEXT, True, "right")
    text(s, verb, ((a.right + b.left) // 2, y + 14), 13, theme.MUTED, align="center")


def v_edge(s, top: str, bottom: str, card_t: str, card_b: str, verb: str,
           xt: int = 80, xb: int = 80) -> None:
    a, b = entity_rect(top), entity_rect(bottom)
    x1, x2 = a.x + xt, b.x + xb
    y1, y2 = a.bottom, b.top
    mid = (y1 + y2) // 2
    if x1 == x2:
        line(s, [(x1, y1), (x2, y2)])
        text(s, verb, (x1 + 12, mid - 9), 13, theme.MUTED)
    else:
        line(s, [(x1, y1), (x1, mid), (x2, mid), (x2, y2)])
        text(s, verb, ((x1 + x2) // 2, mid - 24), 13, theme.MUTED, align="center")
    text(s, card_t, (x1 + 10, y1 + 4), 14, theme.TEXT, True)
    text(s, card_b, (x2 + 10, y2 - 24), 14, theme.TEXT, True)


def make_erd(path: Path) -> None:
    W, H = 1780, 800
    s = pygame.Surface((W, H))
    s.fill(theme.BG)
    text(s, "ENTITY RELATIONSHIP DIAGRAM", (50, 28), 13, theme.ACCENT, True)
    text(s, "Model data Pathfinding Visualizer", (50, 46), 28, theme.TEXT, True)

    h_edge(s, "MAZE_GENERATOR", "GRID", "1", "N", "mengisi")
    h_edge(s, "GRID", "SEARCH_RUN", "1", "N", "dijelajahi")
    h_edge(s, "SEARCH_RUN", "ALGORITHM", "N", "1", "memakai")
    h_edge(s, "MARKER", "CELL", "1", "0..1", "menempati")
    h_edge(s, "CELL", "SEARCH_EVENT", "1", "N", "disentuh")
    v_edge(s, "GRID", "CELL", "1", "N", "terdiri dari")
    v_edge(s, "SEARCH_RUN", "SEARCH_EVENT", "1", "N", "mencatat")
    v_edge(s, "SEARCH_RUN", "RESULT", "1", "0..1", "menghasilkan", xt=280, xb=60)

    for name in ENTITIES:
        draw_entity(s, name)

    y = 700
    text(s, "Keterangan", (50, y), 13, theme.ACCENT, True)
    bx = 50
    for key, color, desc in (("PK", theme.PATH, "primary key"), ("FK", theme.ACCENT, "foreign key")):
        badge = pygame.Rect(bx, y + 28, 24, 17)
        pygame.draw.rect(s, color, badge, border_radius=4)
        text(s, key, badge.center, 11, theme.ACCENT_TEXT, True, "center")
        text(s, desc, (bx + 32, y + 27), 13, theme.MUTED)
        bx += 150
    text(s, "1 = satu     N = banyak     0..1 = opsional", (bx + 20, y + 27), 13, theme.MUTED)
    text(s, "Aplikasi tidak memakai database. ERD ini adalah model data konseptual yang dipetakan "
            "ke objek Python di memori (lihat docs/PENJELASAN.md).",
         (50, y + 54), 13, theme.MUTED)
    pygame.image.save(s, str(path))


if __name__ == "__main__":
    out = Path(__file__).resolve().parent
    make_prd(out / "prd.png")
    make_erd(out / "erd.png")
    print("ditulis:", out / "prd.png", out / "erd.png")
