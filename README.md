# Pathfinding Visualizer

Visualizer algoritma pencarian rute pada grid, murni Python + pygame.

## Menjalankan

```
pip install -r requirements.txt
python main.py
```

## Cara pakai

| Aksi | Cara |
| --- | --- |
| Gambar dinding / lumpur | Pilih alat, lalu klik-seret di grid |
| Hapus | Klik kanan, atau alat *Hapus* (klik sel yang sudah terisi juga menghapusnya) |
| Pindahkan start / tujuan | Seret titik hijau / merah |
| Labirin otomatis | **Buat Labirin** (Recursive Backtracking, dianimasikan) |
| Jalankan | **Mulai** (Spasi), **Langkah** (S) untuk satu langkah |
| Bandingkan | **Bandingkan** menjalankan keempat algoritma pada grid yang sama; angka hijau = sel paling sedikit di antara algoritma dengan jalur optimal |

Lumpur berbiaya 5 (sel biasa 1). BFS dan DFS mengabaikan biaya, sedangkan Dijkstra dan A* menghindari lumpur.

## Struktur

- `pathviz/grid.py` — grid 2D (matrix), tetangga, biaya sel
- `pathviz/algorithms.py` — BFS (queue), DFS (stack), Dijkstra & A* (priority queue / heap), ditulis sebagai generator
- `pathviz/maze.py` — Recursive Backtracking dengan stack eksplisit
- `pathviz/app.py` — antarmuka pygame
- `docs/PENJELASAN.md` — penjelasan lengkap algoritma, struktur data, PRD, dan ERD
- `tests/` — `python -m unittest discover -s tests -t .`
