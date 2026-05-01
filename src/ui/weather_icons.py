"""
weather_icons.py — Versión Corregida con Centrado Dinámico.
Soluciona el desplazamiento de los iconos dentro de los marcos.
"""
from __future__ import annotations
import os
from PIL import Image, ImageDraw

_ICONS_CACHE = {}

def get_icon_key(description: str) -> str:
    desc = (description or "").lower()
    if "storm" in desc or "thunder" in desc: return "storm"
    if "snow" in desc: return "snow"
    if "rain" in desc or "drizzle" in desc: return "rain"
    if "fog" in desc or "mist" in desc: return "fog"
    if "sun" in desc or "clear" in desc: return "sun"
    return "partly"

def draw_weather_icon(img, description, cx, cy, size=50):
    """Dibuja el icono centrado dinámicamente según el tamaño solicitado."""
    key = get_icon_key(description)
    cache_key = (key, size)
    
    if cache_key not in _ICONS_CACHE:
        base_dir = os.path.dirname(__file__)
        assets_dir = os.path.join(base_dir, "..", "assets", "weather")
        path = os.path.join(assets_dir, f"{key}.png")
        if os.path.exists(path):
            try:
                icon = Image.open(path).convert("RGBA")
                _ICONS_CACHE[cache_key] = icon.resize((size, size), Image.LANCZOS)
            except:
                _ICONS_CACHE[cache_key] = None
        else:
            _ICONS_CACHE[cache_key] = None
            
    icon = _ICONS_CACHE.get(cache_key)
    if icon:
        # Centrado perfecto: restamos la mitad del tamaño solicitado
        img.paste(icon, (cx - size // 2, cy - size // 2), icon)

def draw_moon(img, cx, cy, r, phase_frac, phase_name=""):
    draw = ImageDraw.Draw(img)
    # Luna simple pero centrada
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(230, 230, 200))
    if phase_frac < 0.5: # Ejemplo simple de fase
        draw.ellipse([cx-r+5, cy-r, cx+r+5, cy+r], fill=(BG if 'BG' in globals() else (5,10,25)))
