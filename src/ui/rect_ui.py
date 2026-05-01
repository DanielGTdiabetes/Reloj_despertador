"""
rect_ui.py — Versión Gráfica Premium.
- Menú con Iconos Grandes y etiquetas limpias.
- Pronóstico con degradados suaves y bordes iluminados.
- UI de WiFi y Alarma rediseñada.
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

W, H = 284, 76
PAD  = 4
GAP  = 8

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
    ICON_SIZE = 40

    def __init__(self) -> None:
        pass

    def render_forecast(self, forecast_data: list) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        days = forecast_data[1:5]
        n = 4
        card_w = (W - PAD*2 - GAP*(n-1)) // n
        card_h = H - PAD*2
        for i in range(n):
            day = days[i] if i < len(days) else {}
            x1 = PAD + i * (card_w + GAP)
            g_idx = i % len(GRADIENTS)
            c1, c2 = GRADIENTS[g_idx]
            
            # Fondo degradado con borde iluminado
            card_img = _create_v_gradient(card_w, card_h, c1, c2)
            mask = Image.new("L", (card_w, card_h), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, card_w, card_h], radius=10, fill=255)
            img.paste(card_img, (x1, PAD), mask)
            
            draw = ImageDraw.Draw(img)
            # Borde sutil
            draw.rounded_rectangle([x1, PAD, x1+card_w, PAD+card_h], radius=10, outline=(255,255,255,40), width=1)
            
            # Texto y Icono
            wd = day.get("weekday", (time.localtime().tm_wday+i+1))%7
            _text_center_x(draw, PAD+4, ["LUN","MAR","MIE","JUE","VIE","SAB","DOM"][wd], F.card_day, WHITE, x1, x1+card_w)
            
            icon = ICONS.get(condition_to_icon_file(day.get("description","")), self.ICON_SIZE)
            img.paste(icon, (x1+(card_w-self.ICON_SIZE)//2, PAD+16), icon)
            
            tmax = day.get("temp_max")
            if tmax is not None:
                _text_center_x(draw, H-PAD-16, f"{tmax:.0f}\u00b0", F.card_temp, WHITE, x1, x1+card_w)
        return img

    def render_menu(self, items, index) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        
        item_w = W // 3
        for i in range(index - 1, index + 2):
            if i < 0 or i >= len(items): continue
            slot = i - (index - 1)
            x1, x2 = slot * item_w, (slot+1) * item_w
            is_active = (i == index)
            
            if is_active:
                # Slot central destacado con degradado
                grad = _create_v_gradient(item_w-10, H-10, PURPLE, (50, 20, 80))
                mask = Image.new("L", (item_w-10, H-10), 0)
                ImageDraw.Draw(mask).rounded_rectangle([0,0,item_w-10,H-10], radius=15, fill=255)
                img.paste(grad, (x1+5, 5), mask)
                draw_menu_icon(draw, x1+(item_w-34)//2, 12, 34, items[i][0])
                _text_center_x(draw, 52, items[i][1].upper(), F.menu_label, WHITE, x1, x2)
            else:
                draw_menu_icon(draw, x1+(item_w-24)//2, 20, 24, items[i][0])
                # No ponemos texto a los laterales para limpiar la UI
        return img

    def render_alarm(self, alarm, field) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        h, m = alarm.get("hour", 7), alarm.get("minute", 0)
        draw.rounded_rectangle([20, 10, W-20, H-10], radius=15, fill=DARK_CARD)
        _text_center_x(draw, 15, "HORA ALARMA", F.small, CYAN)
        t_str = f"{h:02d} : {m:02d}"
        _text_center_x(draw, 32, t_str, F.clock, WHITE if field=="enabled" else (CYAN if field=="hour" or field=="minute" else WHITE))
        # Cursor indicador
        if field == "hour": draw.rectangle([100, 60, 135, 63], fill=CYAN)
        elif field == "minute": draw.rectangle([150, 60, 185, 63], fill=CYAN)
        return img

    def render_brightness(self, r, rect, target) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        for i, (label, val, act) in enumerate([("REDONDA", r, target=="round"), ("RECT", rect, target=="rect")]):
            y = 15 + i*30
            col = CYAN if act else DIM_WHITE
            draw.text((30, y), label, font=F.small, fill=col)
            draw.rectangle([100, y+4, 230, y+10], fill=DARK_CARD)
            draw.rectangle([100, y+4, 100+int(130*val/100), y+10], fill=col)
            draw.text((240, y), f"{val}%", font=F.small, fill=WHITE)
        return img

    def render_wifi_scan(self, nets, index, scanning) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        if scanning: _text_center_x(draw, 30, "BUSCANDO REDES...", F.menu_label, CYAN)
        elif not nets: _text_center_x(draw, 30, "SIN REDES DISPONIBLES", F.menu_label, PURPLE)
        else:
            net = nets[index]
            draw.rounded_rectangle([20, 10, W-20, H-10], radius=12, fill=DARK_CARD)
            _text_center_x(draw, 15, f"RED {index+1}/{len(nets)}", F.small, CYAN)
            _text_center_x(draw, 35, net.get("ssid", "???")[:20], F.menu_label, WHITE)
            # Señal
            s = net.get("signal", 0)
            for b in range(4): draw.rectangle([W-60+b*6, H-25-b*3, W-60+b*6+4, H-25], fill=CYAN if b<s else BG)
        return img

    def render_wifi_keyboard(self, ssid, password, groups, group, char, level) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw.text((20, 10), f"WIFI: {ssid[:15]}", font=F.small, fill=CYAN)
        draw.rectangle([20, 25, W-20, 45], outline=WHITE)
        draw.text((25, 28), password + ("|" if int(time.time()*2)%2==0 else ""), font=F.menu_label, fill=WHITE)
        # Teclas T9
        txt = groups[group]
        if level == 1: txt = f" > {txt[char]} < "
        _text_center_x(draw, 50, txt, F.menu_label, PURPLE)
        return img

    def render_ringing(self, title, option) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        col = CYAN if int(time.time()*4)%2==0 else PURPLE
        draw.rectangle([0,0,W-1,H-1], outline=col, width=5)
        _text_center_x(draw, 10, "¡ ALARMA !", F.menu_label, col)
        lbl = "DETENER" if option == 0 else "POSPONER"
        _text_center_x(draw, 35, lbl, F.clock, WHITE)
        return img
