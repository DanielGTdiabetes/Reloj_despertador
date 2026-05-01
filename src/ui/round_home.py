"""
round_home.py — Versión DEFINITIVA PIXEL-PERFECT.
Basada en la comparación de fotos. Máximo realismo y estabilidad.
"""
from __future__ import annotations
import math
import time
from PIL import Image, ImageDraw
from .theme import F, CYAN, PURPLE, BG, WHITE, DIM_WHITE, AMBER, ICONS, draw_menu_icon
from .weather_icons import draw_weather_icon, draw_moon

W = H = 240
CX = CY = 120
ARC_R = 114
ARC_THICK = 5

def _text_center(draw, y, text, font, fill):
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text(((W - (bb[2]-bb[0])) // 2, y), text, font=font, fill=fill)

class RoundHomeScreen:
    def _draw_solar_arc(self, draw, sun_info):
        progress = sun_info.get("progress", 0.5)
        box = [CX-ARC_R, CY-ARC_R, CX+ARC_R, CY+ARC_R]
        # Fondo sutil
        draw.arc(box, start=-90, end=270, fill=(20, 25, 45), width=ARC_THICK)
        # Parte Púrpura (izquierda)
        draw.arc(box, start=90, end=270, fill=PURPLE, width=ARC_THICK)
        # Parte Cian (progreso)
        end_angle = -90 + int(180 * max(0, min(1, progress)))
        draw.arc(box, start=-90, end=end_angle, fill=CYAN, width=ARC_THICK)
        # Punto Sol
        rad = math.radians(end_angle)
        sx, sy = CX + ARC_R * math.cos(rad), CY + ARC_R * math.sin(rad)
        draw.ellipse([sx-6, sy-6, sx+6, sy+6], fill=(255, 200, 60))

    def render(self, now, weather, sun_info, moon, alarm, status) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        self._draw_solar_arc(draw, sun_info)

        # 1. Fecha (VIE 1 MAY + Punto)
        d_es = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"]
        m_es = ["ENE","FEB","MAR","ABR","MAY","JUN","JUL","AGO","SEP","OCT","NOV","DIC"]
        date_str = f"{d_es[now.weekday()]} {now.day} {m_es[now.month-1]}"
        bb_d = draw.textbbox((0, 0), date_str, font=F.date_top)
        tw_d = bb_d[2]-bb_d[0]
        tx_d = (W - tw_d) // 2
        draw.text((tx_d, 24), date_str, font=F.date_top, fill=CYAN)
        draw.ellipse([tx_d + tw_d + 10, 32, tx_d + tw_d + 16, 38], fill=CYAN)

        # 2. Reloj Gigante (Proporción exacta)
        _text_center(draw, 44, now.strftime("%H:%M"), F.clock, WHITE)

        # 3. Min / Max (Colores Cian y Ámbar)
        t_max = weather.get("temp_max") or 24
        t_min = weather.get("temp_min") or 14
        min_txt = f"min {t_min:.0f}°"
        max_txt = f"max {t_max:.0f}°"
        
        bb_min = draw.textbbox((0, 0), min_txt, font=F.weather_sub)
        bb_max = draw.textbbox((0, 0), max_txt, font=F.weather_sub)
        gap = 20
        total_mm = (bb_min[2]-bb_min[0]) + (bb_max[2]-bb_max[0]) + gap
        start_mm = (W - total_mm) // 2
        
        draw.text((start_mm, 114), min_txt, font=F.weather_sub, fill=CYAN)
        draw.text((start_mm + (bb_min[2]-bb_min[0]) + gap, 114), max_txt, font=F.weather_sub, fill=AMBER)

        # 4. Icono 3D
        desc = (weather.get("description") or "").upper()
        draw_weather_icon(img, desc, CX, 146, size=62)

        # 5. Descripción y Temperatura actual
        _text_center(draw, 178, desc[:22], F.small, DIM_WHITE)
        temp = weather.get("temp")
        _text_center(draw, 192, f"{temp:.1f}\u00b0C" if temp else "--.-°C", F.temp_big, CYAN)

        # 6. Alarma inferior (Con icono de campana naranja)
        if alarm.get("enabled"):
            h_str = f"{alarm.get('hour', 7):02d}:{alarm.get('minute', 0):02d}"
            days = alarm.get("days", [0,1,2,3,4])
            d_str = "L-V" if days == [0,1,2,3,4] else "S-D" if days == [5,6] else "..."
            full_a = f"  {h_str}  {d_str}"
            bb_a = draw.textbbox((0, 0), full_a, font=F.weather_sub)
            ax = (W - (bb_a[2]-bb_a[0] + 18)) // 2
            draw.text((ax, 212), "🔔", font=F.weather_sub, fill=AMBER)
            draw.text((ax + 20, 214), full_a, font=F.weather_sub, fill=AMBER)

        return img

    def render_night(self, now, moon, alarm, sun_info=None) -> Image.Image:
        img = Image.new("RGB", (W, H), (5, 10, 25))
        draw = ImageDraw.Draw(img)
        _text_center(draw, 50, now.strftime("%H:%M"), F.clock, WHITE)
        draw_moon(img, CX, CY + 40, r=35, phase_frac=moon.get("phase", 0.5))
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
