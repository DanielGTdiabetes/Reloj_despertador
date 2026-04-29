import math
import os
from PIL import Image, ImageDraw, ImageFont


FONT_CANDIDATES = [
    os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "arialbd.ttf"),
    os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "arial.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def load_font(size, bold=True):
    for path in FONT_CANDIDATES:
        if not os.path.exists(path):
            continue
        if bold and ("Bold" not in path and "arialbd" not in path):
            continue
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def text_size(draw, text, font):
    box = draw.textbbox((0, 0), str(text), font=font)
    return box[2] - box[0], box[3] - box[1]


def center_text(draw, xy, text, font, fill, anchor="mm"):
    draw.text(xy, str(text), fill=fill, font=font, anchor=anchor)


def fit_text(draw, text, max_width, start_size, min_size=8, bold=True):
    text = str(text)
    for size in range(start_size, min_size - 1, -1):
        font = load_font(size, bold=bold)
        if text_size(draw, text, font)[0] <= max_width:
            return font
    return load_font(min_size, bold=bold)


def gradient(size, top, bottom):
    width, height = size
    img = Image.new("RGB", size, top)
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / max(1, height - 1)
        color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        draw.line((0, y, width, y), fill=color)
    return img


def round_mask(size):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size[0] - 1, size[1] - 1), fill=255)
    return mask


def apply_round_mask(img):
    bg = Image.new("RGB", img.size, (0, 0, 0))
    return Image.composite(img, bg, round_mask(img.size))


def condition_kind(text):
    desc = (text or "").lower()
    if any(x in desc for x in ("storm", "thunder", "tormenta", "trueno")):
        return "storm"
    if any(x in desc for x in ("snow", "nieve", "nevada")):
        return "snow"
    if any(x in desc for x in ("rain", "drizzle", "lluv", "chubasco")):
        return "rain"
    if any(x in desc for x in ("fog", "mist", "haze", "niebla", "bruma")):
        return "fog"
    if any(x in desc for x in ("cloud", "nube", "nublado", "nuboso", "overcast", "cubierto")):
        if any(x in desc for x in ("few", "scattered", "parcial", "intervalos")):
            return "partly"
        return "cloud"
    if any(x in desc for x in ("clear", "sun", "despejado", "soleado")):
        return "sun"
    return "partly"


def draw_sun(draw, cx, cy, radius):
    for i in range(12):
        a = math.radians(i * 30)
        x1 = cx + math.cos(a) * (radius + 5)
        y1 = cy + math.sin(a) * (radius + 5)
        x2 = cx + math.cos(a) * (radius + 14)
        y2 = cy + math.sin(a) * (radius + 14)
        draw.line((x1, y1, x2, y2), fill=(255, 210, 20), width=max(2, radius // 6))
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(255, 224, 35))
    inner = int(radius * 0.58)
    draw.ellipse((cx - inner, cy - inner, cx + inner, cy + inner), fill=(255, 246, 120))


def draw_cloud(draw, cx, cy, radius, fill=(225, 232, 246)):
    r = radius
    draw.ellipse((cx - r - 8, cy - 1, cx + 4, cy + r + 3), fill=fill)
    draw.ellipse((cx - r // 2 - 7, cy - r, cx + r // 2 + 7, cy + 4), fill=fill)
    draw.ellipse((cx, cy - 8, cx + r + 10, cy + r + 2), fill=fill)
    draw.rectangle((cx - r - 4, cy + 1, cx + r + 7, cy + r + 2), fill=fill)


def draw_rain(draw, cx, cy, radius):
    draw_cloud(draw, cx, cy - radius // 2, radius, fill=(185, 202, 226))
    for i, dx in enumerate((-14, -5, 5, 14)):
        y = cy + 8 + (i % 2) * 5
        draw.line((cx + dx, y, cx + dx - 4, y + 13), fill=(70, 180, 255), width=3)
        draw.ellipse((cx + dx - 6, y + 10, cx + dx - 1, y + 16), fill=(70, 180, 255))


def draw_storm(draw, cx, cy, radius):
    draw_cloud(draw, cx, cy - radius // 2, radius, fill=(158, 170, 195))
    pts = [
        (cx - 4, cy + 2), (cx - 13, cy + 22), (cx - 2, cy + 19),
        (cx - 10, cy + 40), (cx + 14, cy + 12), (cx + 2, cy + 15),
    ]
    draw.polygon(pts, fill=(255, 232, 30))
    draw.line(pts, fill=(255, 255, 190), width=2)


def draw_snow(draw, cx, cy, radius):
    draw_cloud(draw, cx, cy - radius // 2, radius, fill=(210, 222, 238))
    for dx, dy in ((-13, 12), (-2, 18), (12, 12)):
        px, py = cx + dx, cy + dy
        for i in range(6):
            a = math.radians(i * 60)
            draw.line((px, py, px + math.cos(a) * 8, py + math.sin(a) * 8),
                      fill=(230, 248, 255), width=2)


def draw_fog(draw, cx, cy, radius):
    draw_cloud(draw, cx, cy - radius // 2, radius, fill=(196, 204, 214))
    for i in range(4):
        y = cy + 12 + i * 8
        draw.arc((cx - radius - 18, y - 8, cx + radius + 18, y + 8),
                 0, 180, fill=(170, 186, 205), width=3)


def draw_partly(draw, cx, cy, radius):
    draw_sun(draw, cx - radius // 2, cy - radius // 2, max(8, int(radius * 0.55)))
    draw_cloud(draw, cx + radius // 4, cy + radius // 5, max(10, int(radius * 0.70)))


def draw_moon(draw, cx, cy, radius, phase=0.55):
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(225, 230, 245))
    offset = int(radius * (0.9 - abs(phase - 0.5)))
    shadow = (18, 24, 52)
    if phase < 0.5:
        draw.ellipse((cx - radius + offset, cy - radius, cx + radius + offset, cy + radius), fill=shadow)
    else:
        draw.ellipse((cx - radius - offset, cy - radius, cx + radius - offset, cy + radius), fill=shadow)
    for dx, dy, rr in ((-8, -7, 3), (8, 9, 4), (4, -14, 2)):
        draw.ellipse((cx + dx - rr, cy + dy - rr, cx + dx + rr, cy + dy + rr), fill=(202, 207, 225))


def draw_weather_icon(draw, cx, cy, size, condition, night=False, moon_phase=0.55):
    kind = condition_kind(condition)
    radius = max(7, size // 2)
    if night and kind in ("sun", "partly"):
        draw_moon(draw, cx, cy, radius, moon_phase)
    elif kind == "sun":
        draw_sun(draw, cx, cy, radius)
    elif kind == "cloud":
        draw_cloud(draw, cx, cy, radius)
    elif kind == "rain":
        draw_rain(draw, cx, cy, radius)
    elif kind == "storm":
        draw_storm(draw, cx, cy, radius)
    elif kind == "snow":
        draw_snow(draw, cx, cy, radius)
    elif kind == "fog":
        draw_fog(draw, cx, cy, radius)
    else:
        draw_partly(draw, cx, cy, radius)

