"""
Color palettes and gradients for the UI
"""

class Colors:
    DARK_BG = (10, 10, 20)
    DARK_SURFACE = (20, 20, 35)
    DARK_CARD = (30, 30, 50)
    WHITE = (255, 255, 255)
    LIGHT_GRAY = (200, 200, 210)
    MID_GRAY = (120, 120, 130)
    DARK_GRAY = (60, 60, 70)
    ACCENT_BLUE = (80, 140, 255)
    ACCENT_ORANGE = (255, 160, 50)
    ACCENT_GREEN = (80, 220, 120)
    ACCENT_RED = (255, 80, 80)
    ACCENT_YELLOW = (255, 220, 80)
    ACCENT_PURPLE = (160, 100, 255)
    SUNRISE_GRADIENT = [(255, 140, 50), (255, 200, 100), (255, 240, 180)]
    DAY_SKY = (135, 170, 220)
    NIGHT_SKY = (10, 10, 30)
    SUNSET_SKY = (180, 100, 80)
    MOON_GLOW = (220, 220, 240)
    RAIN_BLUE = (100, 150, 255)
    CLOUD_GRAY = (180, 180, 190)
    ALERT_RED = (255, 60, 60)
    ALERT_ORANGE = (255, 160, 40)
    ALERT_YELLOW = (255, 220, 60)

GRADIENTS = {
    "sunrise": [
        (255, 140, 50), (255, 180, 80), (255, 220, 120), (255, 240, 180)
    ],
    "sunset": [
        (180, 80, 60), (220, 120, 80), (255, 180, 100), (255, 220, 160)
    ],
    "day_sky": [
        (100, 150, 220), (135, 170, 220), (170, 200, 240)
    ],
    "night_sky": [
        (5, 5, 20), (10, 10, 30), (15, 15, 40)
    ],
    "card": [
        (25, 25, 45), (35, 35, 55)
    ]
}
