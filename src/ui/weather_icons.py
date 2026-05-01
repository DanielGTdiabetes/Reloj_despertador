"""
weather_icons.py — Gestor de iconos meteorológicos.
Carga PNGs de alta calidad desde assets/weather o dibuja fallbacks con PIL.
"""
from __future__ import annotations
import os
import math
from PIL import Image, ImageDraw

# Cache de iconos cargados
_CACHE: dict[tuple[str, int], Image.Image] = {}

# ── Colores Luna ──────────────────────────────────────────────────────────────
MOON_LIT    = (232, 221, 184)
MOON_DARK   = ( 26,  32,  48)
MOON_BORDER = ( 42,  52,  72)

def get_icon_key(description: str) -> str:
    """Mapea descripción de OWM a nombre de archivo interno."""
    desc = (description or "").lower()
    mapping = [
        (("storm", "thunder", "tormenta", "rayo"),   "storm"),
        (("snow",  "nieve",   "granizo"),             "snow"),
        (("rain",  "lluvia",  "drizzle", "llovizna"), "rain"),
        (("wind",  "viento"),                         "wind"),
        (("fog",   "mist",    "niebla",  "bruma"),    "fog"),
        (("partly","parcial", "nublado", "clouds"),   "partly"),
        (("cloud", "nube",    "overcast"),            "cloud"),
        (("clear", "sun",     "sol",     "despej"),   "sun"),
    ]
    for keywords, key in mapping:
        if any(k in desc for k in keywords):
            return key
    return "partly"

def draw_weather_icon(img: Image.Image, description: str,
                      cx: int, cy: int, size: int = 52) -> None:
    """
    Dibuja un icono. Prioriza PNG de assets/weather/{key}.png.
    """
    key = get_icon_key(description)
    icon_filename = f"{key}.png"
    cache_key = (icon_filename, size)
    
    if cache_key not in _CACHE:
        # Buscar en assets/weather
        base_dir = os.path.dirname(__file__)
        path = os.path.join(base_dir, "..", "assets", "weather", icon_filename)
        
        if os.path.exists(path):
            try:
                icon_img = Image.open(path).convert("RGBA")
                icon_img = icon_img.resize((size, size), Image.LANCZOS)
                _CACHE[cache_key] = icon_img
            except Exception as e:
                print(f"[WeatherIcons] Error cargando {path}: {e}")
                _CACHE[cache_key] = None
        else:
            # print(f"[WeatherIcons] No existe: {path}")
            _CACHE[cache_key] = None

    asset = _CACHE[cache_key]
    if asset:
        img.paste(asset, (cx - size // 2, cy - size // 2), asset)
    else:
        # Fallback básico si no hay PNG
        draw = ImageDraw.Draw(img)
        draw.ellipse([cx-size//3, cy-size//3, cx+size//3, cy+size//3], fill=(80,80,100))

def draw_moon(img: Image.Image, cx: int, cy: int, r: int,
              phase_frac: float, phase_name: str = "") -> None:
    """Dibuja la luna en la fase indicada."""
    draw = ImageDraw.Draw(img)
    # Fondo oscuro
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=MOON_DARK, outline=MOON_BORDER, width=1)
    
    if phase_frac < 0.03 or phase_frac > 0.97: return # Nueva
    
    waning = phase_frac >= 0.5
    phase_01 = (phase_frac - 0.5) * 2 if waning else phase_frac * 2
    ellipse_rx = abs(math.cos(math.pi * phase_01)) * r
    
    lit = Image.new("RGBA", (r * 2 + 2, r * 2 + 2), (0, 0, 0, 0))
    ld  = ImageDraw.Draw(lit)
    
    if not waning:
        ld.ellipse([0, 0, r*2, r*2], fill=(*MOON_LIT, 255))
        ld.rectangle([0, 0, r, r*2], fill=(0, 0, 0, 0))
        if ellipse_rx > 1:
            t_img = Image.new("RGBA", (r*2+2, r*2+2), (0, 0, 0, 0))
            td = ImageDraw.Draw(t_img)
            ex0, ex1 = r - int(ellipse_rx), r + int(ellipse_rx)
            td.ellipse([ex0, 0, ex1, r*2], fill=(*MOON_DARK, 255))
            lit.paste((0,0,0,0), mask=t_img.split()[3])
            if phase_01 > 0.5:
                ImageDraw.Draw(lit).ellipse([ex0, 0, ex1, r*2], fill=(*MOON_LIT, 255))
    else:
        ld.ellipse([0, 0, r*2, r*2], fill=(*MOON_LIT, 255))
        ld.rectangle([r, 0, r*2+2, r*2], fill=(0, 0, 0, 0))
        if ellipse_rx > 1:
            t_img = Image.new("RGBA", (r*2+2, r*2+2), (0, 0, 0, 0))
            td = ImageDraw.Draw(t_img)
            ex0, ex1 = r - int(ellipse_rx), r + int(ellipse_rx)
            td.ellipse([ex0, 0, ex1, r*2], fill=(*MOON_LIT, 255))
            lit = Image.alpha_composite(lit, t_img)
            if phase_01 > 0.5:
                ImageDraw.Draw(lit).ellipse([ex0, 0, ex1, r*2], fill=(0, 0, 0, 0))
                
    img.paste(lit, (cx - r, cy - r), lit)
