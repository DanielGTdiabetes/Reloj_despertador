"""
Weather Screen - Round display (240x240)
Shows weather status, sunrise/sunset, moon phase
"""

from PIL import Image, ImageDraw, ImageFont
import os
import math
from graphics.renderer import Renderer
from graphics.colors import Colors

class WeatherRoundScreen:
    """UI for the circular GC9A01 display"""

    WIDTH = 240
    HEIGHT = 240
    CENTER = 120

    def __init__(self, renderer=None):
        self.renderer = renderer or Renderer(self.WIDTH, self.HEIGHT)
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        self._load_fonts()

    def _load_fonts(self):
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        for path in font_paths:
            if os.path.exists(path):
                try:
                    self.font_large = ImageFont.truetype(path, 48)
                    self.font_medium = ImageFont.truetype(path, 32)
                    self.font_small = ImageFont.truetype(path, 20)
                    self.font_tiny = ImageFont.truetype(path, 16)
                    return
                except:
                    pass
        self.font_large = ImageFont.load_default()
        self.font_medium = ImageFont.load_default()
        self.font_small = ImageFont.load_default()
        self.font_tiny = ImageFont.load_default()

    def render_sunrise(self, progress, sunrise_time, sunset_time, temp, condition, icon):
        img = self.renderer.create_canvas(Colors.NIGHT_SKY)
        draw = ImageDraw.Draw(img)
        cx, cy = self.CENTER, self.CENTER
        r = 100

        is_day = 0.1 < progress < 0.9
        if is_day:
            sky_top = (100, 150, 220)
            sky_bottom = (170, 200, 240)
        else:
            sky_top = (10, 10, 30)
            sky_bottom = (20, 20, 50)

        for y in range(self.renderer.render_height):
            t = y / self.renderer.render_height
            cr = int(sky_top[0] + (sky_bottom[0] - sky_top[0]) * t)
            cg = int(sky_top[1] + (sky_bottom[1] - sky_top[1]) * t)
            cb = int(sky_top[2] + (sky_bottom[2] - sky_top[2]) * t)
            draw.line([(0, y), (self.renderer.render_width, y)], fill=(cr, cg, cb))

        if is_day:
            sun_progress = progress
            sun_angle = math.pi * (1 - sun_progress)
            sun_x = cx + int(r * 0.8 * math.cos(sun_angle))
            sun_y = cy - int(r * 0.8 * math.sin(sun_progress * math.pi))
            self.renderer.draw_sun(draw, sun_x, sun_y, 25)

        draw.arc(
            (cx - r, cy - r, cx + r, cy + r),
            180, 360,
            fill=(255, 140, 50),
            width=3
        )

        if progress > 0:
            fill_angle = 180 + int(progress * 180)
            for angle in range(180, fill_angle):
                rad = angle * math.pi / 180
                x1 = cx + int((r - 5) * math.cos(rad))
                y1 = cy + int((r - 5) * math.sin(rad))
                x2 = cx + int((r + 5) * math.cos(rad))
                y2 = cy + int((r + 5) * math.sin(rad))
                draw.line([(x1, y1), (x2, y2)], fill=(255, 180, 80))

        horizon_y = cy + 10
        draw.rectangle((0, horizon_y, self.renderer.render_width, self.renderer.render_height), fill=(30, 50, 30))

        temp_str = f"{temp:.0f}°C"
        temp_bbox = draw.textbbox((0, 0), temp_str, font=self.font_medium)
        temp_w = temp_bbox[2] - temp_bbox[0]
        draw.text((cx - temp_w // 2, 15), temp_str, fill=(255, 255, 255), font=self.font_medium)

        cond_bbox = draw.textbbox((0, 0), condition.title(), font=self.font_tiny)
        cond_w = cond_bbox[2] - cond_bbox[0]
        draw.text((cx - cond_w // 2, 45), condition.title(), fill=(200, 200, 210), font=self.font_tiny)

        sunrise_str = sunrise_time.strftime("%H:%M") if hasattr(sunrise_time, 'strftime') else str(sunrise_time)[:5]
        sunset_str = sunset_time.strftime("%H:%M") if hasattr(sunset_time, 'strftime') else str(sunset_time)[:5]

        draw.text((10, self.renderer.render_height - 40), f"↑{sunrise_str}", fill=(255, 200, 100), font=self.font_tiny)
        ss_bbox = draw.textbbox((0, 0), f"↓{sunset_str}", font=self.font_tiny)
        ss_w = ss_bbox[2] - ss_bbox[0]
        draw.text((self.renderer.render_width - ss_w - 10, self.renderer.render_height - 40), f"↓{sunset_str}", fill=(255, 140, 50), font=self.font_tiny)

        return self.renderer.render(img)

    def render_moon(self, phase_index, phase_name, illumination):
        img = self.renderer.create_canvas(Colors.NIGHT_SKY)
        draw = ImageDraw.Draw(img)
        cx, cy = self.CENTER, self.CENTER

        for i in range(50):
            x = (i * 137) % self.renderer.render_width
            y = (i * 97) % self.renderer.render_height
            brightness = 100 + (i % 3) * 50
            draw.ellipse((x, y, x + 2, y + 2), fill=(brightness, brightness, brightness + 20))

        moon_radius = 60
        phase_value = phase_index / 8.0
        self.renderer.draw_moon(draw, cx, cy - 20, moon_radius, phase=phase_value)

        phase_bbox = draw.textbbox((0, 0), phase_name, font=self.font_small)
        phase_w = phase_bbox[2] - phase_bbox[0]
        draw.text((cx - phase_w // 2, cy + 60), phase_name, fill=(200, 200, 220), font=self.font_small)

        illum_str = f"{illumination:.0f}%"
        illum_bbox = draw.textbbox((0, 0), illum_str, font=self.font_tiny)
        illum_w = illum_bbox[2] - illum_bbox[0]
        draw.text((cx - illum_w // 2, cy + 90), illum_str, fill=(150, 150, 170), font=self.font_tiny)

        return self.renderer.render(img)

    def render_weather_icon(self, condition, temp, humidity, wind):
        img = self.renderer.create_canvas(Colors.NIGHT_SKY)
        draw = ImageDraw.Draw(img)
        cx, cy = self.CENTER, self.CENTER

        is_daytime = condition.lower() in ["clear", "sun", "few clouds", "scattered clouds"]
        if is_daytime:
            sky_top = (100, 150, 220)
            sky_bottom = (170, 200, 240)
        else:
            sky_top = (10, 10, 30)
            sky_bottom = (20, 20, 50)

        for y in range(self.renderer.render_height):
            t = y / self.renderer.render_height
            cr = int(sky_top[0] + (sky_bottom[0] - sky_top[0]) * t)
            cg = int(sky_top[1] + (sky_bottom[1] - sky_top[1]) * t)
            cb = int(sky_top[2] + (sky_bottom[2] - sky_top[2]) * t)
            draw.line([(0, y), (self.renderer.render_width, y)], fill=(cr, cg, cb))

        self.renderer.draw_weather_icon(draw, cx, cy - 20, 120, condition)

        temp_str = f"{temp:.0f}°C"
        temp_bbox = draw.textbbox((0, 0), temp_str, font=self.font_medium)
        temp_w = temp_bbox[2] - temp_bbox[0]
        draw.text((cx - temp_w // 2, cy + 50), temp_str, fill=(255, 255, 255), font=self.font_medium)

        details = f"H:{humidity:.0f}%  V:{wind:.1f}km/h"
        det_bbox = draw.textbbox((0, 0), details, font=self.font_tiny)
        det_w = det_bbox[2] - det_bbox[0]
        draw.text((cx - det_w // 2, cy + 85), details, fill=(150, 150, 170), font=self.font_tiny)

        return self.renderer.render(img)

    def render_alert(self, alert):
        img = self.renderer.create_canvas(Colors.NIGHT_SKY)
        draw = ImageDraw.Draw(img)
        cx, cy = self.CENTER, self.CENTER

        for i in range(8):
            y = i * (self.renderer.render_height // 8)
            color = alert["color"] if i % 2 == 0 else Colors.NIGHT_SKY
            draw.rectangle((0, y, self.renderer.render_width, y + self.renderer.render_height // 8), fill=color)

        alert_icon = "⚠"
        icon_bbox = draw.textbbox((0, 0), alert_icon, font=self.font_large)
        icon_w = icon_bbox[2] - icon_bbox[0]
        draw.text((cx - icon_w // 2, 30), alert_icon, fill=(255, 255, 255), font=self.font_large)

        msg = alert.get("message", "")
        msg_bbox = draw.textbbox((0, 0), msg, font=self.font_medium)
        msg_w = msg_bbox[2] - msg_bbox[0]
        draw.text((cx - msg_w // 2, cy - 10), msg, fill=(255, 255, 255), font=self.font_medium)

        level = alert.get("level", "low").upper()
        level_bbox = draw.textbbox((0, 0), level, font=self.font_small)
        level_w = level_bbox[2] - level_bbox[0]
        draw.text((cx - level_w // 2, cy + 30), level, fill=alert["color"], font=self.font_small)

        return self.renderer.render(img)
