#!/usr/bin/env python3
"""
render_mouth_frames.py
Pre-renders minion mouth animations for ST7789 rect display (284x76).

Clipping strategy: teeth are drawn on a separate layer and composited onto
the main image using the interior-polygon as mask, so they can NEVER bleed
outside the dark mouth area into the lip ring.

Tooth tracking: tooth_top_y is derived from both int_top_y (center arch) and
cy (corner height) so teeth follow the visible lip animation naturally.

Output: src/assets/animations/mouth_*.npy  (uint8 RGB, shape N x H x W x 3)
Run ONCE on Windows:  python scripts/render_mouth_frames.py
"""

import os
import numpy as np
from PIL import Image, ImageDraw
import math

# -- Canvas -------------------------------------------------------------------
W, H = 284, 76
MCX  = W // 2   # 142

# -- Palette ------------------------------------------------------------------
SKIN        = (168, 108,  62)
LIP_COL     = (155,  72,  85)
LIP_EDGE    = (110,  42,  55)
MOUTH_INT   = ( 88,  14,   6)
TEETH_COL   = (248, 240, 228)
TOOTH_SHADE = (200, 188, 172)
TOOTH_DIV   = ( 60,  10,   5)
GUM_UP      = (190,  60,  70)
GUM_DN      = (165,  28,  38)
TONGUE_COL  = (215,  50,  62)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "assets", "animations")

# -- Easing -------------------------------------------------------------------
def _eio(t):
    t = float(np.clip(t, 0, 1)); return t*t*(3-2*t)
def _eo(t):
    t = float(np.clip(t, 0, 1)); return 1-(1-t)**2
def _l(a, b, t):
    return a + (b-a)*float(np.clip(t, 0, 1))

# -- Bezier -------------------------------------------------------------------
def _qb(p0, p1, p2, n=80):
    pts = []
    for i in range(n+1):
        t=i/n; u=1-t
        pts.append((u*u*p0[0]+2*t*u*p1[0]+t*t*p2[0],
                    u*u*p0[1]+2*t*u*p1[1]+t*t*p2[1]))
    return pts

def _ip(pts):
    return [(int(round(x)), int(round(y))) for x,y in pts]

# -- Tooth helpers (draw onto any ImageDraw) ----------------------------------
def _upper_tooth(draw, cx, gum_y, tw, th):
    x0 = int(cx - tw * 0.44);  x1 = int(cx + tw * 0.44)
    y0 = int(gum_y);            y1 = int(gum_y + th)
    if y1 <= y0: return
    r = max(2, min(int(tw * 0.13), 4))
    draw.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=TEETH_COL)
    draw.line([(x0+1, y0+1), (x0+1, y1-r)], fill=TOOTH_SHADE, width=1)
    draw.line([(x1-1, y0+1), (x1-1, y1-r)], fill=TOOTH_SHADE, width=1)
    draw.line([(x1,   y0),   (x1,   y1)],   fill=TOOTH_DIV,   width=1)

def _lower_tooth(draw, cx, gum_y, tw, th):
    x0 = int(cx - tw * 0.44);  x1 = int(cx + tw * 0.44)
    y0 = int(gum_y - th);      y1 = int(gum_y)
    if y0 >= y1: return
    r = max(2, min(int(tw * 0.13), 4))
    draw.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=TEETH_COL)
    draw.line([(x0+1, y0+r), (x0+1, y1-1)], fill=TOOTH_SHADE, width=1)
    draw.line([(x1-1, y0+r), (x1-1, y1-1)], fill=TOOTH_SHADE, width=1)
    draw.line([(x1,   y0),   (x1,   y1)],   fill=TOOTH_DIV,   width=1)

