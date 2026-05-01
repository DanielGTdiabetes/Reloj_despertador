"""
theme.py — Versión Premium con icono de ubicación añadido.
CAMBIO respecto a la versión anterior:
  - draw_menu_icon(): añadido case "location" (pin de mapa)
  - Sin cambios en colores, fuentes ni iconos existentes.
"""
from __future__ import annotations
import os
from typing import Optional
from PIL import Image, ImageFont

_ASSETS      = os.path.join(os.path.dirname(__file__), "..", "assets")
_FONTS       = os.path.join(_ASSETS, "fonts")
_ICONS       = os.path.join(_ASSETS, "weather")
_MENU_ICONS  = os.path.join(_ASSETS, "menu_icons")

# ── Colores Premium ───────────────────────────────────────────────────────────

BG        = (5, 10, 25)
CYAN      = (120, 220, 255)
PURPLE    = (190, 140, 255)
WHITE     = (255, 255, 255)
YELLOW    = (255, 220,   0)
AMBER     = (255, 180,  60)
DIM_WHITE = (160, 170, 185)
DARK_CARD = (20,  30,  45)

GRADIENTS = [
    ((255, 80, 80),   (100, 30,  30)),
    ((140, 255, 100), ( 40, 100, 30)),
    ((100, 200, 255), ( 30,  60, 120)),
    ((200, 120, 255), ( 80,  40, 120)),
]

# ── Fuentes ───────────────────────────────────────────────────────────────────

def _ttf(name: str, size: int) -> ImageFont.FreeTypeFont:
    path = os.path.join(_FONTS, name)
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()

class _Fonts:
    _inst: Optional["_Fonts"] = None
    def __new__(cls) -> "_Fonts":
        if cls._inst is None:
            cls._inst = super().__new__(cls)
            cls._inst._loaded = False
        return cls._inst
    def _ensure(self) -> None:
        if self._loaded: return
        self.clock       = _ttf("arialbd.ttf", 64)
        self.date_top    = _ttf("arialbd.ttf", 20)
        self.weather_sub = _ttf("arialbd.ttf", 11)
        self.temp_big    = _ttf("arialbd.ttf", 20)
        self.card_day    = _ttf("arialbd.ttf", 13)
        self.card_temp   = _ttf("arial.ttf",   11)
        self.menu_label  = _ttf("arialbd.ttf", 15)
        self.small       = _ttf("arial.ttf",   11)
        self._loaded     = True
    def __getattr__(self, name: str):
        self._ensure()
        return object.__getattribute__(self, name)

F = _Fonts()

# ── Iconos de clima (cache PNG) ───────────────────────────────────────────────

_COND_MAP: list[tuple[tuple[str, ...], str]] = [
    (("storm", "thunder"),        "storm.png"),
    (("snow",),                   "snow.png"),
    (("rain", "drizzle"),         "rain.png"),
    (("wind",),                   "wind.png"),
    (("fog", "mist"),             "fog.png"),
    (("partly",),                 "partly.png"),
    (("cloud", "nub"),            "cloud.png"),
    (("clear", "sun"),            "sun.png"),
]

def condition_to_icon_file(description: str) -> str:
    desc = (description or "").lower()
    for keywords, fname in _COND_MAP:
        if any(k in desc for k in keywords):
            return fname
    return "partly.png"

class _IconCache:
    _inst: Optional["_IconCache"] = None
    def __new__(cls) -> "_IconCache":
        if cls._inst is None:
            cls._inst = super().__new__(cls)
            cls._inst._cache: dict[tuple[str, int], Image.Image] = {}
        return cls._inst
    def get(self, filename: str, size: int) -> Image.Image:
        key = (filename, size)
        if key not in self._cache:
            path = os.path.join(_ICONS, filename)
            if os.path.exists(path):
                img = Image.open(path).convert("RGBA")
                img = img.resize((size, size), Image.LANCZOS)
                self._cache[key] = img
            else:
                self._cache[key] = Image.new("RGBA", (size, size), (0,0,0,0))
        return self._cache[key]

ICONS = _IconCache()

# ── Cache de iconos de menú ───────────────────────────────────────────────────

