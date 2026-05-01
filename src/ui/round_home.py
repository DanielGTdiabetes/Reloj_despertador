"""
round_home.py — Pantalla redonda GC9A01 240×240.

Estilo Mid-Century Retro-Futurista:
  - Reloj HH:MM en Ámbar (#FFBF00), arialbd.ttf 76pt, centrado.
  - Segundos en 24pt, blanco al 60%.
  - Fecha en 18pt, cuarto inferior.
  - Anillo perimetral: arco base gris + arco progreso Ámbar (segundo a segundo).
  - Icono campana (primitivas) si hay alarma activa, esquina superior derecha.
  - Modo ALARM_RINGING: dos frames precalculados que alternan entre Ámbar y Fósforo.
  - render_focus(): pantalla de estado/menú centrada en la redonda.
"""
from __future__ import annotations

import math
import time
from typing import Optional

from PIL import Image, ImageDraw

from .theme import (
    F, AMBER, PHOSPHOR, BG, WHITE, DIM_WHITE, ARC_BASE
)

W = H = 240
CX = CY = 120
ARC_THICK = 8
ARC_R_OUT = 116   # radio exterior del anillo
ARC_R_IN  = ARC_R_OUT - ARC_THICK


def _text_center(draw: ImageDraw.ImageDraw, y: int, text: str, font, fill) -> None:
    """Dibuja texto centrado horizontalmente en y."""
    bb = draw.textbbox((0, 0), text, font=font)
    w = bb[2] - bb[0]
    draw.text(((W - w) // 2, y), text, font=font, fill=fill)


def _draw_arc_ring(draw: ImageDraw.ImageDraw, progress: float) -> None:
    """
    Dibuja el anillo perimetral.
    progress: 0.0–1.0 (fracción del segundo en el minuto).
    """
    box = [CX - ARC_R_OUT, CY - ARC_R_OUT, CX + ARC_R_OUT, CY + ARC_R_OUT]

    # Base gris completa
    draw.arc(box, start=0, end=360, fill=ARC_BASE, width=ARC_THICK)

    # Arco de progreso (empieza desde las 12, va en sentido horario)
    if progress > 0:
        end_angle = -90 + progress * 360
        draw.arc(box, start=-90, end=end_angle, fill=AMBER, width=ARC_THICK)


def _draw_bell(draw: ImageDraw.ImageDraw, color) -> None:
    """
    Dibuja un icono de campana con primitivas PIL en la esquina sup. derecha.
    Tamaño: ~22×22px en (205, 8).
    """
    ox, oy = 205, 8
    # Cuerpo campana (elipse achatada)
    draw.ellipse([ox, oy + 4, ox + 18, oy + 16], fill=color)
    # Mango superior (arco pequeño)
    draw.arc([ox + 5, oy, ox + 13, oy + 8], start=180, end=0, fill=color, width=2)
    # Badajo (línea + punto)
    draw.line([ox + 9, oy + 16, ox + 9, oy + 20], fill=color, width=2)
    draw.ellipse([ox + 7, oy + 19, ox + 11, oy + 23], fill=color)
    # Base trapezoidal
    draw.polygon([(ox + 2, oy + 15), (ox + 16, oy + 15),
                  (ox + 18, oy + 19), (ox, oy + 19)], fill=color)


class RoundHomeScreen:
    """Renderer para la pantalla redonda GC9A01 240×240."""

    DAYS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    MONTHS_ES = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun",
                 "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

    def __init__(self) -> None:
        # Precalcular los dos frames de parpadeo de alarma
        self._blink_frames = [
            self._make_blink_frame(AMBER),
            self._make_blink_frame(PHOSPHOR),
        ]
        self._blink_idx = 0
        self._last_blink = 0.0

    # ── Frame de alarma sonando ───────────────────────────────────────────────

    def _make_blink_frame(self, arc_color: tuple) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # Anillo completo en el color dado
        box = [CX - ARC_R_OUT, CY - ARC_R_OUT, CX + ARC_R_OUT, CY + ARC_R_OUT]
        draw.arc(box, start=0, end=360, fill=arc_color, width=ARC_THICK + 2)

        # Texto ALARMA
        _text_center(draw, 90, "ALARMA", F.focus_ttl, arc_color)
        _text_center(draw, 130, "! ! !", F.seconds, arc_color)

        return img

    def _ringing_frame(self) -> Image.Image:
        now = time.time()
        if now - self._last_blink >= 0.5:
            self._blink_idx = 1 - self._blink_idx
            self._last_blink = now
        return self._blink_frames[self._blink_idx]

    # ── Render principal ──────────────────────────────────────────────────────

    def render(self, now, weather: dict, sun_info: dict,
               moon: dict, alarm: dict, status: str) -> Image.Image:

        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # Anillo de segundos
        progress = now.second / 60.0
        _draw_arc_ring(draw, progress)

        # HH:MM
        time_str = now.strftime("%H:%M")
        bb = draw.textbbox((0, 0), time_str, font=F.clock)
        tw = bb[2] - bb[0]
        th = bb[3] - bb[1]
        clock_y = CY - th // 2 - 14
        draw.text(((W - tw) // 2, clock_y), time_str, font=F.clock, fill=AMBER)

        # Segundos
        sec_str = now.strftime(":%S")
        bb2 = draw.textbbox((0, 0), sec_str, font=F.seconds)
        sec_y = clock_y + th + 2
        draw.text(((W - (bb2[2] - bb2[0])) // 2, sec_y), sec_str,
                  font=F.seconds, fill=DIM_WHITE)

        # Fecha
        wd  = self.DAYS_ES[now.weekday()]
        mon = self.MONTHS_ES[now.month]
        date_str = f"{wd} {now.day} {mon}"
        bb3 = draw.textbbox((0, 0), date_str, font=F.date)
        date_y = H - (bb3[3] - bb3[1]) - 22
        draw.text(((W - (bb3[2] - bb3[0])) // 2, date_y), date_str,
                  font=F.date, fill=DIM_WHITE)

        # Icono campana si alarma activa
        if alarm.get("enabled"):
            _draw_bell(draw, AMBER)

        return img

    def render_alarm_ringing(self) -> Image.Image:
        return self._ringing_frame()

    # ── Render de enfoque (menú, ajuste, etc.) ───────────────────────────────

    def render_focus(self, title: str, subtitle: str,
                     kind: str = "", value: Optional[str] = None) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # Arco completo en ámbar decorativo
        box = [CX - ARC_R_OUT, CY - ARC_R_OUT, CX + ARC_R_OUT, CY + ARC_R_OUT]
        draw.arc(box, start=0, end=360, fill=AMBER, width=3)

        # Subtítulo arriba
        _text_center(draw, 60, subtitle, F.focus_sub, DIM_WHITE)

        # Título
        _text_center(draw, 90, title, F.focus_ttl, AMBER)

        # Valor (si lo hay)
        if value is not None:
            _text_center(draw, 138, value, F.focus_val, WHITE)

        return img
