"""
rect_ui.py — Versión DEFINITIVA (320px + Iconos Seguros).
Ajustado para que la lluvia no se salga y todo esté centrado.
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

# Full width 320 para centrado perfecto del marco hardware
W, H = 320, 76
PAD  = 6
GAP  = 10

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
    ICON_SIZE = 28   # Tamaño reducido para que la lluvia respire

    def render_forecast(self, forecast_data: list) -> Image.Image:
        img  = Image.new("RGB", (W, H), BG)
        days = forecast_data[1:5]
        n    = 4
        card_w = (W - PAD*2 - GAP*(n-1)) // n
        card_h = H - PAD*2

        GRAD_COLORS = [
            ((100, 80, 200), (40, 30, 100)),
            ((60, 140, 220), (20, 60, 120)),
            ((80, 160, 100), (30, 80, 50)),
            ((200, 100, 60), (100, 40, 20)),
        ]

        for i in range(n):
            day  = days[i] if i < len(days) else {}
            x1   = PAD + i * (card_w + GAP)
            c1, c2 = GRAD_COLORS[i % len(GRAD_COLORS)]
            card_img = _create_v_gradient(card_w, card_h, c1, c2)
            mask     = Image.new("L", (card_w, card_h), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, card_w, card_h], radius=8, fill=255)
            img.paste(card_img, (x1, PAD), mask)
            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle([x1, PAD, x1+card_w, PAD+card_h],
                                   radius=8, outline=(255,255,255,30), width=1)
            wd = day.get("weekday", (time.localtime().tm_wday + i + 1) % 7)
            _text_center_x(draw, PAD+2, ["LUN","MAR","MIE","JUE","VIE","SAB","DOM"][wd], F.card_day, WHITE, x1, x1+card_w)
            
            # Posición de icono subida 2px para dar margen inferior
            draw_weather_icon(img, day.get("description", ""), x1 + card_w // 2, PAD + 10 + self.ICON_SIZE // 2, size=self.ICON_SIZE)
            
            tmax = day.get("temp_max")
            if tmax is not None:
                _text_center_x(draw, H-PAD-13, f"{tmax:.0f}\u00b0", F.card_temp, WHITE, x1, x1+card_w)
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
                draw.rounded_rectangle([x1+10, 5, x1+item_w-10, H-5], radius=12, outline=CYAN, width=2)
                draw_menu_icon(draw, x1+(item_w-34)//2, 12, 34, items[i][0])
                _text_center_x(draw, 52, items[i][1].upper(), F.menu_label, WHITE, x1, x2)
            else:
                draw_menu_icon(draw, x1+(item_w-24)//2, 22, 24, items[i][0])
        return img

    def render_location(self, digits, active_idx, updating=False) -> Image.Image:
        img = Image.new("RGB", (W, H), BG); draw = ImageDraw.Draw(img)
        _text_center_x(draw, 6, "GEOLOCALIZANDO..." if updating else "CÓDIGO POSTAL", F.small, CYAN, 0, W)
        box_w, box_h = 32, 38
        x_start = (W - (box_w*5 + 32)) // 2
        for i, digit in enumerate(digits[:5]):
            x = x_start + i * (box_w + 8)
            is_active = (i == active_idx) and not updating
            draw.rounded_rectangle([x, 22, x+box_w, 60], radius=5, fill=(20,40,60) if is_active else (15,20,30), outline=CYAN if is_active else (50,70,90), width=2)
            _text_center_x(draw, 28, str(digit), F.clock, CYAN if is_active else WHITE, x, x+box_w)
        return img

    def render_alarm(self, alarm, field) -> Image.Image:
        img = Image.new("RGB", (W, H), BG); draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([50, 8, W-50, H-8], radius=12, fill=DARK_CARD)
        _text_center_x(draw, 12, "HORA ALARMA", F.small, CYAN, 0, W)
        _text_center_x(draw, 34, f"{alarm.get('hour',7):02d}:{alarm.get('minute',0):02d}", F.clock, WHITE, 0, W)
        return img

    def render_brightness(self, r, rect, target) -> Image.Image:
        img = Image.new("RGB", (W, H), BG); draw = ImageDraw.Draw(img)
        for i, (lbl, val, act) in enumerate([("REDONDA", r, target=="round"), ("RECT", rect, target=="rect")]):
            y = 16 + i * 28; col = CYAN if act else DIM_WHITE
            draw.text((50, y), lbl, font=F.small, fill=col)
            draw.rectangle([130, y+4, 270, y+10], fill=DARK_CARD)
            draw.rectangle([130, y+4, 130+int(140*val/100), y+10], fill=col)
        return img

    def render_wifi_scan(self, nets, index, scanning) -> Image.Image:
        img = Image.new("RGB", (W, H), BG); draw = ImageDraw.Draw(img)
        if scanning: _text_center_x(draw, 28, "BUSCANDO REDES...", F.menu_label, CYAN, 0, W)
        elif nets:
            draw.rounded_rectangle([50, 8, W-50, H-8], radius=10, fill=DARK_CARD)
            _text_center_x(draw, 32, nets[index].get("ssid", "")[:22], F.menu_label, WHITE, 0, W)
        return img

    def render_wifi_keyboard(self, ssid, password, groups, group, char, level) -> Image.Image:
        img = Image.new("RGB", (W, H), BG); draw = ImageDraw.Draw(img)
        draw.rectangle([30, 22, W-30, 42], outline=WHITE, width=1)
        draw.text((34, 25), password[:22], font=F.menu_label, fill=WHITE)
        _text_center_x(draw, 50, groups[group], F.menu_label, PURPLE, 0, W)
        return img

    def render_ringing(self, title, option) -> Image.Image:
        img = Image.new("RGB", (W, H), BG); draw = ImageDraw.Draw(img)
        col = CYAN if int(time.time()*4)%2==0 else AMBER
        draw.rectangle([0,0,W-1,H-1], outline=col, width=4)
        _text_center_x(draw, 32, "DETENER" if option==0 else "POSPONER", F.clock, WHITE, 0, W)
        return img
