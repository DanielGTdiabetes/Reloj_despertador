"""
Alarm Service - Alarm logic and scheduling
"""

import json
import time
import os

class AlarmService:
    """Manages alarm settings and triggers"""

    def __init__(self, config_path="config/config.json", audio=None):
        with open(config_path) as f:
            self.config = json.load(f)

        self.audio = audio
        self.alarm_config = self.config["alarm"]
        self._is_ringing = False
        self._last_trigger = None
        self._snoozed_until = 0

    def is_enabled(self):
        return self.alarm_config.get("enabled", False)

    def set_enabled(self, enabled):
        self.alarm_config["enabled"] = enabled
        self._save_config()

    def toggle(self):
        self.alarm_config["enabled"] = not self.alarm_config["enabled"]
        self._save_config()
        return self.alarm_config["enabled"]

    def get_time(self):
        return self.alarm_config.get("hour", 7), self.alarm_config.get("minute", 0)

    def set_time(self, hour, minute):
        self.alarm_config["hour"] = max(0, min(23, hour))
        self.alarm_config["minute"] = max(0, min(59, minute))
        self._save_config()

    def get_days(self):
        return self.alarm_config.get("days", [0, 1, 2, 3, 4, 5, 6])

    def set_days(self, days):
        self.alarm_config["days"] = days
        self._save_config()

    def get_volume(self):
        return self.alarm_config.get("volume", 80)

    def set_volume(self, volume):
        self.alarm_config["volume"] = max(0, min(100, volume))
        if self.audio:
            self.audio.set_volume(self.alarm_config["volume"])
        self._save_config()

    def check_alarm(self, hour, minute, weekday):
        if not self.is_enabled():
            return False

        if self._snoozed_until > time.time():
            return False

        today_key = (hour, minute)
        alarm_key = (self.alarm_config["hour"], self.alarm_config["minute"])

        if today_key == alarm_key and weekday in self.get_days():
            today_str = f"{hour}:{minute}"
            if today_str != self._last_trigger:
                self._last_trigger = today_str
                return True

        return False

    def trigger(self):
        self._is_ringing = True
        if self.audio:
            sound = self.alarm_config.get("alarm_sounds", ["src/assets/sounds/alarm1.wav"])
            if sound and os.path.exists(sound[0]):
                self.audio.set_volume(self.get_volume())
                self.audio.play_file(sound[0], loop=True)
            else:
                beep_path = "src/assets/sounds/beep.wav"
                if not os.path.exists(beep_path):
                    self.audio.generate_beep(beep_path)
                self.audio.play_file(beep_path, loop=True)

    def stop(self):
        self._is_ringing = False
        if self.audio:
            self.audio.stop()

    def snooze(self):
        self.stop()
        snooze_minutes = self.alarm_config.get("snooze_minutes", 5)
        self._snoozed_until = time.time() + snooze_minutes * 60

    def is_ringing(self):
        return self._is_ringing

    def get_snoozed_until(self):
        return self._snoozed_until

    def _save_config(self):
        self.config["alarm"] = self.alarm_config
        config_path = "config/config.json"
        temp_path = config_path + ".tmp"
        with open(temp_path, "w") as f:
            json.dump(self.config, f, indent=4)
        os.replace(temp_path, config_path)
