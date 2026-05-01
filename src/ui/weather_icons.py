"""
weather_icons.py — Versión Ultra-Ligera para Pi Zero.
"""
from __future__ import annotations
import os
from PIL import Image, ImageDraw

# Cache global para evitar carga en tiempo de render
_ICONS_CACHE = {}

def load_all_icons(size=50):
    base_dir = os.path.dirname(__file__)
    assets_dir = os.path.join(base_dir, "..", "assets", "weather")
    keys = ["sun", "partly", "cloud", "rain", "storm", "snow", "fog", "wind"]
    for k in keys:
        path = os.path.join(assets_dir, f"{k}.png")
        if os.path.exists(path):
            img = Image.open(path).convert("RGBA")
            _ICONS_CACHE[k] = img.resize((size, size), Image.LANCZOS)

def get_icon_key(description: str) -> str:
    desc = (description or "").lower()
    if "storm" in desc or "thunder" in desc: return "storm"
    if "snow" in desc: return "snow"
    if "rain" in desc or "drizzle" in desc: return "rain"
    if "fog" in desc or "mist" in desc: return "fog"
    if "sun" in desc or "clear" in desc: return "sun"
    return "partly"

def draw_weather_icon(img, description, cx, cy, size=50):
    if not _ICONS_CACHE: load_all_icons(size)
    key = get_icon_key(description)
    icon = _ICONS_CACHE.get(key)
    if icon:
        img.paste(icon, (cx - size // 2, cy - size // 2), icon)

def draw_moon(img, cx, cy, r, phase_frac, phase_name=""):
    draw = ImageDraw.Draw(img)
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(230, 230, 200))
