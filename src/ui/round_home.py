"""
round_home.py — Versión DEFINITIVA (Idéntica a la captura del usuario).
"""
from __future__ import annotations
import math
import time
import random
from PIL import Image, ImageDraw, ImageFilter
from .theme import (
    F, CYAN, PURPLE, BG, WHITE, DIM_WHITE, ICONS,
    condition_to_icon_file, draw_menu_icon
)
from .weather_icons import draw_weather_icon, draw_moon

W = H = 240
CX = CY = 120
ARC_R = 114
ARC_THICK = 5

# Colores de la captura
AMBER = (255, 140, 50)
SUN_DOT = (255, 200, 60)

def _text_center(draw, y: int, text: str, font, fill) -> None:
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text(((W - (bb[2]-bb[0])) // 2, y), text, font=font, fill=fill)

class RoundHomeScreen:
    def __init__(self) -> None:
        pass

    def _draw_solar_arc(self, draw: ImageDraw.Draw, sun_info: dict):
        period = sun_info.get("period", "day")
        progress = sun_info.get("progress", 0.5)
        
        box = [CX - ARC_R, CY - ARC_R, CX + ARC_R, CY + ARC_R]
        # Fondo del arco
        draw.arc(box, start=-90, end=270, fill=(20, 25, 45), width=ARC_THICK + 2)
        # Lado Púrpura (izquierdo)
        draw.arc(box, start=90, end=270, fill=PURPLE, width=ARC_THICK)
        
        # Lado Cian (progreso solar)
        is_day = 0.0 <= progress <= 1.0
        if is_day:
            end_angle = -90 + int(180 * progress)
            draw.arc(box, start=-90, end=end_angle, fill=CYAN, width=ARC_THICK)
            # Punto Sol
            rad = math.radians(end_angle)
            sx, sy = CX + ARC_R * math.cos(rad), CY + ARC_R * math.sin(rad)
            draw.ellipse([sx-6, sy-6, sx+6, sy+6], fill=SUN_DOT)
        else:
            draw.arc(box, start=-90, end=90, fill=CYAN, width=ARC_THICK)

    def _draw_glow_clock(self, img, time_str, y):
        # Capa de resplandor
        glow = Image.new("RGBA", (W, H), (0,0,0,0))
        gd = ImageDraw.Draw(glow)
        bb = gd.textbbox((0, 0), time_str, font=F.clock)
        tx = (W - (bb[2]-bb[0])) // 2
        
        gd.text((tx, y), time_str, font=F.clock, fill=(255, 255, 255, 130))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=3))
        img.paste(glow, (0, 0), glow)
        
        # Texto principal
        draw = ImageDraw.Draw(img)
        draw.text((tx, y), time_str, font=F.clock, fill=WHITE)

    def _draw_alarm_badge(self, draw, alarm, y):
        if not alarm.get("enabled"): return
        h_str = f"{alarm.get('hour', 7):02d}:{alarm.get('minute', 0):02d}"
        days_map = {0:"L", 1:"M", 2:"X", 3:"J", 4:"V", 5:"S", 6:"D"}
        days_list = alarm.get("days", [0,1,2,3,4])
        days_str = "".join(days_map[d] for d in sorted(days_list))
        if len(days_list) == 5 and all(d < 5 for d in days_list): days_str = "L-V"
        
        full_text = f" {h_str}  {days_str}"
        bb = draw.textbbox((0, 0), full_text, font=F.weather_sub)
        w = bb[2]-bb[0] + 20
        start_x = (W - w) // 2
        
        # Campana
        draw.text((start_x, y-2), "🔔", font=F.weather_sub, fill=AMBER)
        draw.text((start_x + 20, y), f"{h_str}  {days_str}", font=F.weather_sub, fill=AMBER)

    def render(self, now, weather, sun_info, moon, alarm, status) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # 1. Arco
        self._draw_solar_arc(draw, sun_info)

        # 2. Fecha con Punto
        days_es = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"]
        months_es = ["ENE","FEB","MAR","ABR","MAY","JUN","JUL","AGO","SEP","OCT","NOV","DIC"]
        date_str = f"{days_es[now.weekday()]} {now.day} {months_es[now.month-1]}"
        bb = draw.textbbox((0, 0), date_str, font=F.date_top)
        tx = (W - (bb[2]-bb[0])) // 2
        draw.text((tx, 26), date_str, font=F.date_top, fill=CYAN)
        draw.ellipse([tx + (bb[2]-bb[0]) + 8, 34, tx + (bb[2]-bb[0]) + 14, 40], fill=CYAN)

        # 3. Reloj con Glow
        self._draw_glow_clock(img, now.strftime("%H:%M"), 48)

        # 4. Min / Max
        temp_max = weather.get("temp_max") or weather.get("temp", 0) + 2
        temp_min = weather.get("temp_min") or weather.get("temp", 0) - 2
        minmax = f"min {temp_min:.0f}°  max {temp_max:.0f}°"
        
        bb_mm = draw.textbbox((0, 0), minmax, font=F.weather_sub)
        mm_x = (W - (bb_mm[2]-bb_mm[0])) // 2
        # Dibujar partes de colores
        draw.text((mm_x, 100), f"min {temp_min:.0f}°", font=F.weather_sub, fill=CYAN)
        draw.text((mm_x + (bb_mm[2]-bb_mm[0]) - 50, 100), f"max {temp_max:.0f}°", font=F.weather_sub, fill=AMBER)

        # 5. Icono Weather
        desc = (weather.get("description") or "").upper()
        draw_weather_icon(img, desc, CX, 135, size=55)

        # 6. Desc y Temp
        _text_center(draw, 168, desc, F.weather_sub, (160, 160, 170))
        temp = weather.get("temp")
        temp_str = f"{temp:.1f}\u00b0C" if temp is not None else "--.-°C"
        _text_center(draw, 182, temp_str, F.temp_big, CYAN)

        # 7. Alarm Badge
        self._draw_alarm_badge(draw, alarm, 208)

        return img

    def render_night(self, now, moon, alarm, sun_info=None) -> Image.Image:
        # Reutilizamos la lógica premium de noche
        img = Image.new("RGB", (W, H), (5, 8, 20))
        draw = ImageDraw.Draw(img)
        self._draw_solar_arc(draw, sun_info or {"period":"night", "progress":-1})
        self._draw_glow_clock(img, now.strftime("%H:%M"), 48)
        draw_moon(img, CX, CY + 35, r=35, phase_frac=moon.get("phase", 0))
        _text_center(draw, 205, moon.get("phase_name", "").upper(), F.weather_sub, WHITE)
        return img

    def render_focus(self, title, subtitle, kind="", value=None) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_menu_icon(draw, CX-35, CY-75, 70, kind)
        _text_center(draw, CY+5, title.upper(), F.date_top, WHITE)
        if value: _text_center(draw, CY+35, str(value), F.clock, CYAN)
        _text_center(draw, H-45, subtitle, F.weather_sub, DIM_WHITE)
        return img

    def render_alarm_ringing(self) -> Image.Image:
        img = Image.new("RGB", (W, H), (180, 20, 20) if int(time.time()*2)%2==0 else BG)
        draw = ImageDraw.Draw(img)
        _text_center(draw, CY-20, "ALARMA", F.clock, WHITE)
        return img
