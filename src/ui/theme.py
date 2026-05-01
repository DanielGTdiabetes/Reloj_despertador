"""
theme.py — Sistema de diseño compartido: Mid-Century Retro-Futurista.

Paleta:
  BG       = Negro puro         (#000000)
  AMBER    = Naranja Ámbar      (#FFBF00)  — acento principal
  PHOSPHOR = Verde Fósforo      (#39FF14)  — alarma / estado activo

Uso:
  from ui.theme import T
  draw.text((x, y), text, font=T.font_clock, fill=T.AMBER)
"""
from __future__ import annotations

import os
from typing import Optional

from PIL import Image, ImageFont

_ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
_FONTS  = os.path.join(_ASSETS, "fonts")
_ICONS  = os.path.join(_ASSETS, "weather")

# ── Colores ──────────────────────────────────────────────────────────────────

BG        = (0,   0,   0)
AMBER     = (255, 191,   0)
PHOSPHOR  = (57,  255,  20)
WHITE     = (255, 255, 255)
DIM_WHITE = (153, 153, 153)   # ~60% blanco
DARK_CARD = (34,  34,  34)
ARC_BASE  = (51,  51,  51)
MENU_HL   = AMBER               # ítem de menú activo fondo
MENU_TXT  = (0,   0,   0)       # texto sobre ítem activo
COLD_BLUE = (102, 153, 255)     # temperatura mínima

# ── Fuentes ───────────────────────────────────────────────────────────────────

def _ttf(name: str, size: int) -> ImageFont.FreeTypeFont:
    path = os.path.join(_FONTS, name)
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


class _Fonts:
    """Carga perezosa de fuentes — singleton."""
    _inst: Optional["_Fonts"] = None

    def __new__(cls) -> "_Fonts":
        if cls._inst is None:
            cls._inst = super().__new__(cls)
            cls._inst._loaded = False
        return cls._inst

    def _ensure(self) -> None:
        if self._loaded:
            return
        self.clock      = _ttf("arialbd.ttf", 76)   # HH:MM en redonda
        self.seconds    = _ttf("arialbd.ttf", 24)   # :SS en redonda
        self.date       = _ttf("arial.ttf",   18)   # fecha en redonda
        self.focus_ttl  = _ttf("arialbd.ttf", 32)   # título en render_focus
        self.focus_val  = _ttf("arialbd.ttf", 40)   # valor en render_focus
        self.focus_sub  = _ttf("arial.ttf",   16)   # subtítulo en render_focus
        self.menu_act   = _ttf("arialbd.ttf", 14)   # ítem menú activo (rect)
        self.menu_inn   = _ttf("arial.ttf",   13)   # ítem menú inactivo (rect)
        self.alarm_hm   = _ttf("arialbd.ttf", 36)   # HH|MM edición alarma (rect)
        self.card_day   = _ttf("arialbd.ttf", 11)   # día de la semana en tarjeta
        self.card_temp  = _ttf("arial.ttf",   10)   # temperatura en tarjeta
        self.small      = _ttf("arial.ttf",   12)   # uso general pequeño
        self._loaded = True

    def __getattr__(self, name: str):
        self._ensure()
        return object.__getattribute__(self, name)


F = _Fonts()   # Singleton de fuentes — importar con: from ui.theme import F


# ── Iconos meteorológicos ─────────────────────────────────────────────────────

# Mapa: fragmento de descripción → nombre de archivo PNG
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
    """Devuelve el nombre del archivo PNG para una descripción de clima."""
    desc = (description or "").lower()
    for keywords, fname in _COND_MAP:
        if any(k in desc for k in keywords):
            return fname
    return "partly.png"


class _IconCache:
    """Carga y redimensiona iconos una sola vez."""
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
            else:
                # Fallback: cuadrado vacío
                img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            self._cache[key] = img
        return self._cache[key]

    def composite_on_black(self, filename: str, size: int) -> Image.Image:
        """Devuelve el icono PNG compuesto sobre fondo negro puro (RGB)."""
        icon = self.get(filename, size)
        base = Image.new("RGB", (size, size), BG)
        base.paste(icon, (0, 0), icon)
        return base


ICONS = _IconCache()   # Singleton de iconos — from ui.theme import ICONS
