"""
rect_ui.py — Versión Gráfica Premium + render_location().
CAMBIOS respecto a la versión anterior:
  - render_location(): entrada de código postal con dígitos resaltados
  - render_forecast(): muestra días 1-4 (sin hoy) e iconos de weather_icons
  - render_menu(): compatible con 5 ítems de menú (incluye Ubicacion)

Sin cambios en: render_alarm, render_brightness, render_wifi_scan,
render_wifi_keyboard, render_ringing.
"""
from __future__ import annotations
import time
import math
from PIL import Image, ImageDraw
from .theme import (
    F, CYAN, PURPLE, BG, WHITE, DIM_WHITE,
    DARK_CARD, GRADIENTS, ICONS, condition_to_icon_file,
    draw_menu_icon
)
from .weather_icons import draw_weather_icon

W, H = 284, 76
PAD  = 4
GAP  = 8

# Colores adicionales
AMBER      = (255, 180,  60)
GREEN      = ( 80, 200, 120)
RED_DIM    = (200,  80,  80)

def _create_v_gradient(w, h, color1, color2) -> Image.Image:
    grad = Image.new("RGB", (1, 2))
    grad.putpixel((0, 0), color1)
    grad.putpixel((0, 1), color2)
    return grad.resize((w, h), Image.BILINEAR)

