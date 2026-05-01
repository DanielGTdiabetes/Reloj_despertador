"""
round_home.py — Pantalla redonda premium.
CAMBIOS respecto a la versión anterior:
  - _draw_solar_arc(): arco con progreso solar + punto sol + colores por período
  - render(): iconos meteorológicos PIL de alta calidad, temp min/max, badge campana
  - render_night(): pantalla de noche con luna por fases, estrellas, badge alarma
  - render_focus(): compatible con icono 'location' (pin de mapa)
  - get_period(): función auxiliar que espeja la lógica de SunService

Compatible 100% con app.py — no cambia ninguna firma de método existente.
Solo se añade render_night() que app.py llama cuando period == 'night'.
"""
from __future__ import annotations
import math
import time
import random
from typing import Optional
from PIL import Image, ImageDraw
from .theme import (
    F, CYAN, PURPLE, BG, WHITE, DIM_WHITE, ICONS,
    condition_to_icon_file, draw_menu_icon
)
from .weather_icons import draw_weather_icon, draw_moon

# ── Dimensiones ───────────────────────────────────────────────────────────────
W = H = 240
CX = CY = 120
ARC_R     = 114
ARC_THICK = 5

# ── Colores adicionales ───────────────────────────────────────────────────────
AMBER    = (255, 180,  60)
DIM_CYAN = ( 60, 110, 140)
SUN_DOT  = (255, 200,  60)
MOON_TXT = (220, 210, 170)
RED_DIM  = (200,  80,  80)

