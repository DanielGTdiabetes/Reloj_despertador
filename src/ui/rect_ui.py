"""
rect_ui.py — Pantalla rectangular estilo Modern Glassmorphism.
- 4 días de pronóstico (Mañana en adelante).
- Fondos de tarjeta con degradados vibrantes.
- Layout limpio y moderno.
"""
from __future__ import annotations

import time
from PIL import Image, ImageDraw

from .theme import (
    F, CYAN, PURPLE, BG, WHITE, DIM_WHITE,
    DARK_CARD, GRADIENTS, ICONS, condition_to_icon_file,
)

W, H = 284, 76
PAD  = 4
GAP  = 6

DAYS_ES = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"]

def _create_v_gradient(w, h, color1, color2) -> Image.Image:
    """Crea un degradado vertical rápido usando resize."""
    grad = Image.new("RGB", (1, 2))
    grad.putpixel((0, 0), color1)
    grad.putpixel((0, 1), color2)
    return grad.resize((w, h), Image.BILINEAR)

def _text_center_x(draw, y, text, font, fill, x0, x1):
    bb = draw.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    draw.text((x0 + (x1 - x0 - tw) // 2, y), text, font=font, fill=fill)

class RectUIScreen:
    ICON_SIZE = 36

    def __init__(self) -> None:
        self._last_blink = 0.0

    def render_forecast(self, forecast_data: list) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        
        days = forecast_data[1:5] # Mañana + 3 días
        n = 4
        card_w = (W - PAD * 2 - GAP * (n - 1)) // n
        card_h = H - PAD * 2

        for i in range(n):
            day = days[i] if i < len(days) else {}
            x1 = PAD + i * (card_w + GAP)
            
            # 1. Fondo Degradado
            g_idx = i % len(GRADIENTS)
            c1, c2 = GRADIENTS[g_idx]
            card_bg = _create_v_gradient(card_w, card_h, c1, c2)
            
            # Crear máscara para bordes redondeados
            mask = Image.new("L", (card_w, card_h), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, card_w, card_h], radius=8, fill=255)
            
            img.paste(card_bg, (x1, PAD), mask)
            
            # 2. Contenido
            draw = ImageDraw.Draw(img)
            x2 = x1 + card_w
            
            # Día
            wd = day.get("weekday", (time.localtime().tm_wday + i + 1)) % 7
            _text_center_x(draw, PAD + 4, DAYS_ES[wd], F.card_day, WHITE, x1, x2)
            
            # Icono
            desc = day.get("description", "")
            fname = condition_to_icon_file(desc)
            icon = ICONS.get(fname, self.ICON_SIZE)
            img.paste(icon, (x1 + (card_w - self.ICON_SIZE) // 2, PAD + 18), icon)
            
            # Temps
            tmax = day.get("temp_max")
            tmin = day.get("temp_min")
            if tmax is not None and tmin is not None:
                temp_txt = f"\u2191{tmax:.0f}\u00b0 \u2193{tmin:.0f}\u00b0"
                _text_center_x(draw, H - PAD - 16, temp_txt, F.card_temp, WHITE, x1, x2)

        return img

    def render_menu(self, items, index) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        # Estilo simplificado para el menú en este tema
        item_w = W // 3
        for i in range(index - 1, index + 2):
            if i < 0 or i >= len(items): continue
            slot = i - (index - 1)
            x1 = slot * item_w
            is_active = (i == index)
            if is_active:
                draw.rounded_rectangle([x1+5, 5, x1+item_w-5, H-5], radius=10, fill=PURPLE)
                col = WHITE
            else:
                col = CYAN
            _text_center_x(draw, H//2 - 10, items[i][1], F.menu_act, col, x1, x1 + item_w)
        return img

    def render_alarm(self, alarm, field) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        h, m = alarm.get("hour", 7), alarm.get("minute", 0)
        _text_center_x(draw, 10, "CONFIGURAR ALARMA", F.small, CYAN)
        time_str = f"{h:02d}:{m:02d}"
        _text_center_x(draw, 25, time_str, F.clock if hasattr(F, 'clock') else F.card_day, WHITE)
        return img

    def render_brightness(self, r, rect, target) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        _text_center_x(draw, 10, "BRILLO", F.small, CYAN)
        val = r if target == "round" else rect
        draw.rectangle([50, 40, 234, 50], fill=DARK_CARD)
        draw.rectangle([50, 40, 50 + int(184 * val/100), 50], fill=CYAN)
        return img

    def render_wifi_scan(self, nets, index, scanning) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        if scanning: _text_center_x(draw, 30, "BUSCANDO...", F.small, CYAN)
        elif not nets: _text_center_x(draw, 30, "SIN REDES", F.small, CYAN)
        else:
            net = nets[index]
            _text_center_x(draw, 20, "SELECCIONAR WIFI", F.small, CYAN)
            _text_center_x(draw, 40, net.get("ssid", "???"), F.menu_act, WHITE)
        return img

    def render_wifi_keyboard(self, ssid, password, groups, group, char, level) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        _text_center_x(draw, 10, f"PASS: {ssid[:15]}", F.small, CYAN)
        _text_center_x(draw, 30, password + "_", F.menu_act, WHITE)
        return img

    def render_ringing(self, title, option) -> Image.Image:
        img = Image.new("RGB", (W, H), (255, 0, 0) if int(time.time()*4)%2==0 else BG)
        draw = ImageDraw.Draw(img)
        _text_center_x(draw, 25, "¡¡ ALARMA !!", F.menu_act, WHITE)
        return img
