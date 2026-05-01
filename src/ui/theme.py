"""
theme.py — Configuración visual Ultra-Premium COMPLETA.
Restaurada compatibilidad con rect_ui.py y mantenidas fuentes gigantes.
"""
from __future__ import annotations
import os
from PIL import Image, ImageFont

# Rutas absolutas
_BASE = os.path.dirname(os.path.abspath(__file__))
_ASSETS = os.path.join(_BASE, "..", "assets")
_FONTS = os.path.join(_ASSETS, "fonts")
_ICONS = os.path.join(_ASSETS, "weather")
_MENU_ICONS = os.path.join(_ASSETS, "menu_icons")

# Colores Premium
BG = (5, 10, 25)
CYAN = (120, 225, 255)
PURPLE = (190, 140, 255)
WHITE = (255, 255, 255)
YELLOW = (255, 220, 0)
AMBER = (255, 160, 60)
DIM_WHITE = (150, 160, 175)
DARK_CARD = (20, 30, 45)

GRADIENTS = [
    ((255, 80, 80),   (100, 30,  30)),
    ((140, 255, 100), ( 40, 100, 30)),
    ((100, 200, 255), ( 30,  60, 120)),
    ((200, 120, 255), ( 80,  40, 120)),
]

def _ttf(name: str, size: int) -> ImageFont.FreeTypeFont:
    path = os.path.join(_FONTS, name)
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except: pass
    return ImageFont.load_default()

class _Fonts:
    def __init__(self):
        self.clock = _ttf("arialbd.ttf", 84)      # Reloj gigante
        self.date_top = _ttf("arialbd.ttf", 22)   # Fecha
        self.weather_sub = _ttf("arialbd.ttf", 14) # Secundarios
        self.temp_big = _ttf("arialbd.ttf", 26)    # Temp grande
        self.card_day = _ttf("arialbd.ttf", 13)
        self.card_temp = _ttf("arial.ttf", 11)
        self.menu_label = _ttf("arialbd.ttf", 15)
        self.small = _ttf("arial.ttf", 12)

F = _Fonts()

class _IconCache:
    def __init__(self):
        self._cache = {}
    def get(self, filename, size):
        key = (filename, size)
        if key not in self._cache:
            path = os.path.join(_ICONS, filename)
            if os.path.exists(path):
                img = Image.open(path).convert("RGBA")
                self._cache[key] = img.resize((size, size), Image.LANCZOS)
            else:
                self._cache[key] = None
        return self._cache[key]

ICONS = _IconCache()

def condition_to_icon_file(description: str) -> str:
    desc = (description or "").lower()
    mapping = [
        (("storm", "thunder"), "storm.png"), (("snow",), "snow.png"),
        (("rain", "drizzle"), "rain.png"), (("wind",), "wind.png"),
        (("fog", "mist"), "fog.png"), (("partly",), "partly.png"),
        (("cloud", "nub"), "cloud.png"), (("clear", "sun"), "sun.png")
    ]
    for keywords, fname in mapping:
        if any(k in desc for k in keywords): return fname
    return "partly.png"

def draw_menu_icon(draw, x, y, size, kind):
    path = os.path.join(_MENU_ICONS, f"{kind}.png")
    if os.path.exists(path):
        try:
            icon = Image.open(path).convert("RGBA").resize((size, size))
            draw._image.paste(icon, (x, y), icon)
        except: pass
