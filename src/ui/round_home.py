"""
round_home.py — Versión DEFINITIVA recuperada de deploy2.
Ajustada con el punto decorativo y formato de fecha de la captura.
"""
from __future__ import annotations
import math
import time
import random
from PIL import Image, ImageDraw
from .theme import (
    F, CYAN, PURPLE, BG, WHITE, DIM_WHITE, ICONS,
    condition_to_icon_file, draw_menu_icon
)
from .weather_icons import draw_weather_icon, draw_moon

W = H = 240
CX = CY = 120
ARC_R     = 114
ARC_THICK = 5

AMBER    = (255, 180, 60)
SUN_DOT  = (255, 200, 60)
MOON_TXT = (220, 210, 170)

_ARC_PALETTE = {
    "day":   {"a": CYAN, "b": PURPLE, "dot": SUN_DOT},
    "night": {"a": (80, 80, 160), "b": (40, 40, 100), "dot": (100, 100, 220)},
}

def _text_center(draw, y, text, font, fill):
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text(((W - (bb[2]-bb[0])) // 2, y), text, font=font, fill=fill)

def _draw_solar_arc(draw, sun_info):
    period = sun_info.get("period", "day")
    progress = sun_info.get("progress", 0.5)
    pal = _ARC_PALETTE.get(period, _ARC_PALETTE["day"])
    box = [CX - ARC_R, CY - ARC_R, CX + ARC_R, CY + ARC_R]
    
    # Track base
    draw.arc(box, start=-90, end=270, fill=(15, 20, 35), width=ARC_THICK)
    # Lado fijo
    draw.arc(box, start=90, end=270, fill=pal["b"], width=ARC_THICK)
    
    # Progreso
    is_day = 0.0 <= progress <= 1.0
    if is_day:
        end_angle = -90 + int(180 * progress)
        draw.arc(box, start=-90, end=end_angle, fill=pal["a"], width=ARC_THICK)
        # Punto sol
        rad = math.radians(end_angle)
        sx, sy = CX + ARC_R * math.cos(rad), CY + ARC_R * math.sin(rad)
        draw.ellipse([sx-6, sy-6, sx+6, sy+6], fill=pal["dot"])
    else:
        draw.arc(box, start=-90, end=90, fill=pal["a"], width=ARC_THICK)

def _draw_alarm_badge(draw, alarm, y):
    if not alarm.get("enabled"): return
    h_str = f"{alarm.get('hour', 7):02d}:{alarm.get('minute', 0):02d}"
    days_list = alarm.get("days", [0,1,2,3,4])
    days_map = {0:"L", 1:"M", 2:"X", 3:"J", 4:"V", 5:"S", 6:"D"}
    days_str = "".join(days_map[d] for d in sorted(days_list))
    if days_list == [0,1,2,3,4]: days_str = "L-V"
    
    full_text = f"  {h_str}  {days_str}"
    bb = draw.textbbox((0, 0), full_text, font=F.weather_sub)
    w_total = bb[2]-bb[0] + 16
    start_x = (W - w_total) // 2
    
    draw.text((start_x, y-2), "🔔", font=F.weather_sub, fill=AMBER)
    draw.text((start_x + 18, y), full_text, font=F.weather_sub, fill=AMBER)

def _draw_stars(img):
    draw = ImageDraw.Draw(img)
    rng = random.Random(42)
    for _ in range(40):
        x, y = rng.randint(20, 220), rng.randint(20, 220)
        if (x-CX)**2 + (y-CY)**2 < (ARC_R-8)**2:
            a = rng.randint(50, 180)
            draw.point((x, y), fill=(a, a, a+40))

class RoundHomeScreen:
    def render(self, now, weather, sun_info, moon, alarm, status) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        self._draw_solar_arc(draw, sun_info)

        # 1. Fecha (VIE 1 MAY + Punto) - Proporción deploy2
        d_es = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"]
        m_es = ["ENE","FEB","MAR","ABR","MAY","JUN","JUL","AGO","SEP","OCT","NOV","DIC"]
        date_str = f"{d_es[now.weekday()]} {now.day} {m_es[now.month-1]}"
        bb = draw.textbbox((0, 0), date_str, font=F.date_top)
        tx = (W - (bb[2]-bb[0])) // 2
        draw.text((tx, 22), date_str, font=F.date_top, fill=CYAN)
        draw.ellipse([tx + (bb[2]-bb[0]) + 8, 30, tx + (bb[2]-bb[0]) + 14, 36], fill=CYAN)

        # 2. Hora (Posición deploy2)
        _text_center(draw, 42, now.strftime("%H:%M"), F.clock, WHITE)

        # 3. Min/Max (Bajo la hora)
        t_max = weather.get("temp_max") or 24
        t_min = weather.get("temp_min") or 14
        mm_str = f"min {t_min:.0f}°  max {t_max:.0f}°"
        _text_center(draw, 108, mm_str, F.weather_sub, DIM_WHITE)

        # 4. Icono 3D (Grande, size=60)
        desc = (weather.get("description") or "").upper()
        draw_weather_icon(img, desc, CX, 142, size=60)

        # 5. Desc y Temp
        _text_center(draw, 174, desc[:22], F.weather_sub, (160, 160, 180))
        temp = weather.get("temp")
        _text_center(draw, 188, f"{temp:.1f}\u00b0C" if temp else "--.-°C", F.temp_big, CYAN)

        # 6. Alarma inferior
        _draw_alarm_badge(draw, alarm, 210)
        return img

    def render_night(self, now, moon, alarm, sun_info=None) -> Image.Image:
        img = Image.new("RGB", (W, H), (5, 8, 20))
        draw = ImageDraw.Draw(img)
        _draw_stars(img)
        self._draw_solar_arc(draw, sun_info or {"period":"night", "progress":-1})
        _text_center(draw, 42, now.strftime("%H:%M"), F.clock, WHITE)
        draw_moon(img, CX, CY + 30, r=32, phase_frac=moon.get("phase", 0.5))
        _text_center(draw, 205, moon.get("phase_name", "").upper(), F.weather_sub, WHITE)
        return img

    def render_focus(self, title, subtitle, kind="", value=None) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_menu_icon(draw, CX-30, CY-60, 60, kind)
        _text_center(draw, CY+10, title.upper(), F.date_top, WHITE)
        if value: _text_center(draw, CY+35, str(value), F.clock, CYAN)
        return img

    def render_alarm_ringing(self) -> Image.Image:
        img = Image.new("RGB", (W, H), (180, 20, 20) if int(time.time()*2)%2==0 else BG)
        draw = ImageDraw.Draw(img)
        _text_center(draw, CY-20, "ALARMA", F.clock, WHITE)
        return img
