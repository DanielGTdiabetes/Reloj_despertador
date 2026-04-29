import datetime as dt
import math
from PIL import Image, ImageDraw

from graphics.icons import (
    apply_round_mask,
    center_text,
    draw_moon,
    draw_weather_icon,
    fit_text,
    gradient,
    load_font,
    text_size,
)


class RoundHomeScreen:
    WIDTH = 240
    HEIGHT = 240

    def __init__(self, scale=2):
        self.scale = scale
        self.rw = self.WIDTH * scale
        self.rh = self.HEIGHT * scale
        self.font_time = load_font(78 * scale)
        self.font_date = load_font(17 * scale)
        self.font_small = load_font(12 * scale, bold=False)
        self.font_medium = load_font(16 * scale)
        self.font_temp = load_font(28 * scale)

    def render(self, now, current, sun, moon, alarm=None, status=""):
        img = self._background(sun.get("period", "day"))
        draw = ImageDraw.Draw(img)
        s = self.scale
        cx, cy = self.rw // 2, self.rh // 2

        self._draw_second_ring(draw, cx, cy, int(112 * s), now.second)
        self._draw_sun_band(draw, sun)

        condition = current.get("description") or current.get("main") or "despejado"
        temp = current.get("temp")
        is_night = sun.get("period") == "night"

        if is_night:
            draw_moon(draw, cx, int(45 * s), int(21 * s), moon.get("phase", 0.5))
        else:
            draw_weather_icon(draw, cx, int(45 * s), int(42 * s), condition)

        day = self._day_name(now.weekday()).upper()
        date_text = f"{day} {now.day:02d}/{now.month:02d}"
        center_text(draw, (cx, int(75 * s)), date_text, self.font_date, (170, 220, 255))

        time_text = now.strftime("%H:%M")
        center_text(draw, (cx, int(122 * s)), time_text, self.font_time, (255, 255, 255))

        temp_text = "--C" if temp is None else f"{round(float(temp))}C"
        center_text(draw, (int(74 * s), int(164 * s)), temp_text, self.font_temp, (255, 236, 150))

        desc = self._clean_condition(condition).upper()
        desc_font = fit_text(draw, desc, int(126 * s), 17 * s, 9 * s)
        draw.text((int(111 * s), int(149 * s)), desc, fill=(210, 230, 255), font=desc_font)

        humidity = current.get("humidity")
        wind = current.get("wind_speed")
        details = []
        if humidity is not None:
            details.append(f"H {int(humidity)}%")
        if wind is not None:
            details.append(f"V {round(float(wind) * 3.6)}km/h")
        if not details and status:
            details.append(status)
        draw.text((int(112 * s), int(170 * s)), "  ".join(details[:2]), fill=(130, 175, 215), font=self.font_small)

        sunrise = self._format_time(sun.get("sunrise"))
        sunset = self._format_time(sun.get("sunset"))
        center_text(draw, (int(70 * s), int(205 * s)), f"SOL {sunrise}", self.font_small, (255, 190, 100))
        center_text(draw, (int(170 * s), int(205 * s)), f"NOCHE {sunset}", self.font_small, (160, 185, 255))

        if is_night:
            moon_name = moon.get("name", "Luna")
            moon_font = fit_text(draw, moon_name.upper(), int(150 * s), 12 * s, 8 * s)
            center_text(draw, (cx, int(224 * s)), moon_name.upper(), moon_font, (205, 215, 245))
        elif alarm and alarm.get("enabled"):
            center_text(draw, (cx, int(224 * s)), f"ALARMA {alarm['hour']:02d}:{alarm['minute']:02d}",
                        self.font_small, (255, 170, 120))

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
            draw_weather_icon(draw, cx, int(78 * s), int(58 * s), "partly")

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
            top, bottom = (7, 11, 30), (25, 20, 58)
        elif period in ("sunrise", "sunset"):
            top, bottom = (38, 28, 68), (238, 116, 52)
        else:
            top, bottom = (13, 65, 110), (12, 22, 44)
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

    def _draw_sun_band(self, draw, sun):
        s = self.scale
        x1, x2 = int(41 * s), int(199 * s)
        y = int(190 * s)
        draw.line((x1, y, x2, y), fill=(60, 95, 130), width=int(3 * s))
        p = max(0.0, min(1.0, sun.get("progress", 0.0)))
        draw.line((x1, y, x1 + int((x2 - x1) * p), y), fill=(255, 190, 75), width=int(4 * s))
        sun_x = x1 + int((x2 - x1) * p)
        draw.ellipse((sun_x - 4 * s, y - 4 * s, sun_x + 4 * s, y + 4 * s), fill=(255, 230, 75))

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

