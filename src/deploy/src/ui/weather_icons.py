"""
weather_icons.py — Iconos meteorológicos de alta calidad con PIL.
Renderiza iconos vectoriales usando primitivas PIL/Pillow.
Sin dependencias externas adicionales.
"""
from __future__ import annotations
import math
from PIL import Image, ImageDraw


# ── Paleta de colores ─────────────────────────────────────────────────────────

SUN_CORE    = (255, 229, 102)
SUN_MID     = (255, 184,   0)
SUN_OUTER   = (255, 140,   0)
CLOUD_LIGHT = (232, 238, 248)
CLOUD_MID   = (184, 200, 224)
CLOUD_DARK  = (128, 144, 168)
STORM_CLOUD = ( 74,  80,  96)
RAIN_DROP   = (106, 176, 255)
SNOW_FLAKE  = (168, 216, 255)
SNOW_CLOUD  = (208, 220, 240)
WIND_LINE   = (160, 216, 240)
FOG_LAYER   = (184, 200, 216)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _alpha_paste(base: Image.Image, layer: Image.Image, pos: tuple) -> None:
    """Pega una imagen RGBA sobre base RGB con alpha."""
    if layer.mode != "RGBA":
        layer = layer.convert("RGBA")
    base.paste(layer, pos, layer)