class _MenuIconCache:
    _inst: Optional["_MenuIconCache"] = None
    def __new__(cls) -> "_MenuIconCache":
        if cls._inst is None:
            cls._inst = super().__new__(cls)
            cls._inst._cache: dict[tuple[str,int], Image.Image] = {}
        return cls._inst
    def get(self, kind: str, size: int) -> Optional[Image.Image]:
        key = (kind, size)
        if key not in self._cache:
            path = os.path.join(_MENU_ICONS, f"{kind}.png")
            if os.path.exists(path):
                img = Image.open(path).convert("RGBA")
                img = img.resize((size, size), Image.LANCZOS)
                self._cache[key] = img
            else:
                self._cache[key] = None
        return self._cache[key]

MENU_ICONS = _MenuIconCache()

# ── Iconos de menú (dibujados con PIL como fallback) ─────────────────────────

def draw_menu_icon(draw, x: int, y: int, size: int, kind: str) -> None:
    """
    Dibuja el icono del ítem de menú.
    Primero intenta cargar PNG de assets/menu_icons/{kind}.png.
    Si no existe, dibuja con PIL como fallback.
    kind: "alarm" | "wifi" | "sync" | "weather" | "location" | "brightness"
    """
    # Intentar PNG de alta calidad
    icon_img = MENU_ICONS.get(kind, size)
    if icon_img is not None:
        # Necesitamos la imagen base para hacer paste — se pasa via draw._image
        try:
            base = draw._image
            base.paste(icon_img, (x, y), icon_img)
            return
        except Exception:
            pass

    # Fallback PIL geométrico
    cx, cy = x + size // 2, y + size // 2

    if kind == "alarm":
        draw.chord([x+4, y+4, x+size-4, y+size-2], 180, 0, fill=YELLOW)
        draw.rectangle([x+2, y+size-10, x+size-2, y+size-6], fill=YELLOW)
        draw.ellipse([cx-4, y+size-6, cx+4, y+size+2], fill=WHITE)

    elif kind == "wifi":
        for r in [8, 16, 24]:
            draw.arc([cx-r, cy-r+12, cx+r, cy+r+12], 225, 315, fill=WHITE, width=3)
        draw.ellipse([cx-3, cy+18, cx+3, cy+24], fill=WHITE)

    elif kind == "sync":
        draw.arc([cx-15, cy-15, cx+15, cy+15], 10,  170, fill=CYAN,   width=4)
        draw.arc([cx-15, cy-15, cx+15, cy+15], 190, 350, fill=PURPLE, width=4)
        draw.polygon([(cx+15,cy),(cx+10,cy+10),(cx+20,cy+10)], fill=CYAN)
        draw.polygon([(cx-15,cy),(cx-10,cy-10),(cx-20,cy-10)], fill=PURPLE)

    elif kind == "weather":
        draw.ellipse([x+8, cy, cx+8, y+size-10], fill=WHITE)
        draw.ellipse([cx-8, cy-5, x+size-2, y+size-10], fill=WHITE)
        draw.rectangle([x+12, cy+5, x+size-12, y+size-10], fill=WHITE)

    elif kind == "location":
        pin_r = size // 4
        pin_cx, pin_cy = cx, cy - size // 8
        draw.ellipse([pin_cx-pin_r, pin_cy-pin_r,
                      pin_cx+pin_r, pin_cy+pin_r], fill=(220, 70, 70))
        draw.ellipse([pin_cx-pin_r//3, pin_cy-pin_r//3,
                      pin_cx+pin_r//3, pin_cy+pin_r//3], fill=WHITE)
        draw.polygon([
            (pin_cx - pin_r//2, pin_cy + pin_r//2),
            (pin_cx + pin_r//2, pin_cy + pin_r//2),
            (pin_cx,            pin_cy + size//3),
        ], fill=(220, 70, 70))

    elif kind == "brightness":
        import math
        r_core = size // 5
        r_ray  = int(size * 0.4)
        for i in range(8):
            a = (i * 45) * math.pi / 180
            x1 = cx + int((r_core+2) * math.cos(a))
            y1 = cy + int((r_core+2) * math.sin(a))
            x2 = cx + int(r_ray * math.cos(a))
            y2 = cy + int(r_ray * math.sin(a))
            draw.line([x1, y1, x2, y2], fill=YELLOW, width=2)
        draw.ellipse([cx-r_core, cy-r_core, cx+r_core, cy+r_core], fill=YELLOW)

    else:
        draw.rounded_rectangle([x+5, y+5, x+size-5, y+size-5],
                               radius=5, outline=WHITE, width=2)