def _text_center_x(draw, y, text, font, fill, x0, x1):
    bb = draw.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    draw.text((x0 + (x1 - x0 - tw) // 2, y), text, font=font, fill=fill)


class RectUIScreen:
    ICON_SIZE = 32   # iconos pronóstico

    def __init__(self) -> None:
        pass

    # ── Pronóstico 4 días (sin hoy) ───────────────────────────────────────────

    def render_forecast(self, forecast_data: list) -> Image.Image:
        img  = Image.new("RGB", (W, H), BG)
        days = forecast_data[1:5]        # saltar el día 0 (hoy)
        n    = 4
        card_w = (W - PAD*2 - GAP*(n-1)) // n
        card_h = H - PAD*2

        GRAD_COLORS = [
            ((100, 80, 200), (40, 30, 100)),    # índigo
            ((60, 140, 220), (20, 60, 120)),     # azul
            ((80, 160, 100), (30, 80, 50)),      # verde
            ((200, 100, 60), (100, 40, 20)),     # naranja
        ]

        for i in range(n):
            day  = days[i] if i < len(days) else {}
            x1   = PAD + i * (card_w + GAP)
            c1, c2 = GRAD_COLORS[i % len(GRAD_COLORS)]

            # Fondo degradado con máscara redondeada
            card_img = _create_v_gradient(card_w, card_h, c1, c2)
            mask     = Image.new("L", (card_w, card_h), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, card_w, card_h], radius=8, fill=255)
            img.paste(card_img, (x1, PAD), mask)

            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle([x1, PAD, x1+card_w, PAD+card_h],
                                   radius=8, outline=(255,255,255,30), width=1)

            # Día de la semana
            wd = day.get("weekday", (time.localtime().tm_wday + i + 1) % 7)
            _text_center_x(draw, PAD+3,
                           ["LUN","MAR","MIE","JUE","VIE","SAB","DOM"][wd],
                           F.card_day, WHITE, x1, x1+card_w)

            # Icono meteorológico PIL de alta calidad
            desc = day.get("description", "")
            icon_cx = x1 + card_w // 2
            icon_cy = PAD + 12 + self.ICON_SIZE // 2
            draw_weather_icon(img, desc, icon_cx, icon_cy, size=self.ICON_SIZE)

            # Temperatura máxima
            tmax = day.get("temp_max")
            if tmax is not None:
                _text_center_x(draw, H-PAD-14,
                               f"{tmax:.0f}\u00b0", F.card_temp, WHITE, x1, x1+card_w)
        return img

    # ── Menú (3 slots visibles) ───────────────────────────────────────────────

    def render_menu(self, items, index) -> Image.Image:
        img  = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        item_w = W // 3
        for i in range(index - 1, index + 2):
            if i < 0 or i >= len(items):
                continue
            slot = i - (index - 1)
            x1, x2 = slot * item_w, (slot+1) * item_w
            is_active = (i == index)

            if is_active:
                grad = _create_v_gradient(item_w-10, H-10, (40, 20, 80), (10, 5, 20))
                mask = Image.new("L", (item_w-10, H-10), 0)
                ImageDraw.Draw(mask).rounded_rectangle([0,0,item_w-10,H-10], radius=12, fill=255)
                img.paste(grad, (x1+5, 5), mask)
                draw.rounded_rectangle([x1+5, 5, x1+item_w-5, H-5], radius=12, outline=CYAN, width=2)
                draw_menu_icon(draw, x1+(item_w-34)//2, 12, 34, items[i][0])
                txt = items[i][1].upper()
                _text_center_x(draw, 53, txt, F.menu_label, (0,0,0), x1, x2)
                _text_center_x(draw, 52, txt, F.menu_label, WHITE, x1, x2)
            else:
                draw_menu_icon(draw, x1+(item_w-24)//2, 22, 24, items[i][0])
        return img

    # ── Código postal — NUEVO ────────────────────────────────────────────────

    def render_location(self, digits: list, active_idx: int,
                        updating: bool = False) -> Image.Image:
        """
        Muestra 5 cajas de dígito para introducir el código postal.
        El dígito activo aparece resaltado en cyan.

        Args:
            digits:     Lista de 5 enteros (0-9).
            active_idx: Índice del dígito actualmente editable (0-4).
            updating:   True si se está realizando el geocoding.
        """
        img  = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # Label superior
        label = "GEOLOCALIZANDO..." if updating else "CÓDIGO POSTAL"
        label_color = CYAN if not updating else (200, 200, 100)
        _text_center_x(draw, 6, label, F.small, label_color, 0, W)

        # 5 cajas de dígito
        box_w    = 28
        box_h    = 38
        total_w  = box_w * 5 + 6 * 4   # 5 cajas + 4 gaps de 6px
        x_start  = (W - total_w) // 2
        y_top    = (H - box_h) // 2 + 4

        for i, digit in enumerate(digits[:5]):
            x = x_start + i * (box_w + 6)
            is_active = (i == active_idx) and not updating
            is_done   = (i < active_idx) or updating

            # Fondo de la caja
            if is_active:
                bg_col = (20, 40, 60)
                border = CYAN
                glow   = True
            elif is_done:
                bg_col = (18, 25, 35)
                border = (50, 70, 90)
                glow   = False
            else:
                bg_col = (12, 18, 28)
                border = (30, 40, 55)
                glow   = False

            draw.rounded_rectangle([x, y_top, x+box_w, y_top+box_h],
                                   radius=5, fill=bg_col, outline=border, width=2)
            if glow:
                # Halo exterior cian
                draw.rounded_rectangle([x-2, y_top-2, x+box_w+2, y_top+box_h+2],
                                       radius=7, outline=(*CYAN[:3], 60), width=1)

            # Dígito
            d_str = str(digit)
            bb    = draw.textbbox((0, 0), d_str, font=F.clock)
            dw    = bb[2] - bb[0]
            dh    = bb[3] - bb[1]
            dx    = x + (box_w - dw) // 2
            dy    = y_top + (box_h - dh) // 2 - 2
            col   = CYAN if is_active else (WHITE if is_done else DIM_WHITE)
            draw.text((dx, dy), d_str, font=F.clock, fill=col)

        # Hint inferior
        if updating:
            hint, hint_col = "Buscando ubicacion...", (180, 180, 80)
        elif active_idx < 4:
            hint, hint_col = f"Digito {active_idx+1}/5 · Gira: cambia · Pulsa: sig.", DIM_WHITE
        else:
            hint, hint_col = "Pulsa para confirmar · Hold: retroceder", CYAN
        _text_center_x(draw, H-14, hint, F.small, hint_col, 0, W)

        return img

    # ── Alarma ────────────────────────────────────────────────────────────────

    def render_alarm(self, alarm, field) -> Image.Image:
        img  = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        h, m = alarm.get("hour", 7), alarm.get("minute", 0)
        draw.rounded_rectangle([20, 8, W-20, H-8], radius=12, fill=DARK_CARD)
        _text_center_x(draw, 12, "HORA ALARMA", F.small, CYAN, 0, W)

        # Estado activo/inactivo
        en = alarm.get("enabled", False)
        en_str = "ACTIVA" if en else "DESACTIVADA"
        en_col = AMBER if en else DIM_WHITE
        _text_center_x(draw, 24, en_str, F.small, en_col if field == "enabled" else DIM_WHITE, 0, W)

        t_str = f"{h:02d} : {m:02d}"
        h_col = CYAN if field == "hour"   else WHITE
        m_col = CYAN if field == "minute" else WHITE

        bb = draw.textbbox((0,0), f"{h:02d}", font=F.clock)
        tw = bb[2] - bb[0]
        cx = W // 2
        draw.text((cx - tw - 8, 36), f"{h:02d}", font=F.clock, fill=h_col)
        draw.text((cx - 6,      36), ":",         font=F.clock, fill=DIM_WHITE)
        draw.text((cx + 8,      36), f"{m:02d}", font=F.clock, fill=m_col)

        if field == "hour":
            draw.rectangle([cx-tw-8, H-10, cx-8, H-8], fill=CYAN)
        elif field == "minute":
            draw.rectangle([cx+8, H-10, cx+8+tw, H-8], fill=CYAN)
        return img

    # ── Brillo ────────────────────────────────────────────────────────────────

    def render_brightness(self, r, rect, target) -> Image.Image:
        img  = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        for i, (label, val, act) in enumerate([
            ("REDONDA", r,    target == "round"),
            ("RECT",    rect, target == "rect"),
        ]):
            y   = 16 + i * 28
            col = CYAN if act else DIM_WHITE
            draw.text((28, y), label, font=F.small, fill=col)
            draw.rectangle([100, y+4, 232, y+10], fill=DARK_CARD)
            draw.rectangle([100, y+4, 100+int(132*val/100), y+10], fill=col)
            draw.text((238, y), f"{val}%", font=F.small, fill=WHITE)
        return img

    # ── WiFi — escaneo ────────────────────────────────────────────────────────

    def render_wifi_scan(self, nets, index, scanning) -> Image.Image:
        img  = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        if scanning:
            _text_center_x(draw, 28, "BUSCANDO REDES...", F.menu_label, CYAN, 0, W)
        elif not nets:
            _text_center_x(draw, 28, "SIN REDES DISPONIBLES", F.menu_label, PURPLE, 0, W)
        else:
            net = nets[index]
            draw.rounded_rectangle([20, 8, W-20, H-8], radius=10, fill=DARK_CARD)
            _text_center_x(draw, 12, f"RED {index+1}/{len(nets)}", F.small, CYAN, 0, W)
            _text_center_x(draw, 32, net.get("ssid", "???")[:22], F.menu_label, WHITE, 0, W)
            s = net.get("signal", 0)
            for b in range(4):
                draw.rectangle([W-58+b*8, H-22-b*4, W-58+b*8+5, H-20],
                               fill=CYAN if b < s else DARK_CARD)
        return img

    # ── WiFi — teclado T9 ────────────────────────────────────────────────────

    def render_wifi_keyboard(self, ssid, password, groups, group, char, level) -> Image.Image:
        img  = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw.text((16, 8),  f"WIFI: {ssid[:18]}", font=F.small, fill=CYAN)
        draw.rectangle([16, 22, W-16, 42], outline=WHITE, width=1)
        cursor = "|" if int(time.time() * 2) % 2 == 0 else ""
        draw.text((20, 25), (password + cursor)[:22], font=F.menu_label, fill=WHITE)
        txt = groups[group]
        if level == 1:
            txt = f" > {txt[char]} < "
        _text_center_x(draw, 50, txt, F.menu_label, PURPLE, 0, W)
        return img

    # ── Alarma sonando ────────────────────────────────────────────────────────

    def render_ringing(self, title, option) -> Image.Image:
        img  = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        col  = CYAN if int(time.time() * 4) % 2 == 0 else AMBER
        draw.rectangle([0, 0, W-1, H-1], outline=col, width=4)
        _text_center_x(draw, 8,  "¡ ALARMA !",            F.menu_label, col,   0, W)
        lbl = "DETENER" if option == 0 else "POSPONER"
        _text_center_x(draw, 32, lbl,                     F.clock,      WHITE, 0, W)
        return img
