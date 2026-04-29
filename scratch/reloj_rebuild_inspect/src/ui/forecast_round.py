"""
Forecast Screen - Weekly weather forecast for round display
"""

from PIL import Image, ImageDraw, ImageFont
import os
from graphics.renderer import Renderer
from graphics.colors import Colors

class ForecastScreen:
    """Weekly forecast UI for the circular GC9A01 display"""

    WIDTH = 240
    HEIGHT = 240

    DAY_NAMES_ES = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]

    def __init__(self, renderer=None):
        self.renderer = renderer or Renderer(self.WIDTH, self.HEIGHT)
        self.font_medium = None
        self.font_small = None
        self.font_tiny = None
        self._load_fonts()

    def _load_fonts(self):
        font_paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
        for path in font_paths:
            if os.path.exists(path):
                try:
                    self.font_medium = ImageFont.truetype(path, 28)
                    self.font_small = ImageFont.truetype(path, 18)
                    self.font_tiny = ImageFont.truetype(path, 14)
                    return
                except:
                    pass
        self.font_medium = ImageFont.load_default()
        self.font_small = ImageFont.load_default()
        self.font_tiny = ImageFont.load_default()

    def render_forecast(self, forecast_data):
        img = self.renderer.create_canvas(Colors.NIGHT_SKY)
        draw = ImageDraw.Draw(img)
        cx = self.WIDTH // 2

        title = "PREVISIÓN SEMANAL"
        title_bbox = draw.textbbox((0, 0), title, font=self.font_small)
        title_w = title_bbox[2] - title_bbox[0]
        draw.text((cx - title_w // 2, 5), title, fill=(255, 255, 255), font=self.font_small)

        draw.line([(5, 28), (self.WIDTH - 5, 28)], fill=(40, 40, 60), width=1)

        if not forecast_data:
            no_data = "Sin datos"
            nd_bbox = draw.textbbox((0, 0), no_data, font=self.font_medium)
            nd_w = nd_bbox[2] - nd_bbox[0]
            draw.text((cx - nd_w // 2, 100), no_data, fill=(150, 150, 170), font=self.font_medium)
            return self.renderer.render(img)

        row_height = 28
        start_y = 35
        max_rows = 7

        temps = [day.get("temp", {}).get("day", 0) for day in forecast_data[:max_rows]]
        min_temp = min(temps) if temps else 0
        max_temp = max(temps) if temps else 30
        temp_range = max(max_temp - min_temp, 1)

        for i, day in enumerate(forecast_data[:max_rows]):
            y = start_y + i * row_height
            if y + row_height > self.HEIGHT - 5:
                break

            dt = day.get("dt", 0)
            import datetime
            date = datetime.datetime.fromtimestamp(dt, tz=datetime.timezone.utc)
            day_name = self.DAY_NAMES_ES[date.weekday()]

            temp = day.get("temp", {}).get("day", 0)
            temp_min = day.get("temp", {}).get("min", 0)
            temp_max = day.get("temp", {}).get("max", 0)
            weather = day.get("weather", [{}])[0]
            icon = weather.get("icon", "")
            desc = weather.get("description", "")

            draw.text((5, y + 3), day_name, fill=(200, 200, 210), font=self.font_tiny)

            temp_str = f"{temp:.0f}°"
            t_bbox = draw.textbbox((0, 0), temp_str, font=self.font_small)
            t_w = t_bbox[2] - t_bbox[0]
            temp_color = (255, 100, 50) if temp > 30 else (80, 140, 255) if temp < 10 else (255, 255, 255)
            draw.text((50, y + 1), temp_str, fill=temp_color, font=self.font_small)

            bar_x = 100
            bar_width = 80
            bar_height = 8
            bar_y = y + 8

            min_ratio = (temp_min - min_temp) / temp_range
            max_ratio = (temp_max - min_temp) / temp_range
            draw.rectangle((bar_x, bar_y, bar_x + bar_width, bar_y + bar_height), fill=(40, 40, 60))
            draw.rectangle(
                (bar_x + int(min_ratio * bar_width), bar_y, bar_x + int(max_ratio * bar_width), bar_y + bar_height),
                fill=(255, 140, 50)
            )

            self._draw_mini_icon(draw, 195, y + 2, icon, 16)

        return self.renderer.render(img)

    def _draw_mini_icon(self, draw, x, y, icon_code, size):
        if "01" in icon_code:
            draw.ellipse((x, y, x + size, y + size), fill=(255, 220, 50))
        elif "02" in icon_code or "03" in icon_code or "04" in icon_code:
            draw.ellipse((x, y + size // 4, x + size, y + size * 3 // 4), fill=(180, 180, 190))
        elif "09" in icon_code or "10" in icon_code:
            draw.ellipse((x, y + size // 4, x + size, y + size * 3 // 4), fill=(150, 150, 170))
            for i in range(3):
                draw.line([(x + size // 4 + i * 4, y + size), (x + size // 4 + i * 4, y + size + 4)], fill=(100, 150, 255))
        elif "11" in icon_code:
            draw.polygon([(x + size // 2, y), (x + size, y + size // 2), (x + size // 2, y + size // 2), (x + size * 3 // 4, y + size), (x, y + size // 2), (x + size // 2, y + size // 2)], fill=(255, 255, 100))
        elif "13" in icon_code:
            draw.ellipse((x, y + size // 4, x + size, y + size * 3 // 4), fill=(200, 200, 220))
            draw.ellipse((x + size // 3, y + size, x + size // 3 + 4, y + size + 4), fill=(255, 255, 255))
        elif "50" in icon_code:
            for i in range(3):
                draw.line([(x, y + i * 4), (x + size, y + i * 4)], fill=(180, 180, 190), width=2)
