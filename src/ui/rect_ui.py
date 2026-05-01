"""
rect_ui.py — Pantalla rectangular ST7789 284×76.

Estilo Mid-Century Retro-Futurista MEJORADO.
- Pronóstico con iconos GRANDES (42px).
- Menú GRÁFICO con iconos dibujados con primitivas.
- WiFi Scan con lista detallada.
"""
from __future__ import annotations

import math
import time
from typing import Optional

from PIL import Image, ImageDraw

from .theme import (
    F, AMBER, PHOSPHOR, BG, WHITE, DIM_WHITE,
    DARK_CARD, ARC_BASE, COLD_BLUE, MENU_HL, MENU_TXT,
    ICONS, condition_to_icon_file,
)

W, H = 284, 76
PAD  = 4
GAP  = 4

DAYS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def _text_center_x(draw: ImageDraw.ImageDraw, y: int, text: str, font, fill,
                   x0: int = 0, x1: int = W) -> None:
    bb = draw.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    x = x0 + (x1 - x0 - tw) // 2
    draw.text((x, y), text, font=font, fill=fill)


def _draw_menu_icon(draw: ImageDraw.ImageDraw, x, y, size, kind, color):
    """Dibuja iconos de menú usando primitivas PIL."""
    cx, cy = x + size // 2, y + size // 2
    if kind == "alarm":
        # Campana simplificada
        draw.chord([x + 4, y + 4, x + size - 4, y + size], 180, 0, fill=color)
        draw.rectangle([x + 2, y + size - 6, x + size - 2, y + size - 2], fill=color)
        draw.ellipse([cx - 2, y + size - 3, cx + 2, y + size + 1], fill=color)
    elif kind == "brightness":
        # Sol
        draw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], outline=color, width=2)
        for a in range(0, 360, 45):
            rad = math.radians(a)
            x1, y1 = cx + math.cos(rad) * 8, cy + math.sin(rad) * 8
            x2, y2 = cx + math.cos(rad) * 12, cy + math.sin(rad) * 12
            draw.line([x1, y1, x2, y2], fill=color, width=2)
    elif kind == "wifi":
        # Ondas WiFi
        for r in [6, 12, 18]:
            draw.arc([cx - r, cy - r + 8, cx + r, cy + r + 8], 210, 330, fill=color, width=2)
        draw.ellipse([cx - 2, cy + 10, cx + 2, cy + 14], fill=color)
    elif kind == "sync":
        # Flechas circulares
        draw.arc([cx - 10, cy - 10, cx + 10, cy + 10], 30, 150, fill=color, width=2)
        draw.arc([cx - 10, cy - 10, cx + 10, cy + 10], 210, 330, fill=color, width=2)
        draw.polygon([(cx + 8, cy + 2), (cx + 12, cy + 6), (cx + 4, cy + 6)], fill=color)
        draw.polygon([(cx - 8, cy - 2), (cx - 12, cy - 6), (cx - 4, cy - 6)], fill=color)
    elif kind == "weather":
        # Nube simplificada
        draw.ellipse([x + 4, cy, cx, y + size - 4], fill=color)
        draw.ellipse([cx - 4, y + 4, x + size - 4, y + size - 4], fill=color)
        draw.rectangle([x + 8, cy + 2, x + size - 8, y + size - 4], fill=color)
    else:
        draw.rectangle([x + 4, y + 4, x + size - 4, y + size - 4], outline=color)


