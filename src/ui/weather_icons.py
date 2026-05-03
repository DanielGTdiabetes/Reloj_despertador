from __future__ import annotations
import os
from PIL import Image, ImageDraw

_ICONS_CACHE: dict = {}
_MOON_CACHE: dict = {}

_PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "moon_phases", "processed")
_WEATHER_DIR  = os.path.join(os.path.dirname(__file__), "..", "assets", "weather")


def get_icon_key(description: str) -> str:
    desc = (description or "").lower()
    if "storm" in desc or "thunder" in desc: return "storm"
    if "snow"  in desc:                      return "snow"
    if "rain"  in desc or "drizzle" in desc: return "rain"
    if "fog"   in desc or "mist"    in desc: return "fog"
    if "sun"   in desc or "clear"   in desc: return "sun"
    return "partly"


def draw_weather_icon(img, description, cx, cy, size=50):
    key = get_icon_key(description)
    cache_key = (key, size)
    if cache_key not in _ICONS_CACHE:
        path = os.path.join(_WEATHER_DIR, f"{key}.png")
        if os.path.exists(path):
            try:
                icon = Image.open(path).convert("RGBA")
                _ICONS_CACHE[cache_key] = icon.resize((size, size), Image.LANCZOS)
            except Exception:
                _ICONS_CACHE[cache_key] = None
        else:
            _ICONS_CACHE[cache_key] = None

    icon = _ICONS_CACHE.get(cache_key)
    if icon:
        img.paste(icon, (cx - size // 2, cy - size // 2), icon)


def _phase_to_filename(phase_frac: float) -> str:
    p = phase_frac % 1.0
    if p < 0.06 or p > 0.94: return "new_moon.png"
    if p < 0.23:              return "waxing_crescent.png"
    if p < 0.27:              return "first_quarter.png"
    if p < 0.49:              return "waxing_gibbous.png"
    if p < 0.51:              return "full_moon.png"
    if p < 0.73:              return "waning_gibbous.png"
    if p < 0.77:              return "last_quarter.png"
    return "waning_crescent.png"


def draw_moon(img, cx, cy, r, phase_frac, phase_name=""):
    size = r * 2 + 14   # extra padding para mostrar el glow de la luna
    filename = _phase_to_filename(phase_frac)
    cache_key = (filename, size)

    if cache_key not in _MOON_CACHE:
        path = os.path.join(_PROCESSED_DIR, filename)
        if os.path.exists(path):
            try:
                raw = Image.open(path).convert("RGBA")
                _MOON_CACHE[cache_key] = raw.resize((size, size), Image.LANCZOS)
            except Exception:
                _MOON_CACHE[cache_key] = None
        else:
            _MOON_CACHE[cache_key] = None

    moon = _MOON_CACHE.get(cache_key)
    if moon:
        img.paste(moon, (cx - size // 2, cy - size // 2), moon)
    else:
        # fallback minimalista
        draw = ImageDraw.Draw(img)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(230, 230, 200))
