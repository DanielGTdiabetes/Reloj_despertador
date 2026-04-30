import os

from PIL import Image, ImageDraw

from graphics.icons import condition_kind, fit_text, gradient, load_font, text_size


class RectUIScreen:
    WIDTH = 284
    HEIGHT = 76
    DAYS = ["L", "M", "X", "J", "V", "S", "D"]
    ICON_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "weather"))

    def __init__(self, scale=2):
        self.scale = scale
        self.rw = self.WIDTH * scale
        self.rh = self.HEIGHT * scale
        self.font_tiny = load_font(8 * scale, bold=False)
        self.font_small = load_font(10 * scale)
        self.font_med = load_font(13 * scale)
        self.font_big = load_font(20 * scale)
        self._icons = {}

    def render_forecast(self, daily):
        img = gradient((self.rw, self.rh), (9, 17, 33), (16, 30, 54))
        draw = ImageDraw.Draw(img)
        s = self.scale
        days = (daily or [])[:5]
        if not days:
            return self._empty("Sin prediccion")

        pad_x = int(6 * s)
        pad_y = int(4 * s)
        gap = int(4 * s)
        card_w = (self.rw - pad_x * 2 - gap * 4) // 5
        card_h = self.rh - pad_y * 2

        for i in range(5):
            day = days[i] if i < len(days) else {}
            x1 = pad_x + i * (card_w + gap)
            y1 = pad_y
            x2 = x1 + card_w
            y2 = y1 + card_h
            self._card(draw, x1, y1, x2, y2, i)

            wd = day.get("weekday", i) % 7
            label = self.DAYS[wd]
            draw.text((x1 + card_w // 2, y1 + int(2 * s)), label,
                      fill=(245, 250, 255), font=self.font_small, anchor="ma")

            self._paste_weather_icon(img, x1 + card_w // 2, y1 + int(31 * s),
                                     int(43 * s), day.get("description", "clear"))

            high = day.get("temp_max")
            low = day.get("temp_min")
            if high is not None:
                draw.text((x1 + int(12 * s), y2 - int(15 * s)), f"{round(high)}",
                          fill=(255, 176, 92), font=self.font_small, anchor="ma")
            if low is not None:
                draw.text((x2 - int(12 * s), y2 - int(15 * s)), f"{round(low)}",
                          fill=(120, 216, 255), font=self.font_tiny, anchor="ma")

        return img.resize((self.WIDTH, self.HEIGHT), Image.LANCZOS)

    def render_menu(self, items, index):
        title = "MENU"
        rows = [label for _, label in items]
        return self._list_screen(title, rows, index, footer="Pulsar: entrar   Largo: salir")

    def render_alarm(self, alarm, field):
        img = gradient((self.rw, self.rh), (25, 15, 30), (60, 22, 36))
        draw = ImageDraw.Draw(img)
        s = self.scale
        enabled = "ON" if alarm.get("enabled") else "OFF"
        time_text = f"{alarm.get('hour', 7):02d}:{alarm.get('minute', 0):02d}"
        draw.text((int(10 * s), int(7 * s)), "ALARMA", fill=(255, 205, 120), font=self.font_med)
        draw.text((int(10 * s), int(29 * s)), time_text, fill=(255, 255, 255), font=self.font_big)
        draw.text((int(100 * s), int(32 * s)), enabled, fill=(120, 255, 160) if alarm.get("enabled") else (255, 130, 120),
                  font=self.font_med)

        fields = [("enabled", "Activa"), ("hour", "Hora"), ("minute", "Min")]
        x = int(154 * s)
        for n, (key, label) in enumerate(fields):
            y = int((10 + n * 20) * s)
            fill = (55, 115, 160) if field == key else (31, 45, 72)
            draw.rounded_rectangle((x, y, int(274 * s), y + int(16 * s)), radius=int(5 * s), fill=fill)
            draw.text((x + int(8 * s), y + int(1 * s)), label, fill=(235, 245, 255), font=self.font_small)
        return img.resize((self.WIDTH, self.HEIGHT), Image.LANCZOS)

    def render_brightness(self, round_level, rect_level, selected):
        img = gradient((self.rw, self.rh), (14, 24, 30), (38, 45, 32))
        draw = ImageDraw.Draw(img)
        s = self.scale
        draw.text((int(10 * s), int(7 * s)), "BRILLO", fill=(255, 225, 110), font=self.font_med)
        self._slider(draw, int(15 * s), int(34 * s), int(115 * s), round_level, selected == "round", "Redonda")
        self._slider(draw, int(154 * s), int(34 * s), int(115 * s), rect_level, selected == "rect", "Rect")
        return img.resize((self.WIDTH, self.HEIGHT), Image.LANCZOS)

    def render_wifi_scan(self, networks, index, scanning):
        if scanning:
            return self._empty("Buscando redes WiFi...")
        labels = [f"{n.get('ssid', '')[:18]}  {n.get('signal', 0)}/4" for n in networks[:5]]
        if not labels:
            labels = ["Sin redes", "Reintentar"]
        return self._list_screen("WIFI", labels, index, footer="Pulsar: elegir")

    def render_wifi_keyboard(self, ssid, password, groups, group_index, char_index, level):
        img = gradient((self.rw, self.rh), (8, 24, 42), (19, 45, 68))
        draw = ImageDraw.Draw(img)
        s = self.scale
        ssid_font = fit_text(draw, ssid or "WiFi", int(112 * s), int(13 * s), int(7 * s))
        draw.text((int(7 * s), int(5 * s)), ssid or "WiFi", fill=(155, 225, 255), font=ssid_font)
        masked = "*" * min(len(password), 12)
        draw.text((int(7 * s), int(23 * s)), masked or "Contrasena", fill=(255, 255, 255), font=self.font_med)

        key_w = int(20 * s)
        key_h = int(18 * s)
        y = int(50 * s)
        x = int(3 * s)
        for i, chars in enumerate(groups):
            fill = (35, 145, 190) if i == group_index else (23, 48, 78)
            draw.rounded_rectangle((x, y, x + key_w, y + key_h), radius=int(5 * s), fill=fill)
            label = chars[char_index % len(chars)] if i == group_index and level == 1 else chars[:3]
            key_font = fit_text(draw, label, key_w - int(4 * s), int(10 * s), int(7 * s))
            draw.text((x + key_w // 2, y + int(3 * s)), label, fill=(255, 255, 255), font=key_font, anchor="ma")
            x += key_w + int(3 * s)

        hint = "Grupo" if level == 0 else "Letra"
        draw.text((int(210 * s), int(7 * s)), hint, fill=(255, 218, 90), font=self.font_med)
        draw.text((int(188 * s), int(28 * s)), "Largo borra", fill=(170, 205, 230), font=self.font_tiny)
        return img.resize((self.WIDTH, self.HEIGHT), Image.LANCZOS)

    def render_ringing(self, label, option):
        img = gradient((self.rw, self.rh), (80, 16, 25), (18, 18, 28))
        draw = ImageDraw.Draw(img)
        s = self.scale
        draw.text((int(12 * s), int(6 * s)), "ALARMA", fill=(255, 210, 110), font=self.font_big)
        draw.text((int(12 * s), int(35 * s)), label, fill=(255, 255, 255), font=self.font_med)
        opts = ["Detener", "Posponer"]
        for i, opt in enumerate(opts):
            x = int((150 + i * 65) * s)
            fill = (255, 110, 80) if i == option else (45, 45, 58)
            draw.rounded_rectangle((x, int(25 * s), x + int(58 * s), int(58 * s)), radius=int(6 * s), fill=fill)
            f = fit_text(draw, opt, int(52 * s), int(10 * s), int(7 * s))
            draw.text((x + int(29 * s), int(36 * s)), opt, fill=(255, 255, 255), font=f, anchor="mm")
        return img.resize((self.WIDTH, self.HEIGHT), Image.LANCZOS)

    def _list_screen(self, title, rows, index, footer=""):
        img = gradient((self.rw, self.rh), (10, 18, 36), (20, 33, 58))
        draw = ImageDraw.Draw(img)
        s = self.scale
        draw.text((int(8 * s), int(5 * s)), title, fill=(115, 220, 255), font=self.font_med)
        start_y = int(25 * s)
        visible = rows[:3]
        if index >= 3:
            start = min(index - 2, max(0, len(rows) - 3))
            visible = rows[start:start + 3]
            visible_index = index - start
        else:
            visible_index = index
        for i, row in enumerate(visible):
            y = start_y + int(i * 16 * s)
            selected = i == visible_index
            fill = (45, 125, 170) if selected else (20, 37, 62)
            draw.rounded_rectangle((int(70 * s), y - int(2 * s), int(276 * s), y + int(13 * s)),
                                   radius=int(4 * s), fill=fill)
            font = fit_text(draw, row, int(190 * s), int(10 * s), int(7 * s))
            draw.text((int(76 * s), y - int(1 * s)), row, fill=(255, 255, 255), font=font)
        if footer:
            draw.text((int(8 * s), int(62 * s)), footer, fill=(140, 170, 205), font=self.font_tiny)
        return img.resize((self.WIDTH, self.HEIGHT), Image.LANCZOS)

    def _card(self, draw, x1, y1, x2, y2, index):
        palette = [
            ((34, 43, 78), (20, 35, 58)),
            ((42, 73, 60), (24, 50, 52)),
            ((72, 55, 38), (48, 40, 46)),
            ((37, 73, 92), (21, 42, 72)),
            ((62, 45, 86), (34, 33, 63)),
            ((70, 48, 52), (42, 32, 45)),
            ((36, 65, 90), (20, 38, 61)),
        ]
        top, bottom = palette[index % len(palette)]
        draw.rounded_rectangle((x1, y1, x2, y2), radius=8 * self.scale, fill=bottom)
        for y in range(y1, y2):
            t = (y - y1) / max(1, y2 - y1)
            color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
            draw.line((x1 + 2, y, x2 - 2, y), fill=color)
        draw.rounded_rectangle((x1, y1, x2, y2), radius=8 * self.scale, outline=(255, 255, 255), width=1)

    def _paste_weather_icon(self, img, cx, cy, size, condition):
        kind = condition_kind(condition)
        icon = self._load_icon(kind)
        if icon is None:
            return
        scaled = icon.resize((size, size), Image.LANCZOS)
        img.paste(scaled, (int(cx - size / 2), int(cy - size / 2)), scaled)

    def _load_icon(self, kind):
        if kind in self._icons:
            return self._icons[kind]
        path = os.path.join(self.ICON_DIR, f"{kind}.png")
        if not os.path.exists(path):
            path = os.path.join(self.ICON_DIR, "partly.png")
        try:
            icon = Image.open(path).convert("RGBA")
        except Exception:
            icon = None
        self._icons[kind] = icon
        return icon

    def _slider(self, draw, x, y, width, value, selected, label):
        s = self.scale
        draw.text((x, y - int(18 * s)), label, fill=(235, 245, 255), font=self.font_small)
        draw.rounded_rectangle((x, y, x + width, y + int(10 * s)), radius=int(5 * s), fill=(27, 38, 50))
        fill_w = int(width * max(0, min(100, value)) / 100)
        draw.rounded_rectangle((x, y, x + fill_w, y + int(10 * s)), radius=int(5 * s),
                               fill=(255, 215, 80) if selected else (100, 190, 255))
        draw.text((x + width // 2, y + int(26 * s)), f"{value}%", fill=(255, 255, 255),
                  font=self.font_med, anchor="mm")

    def _empty(self, text):
        img = gradient((self.rw, self.rh), (9, 17, 33), (16, 30, 54))
        draw = ImageDraw.Draw(img)
        font = fit_text(draw, text, int(250 * self.scale), int(17 * self.scale), int(9 * self.scale))
        draw.text((self.rw // 2, self.rh // 2), text, fill=(180, 210, 240), font=font, anchor="mm")
        return img.resize((self.WIDTH, self.HEIGHT), Image.LANCZOS)
