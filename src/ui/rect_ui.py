"""
rect_ui.py — Pantalla rectangular ST7789 284×76.

Estilo Mid-Century Retro-Futurista.
Modos:
  - REPOSO:   Pronóstico 5 días con iconos PNG + primitivas.
  - MENÚ:     Lista vertical con ítem activo en Ámbar.
  - ALARMA:   Edición HH|MM con subrayado Ámbar.
  - BRILLO:   Barra de progreso Ámbar.
  - WIFI SCAN: Lista de redes con barras de señal.
  - WIFI PASS: Teclado T9 con encoder.
  - SONANDO:  Texto ALARMA parpadeando.
"""
from __future__ import annotations

import math
import time
from typing import Optional

from PIL import Image, ImageDraw

from .theme import (
    F, AMBER, PHOSPHOR, BG, WHITE, DIM_WHITE,
    DARK_CARD, ARC_BASE, COLD_BLUE, MENU_TXT,
    ICONS, condition_to_icon_file,
)

W, H = 284, 76
PAD  = 4      # padding general
GAP  = 3      # espacio entre tarjetas de forecast

DAYS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def _text_center_x(draw: ImageDraw.ImageDraw, y: int, text: str, font, fill,
                   x0: int = 0, x1: int = W) -> None:
    """Dibuja texto centrado horizontalmente entre x0 y x1."""
    bb = draw.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    x = x0 + (x1 - x0 - tw) // 2
    draw.text((x, y), text, font=font, fill=fill)


