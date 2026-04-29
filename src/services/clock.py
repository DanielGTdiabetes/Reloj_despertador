import datetime
import json
import time

import pytz

try:
    import ntplib
except Exception:
    ntplib = None


class ClockService:
    """Local clock with optional NTP offset."""

    def __init__(self, config_path="config/config.json", sync_on_start=False):
        with open(config_path, encoding="utf-8") as f:
            self.config = json.load(f)

        tz_name = self.config.get("weather", {}).get("timezone", "Europe/Madrid")
        self.timezone = pytz.timezone(tz_name)
        ntp = self.config.get("ntp", {})
        self.ntp_servers = ntp.get("servers", ["pool.ntp.org"])
        self.sync_interval = int(ntp.get("sync_interval_hours", 6)) * 3600
        self._last_sync = 0
        self._offset = 0.0
        if sync_on_start:
            self.sync_time()

    def sync_time(self):
        if ntplib is None:
            self._last_sync = time.time()
            print("[Clock] ntplib not available; using system clock")
            return False
        client = ntplib.NTPClient()
        for server in self.ntp_servers:
            try:
                response = client.request(server, version=4, timeout=4)
                self._offset = response.offset
                self._last_sync = time.time()
                print(f"[Clock] NTP synced with {server}")
                return True
            except Exception as exc:
                print(f"[Clock] NTP failed with {server}: {exc}")
        self._last_sync = time.time()
        return False

    def now(self):
        utc_now = datetime.datetime.now(datetime.timezone.utc)
        corrected = utc_now + datetime.timedelta(seconds=self._offset)
        return corrected.astimezone(self.timezone)

    def formatted_time(self):
        return self.now().strftime("%H:%M")

    def formatted_seconds(self):
        return self.now().strftime("%H:%M:%S")

    def formatted_date(self):
        return self.now().strftime("%d/%m/%Y")

    def day_of_week(self):
        days_es = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
        return days_es[self.now().weekday()]

    def day_of_week_short(self):
        days_es = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
        return days_es[self.now().weekday()]

    def is_daytime(self):
        hour = self.now().hour
        return 7 <= hour < 21

    def should_sync(self):
        return time.time() - self._last_sync > self.sync_interval
