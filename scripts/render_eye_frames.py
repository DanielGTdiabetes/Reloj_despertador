#!/usr/bin/env python3
"""
render_eye_frames.py
Pre-renders minion eye animations for GC9A01 round display (240×240).
Output: src/assets/animations/eye_*.npy  →  uint8 RGB, shape (N, H, W, 3)

Run ONCE on Windows:  python scripts/render_eye_frames.py
"""

import math
import os

import numpy as np
from PIL import Image, ImageDraw

# ── Canvas ────────────────────────────────────────────────────────────────────
W = H = 240
CX = CY = 120

# ── Palette ───────────────────────────────────────────────────────────────────
SKIN_COL    = (168, 108,  62)   # dark skin tone (eyelid)
BLACK       = (0, 0, 0)
GOGGLE_DARK = (22, 18, 14)      # outer ring dark metal
GOGGLE_MID  = (50, 44, 38)      # inner highlight band
GOGGLE_SHAD = (12, 10, 8)       # shadow just inside ring

SCLERA_COL  = (243, 239, 229)   # warm white

IRIS_IN_COL   = np.array([155, 62, 228], np.float32)   # bright violet center
IRIS_MID_COL  = np.array([ 90, 16, 160], np.float32)   # mid violet
IRIS_EDGE_COL = np.array([ 13,  3,  36], np.float32)   # limbal ring (dark)
COLLAR_COL    = np.array([180, 90, 250], np.float32)    # collarette ring

PUPIL_COL  = (8, 5, 14)         # near-black
SPEC1_COL  = (255, 255, 255)    # main specular
SPEC2_COL  = (210, 225, 255)    # secondary (cool tint)
EYELID_EDG = (16, 12, 8)        # eyelid lower edge line

# ── Geometry ──────────────────────────────────────────────────────────────────
R_OUT  = 116    # goggle outer circle
R_BAND = 110    # metallic highlight band inner edge
R_SHAD =  104   # shadow band inner edge
R_IN   =  100   # sclera starts here
ICX    =  120   # iris center x
ICY    =  123   # iris center y (slightly lower for natural look)
R_IRIS =   63   # iris radius
PW     =   20   # pupil half-width  (horizontal)
PH     =   27   # pupil half-height (vertical oval → creature feel)
MAX_DX =   18   # max horizontal iris travel
MAX_DY =   12   # max vertical iris travel

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "assets", "animations")

# ── Pre-built coordinate grids (computed once) ────────────────────────────────
_YY, _XX = np.mgrid[0:H, 0:W].astype(np.float32)
_DIST_C  = np.sqrt((_XX - CX) ** 2 + (_YY - CY) ** 2)

# ── Easing ────────────────────────────────────────────────────────────────────
def _ease_io(t: float) -> float:
    t = float(np.clip(t, 0, 1))
    return t * t * (3 - 2 * t)

def _ease_o(t: float) -> float:
    t = float(np.clip(t, 0, 1))
    return 1 - (1 - t) ** 2

def _lerp(a, b, t):
    return a + (b - a) * float(np.clip(t, 0, 1))

# ── Build iris texture (once) ─────────────────────────────────────────────────
def _build_iris_tex() -> np.ndarray:
    """240×240×3 float32.  Violet iris centered at (ICX, ICY), zero outside."""
    dx   = _XX - ICX
    dy   = _YY - ICY
    dist = np.sqrt(dx ** 2 + dy ** 2)
    t    = np.clip(dist / R_IRIS, 0, 1.0)
    ang  = np.arctan2(dy, dx)

    # Radial colour gradient: inner → mid → limbal
    b_mid  = np.clip(t / 0.68, 0, 1)[..., None]
    b_edge = np.clip((t - 0.68) / 0.32, 0, 1)[..., None]
    col    = IRIS_IN_COL  * (1 - b_mid)  + IRIS_MID_COL  * b_mid
    col    = col          * (1 - b_edge) + IRIS_EDGE_COL  * b_edge

    # Multi-frequency fiber texture (radial striations)
    fiber = (np.sin(ang * 40) * 0.11
           + np.sin(ang * 21 + 0.9) * 0.065
           + np.sin(ang * 9  - 0.4) * 0.035)
    col  *= (1.0 + fiber[..., None])

    # Collarette ring at t ≈ 0.37 (structural ring of the iris)
    c_dist  = np.abs(t - 0.37)
    c_blend = np.clip(1.0 - c_dist / 0.048, 0, 1)[..., None] * 0.50
    col     = col * (1 - c_blend) + COLLAR_COL * c_blend

    # Zero outside iris circle
    mask = (dist < R_IRIS).astype(np.float32)[..., None]
    return np.clip(col, 0, 255) * mask


