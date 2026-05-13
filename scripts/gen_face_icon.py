"""Genera face_anim.png — estilo emoji de color, igual que el resto de iconos del menu."""
from PIL import Image, ImageDraw
import math, os

SIZE = 64
img  = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

cx, cy = SIZE // 2, SIZE // 2
R = 28

# -- Cara amarilla (disco con borde oscuro) -----------------------------------
FACE_FILL   = (255, 214,  10, 255)   # amarillo emoji
FACE_BORDER = (180, 140,   0, 255)   # borde dorado oscuro
draw.ellipse([cx-R,   cy-R,   cx+R,   cy+R],   fill=FACE_BORDER)
draw.ellipse([cx-R+2, cy-R+2, cx+R-2, cy+R-2], fill=FACE_FILL)

# -- Ojos (ovales negros con reflejo blanco) ----------------------------------
EYE   = ( 40,  30,  10, 255)
WHITE = (255, 255, 255, 230)
for ex in (cx - 9, cx + 9):
    ey = cy - 7
    draw.ellipse([ex-4, ey-5, ex+4, ey+5], fill=EYE)
    draw.ellipse([ex-2, ey-3, ex,   ey-1], fill=WHITE)

# -- Sonrisa con dientes ------------------------------------------------------
MOUTH_INT = ( 80,  20,  10, 255)
TEETH     = (255, 252, 245, 255)
GUM       = (220,  90, 100, 255)

mouth_pts = []
for i in range(25):
    ang = math.pi * (0.08 + 0.84 * i / 24)
    mouth_pts.append((cx + 15 * math.cos(ang), cy + 8 + 13 * math.sin(ang)))
mouth_poly = [(cx - 15, cy + 8)] + [(round(x), round(y)) for x, y in mouth_pts] + [(cx + 15, cy + 8)]
draw.polygon(mouth_poly, fill=MOUTH_INT)
draw.rectangle([cx - 14, cy + 8, cx + 14, cy + 15], fill=TEETH)
for dx in (-7, 0, 7):
    draw.line([(cx + dx, cy + 8), (cx + dx, cy + 15)], fill=(200, 190, 175, 200), width=1)
draw.rectangle([cx - 14, cy + 6, cx + 14, cy + 10], fill=GUM)

# -- Destellos de animacion (3 estrellas de 4 puntas fuera de la cara) --------
STAR_COL = (255, 255, 255, 240)
for ang_deg, dist, arm in [(40, R + 8, 4), (15, R + 10, 3), (65, R + 9, 3)]:
    a  = math.radians(ang_deg)
    sx = cx + dist * math.cos(a)
    sy = cy - dist * math.sin(a)
    draw.line([(sx - arm, sy), (sx + arm, sy)], fill=STAR_COL, width=2)
    draw.line([(sx, sy - arm), (sx, sy + arm)], fill=STAR_COL, width=2)

out = os.path.abspath(os.path.join(os.path.dirname(__file__),
                      "..", "src", "assets", "menu_icons", "face_anim.png"))
img.save(out)
print(f"Guardado: {out}  ({os.path.getsize(out)} bytes)")
