"""
theme.py — Configuración visual Ultra-Premium.
Forzando fuentes grandes y colores exactos de la captura.
"""
from __future__ import annotations
import os
from typing import Optional
from PIL import Image, ImageFont

# Rutas absolutas para evitar fallos en la Pi
_BASE = os.path.dirname(os.path.abspath(__file__))
_ASSETS = os.path.join(_BASE, "..", "assets")
_FONTS = os.path.join(_ASSETS, "fonts")
_ICONS = os.path.join(_ASSETS, "weather")
_MENU_ICONS = os.path.join(_ASSETS, "menu_icons")

# Colores de la captura
BG = (5, 10, 25)
CYAN = (120, 225, 255)
PURPLE = (190, 140, 255)
WHITE = (255, 255, 255)
AMBER = (255, 160, 60)
DIM_WHITE = (150, 160, 175)

def _ttf(name: str, size: int) -> ImageFont.FreeTypeFont:
    path = os.path.join(_FONTS, name)
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except: pass
    return ImageFont.load_default()

class _Fonts:
    def __init__(self):
        self.clock = _ttf("arialbd.ttf", 84)      # Reloj gigante como en la foto
        self.date_top = _ttf("arialbd.ttf", 22)   # Fecha clara
        self.weather_sub = _ttf("arialbd.ttf", 14) # Textos secundarios
        self.temp_big = _ttf("arialbd.ttf", 26)    # Temperatura actual grande
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

def draw_menu_icon(draw, x, y, size, kind):
    # Simplificado para estabilidad
    path = os.path.join(_MENU_ICONS, f"{kind}.png")
    if os.path.exists(path):
        try:
            icon = Image.open(path).convert("RGBA").resize((size, size))
            draw._image.paste(icon, (x, y), icon)
        except: pass