_IRIS_TEX = _build_iris_tex()   # built at import, reused for every frame

# ── Build sclera layer (once) ─────────────────────────────────────────────────
def _build_sclera() -> np.ndarray:
    """240×240×3 float32 warm-white sclera with subtle radial vignette."""
    col = np.full((H, W, 3), SCLERA_COL, dtype=np.float32)
    t   = np.clip(_DIST_C / R_IN, 0, 1)[..., None]
    col *= (1.0 - t * 0.10)
    return col

_SCLERA = _build_sclera()

# ── Eyelash renderer (PIL overlay) ───────────────────────────────────────────
def _draw_eyelashes(arr: np.ndarray, eff_lid: float) -> np.ndarray:
    """Draw curved eyelashes along the eyelid edge.  Returns uint8 RGB array."""
    top_y = CY - R_IN + 1
    bot_y = CY + R_IN - 1
    lid_y = top_y + eff_lid * (bot_y - top_y)

    # x-extent of the goggle at lid_y
    dy = lid_y - CY
    if abs(dy) >= R_IN - 4:
        return arr

    dx_ext  = math.sqrt(max(0.0, (R_IN - 4) ** 2 - dy ** 2))
    x_left  = CX - dx_ext
    x_right = CX + dx_ext
    span    = x_right - x_left

    img  = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)

    LASH_COLOR = (8, 6, 4)
    N_LASHES   = 9

    for i in range(N_LASHES):
        pos = (i + 0.5) / N_LASHES          # 0 … 1 along the lash line
        lx  = x_left + pos * span
        # Curved lid at this x (matches the numpy mask above)
        x_n   = (lx - CX) / float(R_IN)
        ly    = lid_y + 5.0 * (1.0 - x_n ** 2)

        # Centre factor: 1 at centre, 0 at corners
        centre = 1.0 - abs(pos - 0.5) * 2.0

        # Length: 9 px at corners → 17 px at centre
        length = 9.0 + centre * 8.0

        # Fan direction: lashes spread outward from centre
        x_bias = (pos - 0.5) * 2.0          # –1 left … +1 right

        # Bezier control & end points  (lash hangs below lid edge)
        p0 = (lx,                  ly)
        p1 = (lx + x_bias * length * 0.30,  ly + length * 0.55)
        p2 = (lx + x_bias * length * 0.52,  ly + length * 0.95)

        # Approximate bezier with 16 segments
        pts = []
        for s in range(17):
            t = s / 16.0
            u = 1.0 - t
            bx = u*u*p0[0] + 2*t*u*p1[0] + t*t*p2[0]
            by = u*u*p0[1] + 2*t*u*p1[1] + t*t*p2[1]
            pts.append((bx, by))

        # Draw with taper: thick at root, 1px at tip
        for s in range(len(pts) - 1):
            w = 3 if s < 4 else (2 if s < 10 else 1)
            draw.line([pts[s], pts[s + 1]], fill=LASH_COLOR, width=w)

    return np.array(img)


