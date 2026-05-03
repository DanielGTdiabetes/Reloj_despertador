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

    def _draw_battery_indicator(self, img, battery_state) -> None:
        """Indicador de batería — lado derecho, simétrico al icono de alarma.

        Posición: X=177, Y=148 (espejo de la alarma en X=63, Y=148).
        Se dibuja solo si battery_state no es None (HAT presente y habilitado).

        Geometría:
          ┌──────────────────┬──┐
          │ relleno SOC %    │+ │  ← cuerpo 22×12 + polo derecho 3×6
          └──────────────────┴──┘
                  85%             ← texto porcentaje debajo
        """
        if battery_state is None:
            return

        draw = ImageDraw.Draw(img)
        soc   = battery_state.get("soc", 0) or 0
        level = battery_state.get("level", "ok")

        # Color según nivel de carga
        if level == "shutdown":
            # Parpadeo rojo crítico
            col = (255, 40, 40) if int(time.time() * 2) % 2 == 0 else (100, 0, 0)
        elif level == "critical":
            col = (255, 80, 20)   # naranja intenso
        elif level == "warning":
            col = (255, 200, 0)   # amarillo
        else:
            col = (60, 200, 80)   # verde normal

        # Centro del indicador (simétrico al icono de alarma)
        bx, by = 177, 145

        # Cuerpo de la batería: 22×12 px
        bw, bh = 22, 12
        x0, y0 = bx - bw // 2, by - bh // 2
        x1, y1 = x0 + bw, y0 + bh
        draw.rectangle([x0, y0, x1, y1], outline=col, width=1)

        # Polo positivo (+): 3×6 px pegado a la derecha
        px_w, px_h = 3, 6
        draw.rectangle([x1 + 1, by - px_h // 2, x1 + px_w, by + px_h // 2], fill=col)

        # Relleno interior proporcional al SOC
        inner_w = bw - 4   # margen interior 2 px por lado
        fill_w  = max(0, int(inner_w * min(100.0, soc) / 100.0))
        if fill_w > 0:
            draw.rectangle([x0 + 2, y0 + 2, x0 + 2 + fill_w, y1 - 2], fill=col)

        # Texto porcentaje
        pct_str = f"{soc:.0f}%"
        bb = draw.textbbox((0, 0), pct_str, font=F.small)
        tw = bb[2] - bb[0]
        draw.text((bx - tw // 2, y1 + 3), pct_str, font=F.small, fill=col)

    def render(self, now, weather, sun_info, moon, alarm, status, battery=None) -> Image.Image:
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

        # Indicador de Alarma LATERAL (izquierda)
        self._draw_sidebar_alarm(img, alarm)

        # Indicador de Batería LATERAL (derecha, simétrico a la alarma)
        self._draw_battery_indicator(img, battery)

        # Desc y Temp
        _text_center(draw, 178, desc[:22], F.small, DIM_WHITE)
        temp = weather.get("temp")
        _text_center(draw, 194, f"{temp:.1f}°C" if temp else "--.-°C", F.temp_big, th["temp"])

        return img

    def render_night(self, now, moon, alarm, sun_info=None, battery=None) -> Image.Image:
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

        # Indicador de batería (modo noche — esquina derecha)
        self._draw_battery_indicator(img, battery)

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
