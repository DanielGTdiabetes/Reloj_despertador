"""
round_home.py — Pantalla redonda con iconos en el menú.
"""
from __future__ import annotations
import math
import time
from typing import Optional
from PIL import Image, ImageDraw
from .theme import (
    F, CYAN, PURPLE, BG, WHITE, DIM_WHITE, ICONS, condition_to_icon_file
)

W = H = 240
CX = CY = 120
ARC_THICK = 10
ARC_R = 114

def _text_center(draw, y, text, font, fill):
    bb = draw.textbbox((0, 0), text, font=font)
    w = bb[2] - bb[0]
    draw.text(((W - w) // 2, y), text, font=font, fill=fill)

def _draw_icon_primitive(draw, x, y, size, kind, color):
    """Iconos minimalistas dibujados con primitivas."""
    cx, cy = x + size // 2, y + size // 2
    if kind == "alarm":
        draw.chord([x+4, y+4, x+size-4, y+size-4], 180, 0, fill=color)
        draw.rectangle([x+2, y+size-8, x+size-2, y+size-4], fill=color)
        draw.ellipse([cx-3, y+size-4, cx+3, y+size+2], fill=color)
    elif kind == "brightness":
        draw.ellipse([cx-8, cy-8, cx+8, cy+8], outline=color, width=3)
        for a in range(0, 360, 45):
            r = math.radians(a)
            draw.line([cx+math.cos(r)*10, cy+math.sin(r)*10, cx+math.cos(r)*16, cy+math.sin(r)*16], fill=color, width=3)
    elif kind == "wifi":
        for r in [10, 20, 30]:
            draw.arc([cx-r, cy-r+15, cx+r, cy+r+15], 225, 315, fill=color, width=3)
        draw.ellipse([cx-4, cy+20, cx+4, cy+28], fill=color)
    elif kind == "sync":
        draw.arc([cx-15, cy-15, cx+15, cy+15], 0, 270, fill=color, width=4)
        draw.polygon([(cx+15, cy-5), (cx+10, cy+5), (cx+20, cy+5)], fill=color)
    elif kind == "weather":
        draw.ellipse([x+5, cy-5, cx, y+size-10], fill=color)
        draw.ellipse([cx-5, y+5, x+size-5, y+size-10], fill=color)
        draw.rectangle([x+10, cy, x+size-10, y+size-10], fill=color)
    else:
        draw.rectangle([x+10, y+10, x+size-10, y+size-10], outline=color, width=2)

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
        
        # Icono central
        _draw_icon_primitive(draw, CX-30, CY-60, 60, kind, CYAN)
        
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
