"""
round_home.py — Margen de Seguridad para Descripciones.
Desplazado el texto inferior para evitar solapamientos con iconos grandes.
"""
from __future__ import annotations
import math
import time
import os
from PIL import Image, ImageDraw
from .theme import F, CYAN, PURPLE, BG, WHITE, DIM_WHITE, AMBER, YELLOW, ICONS, draw_menu_icon
from .weather_icons import draw_weather_icon, draw_moon

W = H = 240
CX = CY = 120
ARC_R = 114
ARC_THICK = 5

def _text_center(draw, y, text, font, fill):
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text(((W - (bb[2]-bb[0])) // 2, y), text, font=font, fill=fill)

class RoundHomeScreen:
    @staticmethod
    def _star_points(cx, cy, r_out, r_in, n=5, offset_deg=0):
        pts = []
        for i in range(n * 2):
            r = r_out if i % 2 == 0 else r_in
            a = math.radians(offset_deg + i * 180 / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return pts

    def _draw_seconds_ring(self, draw):
        # Usa time.time() para fracción de segundo → barrido suave a 5 FPS
        seconds = time.time() % 60.0
        angle = -90.0 + (seconds / 60.0) * 360.0

        box = [CX - ARC_R, CY - ARC_R, CX + ARC_R, CY + ARC_R]

        # Anillo base muy oscuro
        draw.arc(box, start=0, end=360, fill=(18, 22, 38), width=ARC_THICK)

        # Cola: últimos ~8 segundos (48°) en cyan tenue
        tail_start = int(angle) - 48
        draw.arc(box, start=tail_start, end=int(angle), fill=(0, 80, 130), width=ARC_THICK)

        # Estrella amarilla en la punta
        rad = math.radians(angle)
        sx = CX + ARC_R * math.cos(rad)
        sy = CY + ARC_R * math.sin(rad)
        star = self._star_points(sx, sy, r_out=5.5, r_in=2.2, n=5, offset_deg=-90)
        draw.polygon(star, fill=YELLOW)

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
                img.paste(icon, (ax - size//2, ay - size//2), icon)
            else:
                draw = ImageDraw.Draw(img)
                col = AMBER if enabled else (60, 65, 80)
                draw.text((ax-10, ay-10), "🔔" if enabled else "🔕", font=F.weather_sub, fill=col)
        except: pass

    def render(self, now, weather, sun_info, moon, alarm, status) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        self._draw_seconds_ring(draw)

        # 1. Fecha
        d_es = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"]
        m_es = ["ENE","FEB","MAR","ABR","MAY","JUN","JUL","AGO","SEP","OCT","NOV","DIC"]
        date_str = f"{d_es[now.weekday()]} {now.day} {m_es[now.month-1]}"
        _text_center(draw, 22, date_str, F.date_top, CYAN)

        # 2. Reloj
        _text_center(draw, 40, now.strftime("%H:%M"), F.clock, WHITE)

        # 3. Min / Max
        t_max = weather.get("temp_max") or 24
        t_min = weather.get("temp_min") or 14
        min_txt, max_txt = f"min {t_min:.0f}°", f"max {t_max:.0f}°"
        bb_min = draw.textbbox((0, 0), min_txt, font=F.weather_sub)
        bb_max = draw.textbbox((0, 0), max_txt, font=F.weather_sub)
        total_mm = (bb_min[2]-bb_min[0]) + (bb_max[2]-bb_max[0]) + 20
        start_mm = (W - total_mm) // 2
        draw.text((start_mm, 108), min_txt, font=F.weather_sub, fill=CYAN)
        draw.text((start_mm + (bb_min[2]-bb_min[0]) + 20, 108), max_txt, font=F.weather_sub, fill=AMBER)

        # 4. Icono Central (Posición fija)
        desc = (weather.get("description") or "").upper()
        draw_weather_icon(img, desc, CX, 140, size=55)

        # 5. Indicador de Alarma LATERAL
        self._draw_sidebar_alarm(img, alarm)

        # 6. Desc y Temp (Bajamos 5-8 píxeles para que no toquen el icono)
        _text_center(draw, 178, desc[:22], F.small, DIM_WHITE)
        temp = weather.get("temp")
        _text_center(draw, 194, f"{temp:.1f}\u00b0C" if temp else "--.-°C", F.temp_big, CYAN)

        return img

    def render_night(self, now, moon, alarm, sun_info=None) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        self._draw_seconds_ring(draw)
        _text_center(draw, 45, now.strftime("%H:%M"), F.clock, WHITE)
        draw_moon(img, CX, CY + 35, r=35, phase_frac=moon.get("phase", 0.5))
        return img

    def render_focus(self, title, subtitle, kind="", value=None) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        
        # Icono un poco más pequeño y centrado
        icon_size = 50
        draw_menu_icon(draw, CX - icon_size//2, CY - 80, icon_size, kind)
        
        # Título en tamaño mediano
        _text_center(draw, CY - 10, title.upper(), F.date_top, WHITE)
        
        # Valor en tamaño intermedio (temp_big = 26px), no el gigante del reloj
        if value:
            _text_center(draw, CY + 25, str(value).upper(), F.temp_big, CYAN)
            
        # Subtítulo pequeño abajo
        if subtitle:
            _text_center(draw, CY + 60, subtitle, F.small, DIM_WHITE)
            
        return img

    def render_alarm_ringing(self) -> Image.Image:
        # Fondo rojo parpadeante
        img = Image.new("RGB", (W, H), (200, 0, 0) if int(time.time()*2)%2==0 else BG)
        draw = ImageDraw.Draw(img)
        
        # Texto "ALARMA" con la nueva fuente de 45px centrada
        _text_center(draw, CY - 25, "ALARMA", F.alarm_ringing, WHITE)
        
        # Instrucción pequeña abajo
        _text_center(draw, CY + 30, "PULSA PARA DETENER", F.small, WHITE)
        
        return img
