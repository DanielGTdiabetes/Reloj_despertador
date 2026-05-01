"""
round_home.py — Versión Ultra-Ligera (Estilo Captura, Máxima Fluidez).
"""
from __future__ import annotations
import math
import time
from PIL import Image, ImageDraw
from .theme import F, CYAN, PURPLE, BG, WHITE, DIM_WHITE, draw_menu_icon
from .weather_icons import draw_weather_icon, draw_moon

W = H = 240
CX = CY = 120
ARC_R = 114
ARC_THICK = 4

def _text_center(draw, y: int, text: str, font, fill) -> None:
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text(((W - (bb[2]-bb[0])) // 2, y), text, font=font, fill=fill)

class RoundHomeScreen:
    def __init__(self) -> None:
        pass

    def render(self, now, weather, sun_info, moon, alarm, status) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # 1. Arco Solar Simplificado (Menos comandos SPI)
        progress = sun_info.get("progress", 0.5)
        box = [CX - ARC_R, CY - ARC_R, CX + ARC_R, CY + ARC_R]
        draw.arc(box, start=90, end=270, fill=PURPLE, width=ARC_THICK)
        end_angle = -90 + int(180 * max(0, min(1, progress)))
        draw.arc(box, start=-90, end=end_angle, fill=CYAN, width=ARC_THICK)

        # 2. Fecha (Layout captura)
        days_es = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"]
        date_str = f"{days_es[now.weekday()]} {now.day:02d}"
        _text_center(draw, 30, date_str, F.date_top, CYAN)

        # 3. Reloj Central
        time_str = now.strftime("%H:%M")
        _text_center(draw, 55, time_str, F.clock, WHITE)

        # 4. Min / Max
        temp_max = weather.get("temp_max") or 25
        temp_min = weather.get("temp_min") or 15
        _text_center(draw, 110, f"{temp_min:.0f}\u00b0  {temp_max:.0f}\u00b0", F.weather_sub, DIM_WHITE)

        # 5. Icono Weather (Ligero)
        desc = (weather.get("description") or "").upper()
        draw_weather_icon(img, desc, CX, 145, size=45)

        # 6. Temp actual
        temp = weather.get("temp")
        temp_str = f"{temp:.1f}\u00b0C" if temp is not None else "--.-°C"
        _text_center(draw, 185, temp_str, F.temp_big, CYAN)

        return img

    def render_night(self, now, moon, alarm, sun_info=None) -> Image.Image:
        img = Image.new("RGB", (W, H), (5, 5, 15))
        draw = ImageDraw.Draw(img)
        _text_center(draw, 60, now.strftime("%H:%M"), F.clock, WHITE)
        draw_moon(img, CX, CY + 40, r=30, phase_frac=moon.get("phase", 0))
        return img

    def render_focus(self, title, subtitle, kind="", value=None) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_menu_icon(draw, CX-30, CY-70, 60, kind)
        _text_center(draw, CY+10, title.upper(), F.date_top, WHITE)
        if value: _text_center(draw, CY+40, str(value), F.clock, CYAN)
        return img

    def render_alarm_ringing(self) -> Image.Image:
        img = Image.new("RGB", (W, H), (150, 0, 0) if int(time.time()*2)%2==0 else BG)
        draw = ImageDraw.Draw(img)
        _text_center(draw, CY-20, "ALARMA", F.clock, WHITE)
        return img
