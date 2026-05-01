"""
round_home.py — Versión EQUILIBRADA (Sin solapamientos).
Reloj ajustado y badge de alarma siempre visible.
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
        draw.arc(box, start=-90, end=270, fill=(20, 25, 45), width=ARC_THICK)
        draw.arc(box, start=90, end=270, fill=PURPLE, width=ARC_THICK)
        end_angle = -90 + int(180 * max(0, min(1, progress)))
        draw.arc(box, start=-90, end=end_angle, fill=CYAN, width=ARC_THICK)
        rad = math.radians(end_angle)
        sx, sy = CX + ARC_R * math.cos(rad), CY + ARC_R * math.sin(rad)
        draw.ellipse([sx-5, sy-5, sx+5, sy+5], fill=(255, 200, 60))

    def render(self, now, weather, sun_info, moon, alarm, status) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        self._draw_solar_arc(draw, sun_info)

        # 1. Fecha (Más arriba)
        d_es = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"]
        m_es = ["ENE","FEB","MAR","ABR","MAY","JUN","JUL","AGO","SEP","OCT","NOV","DIC"]
        date_str = f"{d_es[now.weekday()]} {now.day} {m_es[now.month-1]}"
        bb_d = draw.textbbox((0, 0), date_str, font=F.date_top)
        tx_d = (W - (bb_d[2]-bb_d[0])) // 2
        draw.text((tx_d, 22), date_str, font=F.date_top, fill=CYAN)
        draw.ellipse([tx_d + (bb_d[2]-bb_d[0]) + 10, 28, tx_d + (bb_d[2]-bb_d[0]) + 16, 34], fill=CYAN)

        # 2. Reloj (Ajustado)
        _text_center(draw, 40, now.strftime("%H:%M"), F.clock, WHITE)

        # 3. Min / Max (Bajado para que no lo pise el reloj)
        t_max = weather.get("temp_max") or 24
        t_min = weather.get("temp_min") or 14
        min_txt, max_txt = f"min {t_min:.0f}°", f"max {t_max:.0f}°"
        bb_min = draw.textbbox((0, 0), min_txt, font=F.weather_sub)
        bb_max = draw.textbbox((0, 0), max_txt, font=F.weather_sub)
        total_mm = (bb_min[2]-bb_min[0]) + (bb_max[2]-bb_max[0]) + 20
        start_mm = (W - total_mm) // 2
        draw.text((start_mm, 108), min_txt, font=F.weather_sub, fill=CYAN)
        draw.text((start_mm + (bb_min[2]-bb_min[0]) + 20, 108), max_txt, font=F.weather_sub, fill=AMBER)

        # 4. Icono
        desc = (weather.get("description") or "").upper()
        draw_weather_icon(img, desc, CX, 140, size=55)

        # 5. Desc y Temp
        _text_center(draw, 172, desc[:22], F.small, DIM_WHITE)
        temp = weather.get("temp")
        _text_center(draw, 186, f"{temp:.1f}\u00b0C" if temp else "--.-°C", F.temp_big, CYAN)

        # 6. Alarma (Siempre abajo)
        if alarm.get("enabled"):
            h_str = f"{alarm.get('hour', 7):02d}:{alarm.get('minute', 0):02d}"
            days = alarm.get("days", [0,1,2,3,4])
            d_str = "L-V" if days == [0,1,2,3,4] else "S-D" if days == [5,6] else "..."
            _text_center(draw, 212, f"🔔  {h_str}  {d_str}", F.weather_sub, AMBER)

        return img

    def render_night(self, now, moon, alarm, sun_info=None) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
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