# -- Core renderer ------------------------------------------------------------
def render_mouth(
    hw:  float = 138.0,
    cy:  float =  34.0,
    top: float =   5.0,
    bot: float =  71.0,
    lip: float =  14.0,
) -> np.ndarray:
    lx, rx = MCX - hw, MCX + hw

    # ---- Bezier control points ----------------------------------------------
    o_top = _qb((lx,   cy), (MCX, top),   (rx,   cy))
    o_bot = _qb((lx,   cy), (MCX, bot),   (rx,   cy))
    outer_poly = _ip(o_top) + list(reversed(_ip(o_bot)))

    i_top = _qb((lx+2, cy), (MCX, top+2), (rx-2, cy))
    i_bot = _qb((lx+2, cy), (MCX, bot-2), (rx-2, cy))
    inset_poly = _ip(i_top) + list(reversed(_ip(i_bot)))

    int_lx    = lx + lip
    int_rx    = rx - lip
    int_top_y = top + lip * 0.90
    int_bot_y = bot - lip * 0.90
    interior_h = int_bot_y - int_top_y   # true opening height at centre

    m_top = _qb((int_lx, cy), (MCX, int_top_y), (int_rx, cy))
    m_bot = _qb((int_lx, cy), (MCX, int_bot_y), (int_rx, cy))
    interior_poly = _ip(m_top) + list(reversed(_ip(m_bot)))

    # ---- Base image: lips + interior + gum bands ----------------------------
    img  = Image.new("RGB", (W, H), SKIN)
    draw = ImageDraw.Draw(img)
    draw.polygon(outer_poly, fill=LIP_EDGE)
    draw.polygon(inset_poly, fill=LIP_COL)

    if interior_h < 4:
        mid = _qb((int_lx, cy), (MCX, cy), (int_rx, cy))
        draw.line(_ip(mid), fill=MOUTH_INT, width=3)
        return np.array(img)

    draw.polygon(interior_poly, fill=MOUTH_INT)

    # Gum bands drawn directly (always within interior polygon)
    gum_band_h = max(3, interior_h * 0.13)
    gum_top_pts = _qb((int_lx, cy), (MCX, int_top_y + gum_band_h), (int_rx, cy))
    draw.polygon(_ip(m_top) + list(reversed(_ip(gum_top_pts))), fill=GUM_UP)

    lower_open = interior_h > 18
    if lower_open:
        g2_h = max(3, interior_h * 0.16)
        gum_bot_pts = _qb((int_lx, cy), (MCX, int_bot_y - g2_h), (int_rx, cy))
        draw.polygon(_ip(gum_bot_pts) + list(reversed(_ip(m_bot))), fill=GUM_DN)

    # ---- Teeth layer (composited via interior mask) -------------------------
    # tooth_top_y blends int_top_y (arch centre) and cy (corners) so that
    # teeth visually follow the lip animation — not just the static arch apex.
    tooth_top_y = int_top_y + (cy - int_top_y) * 0.42
    th_u = min(13.0, interior_h * 0.32)

    if interior_h > 8 and th_u > 3:
        # Draw teeth on a copy of current img (same background, only teeth on top)
        teeth_layer = img.copy()
        td = ImageDraw.Draw(teeth_layer)

        # Upper teeth — central 70% of interior width
        teeth_hw_u = (int_rx - int_lx) * 0.35
        span_u     = teeth_hw_u * 2
        n_up       = 5
        tw_u       = span_u / n_up
        x0_u       = MCX - teeth_hw_u
        for i in range(n_up):
            _upper_tooth(td, x0_u + (i + 0.5) * tw_u,
                         tooth_top_y, tw_u * 0.88, th_u)

        # Lower teeth + tongue — all on teeth_layer so composite clips them
        if lower_open:
            g2_h2       = max(3, interior_h * 0.16)
            tooth_bot_y = int_bot_y - g2_h2
            th_l        = min(10.0, interior_h * 0.23)
            if th_l > 3:
                teeth_hw_l = (int_rx - int_lx) * 0.26
                span_l     = teeth_hw_l * 2
                n_lo       = 4
                tw_l       = span_l / n_lo
                x0_l       = MCX - teeth_hw_l
                for i in range(n_lo):
                    _lower_tooth(td, x0_l + (i + 0.5) * tw_l,
                                 tooth_bot_y, tw_l * 0.86, th_l)

            # Tongue — only when mouth is wide open; clipped by interior mask
            if interior_h > 32:
                t_cx  = MCX
                t_cy  = int(int_bot_y - g2_h2 * 0.5)
                t_rx2 = int((int_rx - int_lx) * 0.20)
                t_ry  = int(g2_h2 * 0.50)
                td.ellipse([t_cx - t_rx2, t_cy - t_ry,
                            t_cx + t_rx2, t_cy + t_ry], fill=TONGUE_COL)

        # Interior polygon mask — teeth only visible INSIDE the dark mouth area
        int_mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(int_mask).polygon(interior_poly, fill=255)

        # Composite: teeth_layer where mask=255, original img where mask=0
        img = Image.composite(teeth_layer, img, int_mask)

        # Redraw gum bands on top of teeth (gum covers tooth tops cleanly)
        draw2 = ImageDraw.Draw(img)
        draw2.polygon(_ip(m_top) + list(reversed(_ip(gum_top_pts))), fill=GUM_UP)
        if lower_open:
            draw2.polygon(_ip(gum_bot_pts) + list(reversed(_ip(m_bot))), fill=GUM_DN)

    return np.array(img)


