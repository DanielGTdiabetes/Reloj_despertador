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
    ICON_SIZE = 36

    @staticmethod
    def _period_theme(period: str):
        if period == "sunrise":
            return (55, 28, 5), (80, 45, 10), (200, 120, 30)
        if period == "sunset":
            return (55, 15, 25), (80, 28, 18), (200, 75, 40)
        return BG, (20, 22, 28), (40, 45, 55)

    def render_forecast(self, forecast_data: list, period: str = "day") -> Image.Image:
        bg, card_bg, card_border = self._period_theme(period)
        img  = Image.new("RGB", (W, H), bg)
        days = forecast_data[1:5]
        n    = 4
        card_w = (W - PAD_X*2 - GAP*(n-1)) // n
        card_h = H - PAD_Y*2

        for i in range(n):
            day  = days[i] if i < len(days) else {}
            x1   = PAD_X + i * (card_w + GAP)

            card_img = Image.new("RGB", (card_w, card_h), card_bg)
            mask     = Image.new("L", (card_w, card_h), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, card_w, card_h], radius=8, fill=255)
            img.paste(card_img, (x1, PAD_Y), mask)

            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle([x1, PAD_Y, x1+card_w, PAD_Y+card_h],
                                   radius=8, outline=card_border, width=1)
            wd = day.get("weekday", (time.localtime().tm_wday + i + 1) % 7)
            _text_center_x(draw, PAD_Y+4, ["LUN","MAR","MIE","JUE","VIE","SAB","DOM"][wd], F.card_day, WHITE, x1, x1+card_w)

            draw_weather_icon(img, day.get("description", ""), x1 + card_w // 2, PAD_Y + 19 + self.ICON_SIZE // 2, size=self.ICON_SIZE)
            
            tmax = day.get("temp_max")
            if tmax is not None:
                _text_center_x(draw, H-PAD_Y-16, f"{tmax:.0f}\u00b0", F.card_temp, WHITE, x1, x1+card_w)
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

    def render_location(self, digits, active_idx, updating=False, editing=False) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        if updating:
            _text_center_x(draw, 28, "Geolocalizando...", F.menu_label, CYAN, 0, W)
            return img

        _text_center_x(draw, 4, "CODIGO POSTAL", F.small, DIM_WHITE, 0, W)

        # 5 cajas centradas en 284px
        BW, BH, BGAP = 40, 46, 8
        total = BW * 5 + BGAP * 4      # 232px
        ox = (W - total) // 2          # ~26px margen
        BY1 = 18

        for i, digit in enumerate(digits[:5]):
            bx = ox + i * (BW + BGAP)
            is_cursor = (i == active_idx)
            is_edit   = is_cursor and editing

            if is_edit:
                fill, outline, lw = (45, 25, 0), AMBER, 2
                tc = AMBER
            elif is_cursor:
                fill, outline, lw = DARK_CARD, CYAN, 2
                tc = WHITE
            else:
                fill, outline, lw = (12, 16, 24), (35, 45, 60), 1
                tc = DIM_WHITE

            draw.rounded_rectangle([bx, BY1, bx + BW, BY1 + BH],
                                   radius=7, fill=fill, outline=outline, width=lw)
            # Dígito centrado — F.date_top = 20px bold, cabe en 40×46 sin problemas
            _text_center_x(draw, BY1 + (BH - 20) // 2, str(digit), F.date_top, tc, bx, bx + BW)

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
            # Barra de progreso (deja 34px al final para el texto %)
            bx0, bx1 = 95, W - 52
            bw = bx1 - bx0
            draw.rectangle([bx0, ry+9, bx1, ry+17], fill=(20, 25, 35))
            draw.rectangle([bx0, ry+9, bx0+int(bw*val/100), ry+17], fill=bar_col)
            # Porcentaje (dentro del recuadro, a la derecha)
            draw.text((bx1 + 5, ry+6), f"{val}%", font=F.small, fill=row_col)

        return img

    def render_wifi_scan(self, nets, index, scanning, connected_ssid="") -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        if scanning:
            _text_center_x(draw, 30, "BUSCANDO REDES...", F.menu_label, CYAN, 0, W)
            return img
        if not nets:
            _text_center_x(draw, 30, "Sin redes", F.menu_label, DIM_WHITE, 0, W)
            return img
        # Mostrar hasta 3 redes: la seleccionada en el centro
        for slot, offset in enumerate([-1, 0, 1]):
            i = index + offset
            if i < 0 or i >= len(nets):
                continue
            net = nets[i]
            is_sel = (offset == 0)
            is_connected = connected_ssid and net["ssid"] == connected_ssid
            ry = 6 + slot * 22
            if is_sel:
                # Borde verde si es la red actualmente conectada, cyan si solo seleccionada
                outline_col = (0, 200, 80) if is_connected else CYAN
                draw.rounded_rectangle([8, ry, W-8, ry+20], radius=5,
                                       fill=DARK_CARD, outline=outline_col, width=2)
                # Checkmark + SSID si está conectada
                ssid_x = 18
                if is_connected:
                    draw.text((18, ry+4), "✓", font=F.menu_label, fill=(0, 200, 80))
                    ssid_x = 30
                draw.text((ssid_x, ry+4), net["ssid"][:24], font=F.menu_label, fill=WHITE)
                bars = net.get("signal", 0)
                for b in range(4):
                    bx = W - 30 + b * 6
                    bh = 4 + b * 3
                    col = (0, 200, 80) if (is_connected and b < bars) else (CYAN if b < bars else (30, 40, 55))
                    draw.rectangle([bx, ry+18-bh, bx+4, ry+18], fill=col)
            else:
                # Red no seleccionada: verde si conectada, gris si no
                text_col = (0, 160, 60) if is_connected else (55, 65, 80)
                prefix = "✓ " if is_connected else ""
                draw.text((18, ry+4), (prefix + net["ssid"])[:28], font=F.small, fill=text_col)
        return img

    def render_wifi_keyboard(self, ssid, password, chars, char_idx) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # --- Fila superior: red + contraseña escrita ---
        draw.text((8, 4), f"{ssid[:14]}:", font=F.small, fill=DIM_WHITE)
        # Mostrar últimos 18 chars de la contraseña + cursor parpadeante
        cursor = "|" if int(time.time() * 2) % 2 == 0 else " "
        pwd_show = (password[-18:] if len(password) > 18 else password) + cursor
        draw.text((8, 18), pwd_show, font=F.menu_label, fill=WHITE)

        # --- Separador ---
        draw.line([8, 33, W - 8, 33], fill=(28, 36, 52), width=1)

        # --- Cinta de caracteres: 7 visibles, 36px cada uno ---
        VISIBLE, SW = 7, 36
        ox = (W - VISIBLE * SW) // 2   # margen ~8px
        TY1, TY2 = 37, H - 4           # y=37..72 → 35px de alto

        for slot in range(VISIBLE):
            off = slot - VISIBLE // 2   # -3..+3
            idx = (char_idx + off) % len(chars)
            ch = chars[idx]
            sx = ox + slot * SW
            label = {"OK": "OK", "DEL": "DEL", " ": "SPC"}.get(ch, ch)
            is_center = (off == 0)

            if is_center:
                if ch == "OK":
                    bg, outline, tc = (0, 28, 10), (0, 180, 60), (0, 210, 70)
                elif ch == "DEL":
                    bg, outline, tc = (38, 18, 0), AMBER, AMBER
                else:
                    bg, outline, tc = DARK_CARD, CYAN, WHITE
                draw.rounded_rectangle([sx + 1, TY1, sx + SW - 2, TY2],
                                       radius=5, fill=bg, outline=outline, width=2)
                _text_center_x(draw, TY1 + (TY2 - TY1 - 13) // 2,
                               label, F.menu_label, tc, sx, sx + SW)
            else:
                dist = abs(off)
                col = (65, 80, 100) if dist == 1 else (38, 48, 62)
                _text_center_x(draw, TY1 + (TY2 - TY1 - 12) // 2,
                               label, F.small, col, sx, sx + SW)
        return img

    def render_ringing(self, title, option) -> Image.Image:
        img = Image.new("RGB", (W, H), (150, 0, 0) if int(time.time()*2)%2==0 else BG)
        draw = ImageDraw.Draw(img)
        # Usamos 40px para que "DETENER" o "POSPONER" quepan perfectamente
        txt = "DETENER" if option==0 else "POSPONER"
        _text_center_x(draw, 18, txt, F.alarm_rect, WHITE, 0, W)
        return img
