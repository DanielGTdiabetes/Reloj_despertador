import datetime

import ephem
import pytz


class SunService:
    """Sunrise, sunset and day-period calculations."""

    def __init__(self, lat=39.94, lon=-0.10, timezone="Europe/Madrid"):
        self.observer = ephem.Observer()
        self.observer.lat = str(lat)
        self.observer.lon = str(lon)
        self.observer.pressure = 0
        self.observer.temperature = 0
        self.sun = ephem.Sun()
        self.timezone = pytz.timezone(timezone)

    def get_sunrise_sunset(self, now=None):
        now = now or datetime.datetime.now(self.timezone)
        local_midday = now.replace(hour=12, minute=0, second=0, microsecond=0)
        self.observer.date = local_midday.astimezone(datetime.timezone.utc)
        try:
            sunrise = self.observer.previous_rising(self.sun).datetime().replace(tzinfo=datetime.timezone.utc)
            sunset = self.observer.next_setting(self.sun).datetime().replace(tzinfo=datetime.timezone.utc)
        except Exception:
            sunrise = now.replace(hour=7, minute=0, second=0, microsecond=0).astimezone(datetime.timezone.utc)
            sunset = now.replace(hour=20, minute=0, second=0, microsecond=0).astimezone(datetime.timezone.utc)
        return {
            "sunrise": sunrise.astimezone(self.timezone),
            "sunset": sunset.astimezone(self.timezone),
        }

    def get_sunrise_time(self):
        return self.get_sunrise_sunset()["sunrise"]

    def get_sunset_time(self):
        return self.get_sunrise_sunset()["sunset"]

    def get_sunrise_progress(self):
        now = datetime.datetime.now(self.timezone)
        times = self.get_sunrise_sunset(now)
        sunrise = times["sunrise"]
        sunset = times["sunset"]
        if now <= sunrise:
            return 0.0
        if now >= sunset:
            return 1.0
        return (now - sunrise).total_seconds() / max(1, (sunset - sunrise).total_seconds())

    def is_daytime(self):
        now = datetime.datetime.now(self.timezone)
        times = self.get_sunrise_sunset(now)
        return times["sunrise"] <= now <= times["sunset"]

    def get_time_of_day(self):
        now = datetime.datetime.now(self.timezone)
        times = self.get_sunrise_sunset(now)
        sunrise = times["sunrise"]
        sunset = times["sunset"]
        if now < sunrise or now > sunset:
            return "night"
        if now < sunrise + datetime.timedelta(minutes=70):
            return "sunrise"
        if now > sunset - datetime.timedelta(minutes=70):
            return "sunset"
        return "day"

