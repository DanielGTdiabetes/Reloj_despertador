"""
round_home.py — Versión DEFINITIVA (Proporciones de captura + Estabilidad Pi Zero).
Eliminada redundancia de dibujo para evitar parpadeo en pantalla rectangular.
"""
from __future__ import annotations
import math
import time
from PIL import Image, ImageDraw
from .theme import F, CYAN, PURPLE, BG, WHITE, DIM_WHITE, draw_menu_icon
from .weather_icons import draw_weather_icon, draw_moon

W = H = 240
CX = CY = 120
ARC_R     = 114
ARC_THICK = 5

AMBER    = (255, 180, 60)
SUN_DOT  = (255, 200, 60)

def _text_center(draw, y, text, font, fill):
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text(((W - (bb[2]-bb[0])) // 2, y), text, font=font, fill=fill)

class RoundHomeScreen:
    def __init__(self) -> None:
        pass

    def _draw_solar_arc(self, draw, sun_info):
        progress = sun_info.get("progress", 0.5)
        box = [CX - ARC_R, CY - ARC_R, CX + ARC_R, CY + ARC_R]
        
        # Solo dos arcos (Máxima eficiencia para evitar parpadeo)
        draw.arc(box, start=90, end=270, fill=PURPLE, width=ARC_THICK)
        
        end_angle = -90 + int(180 * max(0, min(1, progress)))
        draw.arc(box, start=-90, end=end_angle, fill=CYAN, width=ARC_THICK)
        
        # Punto sol (Un solo elipse es muy ligero)
        rad = math.radians(end_angle)
        sx, sy = CX + ARC_R * math.cos(rad), CY + ARC_R * math.sin(rad)
        draw.ellipse([sx-5, sy-5, sx+5, sy+5], fill=SUN_DOT)

    def render(self, now, weather, sun_info, moon, alarm, status) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        self._draw_solar_arc(draw, sun_info)

        # 1. Fecha (VIE 1 MAY + Punto) - Proporciones Captura
        d_es = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"]
        m_es = ["ENE","FEB","MAR","ABR","MAY","JUN","JUL","AGO","SEP","OCT","NOV","DIC"]
        date_str = f"{d_es[now.weekday()]} {now.day} {m_es[now.month-1]}"
        bb = draw.textbbox((0, 0), date_str, font=F.date_top)
        tx = (W - (bb[2]-bb[0])) // 2
        draw.text((tx, 22), date_str, font=F.date_top, fill=CYAN)
        draw.ellipse([tx + (bb[2]-bb[0]) + 8, 30, tx + (bb[2]-bb[0]) + 14, 36], fill=CYAN)

        # 2. Hora (Posición Captura)
        _text_center(draw, 42, now.strftime("%H:%M"), F.clock, WHITE)

        # 3. Min/Max
        t_max = weather.get("temp_max") or 24
        t_min = weather.get("temp_min") or 14
        mm_str = f"min {t_min:.0f}°  max {t_max:.0f}°"
        _text_center(draw, 108, mm_str, F.weather_sub, DIM_WHITE)

        # 4. Icono 3D (size=55 para balancear peso/belleza)
        desc = (weather.get("description") or "").upper()
        draw_weather_icon(img, desc, CX, 142, size=55)

        # 5. Desc y Temp
        _text_center(draw, 174, desc[:22], F.weather_sub, (150, 155, 175))
        temp = weather.get("temp")
        _text_center(draw, 188, f"{temp:.1f}\u00b0C" if temp else "--.-°C", F.temp_big, CYAN)

        # 6. Alarma inferior
        if alarm.get("enabled"):
            h_str = f"{alarm.get('hour', 7):02d}:{alarm.get('minute', 0):02d}"
            _text_center(draw, 210, f"🔔  {h_str}", F.weather_sub, AMBER)

        return img

    def render_night(self, now, moon, alarm, sun_info=None) -> Image.Image:
        img = Image.new("RGB", (W, H), (5, 8, 20))
        draw = ImageDraw.Draw(img)
        self._draw_solar_arc(draw, sun_info or {"period":"night", "progress":-1})
        _text_center(draw, 45, now.strftime("%H:%M"), F.clock, WHITE)
        draw_moon(img, CX, CY + 35, r=32, phase_frac=moon.get("phase", 0.5))
        return img

    def render_focus(self, title, subtitle, kind="", value=None) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_menu_icon(draw, CX-30, CY-60, 60, kind)
        _text_center(draw, CY+10, title.upper(), F.date_top, WHITE)
        if value: _text_center(draw, CY+35, str(value), F.clock, CYAN)
        return img

    def render_alarm_ringing(self) -> Image.Image:
        img = Image.new("RGB", (W, H), (150, 0, 0) if int(time.time()*2)%2==0 else BG)
        draw = ImageDraw.Draw(img)
        _text_center(draw, CY-20, "ALARMA", F.clock, WHITE)
        return img
