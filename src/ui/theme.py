"""
theme.py — Sistema de diseño: Modern Glassmorphism (Basado en la imagen).

Paleta:
  BG      = Negro / Azul muy oscuro (#000510)
  CYAN    = Cian brillante          (#64C8FF)
  PURPLE  = Púrpura/Violeta         (#B464FF)
  WHITE   = Blanco puro             (#FFFFFF)
"""
from __future__ import annotations

import os
from typing import Optional

from PIL import Image, ImageFont

_ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
_FONTS  = os.path.join(_ASSETS, "fonts")
_ICONS  = os.path.join(_ASSETS, "weather")

# ── Colores ──────────────────────────────────────────────────────────────────

BG        = (0,   5,   16)    # Fondo azul casi negro
CYAN      = (100, 200, 255)
PURPLE    = (180, 100, 255)
WHITE     = (255, 255, 255)
DIM_WHITE = (180, 190, 200)
DARK_CARD = (20,  30,  45)

# Colores para degradados de tarjetas (Arriba -> Abajo)
GRADIENTS = [
    ((255, 100, 100), (255, 150, 50)),   # Naranja/Rosa
    ((180, 255, 100), (100, 255, 150)),  # Verde/Amarillo
    ((100, 255, 255), (100, 150, 255)),  # Azul/Cian
    ((200, 100, 255), (150, 50,  255)),  # Púrpura/Violeta
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
        # Tamaños ajustados al nuevo diseño
        self.clock      = _ttf("arialbd.ttf", 80)
        self.date_top   = _ttf("arialbd.ttf", 20)   # "VIERNES 25"
        self.weather_sub = _ttf("arialbd.ttf", 14)  # "SOLEADO"
        self.temp_big   = _ttf("arial.ttf",   22)   # "18°C"
        
        self.card_day   = _ttf("arialbd.ttf", 13)
        self.card_temp  = _ttf("arialbd.ttf", 11)
        self.small      = _ttf("arial.ttf",   12)
        self.menu_act   = _ttf("arialbd.ttf", 14)
        self.menu_inn   = _ttf("arial.ttf",   13)
        self._loaded = True

    def __getattr__(self, name: str):
        self._ensure()
        return object.__getattribute__(self, name)

F = _Fonts()

# ── Iconos ────────────────────────────────────────────────────────────────────

_COND_MAP: list[tuple[tuple[str, ...], str]] = [
    (("storm", "thunder", "tormenta", "trueno"),                  "storm.png"),
    (("snow", "nieve", "nevada"),                                  "snow.png"),
    (("rain", "lluvia", "drizzle", "chubasco", "llov"),            "rain.png"),
    (("wind", "viento"),                                           "wind.png"),
    (("fog", "mist", "niebla", "bruma"),                           "fog.png"),
    (("partly", "intervalos", "parcialmente"),                     "partly.png"),
    (("cloud", "nuboso", "nubes", "nublado", "cubierto"),          "cloud.png"),
    (("clear", "sun", "despejado", "soleado"),                     "sun.png"),
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
                self._cache[key] = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        return self._cache[key]

    def composite(self, filename: str, size: int, bg_color: tuple = (0,0,0,0)) -> Image.Image:
        icon = self.get(filename, size)
        if bg_color[3] == 0: # Transparent
            return icon
        base = Image.new("RGBA", (size, size), bg_color)
        base.paste(icon, (0, 0), icon)
        return base

ICONS = _IconCache()
