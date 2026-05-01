"""
round_home.py — Pantalla redonda estilo Modern Glassmorphism.
Diseño:
  - Top: Día y Fecha (Cian)
  - Center: Reloj gigante (Blanco)
  - Bottom: Icono + Clima + Temp (Blanco)
  - Anillo: Segmentos Cian/Púrpura
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

def _text_center(draw: ImageDraw.ImageDraw, y: int, text: str, font, fill) -> None:
    bb = draw.textbbox((0, 0), text, font=font)
    w = bb[2] - bb[0]
    draw.text(((W - w) // 2, y), text, font=font, fill=fill)

class RoundHomeScreen:
    DAYS_ES = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]

    def __init__(self) -> None:
        self._last_blink = 0.0
        self._blink_idx = 0

    def render(self, now, weather, sun_info, moon, alarm, status) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # 1. Anillo decorativo (Cian y Púrpura)
        box = [CX - ARC_R, CY - ARC_R, CX + ARC_R, CY + ARC_R]
        # Dibujamos dos arcos que se encuentran
        sec_progress = now.second / 60.0
        draw.arc(box, start=-90, end=-90 + 180, fill=CYAN, width=ARC_THICK)
        draw.arc(box, start=90, end=90 + 180, fill=PURPLE, width=ARC_THICK)

        # 2. Fecha (Arriba)
        date_str = f"{self.DAYS_ES[now.weekday()]} {now.day}"
        _text_center(draw, 45, date_str, F.date_top, CYAN)

        # 3. Reloj (Centro)
        time_str = now.strftime("%H:%M")
        bb = draw.textbbox((0, 0), time_str, font=F.clock)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        draw.text(((W - tw) // 2, CY - th // 2), time_str, font=F.clock, fill=WHITE)

        # 4. Clima (Abajo)
        desc = (weather.get("description") or "").upper()
        temp = weather.get("temp")

        fname = condition_to_icon_file(desc) if desc else "partly.png"
        icon = ICONS.get(fname, 32)

        temp_str = f"{temp:.0f}\u00b0C" if temp is not None else "--°C"
        label = desc if desc else "..."

        bb_label = draw.textbbox((0, 0), label, font=F.weather_sub)
        label_w = bb_label[2] - bb_label[0]
        total_w = 40 + label_w
        start_x = (W - total_w) // 2
        img.paste(icon, (start_x, 164), icon)
        draw.text((start_x + 40, 168), label, font=F.weather_sub, fill=WHITE)
        _text_center(draw, 188, temp_str, F.temp_big, CYAN)

        return img

    def render_alarm_ringing(self) -> Image.Image:
        # Parpadeo rápido para la alarma
        now = time.time()
        col = CYAN if int(now * 4) % 2 == 0 else PURPLE
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw.ellipse([10, 10, W-10, H-10], outline=col, width=5)
        _text_center(draw, CY - 20, "ALARMA", F.clock, WHITE)
        return img

    def render_focus(self, title, subtitle, kind="", value=None) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        _text_center(draw, 50, title, F.date_top, CYAN)
        if value:
            _text_center(draw, 100, value, F.clock, WHITE)
        _text_center(draw, 180, subtitle, F.weather_sub, DIM_WHITE)
        return img