class RectUIScreen:
    """Renderer para la pantalla rectangular ST7789 284×76."""

    ICON_SIZE = 48   # ¡Iconos gigantes!

    def __init__(self) -> None:
        pass

    # ─────────────────────────────────────────────────────────────────────────
    # MODO REPOSO — Pronóstico 4 días (Mañana en adelante)
    # ─────────────────────────────────────────────────────────────────────────

    def render_forecast(self, forecast_data: list) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # Saltamos el primer día (hoy) y cogemos los 4 siguientes
        days = forecast_data[1:5]
        n = 4
        card_w = (W - PAD * 2 - GAP * (n - 1)) // n
        card_h = H - PAD * 2

        for i in range(n):
            day = days[i] if i < len(days) else {}
            x1 = PAD + i * (card_w + GAP)
            x2 = x1 + card_w
            y1 = PAD
            y2 = y1 + card_h

            draw.rounded_rectangle([x1, y1, x2, y2], radius=6, fill=DARK_CARD)

            # Día (Abreviatura)
            wd = day.get("weekday", (time.localtime().tm_wday + i + 1)) % 7
            _text_center_x(draw, y1 + 3, DAYS_ES[wd], F.card_day, WHITE, x1, x2)

            # Icono meteorológico grande
            desc = day.get("description", "")
            fname = condition_to_icon_file(desc)
            icon = ICONS.composite_on_black(fname, self.ICON_SIZE)
            img.paste(icon, (x1 + (card_w - self.ICON_SIZE) // 2, y1 + 14))

            # Temp Máx (en Ámbar)
            tmax = day.get("temp_max")
            if tmax is not None:
                txt = f"{tmax:.0f}\u00b0"
                _text_center_x(draw, y2 - 14, txt, F.card_temp, AMBER, x1, x2)

        return img

    # ─────────────────────────────────────────────────────────────────────────
    # MODO MENÚ — GRÁFICO
    # ─────────────────────────────────────────────────────────────────────────

    def render_menu(self, items: list, index: int) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # Mostrar 3 items a la vez (el anterior, el actual y el siguiente)
        item_w = W // 3
        for i in range(index - 1, index + 2):
            if i < 0 or i >= len(items):
                continue
            
            slot = i - (index - 1) # 0, 1, 2
            x1 = slot * item_w
            x2 = x1 + item_w
            
            kind, label = items[i]
            is_active = (i == index)
            
            if is_active:
                draw.rectangle([x1 + 4, 4, x2 - 4, H - 4], fill=MENU_HL)
                icon_col, txt_col = MENU_TXT, MENU_TXT
            else:
                icon_col, txt_col = AMBER, DIM_WHITE
            
            # Icono
            _draw_menu_icon(draw, x1 + (item_w - 32) // 2, 10, 32, kind, icon_col)
            # Etiqueta
            _text_center_x(draw, 50, label, F.menu_inn if not is_active else F.menu_act, txt_col, x1, x2)

        return img

    # ─────────────────────────────────────────────────────────────────────────
    # MODO ALARMA — Edición HH:MM
    # ─────────────────────────────────────────────────────────────────────────

    def render_alarm(self, alarm: dict, field: str) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        enabled = alarm.get("enabled", False)
        hour, minute = alarm.get("hour", 7), alarm.get("minute", 0)

        # Indicador visual de estado
        draw.rectangle([10, 10, 60, 66], fill=DARK_CARD)
        _text_center_x(draw, 20, "ALR", F.small, WHITE, 10, 60)
        _text_center_x(draw, 40, "ON" if enabled else "OFF", F.menu_act, PHOSPHOR if enabled else DIM_WHITE, 10, 60)

        # Reloj grande
        time_str = f"{hour:02d}:{minute:02d}"
        hh_str, mm_str = f"{hour:02d}", f"{minute:02d}"
        
        x_base = 80
        draw.text((x_base, 15), hh_str, font=F.alarm_hm, fill=AMBER if field == "hour" else WHITE)
        draw.text((x_base + 50, 15), ":", font=F.alarm_hm, fill=WHITE)
        draw.text((x_base + 70, 15), mm_str, font=F.alarm_hm, fill=AMBER if field == "minute" else WHITE)

        # Subrayado
        if field == "hour":
            draw.rectangle([x_base, 60, x_base + 45, 64], fill=PHOSPHOR)
        elif field == "minute":
            draw.rectangle([x_base + 70, 60, x_base + 115, 64], fill=PHOSPHOR)

        return img

    # ─────────────────────────────────────────────────────────────────────────
    # MODO BRILLO
    # ─────────────────────────────────────────────────────────────────────────

    def render_brightness(self, round_val: int, rect_val: int, target: str) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        _text_center_x(draw, 5, "AJUSTE DE BRILLO", F.small, DIM_WHITE)
        
        for i, (label, val, is_target) in enumerate([
            ("REDONDA", round_val, target == "round"),
            ("RECT", rect_val, target == "rect")
        ]):
            y = 25 + i * 25
            col = PHOSPHOR if is_target else DIM_WHITE
            draw.text((10, y), label, font=F.menu_inn, fill=col)
            
            # Barra
            bx1, bx2 = 80, 240
            draw.rectangle([bx1, y + 2, bx2, y + 12], fill=DARK_CARD)
            fill_w = int((bx2 - bx1) * val / 100)
            if fill_w > 0:
                draw.rectangle([bx1, y + 2, bx1 + fill_w, y + 12], fill=col)
            
            draw.text((bx2 + 10, y), f"{val}%", font=F.small, fill=WHITE)

        return img

    # ─────────────────────────────────────────────────────────────────────────
    # MODO WIFI SCAN — MEJORADO
    # ─────────────────────────────────────────────────────────────────────────

    def render_wifi_scan(self, networks: list, index: int, scanning: bool) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        if scanning:
            _text_center_x(draw, H // 2 - 10, "ESCANEANDO REDES...", F.menu_act, PHOSPHOR)
            return img
        
        if not networks:
            _text_center_x(draw, H // 2 - 10, "NO SE ENCONTRARON REDES", F.menu_act, AMBER)
            return img

        # Lista de redes (3 visibles)
        item_h = 24
        start = max(0, index - 1)
        for i in range(start, start + 3):
            if i >= len(networks): break
            row = i - start
            y = row * item_h
            net = networks[i]
            is_active = (i == index)
            
            if is_active:
                draw.rectangle([0, y, W, y + item_h - 1], fill=(0, 40, 0))
                draw.rectangle([0, y, 4, y + item_h - 1], fill=PHOSPHOR)
            
            ssid = net.get("ssid", "???")[:25]
            draw.text((10, y + 4), ssid, font=F.menu_inn, fill=WHITE if is_active else DIM_WHITE)
            
            # Señal
            bars = net.get("signal", 0)
            for b in range(4):
                draw.rectangle([W - 40 + b * 6, y + 18 - b * 4, W - 40 + b * 6 + 4, y + 18], 
                               fill=PHOSPHOR if b < bars else DARK_CARD)

        return img

    # ─────────────────────────────────────────────────────────────────────────
    # MODO WIFI PASSWORD
    # ─────────────────────────────────────────────────────────────────────────

    def render_wifi_keyboard(self, ssid, password, groups, group, char, level) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        draw.text((10, 5), f"WIFI: {ssid[:20]}", font=F.small, fill=PHOSPHOR)
        
        # Caja de entrada
        draw.rectangle([10, 20, W - 10, 40], outline=WHITE)
        cursor = "_" if int(time.time() * 2) % 2 == 0 else " "
        draw.text((15, 24), f"{password}{cursor}", font=F.menu_inn, fill=WHITE)

        # Teclado T9 inferior
        item_w = W // 5
        for i in range(group - 2, group + 3):
            g_idx = i % len(groups)
            slot = i - (group - 2)
            x = slot * item_w
            is_active = (g_idx == group)
            
            txt = groups[g_idx]
            if is_active and level == 1:
                # Mostrar letras expandidas
                txt = f"<{txt[char]}>"
            
            _text_center_x(draw, 50, txt, F.menu_act if is_active else F.small, 
                          PHOSPHOR if is_active else DIM_WHITE, x, x + item_w)

        return img

    # ─────────────────────────────────────────────────────────────────────────
    # MODO SONANDO
    # ─────────────────────────────────────────────────────────────────────────

    def render_ringing(self, title, option) -> Image.Image:
        now = time.time()
        color = PHOSPHOR if int(now * 4) % 2 == 0 else AMBER
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        draw.rectangle([0, 0, W - 1, H - 1], outline=color, width=4)
        _text_center_x(draw, 10, "¡ ALARMA !", F.clock if hasattr(F, 'clock') else F.alarm_hm, color)
        
        # Opciones
        for i, (label, x) in enumerate([("DETENER", W // 4), ("POSPONER", 3 * W // 4)]):
            is_sel = (i == option)
            if is_sel:
                draw.rectangle([x - 50, 45, x + 50, 68], fill=color)
                draw.text((x - 35, 50), label, font=F.menu_act, fill=BG)
            else:
                draw.text((x - 35, 50), label, font=F.menu_act, fill=WHITE)

        return img
