"""
round_home.py — Pantalla redonda con iconos en el menú.
"""
from __future__ import annotations
import math
import time
from typing import Optional
from PIL import Image, ImageDraw
from .theme import (
    F, CYAN, PURPLE, BG, WHITE, DIM_WHITE, ICONS, 
    condition_to_icon_file, draw_menu_icon
)

W = H = 240
CX = CY = 120
ARC_THICK = 10
ARC_R = 114

def _text_center(draw, y, text, font, fill):
    bb = draw.textbbox((0, 0), text, font=font)
    w = bb[2] - bb[0]
    draw.text(((W - w) // 2, y), text, font=font, fill=fill)


class RoundHomeScreen:
    def __init__(self) -> None:
        pass

    def render(self, now, weather, sun_info, moon, alarm, status) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        box = [CX - ARC_R, CY - ARC_R, CX + ARC_R, CY + ARC_R]
        draw.arc(box, start=-90, end=90, fill=CYAN, width=ARC_THICK)
        draw.arc(box, start=90, end=270, fill=PURPLE, width=ARC_THICK)

        _text_center(draw, 35, f"{now.strftime('%A %d').upper()}", F.date_top, CYAN)
        
        t_str = now.strftime("%H:%M")
        bb = draw.textbbox((0, 0), t_str, font=F.clock)
        draw.text(((W-(bb[2]-bb[0]))//2, 65), t_str, font=F.clock, fill=WHITE)

        desc = (weather.get("description") or "").upper()
        temp = weather.get("temp")
        if desc:
            icon = ICONS.get(condition_to_icon_file(desc), 48)
            icon_y = 138
            img.paste(icon, (CX - 24, icon_y), icon)
            
            label = desc
            temp_str = f"{temp:.1f}\u00b0C" if temp is not None else "--\u00b0C"
            _text_center(draw, icon_y + 44, label, F.weather_sub, WHITE)
            _text_center(draw, icon_y + 58, temp_str, F.temp_big, CYAN)
        return img

    def render_focus(self, title, subtitle, kind="", value=None) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw.ellipse([5, 5, W-5, H-5], outline=PURPLE, width=3)
        
        # Icono central multi-color
        draw_menu_icon(draw, CX-30, CY-60, 60, kind)
        
        _text_center(draw, CY+10, title.upper(), F.date_top, WHITE)
        if value: _text_center(draw, CY+40, value, F.temp_big, CYAN)
        _text_center(draw, H-50, subtitle, F.weather_sub, DIM_WHITE)
        return img

    def render_alarm_ringing(self) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        color = CYAN if int(time.time()*4)%2==0 else PURPLE
        draw.ellipse([10, 10, W-10, H-10], outline=color, width=10)
        _text_center(draw, CY-30, "ALARMA", F.clock, WHITE)
        return img