# ── Core frame renderer ───────────────────────────────────────────────────────
def render_frame(
    pupil_dx: float = 0.0,   # -1 … +1  →  ±MAX_DX px  (left/right)
    pupil_dy: float = 0.0,   # -1 … +1  →  ±MAX_DY px  (up/down, neg=up)
    lid:      float = 0.0,   # 0=fully open, 1=fully closed
    squint:   float = 0.0,   # 0=normal, 1=half-lid suspicious squint
) -> np.ndarray:
    """Returns uint8 RGB array (H×W×3)."""
    arr = np.zeros((H, W, 3), dtype=np.float32)

    # 1. Goggle outer ring (dark metal)
    ring = _DIST_C <= R_OUT
    arr[ring] = GOGGLE_DARK

    # 2. Metallic highlight band (slightly lighter)
    band = _DIST_C <= R_BAND
    arr[band] = GOGGLE_MID

    # 3. Shadow just inside ring
    shad = _DIST_C <= R_SHAD
    arr[shad] = GOGGLE_SHAD

    # 4. Sclera (warm white)
    sc = _DIST_C < R_IN
    arr[sc] = _SCLERA[sc]

    # 5. Iris — shift texture by pupil offset
    px = int(round(ICX + pupil_dx * MAX_DX))
    py = int(round(ICY + pupil_dy * MAX_DY))
    sx, sy = px - ICX, py - ICY

    iris_sh = np.roll(np.roll(_IRIS_TEX, sy, axis=0), sx, axis=1)

    dxi = _XX - px
    dyi = _YY - py
    iris_mask = (np.sqrt(dxi ** 2 + dyi ** 2) < R_IRIS) & sc
    has_color  = iris_sh.sum(axis=2) > 0
    paste      = iris_mask & has_color
    arr[paste] = iris_sh[paste]

    # 6. Pupil (vertical oval)
    pupil = (dxi / PW) ** 2 + (dyi / PH) ** 2 < 1.0
    arr[pupil] = PUPIL_COL

    # 7. Specular highlights
    # Main — oval, upper-left of pupil
    h1x, h1y = px - 7, py - 11
    h1 = ((_XX - h1x) ** 2 / 7.0 ** 2 + (_YY - h1y) ** 2 / 5.0 ** 2) < 1.0
    arr[h1] = SPEC1_COL
    # Secondary — small circle
    h2x, h2y = px + 5, py - 7
    h2 = (_XX - h2x) ** 2 + (_YY - h2y) ** 2 < 9.0
    arr[h2] = SPEC2_COL

    # 8. Eyelid
    eff_lid = float(np.clip(max(lid, squint * 0.52), 0, 1))
    if eff_lid > 0.005:
        top_y  = CY - R_IN + 1
        bot_y  = CY + R_IN - 1
        lid_y  = top_y + eff_lid * (bot_y - top_y)

        # Curved lid edge: slightly convex toward the eye (dips ~5px at centre)
        x_norm    = (_XX - CX) / float(R_IN)          # –1 … +1
        lid_curve = lid_y + 5.0 * (1.0 - x_norm ** 2) # 2-D per-pixel threshold

        lid_px = (_YY <= lid_curve) & sc
        arr[lid_px] = SKIN_COL

        # Subtle crease shadow: eyelid darkens near the top (goggle edge)
        if eff_lid > 0.08:
            crease_y = float(top_y)
            span     = max(lid_y - crease_y, 1.0)
            # normalised distance 0=crease … 1=lid edge
            d_norm   = np.clip((_YY - crease_y) / span, 0, 1)
            shadow   = (0.72 + 0.28 * d_norm)[..., None]  # 0.72 at crease, 1.0 at edge
            skin_f   = np.array(SKIN_COL, dtype=np.float32)
            arr[lid_px] = (skin_f * shadow[lid_px]).clip(0, 255)

        # Dark curved lash line at lid edge
        if eff_lid < 0.96:
            lash_line = (np.abs(_YY - lid_curve) < 2.5) & sc
            arr[lash_line] = EYELID_EDG

    # 9. Black outside display circle (corners are off-display on GC9A01)
    arr[_DIST_C > R_OUT] = BLACK

    # 10. Eyelashes (PIL overlay — only when lid is visible)
    uint8 = arr.clip(0, 255).astype(np.uint8)
    if eff_lid > 0.03:
        uint8 = _draw_eyelashes(uint8, eff_lid)

    return uint8


# ── Animation clip builders ───────────────────────────────────────────────────
def clip_idle() -> np.ndarray:
    return render_frame()[None]          # shape (1, H, W, 3)


def clip_blink_fast(n: int = 8) -> np.ndarray:
    half = n // 2
    frames = []
    for i in range(half):
        frames.append(render_frame(lid=_ease_io(i / max(half - 1, 1))))
    for i in range(half):
        frames.append(render_frame(lid=_ease_o(1 - i / max(half - 1, 1))))
    return np.stack(frames)


