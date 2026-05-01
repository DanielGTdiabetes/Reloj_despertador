"""
rect_ui.py — Versión con Margen de Seguridad Anti-Lluvia (42px).
Evita que el icono pise la temperatura en días de lluvia.
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

    def render_alarm(self, alarm, field) -> Image.Image:
        img = Image.new("RGB", (W, H), BG); draw = ImageDraw.Draw(img)
        enabled = alarm.get("enabled", False)
        
        # Recuadro centrado
        draw.rounded_rectangle([20, 10, W-20, H-10], radius=12, fill=DARK_CARD)
        
        # Estado ON/OFF a la izquierda
        col_st = AMBER if enabled else DIM_WHITE
        draw.text((35, 28), "ON" if enabled else "OFF", font=F.card_day, fill=col_st)
        
        # Hora con fuente de 40px
        time_str = f"{alarm.get('hour',7):02d}:{alarm.get('minute',0):02d}"
        _text_center_x(draw, 18, time_str, F.alarm_rect, WHITE, 0, W)
        
        # Indicador de edición
        if field == "hour":
            draw.line([W//2 - 45, H-15, W//2 - 5, H-15], fill=CYAN, width=3)
        elif field == "minute":
            draw.line([W//2 + 5, H-15, W//2 + 45, H-15], fill=CYAN, width=3)
        elif field == "enabled":
            draw.line([30, H-15, 60, H-15], fill=CYAN, width=3)
            
        return img

    def render_brightness(self, r, rect, target) -> Image.Image:
        img = Image.new("RGB", (W, H), BG); draw = ImageDraw.Draw(img)
        for i, (lbl, val, act) in enumerate([("REDONDA", r, target=="round"), ("RECT", rect, target=="rect")]):
            y = 16 + i * 28; col = CYAN if act else DIM_WHITE
            draw.text((35, y), lbl, font=F.small, fill=col)
            draw.rectangle([115, y+4, 255, y+10], fill=DARK_CARD)
            draw.rectangle([115, y+4, 115+int(140*val/100), y+10], fill=col)
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
