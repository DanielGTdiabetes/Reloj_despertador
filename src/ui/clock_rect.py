"""
Clock Screen - Rectangular display (76x284)
Shows time, date, day of week, and alarm status
"""

from PIL import Image, ImageDraw, ImageFont
import os

class ClockScreen:
    """UI for the rectangular ST7789 display"""

    WIDTH = 76
    HEIGHT = 284

    def __init__(self, renderer=None):
        self.renderer = renderer
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        self._load_fonts()

    def _load_fonts(self):
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        ]
        for path in font_paths:
            if os.path.exists(path):
                try:
                    self.font_large = ImageFont.truetype(path, 48)
                    self.font_medium = ImageFont.truetype(path, 28)
                    self.font_small = ImageFont.truetype(path, 18)
                    self.font_tiny = ImageFont.truetype(path, 14)
                    return
                except:
                    pass
        self.font_large = ImageFont.load_default()
        self.font_medium = ImageFont.load_default()
        self.font_small = ImageFont.load_default()
        self.font_tiny = ImageFont.load_default()

    def render_clock(self, time_str, date_str, day_str, alarm_enabled, alarm_time=None):
        if self.renderer:
            img = self.renderer.create_canvas((10, 10, 20))
        else:
            img = Image.new("RGB", (self.WIDTH, self.HEIGHT), (10, 10, 20))
        draw = ImageDraw.Draw(img)

        w, h = self.WIDTH, self.HEIGHT

        draw.rectangle((0, 0, w - 1, h - 1), outline=(40, 40, 60), width=2)

        time_bbox = draw.textbbox((0, 0), time_str, font=self.font_large)
        time_w = time_bbox[2] - time_bbox[0]
        time_x = (w - time_w) // 2
        draw.text((time_x, 20), time_str, fill=(255, 255, 255), font=self.font_large)

        date_bbox = draw.textbbox((0, 0), date_str, font=self.font_medium)
        date_w = date_bbox[2] - date_bbox[0]
        date_x = (w - date_w) // 2
        draw.text((date_x, 85), date_str, fill=(180, 180, 200), font=self.font_medium)

        day_bbox = draw.textbbox((0, 0), day_str, font=self.font_small)
        day_w = day_bbox[2] - day_bbox[0]
        day_x = (w - day_w) // 2
        draw.text((day_x, 120), day_str, fill=(120, 120, 140), font=self.font_small)

        draw.line([(10, 155), (w - 10, 155)], fill=(40, 40, 60), width=1)

        if alarm_enabled:
            alarm_text = "ALARM"
            alarm_bbox = draw.textbbox((0, 0), alarm_text, font=self.font_small)
            alarm_w = alarm_bbox[2] - alarm_bbox[0]
            alarm_x = (w - alarm_w) // 2
            draw.text((alarm_x, 165), alarm_text, fill=(255, 160, 50), font=self.font_small)

            if alarm_time:
                time_text = f"{alarm_time[0]:02d}:{alarm_time[1]:02d}"
                time_bbox = draw.textbbox((0, 0), time_text, font=self.font_medium)
                time_w = time_bbox[2] - time_bbox[0]
                time_x = (w - time_w) // 2
                draw.text((time_x, 195), time_text, fill=(255, 200, 100), font=self.font_medium)

            bell = "🔔"
            bell_bbox = draw.textbbox((0, 0), bell, font=self.font_small)
            bell_w = bell_bbox[2] - bell_bbox[0]
            bell_x = (w - bell_w) // 2
            draw.text((bell_x, 230), bell, fill=(255, 160, 50), font=self.font_small)
        else:
            off_text = "ALARMA OFF"
            off_bbox = draw.textbbox((0, 0), off_text, font=self.font_small)
            off_w = off_bbox[2] - off_bbox[0]
            off_x = (w - off_w) // 2
            draw.text((off_x, 180), off_text, fill=(80, 80, 100), font=self.font_small)

        if self.renderer:
            return self.renderer.render(img)
        return img

    def render_menu(self, items, selected_index, title="MENU"):
        if self.renderer:
            img = self.renderer.create_canvas((10, 10, 20))
        else:
            img = Image.new("RGB", (self.WIDTH, self.HEIGHT), (10, 10, 20))
        draw = ImageDraw.Draw(img)

        w, h = self.WIDTH, self.HEIGHT
        draw.rectangle((0, 0, w - 1, h - 1), outline=(40, 40, 60), width=2)

        title_bbox = draw.textbbox((0, 0), title, font=self.font_small)
        title_w = title_bbox[2] - title_bbox[0]
        title_x = (w - title_w) // 2
        draw.text((title_x, 8), title, fill=(255, 255, 255), font=self.font_small)
        draw.line([(5, 30), (w - 5, 30)], fill=(40, 40, 60), width=1)

        item_height = 35
        start_y = 40

        visible_items = min(6, len(items))
        if selected_index >= visible_items:
            offset = selected_index - visible_items + 1
        else:
            offset = 0

        for i in range(visible_items):
            idx = i + offset
            if idx >= len(items):
                break

            y = start_y + i * item_height
            item_text = items[idx]

            if idx == selected_index:
                draw.rectangle((3, y - 2, w - 3, y + item_height - 4), fill=(30, 30, 50), outline=(80, 140, 255), width=1)
                draw.text((10, y + 5), f"> {item_text}", fill=(255, 255, 255), font=self.font_small)
            else:
                draw.text((15, y + 5), item_text, fill=(150, 150, 170), font=self.font_small)

        if self.renderer:
            return self.renderer.render(img)
        return img

    def render_alarm_setting(self, hour, minute, enabled):
        if self.renderer:
            img = self.renderer.create_canvas((10, 10, 20))
        else:
            img = Image.new("RGB", (self.WIDTH, self.HEIGHT), (10, 10, 20))
        draw = ImageDraw.Draw(img)

        w, h = self.WIDTH, self.HEIGHT
        draw.rectangle((0, 0, w - 1, h - 1), outline=(40, 40, 60), width=2)

        title = "ALARMA"
        title_bbox = draw.textbbox((0, 0), title, font=self.font_small)
        title_w = title_bbox[2] - title_bbox[0]
        title_x = (w - title_w) // 2
        draw.text((title_x, 10), title, fill=(255, 255, 255), font=self.font_small)

        time_str = f"{hour:02d}:{minute:02d}"
        time_bbox = draw.textbbox((0, 0), time_str, font=self.font_large)
        time_w = time_bbox[2] - time_bbox[0]
        time_x = (w - time_w) // 2
        draw.text((time_x, 50), time_str, fill=(255, 200, 100), font=self.font_large)

        status = "ACTIVA" if enabled else "DESACTIVADA"
        status_color = (80, 220, 120) if enabled else (255, 80, 80)
        status_bbox = draw.textbbox((0, 0), status, font=self.font_medium)
        status_w = status_bbox[2] - status_bbox[0]
        status_x = (w - status_w) // 2
        draw.text((status_x, 120), status, fill=status_color, font=self.font_medium)

        hint = "Girar:Hora  Pulsar:OK"
        hint_bbox = draw.textbbox((0, 0), hint, font=self.font_tiny)
        hint_w = hint_bbox[2] - hint_bbox[0]
        hint_x = (w - hint_w) // 2
        draw.text((hint_x, 200), hint, fill=(100, 100, 120), font=self.font_tiny)

        if self.renderer:
            return self.renderer.render(img)
        return img