# -- Clip builders ------------------------------------------------------------
IDLE_P = dict(hw=138, cy=34, top=5, bot=71, lip=14)

def clip_idle():
    return render_mouth(**IDLE_P)[None]

def clip_smile():
    n_in, hold, n_out = 8, 10, 8
    # cy drops more AND top drops proportionally so teeth follow
    peak = dict(hw=140, cy=25, top=1, bot=73, lip=14)
    frames = []
    for i in range(n_in):
        t = _eio(i/(n_in-1))
        frames.append(render_mouth(
            hw=_l(IDLE_P['hw'],peak['hw'],t), cy=_l(IDLE_P['cy'],peak['cy'],t),
            top=_l(IDLE_P['top'],peak['top'],t), bot=_l(IDLE_P['bot'],peak['bot'],t)))
    for _ in range(hold):
        frames.append(render_mouth(**peak))
    for i in range(n_out):
        t = _eo(1 - i/(n_out-1))
        frames.append(render_mouth(
            hw=_l(IDLE_P['hw'],peak['hw'],t), cy=_l(IDLE_P['cy'],peak['cy'],t),
            top=_l(IDLE_P['top'],peak['top'],t), bot=_l(IDLE_P['bot'],peak['bot'],t)))
    return np.stack(frames)

def clip_surprise():
    n_in, hold, n_out = 6, 8, 8
    peak = dict(hw=84, cy=34, top=3, bot=73, lip=14)
    frames = []
    for i in range(n_in):
        t = _eio(i/(n_in-1))
        frames.append(render_mouth(
            hw=_l(IDLE_P['hw'],peak['hw'],t), cy=_l(IDLE_P['cy'],peak['cy'],t),
            top=_l(IDLE_P['top'],peak['top'],t), bot=_l(IDLE_P['bot'],peak['bot'],t)))
    for _ in range(hold):
        frames.append(render_mouth(**peak))
    for i in range(n_out):
        t = _eo(1 - i/(n_out-1))
        frames.append(render_mouth(
            hw=_l(IDLE_P['hw'],peak['hw'],t), cy=_l(IDLE_P['cy'],peak['cy'],t),
            top=_l(IDLE_P['top'],peak['top'],t), bot=_l(IDLE_P['bot'],peak['bot'],t)))
    return np.stack(frames)