def _draw_cloud_shape(draw: ImageDraw.Draw, x: int, y: int,
                       w: int, h: int, color: tuple, radius: int = 0) -> None:
    """Dibuja una nube volumétrica con círculos superpuestos."""
    # Cuerpo base
    draw.rectangle([x, y + h//3, x + w, y + h], fill=color)
    # Burbuja izquierda pequeña
    r1 = int(w * 0.28)
    draw.ellipse([x, y + h//2 - r1, x + r1*2, y + h//2 + r1], fill=color)
    # Burbuja central grande
    r2 = int(w * 0.36)
    draw.ellipse([x + w//4, y, x + w//4 + r2*2, y + r2*2], fill=color)
    # Burbuja derecha mediana
    r3 = int(w * 0.28)
    draw.ellipse([x + w - r3*2, y + h//4, x + w, y + h//4 + r3*2], fill=color)


# ── Iconos ────────────────────────────────────────────────────────────────────

def _draw_sun(img: Image.Image, cx: int, cy: int, size: int) -> None:
    draw = ImageDraw.Draw(img)
    r_core = size // 4
    r_rays = int(size * 0.42)
    n_rays = 8
    # Rayos
    for i in range(n_rays):
        angle = (i * 360 / n_rays) * math.pi / 180
        x1 = cx + int((r_core + 3) * math.cos(angle))
        y1 = cy + int((r_core + 3) * math.sin(angle))
        x2 = cx + int(r_rays * math.cos(angle))
        y2 = cy + int(r_rays * math.sin(angle))
        draw.line([x1, y1, x2, y2], fill=SUN_MID, width=max(2, size // 18))
    # Núcleo con gradiente simulado (círculos concéntricos)
    for dr in range(r_core, 0, -1):
        t = 1 - dr / r_core
        r = int(SUN_CORE[0] * t + SUN_OUTER[0] * (1-t))
        g = int(SUN_CORE[1] * t + SUN_OUTER[1] * (1-t))
        b = int(SUN_CORE[2] * t + SUN_OUTER[2] * (1-t))
        draw.ellipse([cx-dr, cy-dr, cx+dr, cy+dr], fill=(r, g, b))
    # Brillo central
    rb = max(2, r_core // 3)
    draw.ellipse([cx-rb, cy-rb, cx+rb, cy+rb], fill=(255, 248, 200))


def _draw_cloud(img: Image.Image, cx: int, cy: int, size: int,
                color: tuple = None) -> None:
    draw = ImageDraw.Draw(img)
    color = color or CLOUD_LIGHT
    w = int(size * 0.85)
    h = int(size * 0.55)
    x = cx - w // 2
    y = cy - h // 4
    _draw_cloud_shape(draw, x, y, w, h, CLOUD_MID)
    _draw_cloud_shape(draw, x + 2, y - 2, w - 4, h - 2, color)


def _draw_partly(img: Image.Image, cx: int, cy: int, size: int) -> None:
    draw = ImageDraw.Draw(img)
    # Sol (detrás, desplazado arriba-izquierda)
    scx = cx - size // 8
    scy = cy - size // 6
    sr  = size // 6
    n_rays = 6
    for i in range(n_rays):
        angle = (i * 60 - 15) * math.pi / 180
        x1 = scx + int((sr + 2) * math.cos(angle))
        y1 = scy + int((sr + 2) * math.sin(angle))
        x2 = scx + int((sr + size // 8) * math.cos(angle))
        y2 = scy + int((sr + size // 8) * math.sin(angle))
        draw.line([x1, y1, x2, y2], fill=SUN_MID, width=max(2, size // 22))
    draw.ellipse([scx-sr, scy-sr, scx+sr, scy+sr], fill=SUN_CORE)
    # Nube (encima, desplazada abajo-derecha)
    w = int(size * 0.72)
    h = int(size * 0.48)
    x = cx - w // 4
    y = cy - h // 6
    _draw_cloud_shape(draw, x, y, w, h, CLOUD_MID)
    _draw_cloud_shape(draw, x + 2, y - 2, w - 4, h - 2, CLOUD_LIGHT)


def _draw_rain(img: Image.Image, cx: int, cy: int, size: int) -> None:
    draw = ImageDraw.Draw(img)
    # Nube oscura
    w = int(size * 0.82)
    h = int(size * 0.44)
    x = cx - w // 2
    y = cy - size // 3
    _draw_cloud_shape(draw, x, y, w, h, CLOUD_DARK)
    _draw_cloud_shape(draw, x + 2, y - 2, w - 4, h - 2, CLOUD_MID)
    # Gotas
    drop_y0 = cy + size // 8
    drop_len = size // 7
    drop_x_offsets = [-size//5, -size//12, size//12, size//5]
    stagger = [0, drop_len // 2, 0, drop_len // 2]
    lw = max(2, size // 20)
    for i, dx in enumerate(drop_x_offsets):
        x1 = cx + dx
        y1 = drop_y0 + stagger[i]
        x2 = x1 + 2
        y2 = y1 + drop_len
        draw.line([x1, y1, x2, y2], fill=RAIN_DROP, width=lw)


def _draw_storm(img: Image.Image, cx: int, cy: int, size: int) -> None:
    draw = ImageDraw.Draw(img)
    # Nube muy oscura
    w = int(size * 0.88)
    h = int(size * 0.44)
    x = cx - w // 2
    y = cy - size // 2 + 2
    _draw_cloud_shape(draw, x, y, w, h, (50, 55, 70))
    _draw_cloud_shape(draw, x + 2, y - 2, w - 4, h - 2, STORM_CLOUD)
    # Rayo
    bolt = [
        (cx + size//12,  cy - size//10),
        (cx - size//10,  cy + size//10),
        (cx,             cy + size//10),
        (cx - size//8,   cy + size//2 - 2),
        (cx + size//6,   cy + size//12),
        (cx + size//16,  cy + size//12),
        (cx + size//12,  cy - size//10),
    ]
    draw.polygon(bolt, fill=(255, 224, 64))
    draw.polygon(bolt, outline=(255, 248, 160), width=1)


def _draw_snow(img: Image.Image, cx: int, cy: int, size: int) -> None:
    draw = ImageDraw.Draw(img)
    # Nube clara
    w = int(size * 0.82)
    h = int(size * 0.44)
    x = cx - w // 2
    y = cy - size // 3
    _draw_cloud_shape(draw, x, y, w, h, SNOW_CLOUD)
    _draw_cloud_shape(draw, x + 2, y - 2, w - 4, h - 2, (220, 232, 248))
    # Copos de nieve (hexagonales simplificados)
    flake_positions = [
        (cx - size//5, cy + size//8),
        (cx,           cy + size//5),
        (cx + size//5, cy + size//8),
        (cx - size//10, cy + size//3),
        (cx + size//10, cy + size//3),
    ]
    r_flake = max(3, size // 14)
    lw = max(1, size // 22)
    for fx, fy in flake_positions:
        for angle_deg in range(0, 180, 60):
            angle = angle_deg * math.pi / 180
            x1 = fx + int(r_flake * math.cos(angle))
            y1 = fy + int(r_flake * math.sin(angle))
            x2 = fx - int(r_flake * math.cos(angle))
            y2 = fy - int(r_flake * math.sin(angle))
            draw.line([x1, y1, x2, y2], fill=SNOW_FLAKE, width=lw)
        draw.ellipse([fx-2, fy-2, fx+2, fy+2], fill=(208, 240, 255))


def _draw_wind(img: Image.Image, cx: int, cy: int, size: int) -> None:
    draw = ImageDraw.Draw(img)
    # Líneas onduladas de viento
    lines = [
        (cy - size//5, size * 9//10, 3),
        (cy,           size,         4),
        (cy + size//5, size * 8//10, 3),
        (cy + size//3, size * 7//10, 2),
    ]
    lw = max(2, size // 20)
    x0 = cx - size // 2 + 4
    for ly, lw_mult, alpha_div in lines:
        x1 = x0
        x2 = x0 + int(size * lw_mult / 10)
        # Curva simulada con 3 segmentos
        mid_x = (x1 + x2) // 2
        draw.line([x1, ly, mid_x, ly - size//16, x2, ly], fill=WIND_LINE, width=lw, joint="curve")


def _draw_fog(img: Image.Image, cx: int, cy: int, size: int) -> None:
    draw = ImageDraw.Draw(img)
    # Sol difuso detrás
    r = size // 6
    for dr in range(r + size//8, r - 2, -1):
        alpha = max(0, 180 - (dr - r) * 12)
        draw.ellipse([cx-dr, cy-size//6-dr, cx+dr, cy-size//6+dr],
                     fill=(*SUN_CORE[:3], alpha) if False else (255, 220, 80))
    # Capas de niebla (rectángulos redondeados)
    fog_rows = [
        (cy - size//4,  size * 4//5, 0.55),
        (cy - size//10, size * 9//10, 0.72),
        (cy + size//12, size * 4//5, 0.80),
        (cy + size//3,  size * 7//10, 0.60),
    ]
    lw = max(4, size // 10)
    for fy, fw, opacity in fog_rows:
        x1 = cx - fw // 2
        x2 = cx + fw // 2
        col = tuple(int(c * opacity + 5 * (1-opacity)) for c in FOG_LAYER)
        draw.rounded_rectangle([x1, fy - lw//2, x2, fy + lw//2],
                                radius=lw//2, fill=col)


# ── Dispatcher ────────────────────────────────────────────────────────────────

_COND_MAP = [
    (("storm", "thunder", "tormenta", "rayo"),   "storm"),
    (("snow",  "nieve",   "granizo"),             "snow"),
    (("rain",  "lluvia",  "drizzle", "llovizna"), "rain"),
    (("wind",  "viento"),                         "wind"),
    (("fog",   "mist",    "niebla",  "bruma"),    "fog"),
    (("partly","parcial", "nublado", "clouds"),   "partly"),
    (("cloud", "nube",    "overcast"),            "cloud"),
    (("clear", "sun",     "sol",     "despej"),   "sun"),
]

_DRAWERS = {
    "storm":  _draw_storm,
    "snow":   _draw_snow,
    "rain":   _draw_rain,
    "wind":   _draw_wind,
    "fog":    _draw_fog,
    "partly": _draw_partly,
    "cloud":  _draw_cloud,
    "sun":    _draw_sun,
}

def get_icon_key(description: str) -> str:
    desc = (description or "").lower()
    for keywords, key in _COND_MAP:
        if any(k in desc for k in keywords):
            return key
    return "partly"


# ── Icon Cache ────────────────────────────────────────────────────────────────

_ASSET_CACHE: dict[tuple[str, int], Image.Image] = {}

def draw_weather_icon(img: Image.Image, description: str,
                      cx: int, cy: int, size: int = 52) -> None:
    """
    Dibuja un icono meteorológico. Intenta cargar un PNG de assets/weather,
    si falla, lo dibuja usando primitivas PIL.
    """
    import os
    key_name = get_icon_key(description)
    
    # 1. Intentar cargar desde assets
    icon_filename = f"{key_name}.png"
    cache_key = (icon_filename, size)
    
    if cache_key not in _ASSET_CACHE:
        # Buscar la ruta de assets/weather
        base_dir = os.path.dirname(__file__)
        assets_path = os.path.join(base_dir, "..", "assets", "weather", icon_filename)
        
        if os.path.exists(assets_path):
            try:
                icon_img = Image.open(assets_path).convert("RGBA")
                icon_img = icon_img.resize((size, size), Image.LANCZOS)
                _ASSET_CACHE[cache_key] = icon_img
            except Exception:
                _ASSET_CACHE[cache_key] = None
        else:
            _ASSET_CACHE[cache_key] = None

    icon_asset = _ASSET_CACHE[cache_key]
    
    if icon_asset:
        # Pegar el asset con alpha
        img.paste(icon_asset, (cx - size // 2, cy - size // 2), icon_asset)
    else:
        # 2. Fallback: Dibujo manual (PIL Primitives)
        drawer = _DRAWERS.get(key_name, _draw_partly)
        drawer(img, cx, cy, size)


def render_weather_icon(description: str, size: int = 64,
                        bg: tuple = (5, 10, 25)) -> Image.Image:
    """
    Devuelve una imagen PIL cuadrada con el icono centrado.
    Útil para previsualización o testing.
    """
    img = Image.new("RGB", (size, size), bg)
    draw_weather_icon(img, description, size // 2, size // 2, size)
    return img


# ── Luna ──────────────────────────────────────────────────────────────────────

MOON_LIT    = (232, 221, 184)
MOON_BRIGHT = (255, 248, 224)
MOON_DARK   = ( 26,  32,  48)
MOON_BORDER = ( 42,  52,  72)


def draw_moon(img: Image.Image, cx: int, cy: int, r: int,
              phase_frac: float, phase_name: str = "") -> None:
    """
    Dibuja la luna en la fase indicada sobre `img`.

    Args:
        img:        Imagen PIL (modo RGB).
        cx, cy:     Centro de la luna.
        r:          Radio en píxeles.
        phase_frac: Fracción del ciclo lunar 0.0–1.0
                    (0=nueva, 0.25=cuarto crec., 0.5=llena, 0.75=cuarto meng.)
        phase_name: Nombre de la fase (no usado para dibujo).
    """
    draw = ImageDraw.Draw(img)

    # Fondo oscuro (disco lunar completo)
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=MOON_DARK, outline=MOON_BORDER, width=1)

    if phase_frac < 0.03 or phase_frac > 0.97:
        # Luna nueva — solo halo tenue
        draw.ellipse([cx-r, cy-r, cx+r, cy+r],
                     outline=(42, 60, 90), width=2)
        return

    waning   = phase_frac >= 0.5
    phase_01 = (phase_frac - 0.5) * 2 if waning else phase_frac * 2
    # ellipse_rx: 0 = cuarto, r = llena/nueva
    ellipse_rx = abs(math.cos(math.pi * phase_01)) * r

    # Creamos imagen temporal para la mitad iluminada
    lit = Image.new("RGBA", (r * 2 + 2, r * 2 + 2), (0, 0, 0, 0))
    ld  = ImageDraw.Draw(lit)

    if not waning:
        # Creciente: lado derecho iluminado
        # 1. Semicírculo derecho
        ld.ellipse([0, 0, r*2, r*2], fill=(*MOON_LIT, 255))
        # 2. Tapar lado izquierdo con oscuro
        ld.rectangle([0, 0, r, r*2], fill=(0, 0, 0, 0))
        # 3. Elipse de terminator (puede ser sombra o luz)
        if ellipse_rx > 1:
            # Terminator es una semielipse que tapa/expone el centro
            t_img = Image.new("RGBA", (r*2+2, r*2+2), (0, 0, 0, 0))
            td = ImageDraw.Draw(t_img)
            ex0 = r - int(ellipse_rx)
            ex1 = r + int(ellipse_rx)
            td.ellipse([ex0, 0, ex1, r*2], fill=(*MOON_DARK, 255))
            # El terminator tapa la izquierda de la parte iluminada
            # Cuando phase_01 < 0.5 (primer cuarto), el terminator es sombra sobre luz
            lit.paste((0,0,0,0), mask=t_img.split()[3])
            ld2 = ImageDraw.Draw(lit)
            if phase_01 > 0.5:
                ld2.ellipse([ex0, 0, ex1, r*2], fill=(*MOON_LIT, 255))
    else:
        # Menguante: lado izquierdo iluminado
        ld.ellipse([0, 0, r*2, r*2], fill=(*MOON_LIT, 255))
        ld.rectangle([r, 0, r*2+2, r*2], fill=(0, 0, 0, 0))
        if ellipse_rx > 1:
            t_img = Image.new("RGBA", (r*2+2, r*2+2), (0, 0, 0, 0))
            td = ImageDraw.Draw(t_img)
            ex0 = r - int(ellipse_rx)
            ex1 = r + int(ellipse_rx)
            td.ellipse([ex0, 0, ex1, r*2], fill=(*MOON_LIT, 255))
            lit = Image.alpha_composite(lit, t_img)
            if phase_01 > 0.5:
                ld2 = ImageDraw.Draw(lit)
                ld2.ellipse([ex0, 0, ex1, r*2], fill=(0, 0, 0, 0))

    # Pegar la parte iluminada centrada
    _alpha_paste(img, lit, (cx - r, cy - r))

    # Cráteres sutiles sobre la superficie iluminada
    draw = ImageDraw.Draw(img)
    craters = [
        (cx - r//5,      cy - r//5,      r//8),
        (cx + r//4,      cy + r//6,      r//10),
        (cx - r//8,      cy + r//3,      r//12),
        (cx + r//3 - 2,  cy - r//4,      r//14),
    ]
    for ccx, ccy, cr in craters:
        # Solo dibujar si está dentro del círculo lunar
        if (ccx - cx)**2 + (ccy - cy)**2 < (r - cr)**2:
            draw.ellipse([ccx-cr, ccy-cr, ccx+cr, ccy+cr],
                         fill=tuple(max(0, c - 18) for c in MOON_LIT))

    # Borde final
    draw.ellipse([cx-r, cy-r, cx+r, cy+r],
                 outline=(*MOON_LIT[:3], 80) if False else MOON_BORDER,
                 width=1)


# ── Self-test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os
    out_dir = "/tmp/weather_icons_test"
    os.makedirs(out_dir, exist_ok=True)

    # Test iconos meteorológicos
    for desc in ["sol despejado", "parcialmente nublado", "nube", "lluvia",
                 "tormenta", "nieve", "viento", "niebla"]:
        img = render_weather_icon(desc, size=64)
        fname = desc.replace(" ", "_") + ".png"
        img.save(os.path.join(out_dir, fname))
        print(f"  ✓ {fname}")

    # Test fases lunares
    base = Image.new("RGB", (80, 80), (5, 10, 25))
    phases = [0.01, 0.12, 0.25, 0.38, 0.50, 0.63, 0.75, 0.88]
    for frac in phases:
        img = Image.new("RGB", (80, 80), (5, 10, 25))
        draw_moon(img, 40, 40, 30, frac)
        fname = f"moon_{int(frac*100):03d}.png"
        img.save(os.path.join(out_dir, fname))
        print(f"  ✓ {fname}")

    print(f"\nImágenes guardadas en {out_dir}")
