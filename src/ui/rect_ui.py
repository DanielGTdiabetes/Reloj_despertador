"""
rect_ui.py — Versión con Margen de Seguridad Anti-Lluvia (42px).
Evita que el icono pise la temperatura en días de lluvia.
"""
from __future__ import annotations
import time
import math
from PIL import Image, ImageDraw
from .theme import (
    F, CYAN, PURPLE, BG, WHITE, DIM_WHITE, AMBER,
    DARK_CARD, GRADIENTS, ICONS, condition_to_icon_file,
    draw_menu_icon
)
from .weather_icons import draw_weather_icon

W, H = 284, 76
PAD_X = 12 
PAD_Y = 2
GAP   = 6

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
    ICON_SIZE = 42   # Bajamos a 42 para dejar hueco a las gotas de lluvia

    def render_forecast(self, forecast_data: list) -> Image.Image:
        img  = Image.new("RGB", (W, H), BG)
        days = forecast_data[1:5]
        n    = 4
        card_w = (W - PAD_X*2 - GAP*(n-1)) // n
        card_h = H - PAD_Y*2

        for i in range(n):
            day  = days[i] if i < len(days) else {}
            x1   = PAD_X + i * (card_w + GAP)
            
            # Fondo de tarjeta Gris Carbón muy sutil
            card_img = Image.new("RGB", (card_w, card_h), (20, 22, 28))
            mask     = Image.new("L", (card_w, card_h), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, card_w, card_h], radius=8, fill=255)
            img.paste(card_img, (x1, PAD_Y), mask)
            
            draw = ImageDraw.Draw(img)
            # Borde sutil
            draw.rounded_rectangle([x1, PAD_Y, x1+card_w, PAD_Y+card_h],
                                   radius=8, outline=(40, 45, 55), width=1)
            wd = day.get("weekday", (time.localtime().tm_wday + i + 1) % 7)
            _text_center_x(draw, PAD_Y+1, ["LUN","MAR","MIE","JUE","VIE","SAB","DOM"][wd], F.card_day, WHITE, x1, x1+card_w)
            
            # Icono 42px y ligeramente más arriba (y=32 en lugar de 37) para dar aire abajo
            draw_weather_icon(img, day.get("description", ""), x1 + card_w // 2, PAD_Y + 10 + self.ICON_SIZE // 2, size=self.ICON_SIZE)
            
            tmax = day.get("temp_max")
            if tmax is not None:
                _text_center_x(draw, H-PAD_Y-12, f"{tmax:.0f}\u00b0", F.card_temp, WHITE, x1, x1+card_w)
        return img

    def render_menu(self, items, index) -> Image.Image:
        img  = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        item_w = W // 3
        for i in range(index - 1, index + 2):
            if i < 0 or i >= len(items): continue
            slot = i - (index - 1)
            x1, x2 = slot * item_w, (slot+1) * item_w
            if i == index:
                draw.rounded_rectangle([x1+5, 5, x1+item_w-5, H-5], radius=12, outline=CYAN, width=2)
                draw_menu_icon(draw, x1+(item_w-34)//2, 12, 34, items[i][0])
                _text_center_x(draw, 52, items[i][1].upper(), F.menu_label, WHITE, x1, x2)
            else:
                draw_menu_icon(draw, x1+(item_w-24)//2, 22, 24, items[i][0])
        return img

    def render_location(self, digits, active_idx, updating=False) -> Image.Image:
        img = Image.new("RGB", (W, H), BG); draw = ImageDraw.Draw(img)
        _text_center_x(draw, 6, "CÓDIGO POSTAL", F.small, CYAN, 0, W)
        box_w, box_h = 30, 38
        x_start = (W - (box_w*5 + 24)) // 2
        for i, digit in enumerate(digits[:5]):
            x = x_start + i * (box_w + 6)
            is_active = (i == active_idx) and not updating
            draw.rounded_rectangle([x, 22, x+box_w, 60], radius=5, fill=(20,40,60) if is_active else (15,20,30), outline=CYAN if is_active else (50,70,90), width=2)
            _text_center_x(draw, 28, str(digit), F.clock, CYAN if is_active else WHITE, x, x+box_w)
        return img

    def render_alarm(self, alarm, field, editing=False) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        enabled = alarm.get("enabled", False)

        # Tres cajas: [ON/OFF]  [HH] : [MM]
        # Layout centrado en 284px
        B1W, B2W, B3W, COLON_W, GAP1 = 70, 62, 62, 14, 12
        total = B1W + GAP1 + B2W + COLON_W + B3W   # 220px
        ox = (W - total) // 2                        # ~32px margen
        BY1, BY2, BRAD = 7, H - 7, 9                # y1=7, y2=69 → 62px alto

        b1x = ox
        b2x = ox + B1W + GAP1
        cx  = b2x + B2W                              # inicio zona colon
        b3x = cx + COLON_W

        def _box(bx, bw, f_name):
            active = (field == f_name)
            if active and editing:
                fill, outline, lw = (45, 25, 0), AMBER, 2
            elif active:
                fill, outline, lw = DARK_CARD, CYAN, 2
            else:
                fill, outline, lw = (12, 16, 24), (35, 45, 60), 1
            draw.rounded_rectangle([bx, BY1, bx + bw, BY2],
                                   radius=BRAD, fill=fill, outline=outline, width=lw)

        _box(b1x, B1W, "enabled")
        _box(b2x, B2W, "hour")
        _box(b3x, B3W, "minute")

        # ON/OFF
        st_text = "ON" if enabled else "OFF"
        st_col = AMBER if enabled else DIM_WHITE
        if field == "enabled":
            st_col = WHITE
        txt_y1 = BY1 + (BY2 - BY1 - 26) // 2
        _text_center_x(draw, txt_y1, st_text, F.temp_big, st_col, b1x, b1x + B1W)

        # Hora y minutos (40px)
        txt_y2 = BY1 + (BY2 - BY1 - 40) // 2
        h_col  = AMBER if (field == "hour"   and editing) else WHITE
        m_col  = AMBER if (field == "minute" and editing) else WHITE
        _text_center_x(draw, txt_y2, f"{alarm.get('hour', 7):02d}",   F.alarm_rect, h_col, b2x, b2x + B2W)
        _text_center_x(draw, txt_y2, f"{alarm.get('minute', 0):02d}", F.alarm_rect, m_col, b3x, b3x + B3W)

        # Dos puntos entre hora y minutos
        _text_center_x(draw, txt_y2, ":", F.alarm_rect, DIM_WHITE, cx, cx + COLON_W)

        return img

    def render_brightness(self, r, rect, target, editing=False) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        rows = [("REDONDA", r, "round"), ("RECT", rect, "rect")]
        for i, (lbl, val, key) in enumerate(rows):
            selected = (target == key)
            active_edit = selected and editing

            if active_edit:
                row_col = AMBER
                fill_bg = (35, 20, 0)
                bar_col = AMBER
            elif selected:
                row_col = CYAN
                fill_bg = DARK_CARD
                bar_col = CYAN
            else:
                row_col = DIM_WHITE
                fill_bg = (12, 16, 24)
                bar_col = (50, 70, 90)

            ry = 8 + i * 32
            # Fila con fondo de caja
            draw.rounded_rectangle([10, ry, W-10, ry+26], radius=6,
                                   fill=fill_bg, outline=row_col, width=1 if not selected else 2)
            # Label
            draw.text((18, ry+6), lbl, font=F.small, fill=row_col)
            # Barra de progreso
            bx0, bx1 = 95, W-18
            bw = bx1 - bx0
            draw.rectangle([bx0, ry+9, bx1, ry+17], fill=(20, 25, 35))
            draw.rectangle([bx0, ry+9, bx0+int(bw*val/100), ry+17], fill=bar_col)
            # Porcentaje
            draw.text((bx1+2, ry+6), f"{val}%", font=F.small, fill=row_col)

        return img

    def render_wifi_scan(self, nets, index, scanning) -> Image.Image:
        img = Image.new("RGB", (W, H), BG); draw = ImageDraw.Draw(img)
        if scanning: _text_center_x(draw, 28, "BUSCANDO REDES...", F.menu_label, CYAN, 0, W)
        elif nets:
            draw.rounded_rectangle([30, 8, W-30, H-8], radius=10, fill=DARK_CARD)
            _text_center_x(draw, 32, nets[index].get("ssid", "")[:22], F.menu_label, WHITE, 0, W)
        return img

    def render_wifi_keyboard(self, ssid, password, groups, group, char, level) -> Image.Image:
        img = Image.new("RGB", (W, H), BG); draw = ImageDraw.Draw(img)
        draw.rectangle([20, 22, W-20, 42], outline=WHITE, width=1)
        draw.text((24, 25), password[:22], font=F.menu_label, fill=WHITE)
        _text_center_x(draw, 50, groups[group], F.menu_label, PURPLE, 0, W)
        return img

    def render_ringing(self, title, option) -> Image.Image:
        img = Image.new("RGB", (W, H), (150, 0, 0) if int(time.time()*2)%2==0 else BG)
        draw = ImageDraw.Draw(img)
        # Usamos 40px para que "DETENER" o "POSPONER" quepan perfectamente
        txt = "DETENER" if option==0 else "POSPONER"
        _text_center_x(draw, 18, txt, F.alarm_rect, WHITE, 0, W)
        return img
