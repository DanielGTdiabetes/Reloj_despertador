"""
theme.py — Versión Premium Glassmorphism.
Colores extraídos y suavizados de la imagen de referencia.
"""
from __future__ import annotations
import os
from typing import Optional
from PIL import Image, ImageFont

_ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
_FONTS  = os.path.join(_ASSETS, "fonts")
_ICONS  = os.path.join(_ASSETS, "weather")

# ── Colores Premium ──────────────────────────────────────────────────────────

BG        = (5, 10, 25)      # Azul noche profundo
CYAN      = (120, 220, 255)  # Cian eléctrico suave
PURPLE    = (190, 140, 255)  # Púrpura elegante
WHITE     = (255, 255, 255)
DIM_WHITE = (160, 170, 185)
DARK_CARD = (20,  30,  45)

# Degradados Suaves (Inspirados en la imagen)
GRADIENTS = [
    ((255, 80, 80),  (100, 30, 30)),   # Coral profundo
    ((140, 255, 100), (40, 100, 30)),   # Verde bosque
    ((100, 200, 255), (30, 60, 120)),   # Azul océano
    ((200, 120, 255), (80, 40, 120)),   # Púrpura real
]

# ── Fuentes ───────────────────────────────────────────────────────────────────

def _ttf(name: str, size: int) -> ImageFont.FreeTypeFont:
    path = os.path.join(_FONTS, name)
    if os.path.exists(path): return ImageFont.truetype(path, size)
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
        self.clock      = _ttf("arialbd.ttf", 64)
        self.date_top   = _ttf("arialbd.ttf", 22)
        self.weather_sub = _ttf("arialbd.ttf", 12)
        self.temp_big   = _ttf("arialbd.ttf", 22)
        self.card_day   = _ttf("arialbd.ttf", 14)
        self.card_temp  = _ttf("arial.ttf",   11)
        self.menu_label = _ttf("arialbd.ttf", 16)
        self.small      = _ttf("arial.ttf",   12)
        self._loaded = True
    def __getattr__(self, name: str):
        self._ensure()
        return object.__getattribute__(self, name)

F = _Fonts()

# ── Iconos ────────────────────────────────────────────────────────────────────

_COND_MAP: list[tuple[tuple[str, ...], str]] = [
    (("storm", "thunder"), "storm.png"),
    (("snow",), "snow.png"),
    (("rain", "drizzle"), "rain.png"),
    (("wind",), "wind.png"),
    (("fog", "mist"), "fog.png"),
    (("partly",), "partly.png"),
    (("cloud", "nub"), "cloud.png"),
    (("clear", "sun"), "sun.png"),
]

def condition_to_icon_file(description: str) -> str:
    desc = (description or "").lower()
    for keywords, fname in _COND_MAP:
        if any(k in desc for k in keywords): return fname
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
            else: self._cache[key] = Image.new("RGBA", (size, size), (0,0,0,0))
        return self._cache[key]
    def composite_on_black(self, filename: str, size: int) -> Image.Image:
        icon = self.get(filename, size)
        base = Image.new("RGB", (size, size), (0,0,0))
        base.paste(icon, (0, 0), icon)
        return base

def draw_menu_icon(draw, x, y, size, kind):
    """Dibuja iconos premium multi-color usando primitivas."""
    cx, cy = x + size // 2, y + size // 2
    if kind == "alarm":
        # Cuerpo campana blanco, badajo púrpura
        draw.chord([x+4, y+4, x+size-4, y+size-4], 180, 0, fill=WHITE)
        draw.rectangle([x+2, y+size-10, x+size-2, y+size-5], fill=CYAN)
        draw.ellipse([cx-4, y+size-6, cx+4, y+size+2], fill=PURPLE)
    elif kind == "brightness":
        # Sol con rayos de dos colores
        draw.ellipse([cx-8, cy-8, cx+8, cy+8], outline=WHITE, width=3)
        for i, a in enumerate(range(0, 360, 45)):
            r = math.radians(a)
            col = CYAN if i % 2 == 0 else PURPLE
            draw.line([cx+math.cos(r)*10, cy+math.sin(r)*10, cx+math.cos(r)*18, cy+math.sin(r)*18], fill=col, width=3)
    elif kind == "wifi":
        # Ondas cian y púrpura
        for i, r in enumerate([10, 20, 30]):
            col = CYAN if i == 0 else (PURPLE if i == 1 else WHITE)
            draw.arc([cx-r, cy-r+15, cx+r, cy+r+15], 225, 315, fill=col, width=3)
        draw.ellipse([cx-4, cy+22, cx+4, cy+30], fill=CYAN)
    elif kind == "sync":
        # Flechas circulares encontrándose
        draw.arc([cx-15, cy-15, cx+15, cy+15], 10, 170, fill=CYAN, width=4)
        draw.arc([cx-15, cy-15, cx+15, cy+15], 190, 350, fill=PURPLE, width=4)
        draw.polygon([(cx+15, cy), (cx+10, cy+10), (cx+20, cy+10)], fill=CYAN)
        draw.polygon([(cx-15, cy), (cx-10, cy-10), (cx-20, cy-10)], fill=PURPLE)
    elif kind == "weather":
        # Nube blanca con sol cian
        draw.ellipse([x+5, cy-8, cx+5, cy+2], outline=CYAN, width=2)
        draw.ellipse([x+2, cy, cx+8, y+size-10], fill=WHITE)
        draw.ellipse([cx-8, cy-5, x+size-2, y+size-10], fill=WHITE)
        draw.rectangle([x+10, cy+5, x+size-10, y+size-10], fill=WHITE)
    else:
        draw.rectangle([x+5, y+5, x+size-5, y+size-5], outline=WHITE, width=2)

ICONS = _IconCache()
