import json
import time

import requests


class WeatherService:
    """OpenWeatherMap client with graceful fallback data."""

    def __init__(self, config_path="config/config.json"):
        with open(config_path, encoding="utf-8") as f:
            self.config = json.load(f)

        weather = self.config.get("weather", {})
        location = self.config.get("location", {})
        self.api_key = weather.get("api_key", "")
        self.lat = location.get("lat", weather.get("lat", 39.94))
        self.lon = location.get("lon", weather.get("lon", -0.10))
        self.update_interval = int(weather.get("update_interval_minutes", 15)) * 60
        self._last_update = 0
        self._last_error = ""
        self._current = self._fallback_current()
        self._forecast = self._fallback_forecast()
        self._alerts = []

    def update(self):
        if not self.api_key:
            self._last_error = "Sin API key"
            return False

        for loader in (self._load_classic, self._load_onecall_3, self._load_onecall_25):
            try:
                current, forecast, alerts = loader()
                if current:
                    self._current = current
                if forecast:
                    self._forecast = forecast
                self._alerts = alerts or []
                self._last_update = time.time()
                self._last_error = ""
                print(f"[Weather] updated: {self.get_weather_condition()}")
                return True
            except Exception as exc:
                self._last_error = str(exc)
                print(f"[Weather] source failed: {exc}")
        return False

    def should_update(self):
        return time.time() - self._last_update > self.update_interval

    def get_current(self):
        return self._current or self._fallback_current()

    def get_temperature(self):
        return self.get_current().get("temp")

    def get_humidity(self):
        return self.get_current().get("humidity")

    def get_wind_speed(self):
        return self.get_current().get("wind_speed")

    def get_weather_condition(self):
        return self.get_current().get("description", "")

    def get_weather_main(self):
        return self.get_current().get("main", "")

    def get_weather_icon(self):
        return self.get_current().get("icon", "")

    def get_forecast(self):
        return self._forecast or self._fallback_forecast()

    def get_alerts(self):
        return self._alerts or []

    def has_alerts(self):
        return bool(self._alerts)

    def last_error(self):
        return self._last_error

    def _load_onecall_3(self):
        data = self._get_json(
            "https://api.openweathermap.org/data/3.0/onecall",
            {"exclude": "minutely,hourly", "units": "metric", "lang": "es"},
        )
        return self._parse_onecall(data)

    def _load_onecall_25(self):
        data = self._get_json(
            "https://api.openweathermap.org/data/2.5/onecall",
            {"exclude": "minutely,hourly", "units": "metric", "lang": "es"},
        )
        return self._parse_onecall(data)

    def _load_classic(self):
        current_data = self._get_json(
            "https://api.openweathermap.org/data/2.5/weather",
            {"units": "metric", "lang": "es"},
        )
        forecast_data = self._get_json(
            "https://api.openweathermap.org/data/2.5/forecast",
            {"units": "metric", "lang": "es"},
        )
        current = self._parse_current(current_data)
        forecast = self._daily_from_3h(forecast_data.get("list", []))
        return current, forecast, []

    def _get_json(self, url, params):
        merged = {
            "lat": self.lat,
            "lon": self.lon,
            "appid": self.api_key,
        }
        merged.update(params)
        response = requests.get(url, params=merged, timeout=8)
        response.raise_for_status()
        data = response.json()
        if str(data.get("cod", "200")) not in ("200", "0"):
            raise RuntimeError(data.get("message", "weather API error"))
        return data

    def _parse_onecall(self, data):
        return (
            self._parse_current(data.get("current", {})),
            [self._parse_daily(day) for day in data.get("daily", [])[:7]],
            data.get("alerts", []),
        )

    def _parse_current(self, data):
        weather = (data.get("weather") or [{}])[0]
        return {
            "dt": data.get("dt", int(time.time())),
            "temp": data.get("temp", data.get("main", {}).get("temp")),
            "feels_like": data.get("feels_like", data.get("main", {}).get("feels_like")),
            "humidity": data.get("humidity", data.get("main", {}).get("humidity")),
            "wind_speed": data.get("wind_speed", data.get("wind", {}).get("speed")),
            "main": weather.get("main", ""),
            "description": weather.get("description", ""),
            "icon": weather.get("icon", ""),
        }

    def _parse_daily(self, data):
        weather = (data.get("weather") or [{}])[0]
        temp = data.get("temp", {})
        return {
            "dt": data.get("dt", int(time.time())),
            "temp_max": temp.get("max"),
            "temp_min": temp.get("min"),
            "main": weather.get("main", ""),
            "description": weather.get("description", ""),
            "pop": data.get("pop", 0),
        }

    def _daily_from_3h(self, entries):
        by_day = {}
        for entry in entries:
            day = time.strftime("%Y-%m-%d", time.localtime(entry.get("dt", time.time())))
            item = by_day.setdefault(day, {"temps": [], "entries": []})
            item["temps"].append(entry.get("main", {}).get("temp"))
            item["entries"].append(entry)

        daily = []
        for day, item in list(by_day.items())[:7]:
            temps = [t for t in item["temps"] if t is not None]
            mid = item["entries"][len(item["entries"]) // 2]
            weather = (mid.get("weather") or [{}])[0]
            daily.append({
                "dt": mid.get("dt", int(time.time())),
                "temp_max": max(temps) if temps else None,
                "temp_min": min(temps) if temps else None,
                "main": weather.get("main", ""),
                "description": weather.get("description", ""),
                "pop": 0,
            })
        return daily

    def geocode_postal_es(self, postal_code: str) -> dict:
        """Convierte código postal español en coordenadas. Devuelve {'lat', 'lon', 'name'}."""
        resp = requests.get(
            "http://api.openweathermap.org/geo/1.0/zip",
            params={"zip": f"{postal_code},ES", "appid": self.api_key},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        if "lat" not in data:
            raise RuntimeError(data.get("message", "geocoding sin resultado"))
        return {"lat": data["lat"], "lon": data["lon"], "name": data.get("name", postal_code)}

    def _fallback_current(self):
        return {
            "dt": int(time.time()),
            "temp": None,
            "humidity": None,
            "wind_speed": None,
            "main": "Clear",
            "description": "sin datos",
            "icon": "",
        }

    def _fallback_forecast(self):
        now = int(time.time())
        return [
            {
                "dt": now + i * 86400,
                "temp_max": None,
                "temp_min": None,
                "main": "Clear",
                "description": "sin datos",
                "pop": 0,
            }
            for i in range(7)
        ]