def clip_blink_slow() -> np.ndarray:
    frames = []
    for i in range(6):                          # close
        frames.append(render_frame(lid=_ease_io(i / 5)))
    for _ in range(3):                          # hold
        frames.append(render_frame(lid=1.0))
    for i in range(9):                          # open (slower)
        frames.append(render_frame(lid=_ease_o(1 - i / 8)))
    return np.stack(frames)


def clip_double_blink() -> np.ndarray:
    b1    = clip_blink_fast(8)
    pause = np.stack([render_frame()] * 5)
    b2    = clip_blink_fast(8)
    return np.concatenate([b1, pause, b2])


def clip_saccade(dx_t: float, dy_t: float = 0.0,
                 hold: int = 7, n_move: int = 4) -> np.ndarray:
    frames = []
    for i in range(n_move):
        t = _ease_io(i / max(n_move - 1, 1))
        frames.append(render_frame(pupil_dx=dx_t * t, pupil_dy=dy_t * t))
    for _ in range(hold):
        frames.append(render_frame(pupil_dx=dx_t, pupil_dy=dy_t))
    for i in range(n_move):
        t = _ease_io(1 - i / max(n_move - 1, 1))
        frames.append(render_frame(pupil_dx=dx_t * t, pupil_dy=dy_t * t))
    return np.stack(frames)


def clip_suspicious() -> np.ndarray:
    """Squint eyelid halfway + iris drifts sideways → holds → returns."""
    frames = []
    n = 7
    for i in range(n):
        t = _ease_io(i / (n - 1))
        frames.append(render_frame(squint=t, pupil_dx=_lerp(0, 0.78, t)))
    for _ in range(14):
        frames.append(render_frame(squint=1.0, pupil_dx=0.78))
    for i in range(n):
        t = _ease_io(1 - i / (n - 1))
        frames.append(render_frame(squint=t, pupil_dx=_lerp(0, 0.78, t)))
    return np.stack(frames)


def clip_sleepy() -> np.ndarray:
    """Very slow blink — closes, rests, opens. Looks drowsy."""
    frames = []
    for i in range(10):                         # slow close
        frames.append(render_frame(lid=_ease_io(i / 9)))
    for _ in range(10):                         # rest closed
        frames.append(render_frame(lid=1.0))
    for i in range(13):                         # slow open
        frames.append(render_frame(lid=_ease_o(1 - i / 12)))
    return np.stack(frames)


def clip_saccade_diagonal() -> np.ndarray:
    """Up-right glance — adds personality."""
    return clip_saccade(0.7, -0.8, hold=6, n_move=4)


# ── Clip registry ─────────────────────────────────────────────────────────────
CLIPS = {
    "idle":             clip_idle,
    "blink_fast":       clip_blink_fast,
    "blink_slow":       clip_blink_slow,
    "double_blink":     clip_double_blink,
    "saccade_left":     lambda: clip_saccade(-1.0),
    "saccade_right":    lambda: clip_saccade( 1.0),
    "saccade_up":       lambda: clip_saccade(0.0, -1.0, hold=5),
    "saccade_diagonal": clip_saccade_diagonal,
    "suspicious":       clip_suspicious,
    "sleepy":           clip_sleepy,
}

# ── Preview helper (optional) ─────────────────────────────────────────────────
def preview_clip(name: str, fps: int = 9) -> None:
    """Show a clip in an OpenCV window (dev use only)."""
    try:
        import cv2, time as _t
        arr = CLIPS[name]()
        delay = 1.0 / fps
        for f in arr:
            cv2.imshow(f"eye_{name}", cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            _t.sleep(delay)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except ImportError:
        print("pip install opencv-python  para preview")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Output -> {os.path.abspath(OUT_DIR)}\n")

    total_mb = 0.0
    for name, fn in CLIPS.items():
        print(f"  rendering eye_{name} ...", end="  ", flush=True)
        arr  = fn()
        path = os.path.join(OUT_DIR, f"eye_{name}.npy")
        np.save(path, arr)
        mb = arr.nbytes / 1_048_576
        total_mb += mb
        print(f"{arr.shape[0]:3d} frames   {mb:.1f} MB")

    print(f"\nTotal: {total_mb:.1f} MB")
    print("Listo. Ejecuta: python scripts/render_mouth_frames.py")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        preview_clip(sys.argv[1])
    else:
        main()