def clip_yawn():
    n_in, hold, n_out = 11, 14, 13
    peak = dict(hw=138, cy=36, top=2, bot=74, lip=14)
    frames = []
    for i in range(n_in):
        t = _eio(i/(n_in-1))
        frames.append(render_mouth(
            hw=_l(IDLE_P['hw'],peak['hw'],t), cy=_l(IDLE_P['cy'],peak['cy'],t),
            top=_l(IDLE_P['top'],peak['top'],t), bot=_l(IDLE_P['bot'],peak['bot'],t)))
    for _ in range(hold):
        frames.append(render_mouth(**peak))
    for i in range(n_out):
        t = _eo(1 - i/(n_out-1))
        frames.append(render_mouth(
            hw=_l(IDLE_P['hw'],peak['hw'],t), cy=_l(IDLE_P['cy'],peak['cy'],t),
            top=_l(IDLE_P['top'],peak['top'],t), bot=_l(IDLE_P['bot'],peak['bot'],t)))
    return np.stack(frames)

def clip_smirk():
    n_in, hold, n_out = 6, 10, 7
    peak = dict(hw=138, cy=26, top=2, bot=70, lip=14)
    frames = []
    for i in range(n_in):
        t = _eio(i/(n_in-1))
        frames.append(render_mouth(
            hw=_l(IDLE_P['hw'],peak['hw'],t), cy=_l(IDLE_P['cy'],peak['cy'],t),
            top=_l(IDLE_P['top'],peak['top'],t), bot=_l(IDLE_P['bot'],peak['bot'],t)))
    for _ in range(hold):
        frames.append(render_mouth(**peak))
    for i in range(n_out):
        t = _eo(1 - i/(n_out-1))
        frames.append(render_mouth(
            hw=_l(IDLE_P['hw'],peak['hw'],t), cy=_l(IDLE_P['cy'],peak['cy'],t),
            top=_l(IDLE_P['top'],peak['top'],t), bot=_l(IDLE_P['bot'],peak['bot'],t)))
    return np.stack(frames)

def clip_grimace():
    n_in, hold, n_out = 5, 8, 6
    peak = dict(hw=140, cy=36, top=4, bot=72, lip=13)
    frames = []
    for i in range(n_in):
        t = _eio(i/(n_in-1))
        frames.append(render_mouth(
            hw=_l(IDLE_P['hw'],peak['hw'],t), cy=_l(IDLE_P['cy'],peak['cy'],t),
            top=_l(IDLE_P['top'],peak['top'],t), bot=_l(IDLE_P['bot'],peak['bot'],t)))
    for _ in range(hold):
        frames.append(render_mouth(**peak))
    for i in range(n_out):
        t = _eo(1 - i/(n_out-1))
        frames.append(render_mouth(
            hw=_l(IDLE_P['hw'],peak['hw'],t), cy=_l(IDLE_P['cy'],peak['cy'],t),
            top=_l(IDLE_P['top'],peak['top'],t), bot=_l(IDLE_P['bot'],peak['bot'],t)))
    return np.stack(frames)

# -- Registry -----------------------------------------------------------------
CLIPS = {
    "idle":     clip_idle,
    "smile":    clip_smile,
    "surprise": clip_surprise,
    "yawn":     clip_yawn,
    "smirk":    clip_smirk,
    "grimace":  clip_grimace,
}

def preview_clip(name, fps=10):
    try:
        import cv2, time as _t
        arr = CLIPS[name]()
        for f in arr:
            cv2.imshow(f"mouth_{name}", cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
            if cv2.waitKey(1) & 0xFF == ord("q"): break
            _t.sleep(1.0/fps)
        cv2.waitKey(0); cv2.destroyAllWindows()
    except ImportError:
        print("pip install opencv-python  para preview")

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Output -> {os.path.abspath(OUT_DIR)}\n")
    total = 0.0
    for name, fn in CLIPS.items():
        print(f"  rendering mouth_{name} ...", end="  ", flush=True)
        arr = fn()
        np.save(os.path.join(OUT_DIR, f"mouth_{name}.npy"), arr)
        mb = arr.nbytes/1_048_576; total += mb
        print(f"{arr.shape[0]:3d} frames   {mb:.1f} MB")
    print(f"\nTotal: {total:.1f} MB")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1: preview_clip(sys.argv[1])
    else: main()
