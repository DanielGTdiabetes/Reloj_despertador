"""
remove_moon_bg.py — Elimina el fondo negro de los assets de fases lunares.
Usa BFS flood-fill desde las 4 esquinas con tolerancia de color.
Los resultados quedan en src/assets/moon_phases/processed/
"""
from __future__ import annotations
import numpy as np
from PIL import Image, ImageFilter
from pathlib import Path
from collections import deque


ASSETS_DIR = Path(__file__).parent.parent / "src" / "assets" / "moon_phases"
OUT_DIR = ASSETS_DIR / "processed"
TOLERANCE = 38    # distancia euclidea en RGB para considerar pixel como fondo
FEATHER = 1.2     # radio de blur suave en bordes (px)


def bfs_bg_mask(arr: np.ndarray, seeds: list[tuple[int, int]], tol: float) -> np.ndarray:
    h, w = arr.shape[:2]
    visited = np.zeros((h, w), dtype=bool)
    bg = np.zeros((h, w), dtype=bool)
    queue: deque = deque()

    seed_colors = []
    for (y, x) in seeds:
        if not visited[y, x]:
            visited[y, x] = True
            bg[y, x] = True
            queue.append((y, x))
            seed_colors.append(arr[y, x, :3].astype(float))

    seed_mean = np.mean(seed_colors, axis=0)

    while queue:
        y, x = queue.popleft()
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx]:
                dist = float(np.linalg.norm(arr[ny, nx, :3].astype(float) - seed_mean))
                if dist < tol:
                    visited[ny, nx] = True
                    bg[ny, nx] = True
                    queue.append((ny, nx))

    return bg


def process(src: Path, dst: Path, tol: float, feather: float) -> None:
    img = Image.open(src).convert("RGBA")
    arr = np.array(img, dtype=np.uint8)
    h, w = arr.shape[:2]

    seeds = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
    bg_mask = bfs_bg_mask(arr, seeds, tol)

    # Poner alpha=0 en pixels de fondo
    arr[bg_mask, 3] = 0

    # Feathering suave en los bordes de la luna
    if feather > 0:
        alpha_img = Image.fromarray(arr[:, :, 3], mode="L")
        alpha_img = alpha_img.filter(ImageFilter.GaussianBlur(radius=feather))
        arr[:, :, 3] = np.array(alpha_img, dtype=np.uint8)

    Image.fromarray(arr).save(dst, format="PNG")
    print(f"  OK  {src.name}  ->  {dst}")


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)

    phases = sorted(p for p in ASSETS_DIR.glob("*.png") if p.is_file())
    if not phases:
        print("No se encontraron PNGs en", ASSETS_DIR)
        return

    print(f"Procesando {len(phases)} imágenes con tolerancia={TOLERANCE}, feather={FEATHER}...")
    for src in phases:
        dst = OUT_DIR / src.name
        process(src, dst, TOLERANCE, FEATHER)

    print(f"\nListo. Resultados en: {OUT_DIR}")


if __name__ == "__main__":
    main()