# Paleta de arco según período del día
_ARC_PALETTE = {
    "day":     {"a": CYAN,              "b": PURPLE,            "dot": SUN_DOT},
    "dawn":    {"a": (255, 160,  80),   "b": (180, 100, 220),   "dot": (255, 200, 100)},
    "dusk":    {"a": (255, 100,  60),   "b": (200,  80, 180),   "dot": (255, 140,  80)},
    "night":   {"a": ( 80,  80, 160),   "b": ( 50,  50, 120),   "dot": (100, 100, 200)},
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _text_center(draw: ImageDraw.Draw, y: int, text: str, font, fill: tuple) -> None:
    bb = draw.textbbox((0, 0), text, font=font)
    w  = bb[2] - bb[0]
    draw.text(((W - w) // 2, y), text, font=font, fill=fill)

def _text_right(draw: ImageDraw.Draw, y: int, x_right: int,
                text: str, font, fill: tuple) -> None:
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text((x_right - (bb[2]-bb[0]), y), text, font=font, fill=fill)

def _draw_stars(img: Image.Image, count: int = 45) -> None:
    """Estrellas con posición fija (seed=42)."""
    draw = ImageDraw.Draw(img)
    rng  = random.Random(42)
    for _ in range(count):
        while True:
            x = rng.randint(10, W - 10)
            y = rng.randint(10, H - 10)
            if (x - CX)**2 + (y - CY)**2 < (ARC_R - 8)**2:
                break
        alpha = rng.randint(40, 180)
        size  = rng.randint(1, 2)
        draw.ellipse([x, y, x+size, y+size],
                     fill=(alpha, alpha, min(255, alpha+30)))

# ── Arco solar ────────────────────────────────────────────────────────────────

def _draw_solar_arc(draw: ImageDraw.Draw, period: str, progress: float,
                    sunrise_dt=None, sunset_dt=None) -> None:
    """
    Dibuja el arco exterior de la pantalla redonda con progreso solar.
    progress: 0.0=amanecer, 1.0=atardecer, -1=noche/fuera de rango.
    """
    pal = _ARC_PALETTE.get(period, _ARC_PALETTE["day"])
    box = [CX - ARC_R, CY - ARC_R, CX + ARC_R, CY + ARC_R]

    # Track base
    draw.arc(box, start=-90, end=270, fill=(20, 25, 45), width=ARC_THICK + 2)
    # Arco B (lado izquierdo fijo)
    draw.arc(box, start=90,  end=270, fill=pal["b"],     width=ARC_THICK)

    # Arco A (progreso solar, lado derecho)
    isday = 0.0 <= progress <= 1.0
    if isday and progress > 0.01:
        end_angle = -90 + int(180 * progress)
        draw.arc(box, start=-90, end=end_angle, fill=pal["a"], width=ARC_THICK)
        # Punto sol
        angle_rad = math.radians(-90 + 180 * progress)
        sx = int(CX + ARC_R * math.cos(angle_rad))
        sy = int(CY + ARC_R * math.sin(angle_rad))
        r_dot = ARC_THICK + 2
        draw.ellipse([sx-r_dot, sy-r_dot, sx+r_dot, sy+r_dot], fill=pal["dot"])
    elif not isday:
        draw.arc(box, start=-90, end=90, fill=pal["a"], width=ARC_THICK)

# ── Badge de alarma ───────────────────────────────────────────────────────────

_DAY_LABELS = ["L","M","X","J","V","S","D"]

def _days_label(days: list) -> str:
    if not days: return ""
    s = sorted(days)
    if len(s) == 7:   return "TODOS"
    if s == [0,1,2,3,4]: return "L-V"
    if s == [5,6]:    return "S-D"
    if len(s) <= 3:   return " ".join(_DAY_LABELS[d] for d in s)
    return f"{len(s)}d"

def _draw_alarm_badge(draw: ImageDraw.Draw, alarm: dict, y: int,
                      badge_color: tuple = None) -> None:
    """Dibuja badge de alarma con campana + hora + días."""
    col = badge_color or (AMBER if alarm.get("enabled") else (50, 55, 75))
    if not alarm.get("enabled"):
        _text_center(draw, y, "ALARMA OFF", F.weather_sub, (55, 60, 80))
        return
    h_str = f"{alarm.get('hour', 7):02d}:{alarm.get('minute', 0):02d}"
    days  = _days_label(alarm.get("days", list(range(7))))

    # Campana PIL (simple, clara y reconocible)
    bx, by = CX - 38, y
    bs = 11
    draw.chord([bx, by, bx+bs, by+bs-2], 180, 0, fill=col)
    draw.rectangle([bx-1, by+bs-4, bx+bs+1, by+bs-1], fill=col)
    draw.ellipse([bx+bs//2-2, by+bs-2, bx+bs//2+2, by+bs+3], fill=WHITE)

    # Texto hora
    tx = bx + bs + 5
    draw.text((tx, y), h_str, font=F.weather_sub, fill=col)
    if days:
        bb = draw.textbbox((0, 0), h_str, font=F.weather_sub)
        draw.text((tx + bb[2]-bb[0] + 4, y+1), days, font=F.weather_sub,
                  fill=(*col[:3],) if len(col) == 3 else col)

# ══════════════════════════════════════════════════════════════════════════════
#  CLASE PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

class RoundHomeScreen:

    def __init__(self) -> None:
        pass

    # ── Pantalla de día ───────────────────────────────────────────────────────

    def render(self, now, weather: dict, sun_info: dict,
               moon: dict, alarm: dict, status: str) -> Image.Image:
        """
        Pantalla principal de día/amanecer/atardecer.
        Muestra: arco solar, fecha, hora, temp min/max, icono clima, descripción,
                 temperatura actual, badge alarma.
        """
        img  = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        period   = sun_info.get("period", "day")
        progress = sun_info.get("progress", 0.5)
        sunrise  = sun_info.get("sunrise")
        sunset   = sun_info.get("sunset")
        pal      = _ARC_PALETTE.get(period, _ARC_PALETTE["day"])

        # Arco solar
        _draw_solar_arc(draw, period, progress, sunrise, sunset)

        # Fecha corta
        days_es  = ["LUN","MAR","MIE","JUE","VIE","SAB","DOM"]
        date_str = f"{days_es[now.weekday()]} {now.day:02d}"
        _text_center(draw, 26, date_str, F.date_top, pal["a"])

        # Hora
        t_str = now.strftime("%H:%M")
        bb    = draw.textbbox((0, 0), t_str, font=F.clock)
        draw.text(((W-(bb[2]-bb[0]))//2, 48), t_str, font=F.clock, fill=WHITE)

        # Temp min/max
        temp_max = weather.get("temp_max")
        temp_min = weather.get("temp_min")
        # Intentar obtener de forecast si no viene en current
        if temp_max is None:
            temp_max = weather.get("temp")
        if temp_max is not None and temp_min is not None:
            minmax = f"\u2193{temp_min:.0f}\u00b0  \u2191{temp_max:.0f}\u00b0"
            _text_center(draw, 100, minmax, F.weather_sub, DIM_WHITE)

        # Icono meteorológico PIL
        desc = (weather.get("description") or "").upper()
        draw_weather_icon(img, desc, CX, 128, size=50)

        # Descripción (truncada)
        if desc:
            _text_center(draw, 158, desc[:20], F.weather_sub, DIM_WHITE)

        # Temperatura actual
        temp = weather.get("temp")
        temp_str = f"{temp:.1f}\u00b0C" if temp is not None else "--\u00b0C"
        _text_center(draw, 172, temp_str, F.temp_big, pal["a"])

        # Badge alarma
        _draw_alarm_badge(draw, alarm, 196)

        return img

    # ── Pantalla de noche (luna) ──────────────────────────────────────────────

    def render_night(self, now, moon: dict, alarm: dict,
                     sun_info: dict = None) -> Image.Image:
        """
        Pantalla de noche: fondo estrellado, arco nocturno, hora, fase lunar,
        nombre de fase, badge alarma.

        Args:
            now:      datetime actual (timezone-aware).
            moon:     dict con 'phase' (0.0-1.0), 'phase_name', 'illumination'.
            alarm:    dict con 'enabled', 'hour', 'minute', 'days'.
            sun_info: opcional, para arco correcto.
        """
        img  = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # Fondo nocturno con vignette
        for dr in range(118, 0, -4):
            t   = 1 - dr / 118
            col = (int(5+t*10), int(10+t*12), int(25+t*18))
            draw.ellipse([CX-dr, CY-dr, CX+dr, CY+dr], fill=col)

        # Estrellas
        _draw_stars(img)

        # Arco nocturno
        sun_info = sun_info or {}
        _draw_solar_arc(draw, "night", -1,
                        sun_info.get("sunrise"), sun_info.get("sunset"))

        # Fecha
        days_es  = ["LUN","MAR","MIE","JUE","VIE","SAB","DOM"]
        date_str = f"{days_es[now.weekday()]} {now.day:02d}"
        _text_center(draw, 24, date_str, F.date_top, (80, 80, 165))

        # Hora con efecto pulso (varía con el segundo)
        t_str = now.strftime("%H:%M")
        pulse = (math.sin(time.time() * 0.7) + 1) / 2
        pulse_col = tuple(int(WHITE[i] * (0.72 + 0.28 * pulse)) for i in range(3))
        bb = draw.textbbox((0, 0), t_str, font=F.clock)
        draw.text(((W-(bb[2]-bb[0]))//2, 46), t_str, font=F.clock, fill=pulse_col)

        # Nombre de fase
        phase_name = (moon.get("phase_name") or "").upper()
        _text_center(draw, 110, phase_name, F.weather_sub, MOON_TXT)

        # Luna PIL
        moon_frac = moon.get("phase", 0.5)
        draw_moon(img, CX, CY + 18, r=32, phase_frac=moon_frac,
                  phase_name=phase_name)

        # Iluminación
        illumination = moon.get("illumination", 0)
        _text_center(draw, 188, f"{illumination:.0f}% ilum.", F.weather_sub,
                     (110, 110, 155))

        # Badge alarma
        _draw_alarm_badge(draw, alarm, 204,
                          badge_color=AMBER if alarm.get("enabled") else None)

        return img

    # ── Menú (focus) ─────────────────────────────────────────────────────────

    def render_focus(self, title: str, subtitle: str,
                     kind: str = "", value=None) -> Image.Image:
        """
        Pantalla de foco para estados de menú.
        kind puede ser: alarm, wifi, sync, weather, location, brightness.
        """
        img  = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw.ellipse([5, 5, W-5, H-5], outline=PURPLE, width=3)

        # Icono central
        draw_menu_icon(draw, CX-30, CY-60, 60, kind)

        _text_center(draw, CY+10,  title.upper(), F.date_top, WHITE)
        if value:
            _text_center(draw, CY+35, str(value), F.temp_big, CYAN)
        _text_center(draw, H-48, subtitle, F.weather_sub, DIM_WHITE)
        return img

    # ── Alarma sonando ────────────────────────────────────────────────────────

    def render_alarm_ringing(self) -> Image.Image:
        img  = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        col  = CYAN if int(time.time() * 4) % 2 == 0 else AMBER
        draw.ellipse([10, 10, W-10, H-10], outline=col, width=10)
        _text_center(draw, CY-50, "\u23f0", F.clock, col)   # emoji reloj
        _text_center(draw, CY+10, "ALARMA", F.clock, WHITE)
        return img