class RectUIScreen:
    """Renderer para la pantalla rectangular ST7789 284×76."""

    ICON_SIZE = 28   # píxeles de lado para iconos en tarjetas

    def __init__(self) -> None:
        # Pre-cargar iconos a tamaño de tarjeta
        _all_icons = [
            "storm.png", "snow.png", "rain.png", "wind.png",
            "fog.png", "partly.png", "cloud.png", "sun.png",
        ]
        for fname in _all_icons:
            ICONS.composite_on_black(fname, self.ICON_SIZE)   # warm-up cache

        # Frames de parpadeo para ALARM_RINGING
        self._blink_frames = [
            self._make_ringing_frame(AMBER),
            self._make_ringing_frame(PHOSPHOR),
        ]
        self._blink_idx = 0
        self._last_blink = 0.0

    # ─────────────────────────────────────────────────────────────────────────
    # MODO REPOSO — Pronóstico 5 días
    # ─────────────────────────────────────────────────────────────────────────

    def render_forecast(self, forecast_data: list) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        days = forecast_data[:5]
        n = max(1, len(days))
        total_gap = GAP * (n - 1)
        card_w = (W - PAD * 2 - total_gap) // n
        card_h = H - PAD * 2

        for i, day in enumerate(days):
            x1 = PAD + i * (card_w + GAP)
            x2 = x1 + card_w
            y1 = PAD
            y2 = y1 + card_h

            # Fondo de tarjeta
            draw.rounded_rectangle([x1, y1, x2, y2], radius=6, fill=DARK_CARD)

            # Día de la semana
            wd = day.get("weekday", i) % 7
            day_str = DAYS_ES[wd]
            _text_center_x(draw, y1 + 2, day_str, F.card_day, WHITE, x1, x2)

            # Icono meteorológico (PNG compuesto)
            desc  = day.get("description", day.get("condition", ""))
            fname = condition_to_icon_file(desc)
            icon  = ICONS.composite_on_black(fname, self.ICON_SIZE)
            icon_x = x1 + (card_w - self.ICON_SIZE) // 2
            icon_y = y1 + 14
            img.paste(icon, (icon_x, icon_y))

            # Temperaturas
            tmax = day.get("temp_max")
            tmin = day.get("temp_min")
            temp_y = y2 - 22
            if tmax is not None:
                max_str = f"\u2191{tmax:.0f}\u00b0"
                _text_center_x(draw, temp_y, max_str, F.card_temp, AMBER, x1, x2)
            if tmin is not None:
                min_str = f"\u2193{tmin:.0f}\u00b0"
                _text_center_x(draw, temp_y + 12, min_str, F.card_temp, COLD_BLUE, x1, x2)

        return img

    # ─────────────────────────────────────────────────────────────────────────
    # MODO MENÚ
    # ─────────────────────────────────────────────────────────────────────────

    def render_menu(self, items: list, index: int) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        n = len(items)
        item_h = H // n
        for i, (key, label) in enumerate(items):
            y1 = i * item_h
            y2 = y1 + item_h
            if i == index:
                draw.rounded_rectangle([PAD, y1 + 1, W - PAD, y2 - 1],
                                       radius=5, fill=AMBER)
                _text_center_x(draw, y1 + (item_h - 14) // 2, label,
                                F.menu_act, MENU_TXT)
            else:
                _text_center_x(draw, y1 + (item_h - 13) // 2, label,
                                F.menu_inn, DIM_WHITE)

        return img

    # ─────────────────────────────────────────────────────────────────────────
    # MODO ALARMA — Edición HH:MM
    # ─────────────────────────────────────────────────────────────────────────

    def render_alarm(self, alarm: dict, field: str) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        enabled = alarm.get("enabled", False)
        hour    = int(alarm.get("hour", 7))
        minute  = int(alarm.get("minute", 0))

        # Estado ON/OFF arriba
        status_txt = "ON" if enabled else "OFF"
        status_col = PHOSPHOR if enabled else DIM_WHITE
        _text_center_x(draw, 4, status_txt, F.small, status_col)

        # Bloques HH y MM
        hh_str = f"{hour:02d}"
        mm_str = f"{minute:02d}"
        sep    = ":"

        # Posiciones
        cx = W // 2
        block_y = 20

        bb_h = draw.textbbox((0, 0), hh_str, font=F.alarm_hm)
        bb_m = draw.textbbox((0, 0), mm_str, font=F.alarm_hm)
        bb_s = draw.textbbox((0, 0), sep,    font=F.alarm_hm)

        bw = (bb_h[2] - bb_h[0])
        sw = (bb_s[2] - bb_s[0])
        mw = (bb_m[2] - bb_m[0])
        total = bw + sw + mw + 8

        hh_x = cx - total // 2
        sep_x = hh_x + bw + 4
        mm_x  = sep_x + sw + 4

        hh_col = AMBER if field == "hour"   else DIM_WHITE
        mm_col = AMBER if field == "minute" else DIM_WHITE

        draw.text((hh_x, block_y), hh_str, font=F.alarm_hm, fill=hh_col)
        draw.text((sep_x, block_y), sep,   font=F.alarm_hm, fill=DIM_WHITE)
        draw.text((mm_x, block_y), mm_str, font=F.alarm_hm, fill=mm_col)

        # Subrayado del bloque activo (3px)
        bh = bb_h[3] - bb_h[1]
        underline_y = block_y + bh + 2
        if field == "hour":
            draw.rectangle([hh_x, underline_y, hh_x + bw, underline_y + 3], fill=AMBER)
        elif field == "minute":
            draw.rectangle([mm_x, underline_y, mm_x + mw, underline_y + 3], fill=AMBER)

        return img

    # ─────────────────────────────────────────────────────────────────────────
    # MODO BRILLO
    # ─────────────────────────────────────────────────────────────────────────

    def render_brightness(self, round_val: int, rect_val: int,
                          target: str) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        label = "Brillo redonda" if target == "round" else "Brillo rect"
        value = round_val if target == "round" else rect_val

        _text_center_x(draw, 8, label, F.small, DIM_WHITE)

        # Barra de progreso
        bar_x1, bar_y1 = PAD + 2, 30
        bar_x2, bar_y2 = W - 40, 50
        draw.rounded_rectangle([bar_x1, bar_y1, bar_x2, bar_y2],
                                radius=4, fill=ARC_BASE)
        fill_w = int((bar_x2 - bar_x1) * value / 100)
        if fill_w > 0:
            draw.rounded_rectangle([bar_x1, bar_y1, bar_x1 + fill_w, bar_y2],
                                   radius=4, fill=AMBER)

        # Valor numérico
        val_str = f"{value}%"
        draw.text((bar_x2 + 6, bar_y1 + 2), val_str, font=F.small, fill=WHITE)

        _text_center_x(draw, 58, "Pulsa para cambiar pantalla", F.small, DIM_WHITE)

        return img

    # ─────────────────────────────────────────────────────────────────────────
    # MODO WIFI SCAN
    # ─────────────────────────────────────────────────────────────────────────

    def render_wifi_scan(self, networks: list, index: int,
                         scanning: bool) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        if scanning or not networks:
            msg = "Buscando redes..." if scanning else "Sin redes"
            _text_center_x(draw, H // 2 - 8, msg, F.small, DIM_WHITE)
            return img

        max_visible = 4
        item_h = H // max_visible
        start  = max(0, index - max_visible + 1)

        for row, net in enumerate(networks[start:start + max_visible]):
            i = start + row
            y1 = row * item_h
            active = (i == index)
            col = AMBER if active else DIM_WHITE
            if active:
                draw.rectangle([0, y1, W, y1 + item_h - 1],
                                fill=(40, 32, 0))

            # SSID
            ssid = net.get("ssid", "???")[:22]
            draw.text((PAD + 2, y1 + (item_h - 12) // 2), ssid,
                      font=F.small, fill=col)

            # Barras de señal (4 barras)
            bars = net.get("signal", 0)
            bx = W - PAD - 22
            for b in range(4):
                bh_ = 3 + b * 3
                by_ = y1 + item_h - 4 - bh_
                bc  = AMBER if b < bars else ARC_BASE
                draw.rectangle([bx + b * 6, by_, bx + b * 6 + 4, y1 + item_h - 4],
                                fill=bc)

        return img

    # ─────────────────────────────────────────────────────────────────────────
    # MODO WIFI PASSWORD (T9 con encoder)
    # ─────────────────────────────────────────────────────────────────────────

    def render_wifi_keyboard(self, ssid: str, password: str,
                             groups: list, group: int, char_idx: int,
                             level: int) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # Línea superior: SSID
        draw.text((PAD, 2), f"Red: {ssid[:18]}", font=F.small, fill=DIM_WHITE)

        # Contraseña introducida + cursor parpadeante
        cursor = "|" if int(time.time() * 2) % 2 == 0 else " "
        pass_txt = f"{password}{cursor}"
        draw.text((PAD, 18), pass_txt[:28], font=F.small, fill=WHITE)

        # Separador
        draw.line([(PAD, 32), (W - PAD, 32)], fill=ARC_BASE, width=1)

        # Grupo actual de caracteres
        grp_str = groups[group] if group < len(groups) else ""

        if level == 0:
            # Mostrar grupo completo
            _text_center_x(draw, 38, grp_str, F.menu_act, AMBER)
            hint = "Pulsa para elegir letra"
            _text_center_x(draw, 60, hint, F.small, DIM_WHITE)
        else:
            # Resaltar la letra activa dentro del grupo
            chars = grp_str
            row_txt = ""
            for ci, ch in enumerate(chars):
                row_txt += f"[{ch}]" if ci == char_idx else f" {ch} "
            _text_center_x(draw, 40, row_txt[:30], F.small, WHITE)
            if char_idx < len(chars):
                hl = f"► {chars[char_idx]} ◄"
                _text_center_x(draw, 58, hl, F.menu_act, AMBER)

        return img

    # ─────────────────────────────────────────────────────────────────────────
    # MODO ALARMA SONANDO
    # ─────────────────────────────────────────────────────────────────────────

    def _make_ringing_frame(self, color: tuple) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # Borde perimetral
        draw.rectangle([0, 0, W - 1, H - 1], outline=color, width=3)

        _text_center_x(draw, 8, "ALARMA", F.menu_act, color)

        # Dos opciones
        for x, label in [(W // 4, "Detener"), (3 * W // 4, "Posponer")]:
            bb = draw.textbbox((0, 0), label, font=F.small)
            lw = bb[2] - bb[0]
            draw.text((x - lw // 2, 42), label, font=F.small, fill=color)

        return img

    def render_ringing(self, title: str, option: int) -> Image.Image:
        """
        Devuelve un frame precalculado que alterna entre Ámbar y Fósforo.
        El frame también indica la opción activa (0=Detener, 1=Posponer).
        """
        now = time.time()
        if now - self._last_blink >= 0.5:
            self._blink_idx = 1 - self._blink_idx
            self._last_blink = now

        # Reconstruir con la opción activa indicada
        color = AMBER if self._blink_idx == 0 else PHOSPHOR
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        draw.rectangle([0, 0, W - 1, H - 1], outline=color, width=3)
        _text_center_x(draw, 8, title.upper(), F.menu_act, color)

        labels = ["Detener", "Posponer"]
        for i, (x, label) in enumerate(
                [(W // 4, labels[0]), (3 * W // 4, labels[1])]):
            bb   = draw.textbbox((0, 0), label, font=F.small)
            lw   = bb[2] - bb[0]
            col  = AMBER if i == option else DIM_WHITE
            bx   = x - lw // 2 - 4
            if i == option:
                draw.rounded_rectangle([bx, 40, bx + lw + 8, 58],
                                       radius=4, fill=AMBER)
                draw.text((x - lw // 2, 42), label, font=F.small, fill=(0, 0, 0))
            else:
                draw.text((x - lw // 2, 42), label, font=F.small, fill=DIM_WHITE)

        return img
