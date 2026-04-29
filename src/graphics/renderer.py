"""
Graphics Renderer - High-quality 2x rendering pipeline
All graphics are drawn at 2x resolution then downscaled with LANCZOS for anti-aliasing
"""

from PIL import Image, ImageDraw, ImageFont
import os
import math

class Renderer:
    """High-quality graphics renderer with 2x anti-aliasing pipeline"""

    def __init__(self, width, height, scale=2):
        self.width = width
        self.height = height
        self.scale = scale
        self.render_width = width * scale
        self.render_height = height * scale

    def create_canvas(self, color=(0, 0, 0)):
        return Image.new("RGB", (self.render_width, self.render_height), color)

    def get_draw(self, image):
        return ImageDraw.Draw(image)

    def render(self, image):
        if image.size == (self.render_width, self.render_height):
            return image.resize((self.width, self.height), Image.LANCZOS)
        return image

    def draw_gradient_rect(self, draw, x1, y1, x2, y2, color1, color2, vertical=True):
        w = x2 - x1
        h = y2 - y1
        for i in range(h if vertical else w):
            t = i / max(h if vertical else w, 1)
            r = int(color1[0] + (color2[0] - color1[0]) * t)
            g = int(color1[1] + (color2[1] - color1[1]) * t)
            b = int(color1[2] + (color2[2] - color1[2]) * t)
            if vertical:
                draw.line([(x1, y1 + i), (x2, y1 + i)], fill=(r, g, b))
            else:
                draw.line([(x1 + i, y1), (x1 + i, y2)], fill=(r, g, b))

    def draw_smooth_circle(self, draw, cx, cy, radius, fill=None, outline=None, width=1):
        draw.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            fill=fill,
            outline=outline,
            width=width
        )

    def draw_sun(self, draw, cx, cy, radius):
        glow_radius = int(radius * 1.5)
        for i in range(glow_radius, radius - 5, -2):
            alpha_factor = 1 - (i - radius) / (glow_radius - radius + 5)
            r = int(255 * alpha_factor)
            g = int(200 * alpha_factor)
            b = int(50 * alpha_factor)
            draw.ellipse(
                (cx - i, cy - i, cx + i, cy + i),
                fill=(r, g, b)
            )

        draw.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            fill=(255, 220, 50)
        )

        inner_radius = int(radius * 0.7)
        draw.ellipse(
            (cx - inner_radius, cy - inner_radius, cx + inner_radius, cy + inner_radius),
            fill=(255, 240, 120)
        )

        num_rays = 12
        ray_length = int(radius * 0.5)
        ray_start = radius + 5
        for i in range(num_rays):
            angle = (i * 360 / num_rays) * math.pi / 180
            x1 = cx + int(ray_start * math.cos(angle))
            y1 = cy + int(ray_start * math.sin(angle))
            x2 = cx + int((ray_start + ray_length) * math.cos(angle))
            y2 = cy + int((ray_start + ray_length) * math.sin(angle))
            draw.line([(x1, y1), (x2, y2)], fill=(255, 220, 50), width=int(radius * 0.12))

    def draw_cloud(self, draw, cx, cy, size, fill=(200, 200, 210), outline=None):
        s = size
        draw.ellipse((cx - s, cy - s // 2, cx + s, cy + s // 2), fill=fill, outline=outline)
        draw.ellipse((cx - s // 2 - s // 3, cy - s // 3 - s // 4, cx - s // 2 + s // 3, cy + s // 4), fill=fill)
        draw.ellipse((cx - s // 4, cy - s // 2 - s // 4, cx + s // 4, cy - s // 4), fill=fill)
        draw.ellipse((cx + s // 3, cy - s // 3 - s // 5, cx + s // 3 + s // 2, cy + s // 5), fill=fill)

    def draw_rain_cloud(self, draw, cx, cy, size, num_drops=5):
        self.draw_cloud(draw, cx, cy - size // 4, size, fill=(150, 150, 170))

        drop_start_y = cy + size // 4
        drop_length = size // 2
        spacing = size // (num_drops + 1)
        for i in range(num_drops):
            dx = cx - size // 2 + spacing * (i + 1)
            dy = drop_start_y + (i % 2) * size // 6
            draw.line([(dx, dy), (dx, dy + drop_length)], fill=(100, 150, 255), width=int(size * 0.06))
            draw.ellipse((dx - 2, dy + drop_length - 2, dx + 2, dy + drop_length + 2), fill=(100, 150, 255))

    def draw_thunder(self, draw, cx, cy, size):
        self.draw_rain_cloud(draw, cx, cy - size // 3, size)

        bolt_points = [
            (cx - size // 8, cy),
            (cx + size // 8, cy + size // 4),
            (cx - size // 12, cy + size // 4),
            (cx + size // 6, cy + size // 2),
            (cx - size // 8, cy + size // 3),
            (cx + size // 12, cy + size // 3),
            (cx - size // 6, cy)
        ]
        draw.polygon(bolt_points, fill=(255, 255, 100))
        draw.polygon(bolt_points, outline=(255, 200, 50), width=2)

    def draw_snow(self, draw, cx, cy, size, num_flakes=6):
        self.draw_cloud(draw, cx, cy - size // 4, size, fill=(180, 180, 200))

        for i in range(num_flakes):
            fx = cx - size // 2 + (size // (num_flakes + 1)) * (i + 1)
            fy = cy + size // 4 + (i % 3) * size // 8
            self._draw_snowflake(draw, fx, fy, size // 8)

    def _draw_snowflake(self, draw, cx, cy, size):
        for angle in range(0, 360, 60):
            rad = angle * math.pi / 180
            x = cx + int(size * math.cos(rad))
            y = cy + int(size * math.sin(rad))
            draw.line([(cx, cy), (x, y)], fill=(255, 255, 255), width=max(1, size // 6))

    def draw_wind(self, draw, cx, cy, size, num_lines=4):
        for i in range(num_lines):
            y = cy - size // 2 + (size // (num_lines + 1)) * (i + 1)
            points = []
            for x in range(cx - size, cx + size, 5):
                offset = math.sin((x - cx) * 0.05 + i) * size // 4
                points.append((x, y + int(offset)))
            if len(points) > 1:
                draw.line(points, fill=(180, 200, 220), width=int(size * 0.08))

    def draw_fog(self, draw, cx, cy, size, num_lines=5):
        for i in range(num_lines):
            y = cy - size // 2 + (size // (num_lines - 1)) * i
            w = size * (0.8 + 0.2 * math.sin(i * 0.5))
            points = []
            for x in range(int(cx - w), int(cx + w), 4):
                offset = math.sin((x - cx) * 0.03 + i * 0.8) * size // 6
                points.append((x, y + int(offset)))
            if len(points) > 1:
                draw.line(points, fill=(180, 180, 190), width=int(size * 0.1))

    def draw_moon(self, draw, cx, cy, radius, phase=0.5):
        glow_radius = int(radius * 1.3)
        for i in range(glow_radius, radius - 3, -2):
            alpha = 1 - (i - radius) / (glow_radius - radius + 3)
            r = int(200 * alpha)
            g = int(200 * alpha)
            b = int(230 * alpha)
            draw.ellipse((cx - i, cy - i, cx + i, cy + i), fill=(r, g, b))

        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(220, 220, 240))

        shadow_offset = int(radius * (1 - 2 * abs(phase - 0.5)))
        if phase < 0.5:
            draw.ellipse(
                (cx - radius + shadow_offset, cy - radius, cx + radius + shadow_offset, cy + radius),
                fill=(10, 10, 30)
            )
        else:
            draw.ellipse(
                (cx - radius - shadow_offset, cy - radius, cx + radius - shadow_offset, cy + radius),
                fill=(10, 10, 30)
            )

        craters = [
            (cx - radius // 3, cy - radius // 4, radius // 6),
            (cx + radius // 4, cy + radius // 3, radius // 8),
            (cx + radius // 6, cy - radius // 2, radius // 10),
        ]
        for ccx, ccy, cr in craters:
            draw.ellipse((ccx - cr, ccy - cr, ccx + cr, ccy + cr), fill=(200, 200, 220))

    def draw_sunrise_arc(self, draw, cx, cy, radius, progress, time_of_day):
        if progress <= 0:
            return

        bg_color = (10, 10, 30) if time_of_day == "night" else (135, 170, 220)
        draw.rectangle((0, 0, self.render_width, self.render_height), fill=bg_color)

        draw.arc(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            180, 180 + int(progress * 180),
            fill=(255, 140, 50),
            width=int(radius * 0.08)
        )

        if progress > 0.1:
            sun_cx = cx + int(radius * math.cos(math.pi * (1 - progress)))
            sun_cy = cy - int(radius * math.sin(math.pi * progress))
            sun_radius = int(radius * 0.2)
            self.draw_sun(draw, sun_cx, sun_cy, sun_radius)

        horizon_y = cy
        draw.rectangle((0, horizon_y, self.render_width, self.render_height), fill=(30, 50, 30))

    def draw_weather_icon(self, draw, cx, cy, size, condition):
        condition = condition.lower()
        if "sun" in condition or "clear" in condition:
            self.draw_sun(draw, cx, cy, size // 2)
        elif "cloud" in condition and ("rain" in condition or "drizzle" in condition):
            self.draw_rain_cloud(draw, cx, cy, size // 2)
        elif "cloud" in condition and ("thunder" in condition or "storm" in condition):
            self.draw_thunder(draw, cx, cy, size // 2)
        elif "cloud" in condition and ("snow" in condition or "sleet" in condition):
            self.draw_snow(draw, cx, cy, size // 2)
        elif "cloud" in condition:
            self.draw_cloud(draw, cx, cy, size // 2)
        elif "rain" in condition or "drizzle" in condition:
            self.draw_rain_cloud(draw, cx, cy, size // 2)
        elif "snow" in condition or "sleet" in condition:
            self.draw_snow(draw, cx, cy, size // 2)
        elif "thunder" in condition or "storm" in condition:
            self.draw_thunder(draw, cx, cy, size // 2)
        elif "mist" in condition or "fog" in condition:
            self.draw_fog(draw, cx, cy, size // 2)
        elif "wind" in condition:
            self.draw_wind(draw, cx, cy, size // 2)
        else:
            self.draw_sun(draw, cx, cy, size // 2)

    def draw_temperature_bar(self, draw, x, y, width, height, temp, min_temp, max_temp):
        ratio = max(0, min(1, (temp - min_temp) / max(max_temp - min_temp, 1)))
        filled_width = int(width * ratio)

        color1 = (100, 150, 255)
        color2 = (255, 100, 50)
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)

        draw.rectangle((x, y, x + width, y + height), outline=(100, 100, 120), width=2)
        if filled_width > 0:
            self.draw_gradient_rect(draw, x + 1, y + 1, x + filled_width - 1, y + height - 1, color1, (r, g, b))
