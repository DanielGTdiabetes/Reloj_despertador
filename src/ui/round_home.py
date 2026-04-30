import datetime as dt
import math
import os

from PIL import Image, ImageDraw

from graphics.icons import (
    apply_round_mask,
    center_text,
    condition_kind,
    fit_text,
    gradient,
    load_font,
    text_size,
)


class RoundHomeScreen:
    WIDTH = 240
    HEIGHT = 240
    ICON_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "weather"))

    def __init__(self, scale=2):
        self.scale = scale
        self.rw = self.WIDTH * scale
        self.rh = self.HEIGHT * scale
        self.font_time = load_font(72 * scale)
        self.font_date = load_font(15 * scale)
        self.font_small = load_font(12 * scale, bold=False)
        self.font_medium = load_font(15 * scale)
        self.font_temp = load_font(24 * scale)
        self._icons = {}

    def render(self, now, current, sun, moon, alarm=None, status=""):
        img = self._background(sun.get("period", "day"))
        draw = ImageDraw.Draw(img)
        s = self.scale
        cx, cy = self.rw // 2, self.rh // 2

        self._draw_second_ring(draw, cx, cy, int(112 * s), now.second)

        condition = current.get("description") or current.get("main") or "despejado"
        temp = current.get("temp")
        is_night = sun.get("period") == "night"

        if is_night and not condition:
            self._draw_moon(draw, cx, int(50 * s), int(26 * s), moon.get("phase", 0.5))
        else:
            self._paste_weather_icon(img, cx, int(53 * s), int(82 * s), condition)

        day = self._day_name(now.weekday()).upper()
        date_text = f"{day} {now.day:02d}/{now.month:02d}"
        center_text(draw, (cx, int(24 * s)), date_text, self.font_date, (180, 226, 255))

        time_text = now.strftime("%H:%M")
        center_text(draw, (cx, int(121 * s)), time_text, self.font_time, (255, 255, 255))

        temp_text = "--C" if temp is None else f"{round(float(temp))}C"
        center_text(draw, (cx, int(169 * s)), temp_text, self.font_temp, (255, 232, 126))

        desc = self._clean_condition(condition).upper()
        desc_font = fit_text(draw, desc, int(160 * s), 15 * s, 8 * s)
        center_text(draw, (cx, int(193 * s)), desc, desc_font, (214, 235, 255))

        humidity = current.get("humidity")
        wind = current.get("wind_speed")
        details = []
        if humidity is not None:
            details.append(f"H {int(humidity)}%")
        if wind is not None:
            details.append(f"V {round(float(wind) * 3.6)}km/h")
        if not details and status:
            details.append(status)
        center_text(draw, (cx, int(212 * s)), "  ".join(details[:2]), self.font_small, (146, 194, 230))

        sunrise = self._format_time(sun.get("sunrise"))
        sunset = self._format_time(sun.get("sunset"))
        self._draw_sun_band(draw, sun, sunrise, sunset)

        if alarm and alarm.get("enabled"):
            center_text(draw, (cx, int(228 * s)), f"ALARMA {alarm['hour']:02d}:{alarm['minute']:02d}",
                        self.font_small, (255, 176, 120))

        small = img.resize((self.WIDTH, self.HEIGHT), Image.LANCZOS)
        return apply_round_mask(small)

    def render_focus(self, title, subtitle, kind="menu", value=""):
        img = self._background("day")
        draw = ImageDraw.Draw(img)
        s = self.scale
        cx, cy = self.rw // 2, self.rh // 2
        draw.ellipse((int(26 * s), int(26 * s), int(214 * s), int(214 * s)),
                     outline=(80, 185, 255), width=int(5 * s))
        if kind == "wifi":
            self._draw_wifi(draw, cx, int(78 * s), int(44 * s))
        elif kind == "alarm":
            self._draw_alarm(draw, cx, int(78 * s), int(40 * s))
        elif kind == "brightness":
            self._draw_brightness(draw, cx, int(78 * s), int(40 * s))
        else:
            self._paste_weather_icon(img, cx, int(78 * s), int(78 * s), "partly")

        title_font = fit_text(draw, title.upper(), int(180 * s), 25 * s, 12 * s)
        center_text(draw, (cx, int(134 * s)), title.upper(), title_font, (255, 255, 255))
        sub_font = fit_text(draw, subtitle, int(170 * s), 15 * s, 9 * s, bold=False)
        center_text(draw, (cx, int(161 * s)), subtitle, sub_font, (170, 210, 245))
        if value:
            value_font = fit_text(draw, value, int(150 * s), 22 * s, 10 * s)
            center_text(draw, (cx, int(193 * s)), value, value_font, (255, 228, 120))
        return apply_round_mask(img.resize((self.WIDTH, self.HEIGHT), Image.LANCZOS))

    def _background(self, period):
        if period == "night":
            top, bottom = (5, 9, 26), (21, 18, 58)
        elif period in ("sunrise", "sunset"):
            top, bottom = (30, 25, 70), (235, 108, 54)
        else:
            top, bottom = (8, 55, 112), (7, 18, 44)
        return gradient((self.rw, self.rh), top, bottom)

    def _draw_second_ring(self, draw, cx, cy, radius, second):
        s = self.scale
        box = (cx - radius, cy - radius, cx + radius, cy + radius)
        draw.arc(box, 0, 360, fill=(42, 68, 105), width=int(4 * s))
        end = 270 + int(second / 60 * 360)
        draw.arc(box, 270, end, fill=(0, 230, 255), width=int(6 * s))
        for i in range(12):
            a = math.radians(i * 30 - 90)
            r1, r2 = radius - int(7 * s), radius - int(1 * s)
            draw.line((cx + math.cos(a) * r1, cy + math.sin(a) * r1,
                       cx + math.cos(a) * r2, cy + math.sin(a) * r2),
                      fill=(130, 185, 220), width=max(1, int(1.5 * s)))

    def _draw_sun_band(self, draw, sun, sunrise="", sunset=""):
        s = self.scale
        x1, x2 = int(52 * s), int(188 * s)
        y = int(224 * s)
        draw.line((x1, y, x2, y), fill=(57, 92, 132), width=int(2 * s))
        p = max(0.0, min(1.0, sun.get("progress", 0.0)))
        draw.line((x1, y, x1 + int((x2 - x1) * p), y), fill=(255, 192, 82), width=int(3 * s))
        sun_x = x1 + int((x2 - x1) * p)
        draw.ellipse((sun_x - 3 * s, y - 3 * s, sun_x + 3 * s, y + 3 * s), fill=(255, 231, 90))
        if sunrise and sunset:
            draw.text((int(28 * s), int(218 * s)), sunrise, fill=(255, 196, 108), font=self.font_small, anchor="mm")
            draw.text((int(212 * s), int(218 * s)), sunset, fill=(174, 202, 255), font=self.font_small, anchor="mm")

    def _paste_weather_icon(self, img, cx, cy, size, condition):
        icon = self._load_icon(condition_kind(condition))
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

    def _draw_moon(self, draw, cx, cy, radius, phase=0.55):
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(225, 230, 245))
        offset = int(radius * (0.9 - abs(phase - 0.5)))
        shadow = (18, 24, 52)
        if phase < 0.5:
            draw.ellipse((cx - radius + offset, cy - radius, cx + radius + offset, cy + radius), fill=shadow)
        else:
            draw.ellipse((cx - radius - offset, cy - radius, cx + radius - offset, cy + radius), fill=shadow)

    def _draw_wifi(self, draw, cx, cy, size):
        for i in range(3):
            r = size - i * size // 4
            draw.arc((cx - r, cy - r, cx + r, cy + r), 205, 335, fill=(70, 220, 255), width=max(3, size // 12))
        draw.ellipse((cx - 6, cy + 20, cx + 6, cy + 32), fill=(70, 220, 255))

    def _draw_alarm(self, draw, cx, cy, size):
        draw.ellipse((cx - size, cy - size, cx + size, cy + size), outline=(255, 205, 90), width=max(3, size // 10))
        draw.line((cx, cy, cx, cy - size // 2), fill=(255, 255, 255), width=max(2, size // 12))
        draw.line((cx, cy, cx + size // 3, cy + size // 5), fill=(255, 255, 255), width=max(2, size // 12))
        draw.arc((cx - size - 12, cy - size - 8, cx - 8, cy - size + 20), 180, 350, fill=(255, 120, 90), width=4)
        draw.arc((cx + 8, cy - size - 8, cx + size + 12, cy - size + 20), 190, 360, fill=(255, 120, 90), width=4)

    def _draw_brightness(self, draw, cx, cy, size):
        for i in range(10):
            a = math.radians(i * 36)
            draw.line((cx + math.cos(a) * (size + 5), cy + math.sin(a) * (size + 5),
                       cx + math.cos(a) * (size + 20), cy + math.sin(a) * (size + 20)),
                      fill=(255, 220, 80), width=4)
        draw.ellipse((cx - size, cy - size, cx + size, cy + size), fill=(255, 230, 80))

    def _format_time(self, value):
        if isinstance(value, dt.datetime):
            return value.strftime("%H:%M")
        return "--:--"

    def _day_name(self, weekday):
        return ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"][weekday]

    def _clean_condition(self, condition):
        text = (condition or "despejado").strip()
        if len(text) > 16:
            text = text[:15] + "."
        return text
