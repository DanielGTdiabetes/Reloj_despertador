"""
Alerts Service - Weather alert detection and classification
"""

class AlertsService:
    """Detects and classifies weather alerts"""

    ALERT_LEVELS = {
        "wind": {"high": 50, "medium": 30, "low": 20},
        "heat": {"high": 40, "medium": 35, "low": 30},
        "cold": {"high": -10, "medium": -5, "low": 0},
        "rain": {"high": 50, "medium": 25, "low": 10},
        "humidity": {"high": 95, "medium": 85, "low": 75}
    }

    ALERT_COLORS = {
        "high": (255, 60, 60),
        "medium": (255, 160, 40),
        "low": (255, 220, 60)
    }

    ALERT_ICONS = {
        "wind": "VIENTO FUERTE",
        "heat": "CALOR EXTREMO",
        "cold": "FRÍO INTENSO",
        "rain": "LLUVIA INTENSA",
        "humidity": "HUMEDAD ALTA"
    }

    def __init__(self):
        self._active_alerts = []

    def check_alerts(self, weather_data):
        self._active_alerts = []

        temp = weather_data.get("temp", 0)
        wind = weather_data.get("wind_speed", 0)
        rain = weather_data.get("rain_1h", 0)
        humidity = weather_data.get("humidity", 0)

        if wind >= self.ALERT_LEVELS["wind"]["low"]:
            level = self._get_level(wind, self.ALERT_LEVELS["wind"])
            self._active_alerts.append({
                "type": "wind",
                "level": level,
                "message": f"Viento: {wind:.1f} km/h",
                "color": self.ALERT_COLORS[level]
            })

        if temp >= self.ALERT_LEVELS["heat"]["low"]:
            level = self._get_level(temp, self.ALERT_LEVELS["heat"])
            self._active_alerts.append({
                "type": "heat",
                "level": level,
                "message": f"Calor: {temp:.1f}°C",
                "color": self.ALERT_COLORS[level]
            })

        if temp <= self.ALERT_LEVELS["cold"]["high"]:
            level = "high" if temp <= self.ALERT_LEVELS["cold"]["high"] else "medium"
            self._active_alerts.append({
                "type": "cold",
                "level": level,
                "message": f"Frío: {temp:.1f}°C",
                "color": self.ALERT_COLORS[level]
            })

        if rain >= self.ALERT_LEVELS["rain"]["low"]:
            level = self._get_level(rain, self.ALERT_LEVELS["rain"])
            self._active_alerts.append({
                "type": "rain",
                "level": level,
                "message": f"Lluvia: {rain:.1f} mm/h",
                "color": self.ALERT_COLORS[level]
            })

        return self._active_alerts

    def _get_level(self, value, levels):
        if value >= levels["high"]:
            return "high"
        elif value >= levels["medium"]:
            return "medium"
        return "low"

    def get_alerts(self):
        return self._active_alerts

    def has_alerts(self):
        return len(self._active_alerts) > 0

    def get_highest_alert(self):
        if not self._active_alerts:
            return None
        priority = {"high": 3, "medium": 2, "low": 1}
        return max(self._active_alerts, key=lambda a: priority.get(a["level"], 0))
