from __future__ import annotations
import math
import time
import random
import os
from PIL import Image, ImageDraw
from .theme import F, CYAN, PURPLE, BG, WHITE, DIM_WHITE, AMBER, YELLOW, ICONS, draw_menu_icon
from .weather_icons import draw_weather_icon, draw_moon

W = H = 240
CX = CY = 120
ARC_R = 114
ARC_THICK = 5

# Estrellas fijas para el modo noche (seed determinista = sin parpadeo)
_rng = random.Random(42)
_STARS = [
    (
        _rng.randint(2, W - 3),
        _rng.randint(2, H - 3),
        _rng.choice([0, 0, 0, 0, 1, 1, 2]),          # radio: mayoría puntitos
        _rng.randint(140, 255),                        # brillo
        _rng.choice([(1.0, 1.0, 1.0), (0.85, 0.9, 1.0), (1.0, 1.0, 0.88)]),  # tinte
    )
    for _ in range(75)
]


def _text_center(draw, y, text, font, fill):
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text(((W - (bb[2] - bb[0])) // 2, y), text, font=font, fill=fill)


class RoundHomeScreen:
    def __init__(self):
        self._last_period: str | None = None

    @staticmethod
    def _star_points(cx, cy, r_out, r_in, n=5, offset_deg=0):
        pts = []
        for i in range(n * 2):
            r = r_out if i % 2 == 0 else r_in
            a = math.radians(offset_deg + i * 180 / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return pts

    @staticmethod
    def _period_theme(period):
        if period == "sunrise":
            return {
                "bg":        (18, 10, 4),
                "clock":     (255, 210, 110),
                "date":      AMBER,
                "ring_tail": (110, 55, 8),
                "ring_tip":  (255, 200, 0),
                "temp":      AMBER,
            }
        elif period == "sunset":
            return {
                "bg":        (18, 6, 14),
                "clock":     (255, 150, 70),
                "date":      (220, 100, 50),
                "ring_tail": (110, 30, 8),
                "ring_tip":  (255, 110, 20),
                "temp":      (255, 140, 60),
            }
        else:
            return {
                "bg":        BG,
                "clock":     WHITE,
                "date":      CYAN,
                "ring_tail": (0, 80, 130),
                "ring_tip":  YELLOW,
                "temp":      CYAN,
            }

    def _draw_seconds_ring(self, draw, tail_col=(0, 80, 130), tip_col=YELLOW):
        seconds = time.time() % 60.0
        angle = -90.0 + (seconds / 60.0) * 360.0

        box = [CX - ARC_R, CY - ARC_R, CX + ARC_R, CY + ARC_R]
        draw.arc(box, start=0, end=360, fill=(18, 22, 38), width=ARC_THICK)

        tail_start = int(angle) - 48
        draw.arc(box, start=tail_start, end=int(angle), fill=tail_col, width=ARC_THICK)

        rad = math.radians(angle)
        sx = CX + ARC_R * math.cos(rad)
        sy = CY + ARC_R * math.sin(rad)
        star = self._star_points(sx, sy, r_out=5.5, r_in=2.2, n=5, offset_deg=-90)
        draw.polygon(star, fill=tip_col)

    def _draw_sidebar_alarm(self, img, alarm):
        enabled = alarm.get("enabled", False)
        ax, ay = 63, 148
        size = 24
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "menu_icons", "alarm.png")
            if os.path.exists(icon_path):
                icon = Image.open(icon_path).convert("RGBA").resize((size, size))
                if not enabled:
                    alpha = icon.getchannel('A')
                    icon = Image.new("RGBA", (size, size), (60, 65, 80, 255))
                    icon.putalpha(alpha)
                img.paste(icon, (ax - size // 2, ay - size // 2), icon)
            else:
                draw = ImageDraw.Draw(img)
                col = AMBER if enabled else (60, 65, 80)
                draw.text((ax - 10, ay - 10), "A" if enabled else "a", font=F.weather_sub, fill=col)
        except Exception:
            pass

    def _draw_night_stars(self, draw):
        for (x, y, r, brightness, tint) in _STARS:
            color = tuple(int(brightness * t) for t in tint)
            if r == 0:
                draw.point((x, y), fill=color)
            else:
                draw.ellipse([x - r, y - r, x + r, y + r], fill=color)

    def render(self, now, weather, sun_info, moon, alarm, status) -> Image.Image:
        period = sun_info.get("period", "day")
        th = self._period_theme(period)

        # Blank frame on period change to prevent LCD ghost retention
        if period != self._last_period:
            self._last_period = period
            return Image.new("RGB", (W, H), BG)

        img = Image.new("RGB", (W, H), th["bg"])
        draw = ImageDraw.Draw(img)
        self._draw_seconds_ring(draw, tail_col=th["ring_tail"], tip_col=th["ring_tip"])

        # Fecha
        d_es = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"]
        m_es = ["ENE","FEB","MAR","ABR","MAY","JUN","JUL","AGO","SEP","OCT","NOV","DIC"]
        date_str = f"{d_es[now.weekday()]} {now.day} {m_es[now.month-1]}"
        _text_center(draw, 22, date_str, F.date_top, th["date"])

        # Reloj
        _text_center(draw, 40, now.strftime("%H:%M"), F.clock, th["clock"])

        # Min / Max
        t_max = weather.get("temp_max") or 24
        t_min = weather.get("temp_min") or 14
        min_txt, max_txt = f"min {t_min:.0f}°", f"max {t_max:.0f}°"
        bb_min = draw.textbbox((0, 0), min_txt, font=F.weather_sub)
        bb_max = draw.textbbox((0, 0), max_txt, font=F.weather_sub)
        total_mm = (bb_min[2] - bb_min[0]) + (bb_max[2] - bb_max[0]) + 20
        start_mm = (W - total_mm) // 2
        draw.text((start_mm, 108), min_txt, font=F.weather_sub, fill=CYAN)
        draw.text((start_mm + (bb_min[2] - bb_min[0]) + 20, 108), max_txt, font=F.weather_sub, fill=AMBER)

        # Icono Central
        desc = (weather.get("description") or "").upper()
        draw_weather_icon(img, desc, CX, 152, size=50)

        # Indicador de Alarma LATERAL
        self._draw_sidebar_alarm(img, alarm)

        # Desc y Temp
        _text_center(draw, 178, desc[:22], F.small, DIM_WHITE)
        temp = weather.get("temp")
        _text_center(draw, 194, f"{temp:.1f}°C" if temp else "--.-°C", F.temp_big, th["temp"])

        return img

    def render_night(self, now, moon, alarm, sun_info=None) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # Estrellas de fondo
        self._draw_night_stars(draw)

        self._draw_seconds_ring(draw)

        # Hora
        _text_center(draw, 38, now.strftime("%H:%M"), F.clock, WHITE)

        # Luna (PNG con fondo eliminado, tamaño generoso para mostrar glow)
        phase_frac = moon.get("phase", 0.5)
        draw_moon(img, CX, CY + 32, r=38, phase_frac=phase_frac)

        # Nombre de fase
        phase_name = moon.get("phase_name", "")
        if phase_name:
            _text_center(draw, 200, phase_name, F.small, PURPLE)

        return img

    def render_focus(self, title, subtitle, kind="", value=None) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        icon_size = 50
        draw_menu_icon(draw, CX - icon_size // 2, CY - 80, icon_size, kind)

        _text_center(draw, CY - 10, title.upper(), F.date_top, WHITE)

        if value:
            _text_center(draw, CY + 25, str(value).upper(), F.temp_big, CYAN)

        if subtitle:
            _text_center(draw, CY + 60, subtitle, F.small, DIM_WHITE)

        return img

    def render_alarm_ringing(self) -> Image.Image:
        img = Image.new("RGB", (W, H), (200, 0, 0) if int(time.time() * 2) % 2 == 0 else BG)
        draw = ImageDraw.Draw(img)
        _text_center(draw, CY - 25, "ALARMA", F.alarm_ringing, WHITE)
        _text_center(draw, CY + 30, "PULSA PARA DETENER", F.small, WHITE)
        return img
