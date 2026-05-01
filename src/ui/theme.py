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

_ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
_FONTS  = os.path.join(_ASSETS, "fonts")
_ICONS  = os.path.join(_ASSETS, "weather")

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

# ── Iconos de menú (Diseño PREMIUM / Glassmorphism) ──────────────────────────

def draw_menu_icon(draw, x: int, y: int, size: int, kind: str) -> None:
    """
    Dibuja iconos de menú con estética moderna (Glow, Gradients, Smooth).
    """
    cx, cy = x + size // 2, y + size // 2
    r_base = size // 2 - 4
    
    # 1. Glow / Aura suave de fondo (Glassmorphism effect)
    glow_col = (*CYAN[:3], 40) if kind != "alarm" else (*AMBER[:3], 40)
    for dr in range(3, 0, -1):
        draw.ellipse([cx-r_base-dr, cy-r_base-dr, cx+r_base+dr, cy+r_base+dr], 
                     outline=glow_col, width=1)

    if kind == "alarm":
        # Campana estilizada con degradado
        draw.chord([x+8, y+6, x+size-8, y+size-6], 180, 0, fill=AMBER)
        draw.rounded_rectangle([x+4, y+size-12, x+size-4, y+size-8], radius=2, fill=AMBER)
        draw.ellipse([cx-4, y+size-8, cx+4, y+size-2], fill=WHITE)
        # Brillo superior
        draw.arc([x+12, y+10, x+size-12, y+size-12], 200, 340, fill=WHITE, width=2)

    elif kind == "wifi":
        # Ondas WiFi con gradiente de opacidad
        for i, r in enumerate([10, 18, 26]):
            alpha = int(255 * (i+1)/3)
            col = (*CYAN[:3], alpha) if False else CYAN # PIL sin alpha en lines
            draw.arc([cx-r, cy-r+15, cx+r, cy+r+15], 225, 315, fill=CYAN, width=3)
        draw.ellipse([cx-3, cy+22, cx+3, cy+28], fill=WHITE)

    elif kind == "sync":
        # Flechas circulares dinámicas
        draw.arc([cx-20, cy-20, cx+20, cy+20], 10, 160, fill=CYAN, width=4)
        draw.arc([cx-20, cy-20, cx+20, cy+20], 190, 340, fill=PURPLE, width=4)
        # Puntas de flecha
        draw.polygon([(cx+20, cy), (cx+14, cy+10), (cx+26, cy+10)], fill=CYAN)
        draw.polygon([(cx-20, cy), (cx-14, cy-10), (cx-26, cy-10)], fill=PURPLE)

    elif kind == "weather":
        # Nube volumétrica con sombra
        draw.ellipse([x+6, cy-2, cx+6, y+size-8], fill=DIM_WHITE)
        draw.ellipse([cx-6, cy-10, x+size-2, y+size-8], fill=WHITE)
        draw.rectangle([x+10, cy+2, x+size-10, y+size-8], fill=WHITE)
        # Pequeño sol asomando
        draw.ellipse([cx+4, y+4, cx+18, y+18], fill=AMBER)

    elif kind == "location":
        # Pin de mapa moderno (Drop shape)
        draw.ellipse([cx-14, cy-22, cx+14, cy+6], fill=(240, 80, 80))
        draw.polygon([(cx-12, cy-2), (cx+12, cy-2), (cx, cy+24)], fill=(240, 80, 80))
        draw.ellipse([cx-5, cy-10, cx+5, cy], fill=WHITE)

    elif kind == "brightness":
        # Sol radiante
        draw.ellipse([cx-10, cy-10, cx+10, cy+10], fill=AMBER)
        for i in range(8):
            a = math.radians(i * 45)
            draw.line([cx+math.cos(a)*14, cy+math.sin(a)*14, 
                       cx+math.cos(a)*24, cy+math.sin(a)*24], fill=AMBER, width=3)

    else:
        draw.rounded_rectangle([x+5, y+5, x+size-5, y+size-5],
                               radius=8, outline=WHITE, width=2)
