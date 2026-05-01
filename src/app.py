import os
import queue
import re
import signal
import subprocess
import threading
import time
import traceback

import RPi.GPIO as GPIO

from config_loader import load_config, save_config
from hardware.audio import I2SAudio
from hardware.rotary_encoder import RotaryEncoder
from display import DisplayManager
from paths import CONFIG_PATH as DEFAULT_CONFIG_PATH
from services.clock import ClockService
from services.lunar import LunarService
from services.sun import SunService
from services.weather import WeatherService
from ui.rect_ui import RectUIScreen
from ui.round_home import RoundHomeScreen
from runtime_flags import RuntimeFlags


class State:
    CLOCK = "clock"
    MENU = "menu"
    ALARM = "alarm"
    BRIGHTNESS = "brightness"
    WIFI_SCAN = "wifi_scan"
    WIFI_PASSWORD = "wifi_password"
    ALARM_RINGING = "alarm_ringing"
    LOCATION = "location"


MENU_ITEMS = [
    ("alarm_clock", "ALARMA"), # Se actualizará dinámicamente a "ON 07:00", etc.
    ("brightness", "BRILLO"),
    ("wifi", "WIFI"),
    ("location", "CIUDAD"),
    ("sync", "SYNC"),
    ("weather", "CLIMA"),
]

PASSWORD_GROUPS = ["OK", "<", "abcABC", "defDEF", "ghiGHI", "jklJKL", "mnoMNO", "pqrsPQRS", "tuvTUV", "wxyzWXYZ", "0123456789", "@#-_ ."]


class AlarmClockApp:
    CONFIG_PATH = str(DEFAULT_CONFIG_PATH)

    def __init__(self):
        # GPIO se configura UNA sola vez al arranque. Los drivers solo hacen GPIO.setup().
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        self.flags = RuntimeFlags.from_env()
        self.config = self._load_config()
        self.running = True
        self.state = State.CLOCK
        self.menu_index = 0
        self.tick = 0

        self.alarm = dict(self.config.get("alarm", {}))
        self.alarm.setdefault("enabled", False)
        self.alarm.setdefault("hour", 7)
        self.alarm.setdefault("minute", 0)
        self.alarm.setdefault("days", list(range(7)))
        self.alarm_field = "enabled"
        self.last_alarm_key = None
        self.ring_option = 0
        self.snoozed_until = 0

        ui_cfg = self.config.get("ui", {})
        self.brightness_round = int(ui_cfg.get("brightness_round", 80))
        self.brightness_rect = int(ui_cfg.get("brightness_rect", 80))
        self.brightness_target = "round"

        self.wifi_networks = []
        self.wifi_index = 0
        self.wifi_scanning = False
        self.wifi_ssid = ""
        self.wifi_password = ""
        self.password_group = 0
        self.password_char = 0
        self.password_level = 0

        self.weather_updating = False
        postal = self.config.get("location", {}).get("postal_code", "00000")
        self.location_digits = [int(c) for c in postal.zfill(5)[:5]]
        self.location_digit_idx = 0
        self.location_updating = False
        self.status = f"Arrancando ({self.flags.summary()})"
        self.displays = None
        self.events: queue.Queue[tuple[str, object]] = queue.Queue(maxsize=200)

        self._init_services()
        self._init_ui()
        self._init_hardware()
        self._register_signals()
        self._start_background_refresh()

    def _load_config(self):
        return load_config(self.CONFIG_PATH)

    def _save_config(self):
        save_config(self.config, self.CONFIG_PATH)

    def _init_services(self):
        location = self.config.get("location", self.config.get("weather", {}))
        weather_cfg = self.config.get("weather", {})
        lat = location.get("lat", 39.94)
        lon = location.get("lon", -0.10)
        timezone = weather_cfg.get("timezone", "Europe/Madrid")
        self.clock = ClockService(self.CONFIG_PATH, sync_on_start=False)
        self.weather = WeatherService(self.CONFIG_PATH)
        self.sun = SunService(lat=lat, lon=lon, timezone=timezone)
        self.lunar = LunarService(lat=lat, lon=lon)
        self.audio = None

    def _init_ui(self):
        self.ui_round = RoundHomeScreen()
        self.ui_rect = RectUIScreen()

    def _init_hardware(self):
        self.displays = DisplayManager(
            self.config,
            self.flags,
            brightness_round=self.brightness_round,
            brightness_rect=self.brightness_rect,
        )
        self.displays.init()
        self.encoder = None

        if self.flags.disable_encoder:
            print("[HW] encoder disabled by env")
        else:
            try:
                cfg = self.config["encoder"]
                self.encoder = RotaryEncoder(
                    clk_pin=cfg.get("clk_pin", 5),
                    dt_pin=cfg.get("dt_pin", 6),
                    sw_pin=cfg.get("sw_pin", 13),
                )
                self.encoder.on("rotate_cw", self._on_cw)
                self.encoder.on("rotate_ccw", self._on_ccw)
                self.encoder.on("button_press", self._on_press)
                self.encoder.on("button_long_press", self._on_long_press)
                print("[HW] encoder OK")
            except Exception as exc:
                print(f"[HW] encoder failed: {exc}")
                traceback.print_exc()

        if self.flags.disable_audio:
            print("[HW] audio disabled by env")
        else:
            try:
                audio_cfg = self.config.get("audio", {})
                if audio_cfg.get("enabled", True):
                    self.audio = I2SAudio(device=audio_cfg.get("device", "max98357a"))
                    self.audio.set_volume(self.alarm.get("volume", 80))
                    print("[HW] audio OK")
            except Exception as exc:
                print(f"[HW] audio failed: {exc}")
                traceback.print_exc()

    def _register_signals(self):
        signal.signal(signal.SIGINT, self._stop_signal)
        signal.signal(signal.SIGTERM, self._stop_signal)

    def _start_background_refresh(self):
        threading.Thread(target=self.clock.sync_time, daemon=True).start()
        if self.flags.disable_weather:
            print("[Weather] disabled by env")
        else:
            threading.Thread(target=self._refresh_weather, daemon=True).start()

    def _stop_signal(self, signum, frame):
        self.running = False

    def _on_cw(self, position=None):
        self._emit_event("encoder_rotate", 1)

    def _on_ccw(self, position=None):
        self._emit_event("encoder_rotate", -1)

    def _emit_event(self, kind: str, payload: object = None) -> None:
        try:
            self.events.put_nowait((kind, payload))
        except queue.Full:
            # Prefer dropping input over blocking threads.
            return

    def _rotate(self, delta: int) -> None:
        if delta == 0: return
        print(f"[Debug] Rotate delta: {delta}, current state: {self.state}")
        if self.state == State.MENU:
            self.menu_index = (self.menu_index + delta) % len(MENU_ITEMS)
        elif self.state == State.ALARM:
            if self.alarm_field == "enabled":
                self.alarm["enabled"] = not self.alarm.get("enabled", False)
            elif self.alarm_field == "hour":
                self.alarm["hour"] = (int(self.alarm.get("hour", 7)) + delta) % 24
            elif self.alarm_field == "minute":
                self.alarm["minute"] = (int(self.alarm.get("minute", 0)) + delta) % 60
        elif self.state == State.BRIGHTNESS:
            if self.brightness_target == "round":
                self.brightness_round = max(0, min(100, self.brightness_round + delta * 5))
            else:
                self.brightness_rect = max(0, min(100, self.brightness_rect + delta * 5))
            self._apply_brightness()
        elif self.state == State.WIFI_SCAN:
            self.wifi_index = (self.wifi_index + delta) % max(1, len(self.wifi_networks))
        elif self.state == State.WIFI_PASSWORD:
            if self.password_level == 0:
                self.password_group = (self.password_group + delta) % len(PASSWORD_GROUPS)
                self.password_char = 0
            else:
                chars = PASSWORD_GROUPS[self.password_group]
                self.password_char = (self.password_char + delta) % len(chars)
        elif self.state == State.LOCATION:
            self.location_digits[self.location_digit_idx] = (self.location_digits[self.location_digit_idx] + delta) % 10
        elif self.state == State.ALARM_RINGING:
            self.ring_option = (self.ring_option + delta) % 2

    def _on_press(self):
        self._emit_event("encoder_press")

    def _on_long_press(self):
        self._emit_event("encoder_long_press")

    def _handle_press(self) -> None:
        if self.state == State.CLOCK:
            self.state = State.MENU
            self.menu_index = 0
        elif self.state == State.MENU:
            self._select_menu()
        elif self.state == State.ALARM:
            self._advance_alarm_field()
        elif self.state == State.BRIGHTNESS:
            self.brightness_target = "rect" if self.brightness_target == "round" else "round"
        elif self.state == State.WIFI_SCAN:
            if self.wifi_networks:
                self.wifi_ssid = self.wifi_networks[self.wifi_index].get("ssid", "")
                self.wifi_password = ""
                self.password_group = 0
                self.password_char = 0
                self.password_level = 0
                self.state = State.WIFI_PASSWORD
        elif self.state == State.WIFI_PASSWORD:
            self._password_press()
        elif self.state == State.LOCATION:
            if self.location_digit_idx < 4:
                self.location_digit_idx += 1
            else:
                self._location_confirm()
        elif self.state == State.ALARM_RINGING:
            if self.ring_option == 0:
                self._stop_alarm()
            else:
                self._snooze_alarm()

    def _handle_long_press(self) -> None:
        if self.state == State.CLOCK:
            return
        if self.state == State.ALARM:
            self._save_alarm()
            self.state = State.CLOCK
        elif self.state == State.BRIGHTNESS:
            self._save_brightness()
            self.state = State.CLOCK
        elif self.state == State.WIFI_PASSWORD:
            if self.password_level == 1:
                self.password_level = 0
            elif self.wifi_password:
                self.wifi_password = self.wifi_password[:-1]
            else:
                self.state = State.WIFI_SCAN
        elif self.state == State.LOCATION:
            if self.location_digit_idx > 0:
                self.location_digit_idx -= 1
            else:
                self.state = State.CLOCK
        elif self.state == State.ALARM_RINGING:
            self._snooze_alarm()
        else:
            self.state = State.CLOCK

    def _select_menu(self):
        key = MENU_ITEMS[self.menu_index][0]
        if key == "alarm_clock":
            self.alarm_field = "enabled"
            self.state = State.ALARM
        elif key == "brightness":
            self.brightness_target = "round"
            self.state = State.BRIGHTNESS
        elif key == "wifi":
            self.state = State.WIFI_SCAN
            self._start_wifi_scan()
        elif key == "sync":
            self.status = "Sincronizando"
            threading.Thread(target=self.clock.sync_time, daemon=True).start()
            self.state = State.CLOCK
        elif key == "location":
            postal = self.config.get("location", {}).get("postal_code", "00000")
            self.location_digits = [int(c) for c in postal.zfill(5)[:5]]
            self.location_digit_idx = 0
            self.state = State.LOCATION
        elif key == "weather":
            if self.flags.disable_weather:
                self.status = "Clima desactivado"
            else:
                threading.Thread(target=self._refresh_weather, daemon=True).start()
            self.state = State.CLOCK

    def _advance_alarm_field(self):
        if self.alarm_field == "enabled":
            self.alarm_field = "hour"
        elif self.alarm_field == "hour":
            self.alarm_field = "minute"
        else:
            self._save_alarm()
            self.state = State.CLOCK

    def _password_press(self):
        group = PASSWORD_GROUPS[self.password_group]
        if self.password_level == 0 and group == "OK":
            self._connect_wifi()
            return
        if self.password_level == 0 and group == "<":
            self.wifi_password = self.wifi_password[:-1]
            return
        if self.password_level == 0:
            self.password_level = 1
            self.password_char = 0
        else:
            self.wifi_password += group[self.password_char]
            self.password_level = 0

    def _save_alarm(self):
        self.config["alarm"] = self.alarm
        self._save_config()
        self.status = "Alarma guardada"

    def _apply_brightness(self):
        if self.displays:
            self.displays.set_brightness(round_percent=self.brightness_round, rect_percent=self.brightness_rect)

    def _save_brightness(self):
        self.config.setdefault("ui", {})["brightness_round"] = self.brightness_round
        self.config.setdefault("ui", {})["brightness_rect"] = self.brightness_rect
        self._save_config()
        self._apply_brightness()
        self.status = "Brillo guardado"

    def _start_wifi_scan(self):
        if self.wifi_scanning:
            return
        self.wifi_scanning = True
        self.wifi_networks = []
        self.wifi_index = 0
        threading.Thread(target=self._wifi_scan_worker, daemon=True).start()

    def _wifi_scan_worker(self):
        networks = []
        try:
            out = subprocess.check_output(["iwlist", "wlan0", "scan"], stderr=subprocess.DEVNULL, text=True, timeout=12)
            for cell in out.split("Cell ")[1:]:
                ssid_match = re.search(r'ESSID:"([^"]*)"', cell)
                sig_match = re.search(r"Signal level=(-?\d+)", cell)
                if not ssid_match:
                    continue
                ssid = ssid_match.group(1)
                if not ssid:
                    continue
                sig = int(sig_match.group(1)) if sig_match else -75
                bars = max(0, min(4, (sig + 100) // 12))
                networks.append({"ssid": ssid, "signal": bars})
        except Exception as exc:
            print(f"[WiFi] scan failed: {exc}")

        unique = {}
        for net in networks:
            old = unique.get(net["ssid"])
            if old is None or net["signal"] > old["signal"]:
                unique[net["ssid"]] = net
        self.wifi_networks = sorted(unique.values(), key=lambda n: (-n["signal"], n["ssid"]))
        self.wifi_scanning = False

    def _connect_wifi(self):
        ssid = self.wifi_ssid
        password = self.wifi_password
        if not ssid:
            return
        self.config.setdefault("wifi", {})["ssid"] = ssid
        self.config.setdefault("wifi", {})["password"] = password
        self._save_config()
        threading.Thread(target=self._wifi_connect_worker, args=(ssid, password), daemon=True).start()
        self.status = "Conectando WiFi"
        self.state = State.CLOCK

    def _wifi_connect_worker(self, ssid, password):
        try:
            if self._command_exists("nmcli"):
                subprocess.check_call(["nmcli", "dev", "wifi", "connect", ssid, "password", password], timeout=25)
            else:
                conf = (
                    "ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n"
                    "update_config=1\n"
                    "country=ES\n\n"
                    "network={\n"
                    f'    ssid="{ssid}"\n'
                    f'    psk="{password}"\n'
                    "}\n"
                )
                with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w", encoding="utf-8") as f:
                    f.write(conf)
                subprocess.call(["wpa_cli", "-i", "wlan0", "reconfigure"], timeout=10)
            self.status = "WiFi conectado"
        except Exception as exc:
            self.status = "WiFi fallo"
            print(f"[WiFi] connect failed: {exc}")

    def _command_exists(self, name):
        return subprocess.call(["which", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

    def _location_confirm(self):
        postal = "".join(str(d) for d in self.location_digits)
        self.location_updating = True
        self.status = "Geolocalizando"
        self.state = State.CLOCK
        threading.Thread(target=self._geocode_worker, args=(postal,), daemon=True).start()

    def _geocode_worker(self, postal_code):
        try:
            geo = self.weather.geocode_postal_es(postal_code)
            lat, lon, name = geo["lat"], geo["lon"], geo["name"]
            self.config.setdefault("location", {}).update({
                "lat": lat, "lon": lon, "city": name, "postal_code": postal_code,
            })
            self.config.setdefault("weather", {}).update({
                "lat": lat, "lon": lon, "location": name,
            })
            self._save_config()
            self.weather.lat = lat
            self.weather.lon = lon
            timezone = self.config.get("weather", {}).get("timezone", "Europe/Madrid")
            self.sun = SunService(lat=lat, lon=lon, timezone=timezone)
            self.lunar = LunarService(lat=lat, lon=lon)
            self.status = f"OK: {name}"
            if not self.flags.disable_weather:
                threading.Thread(target=self._refresh_weather, daemon=True).start()
        except Exception as exc:
            self.status = "Error ubicacion"
            print(f"[Location] geocode failed: {exc}")
        finally:
            self.location_updating = False

    def _refresh_weather(self):
        if self.flags.disable_weather:
            self.status = "Clima desactivado"
            return
        if self.weather_updating:
            return
        self.weather_updating = True
        self.status = "Actualizando clima"
        try:
            ok = self.weather.update()
            self.status = "Clima OK" if ok else "Clima sin red"
        finally:
            self.weather_updating = False

    def _check_alarm(self, now):
        if not self.alarm.get("enabled"):
            return
        if self.snoozed_until > time.time():
            return
        days = self.alarm.get("days", list(range(7)))
        key = f"{now.date()}-{now.hour:02d}:{now.minute:02d}"
        if now.weekday() in days and now.hour == self.alarm.get("hour") and now.minute == self.alarm.get("minute"):
            if self.last_alarm_key != key:
                self.last_alarm_key = key
                self._trigger_alarm()

    def _trigger_alarm(self):
        self.state = State.ALARM_RINGING
        self.ring_option = 0
        self.status = "Alarma"
        sounds = self.config.get("audio", {}).get("alarm_sounds", [])
        if self.audio and sounds:
            path = sounds[0]
            if not os.path.isabs(path):
                path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", path))
            self.audio.set_volume(self.alarm.get("volume", 80))
            self.audio.play_file(path, loop=True)

    def _stop_alarm(self):
        if self.audio:
            self.audio.stop()
        self.state = State.CLOCK
        self.status = "Alarma detenida"

    def _snooze_alarm(self):
        if self.audio:
            self.audio.stop()
        self.snoozed_until = time.time() + int(self.alarm.get("snooze_minutes", 5)) * 60
        self.state = State.CLOCK
        self.status = "Pospuesta"

    def _render(self):
        now = self.clock.now()
        if self.state != State.ALARM_RINGING:
            self._check_alarm(now)

        round_img = self._render_round(now)
        rect_img = self._render_rect(now)

        if self.displays:
            self.displays.submit(round_image=round_img, rect_image=rect_img)

    def _render_round(self, now):
        if self.state == State.CLOCK:
            times = self.sun.get_sunrise_sunset(now)
            sun_info = {
                "period":   self.sun.get_time_of_day(),
                "progress": self.sun.get_sunrise_progress(),
                "sunrise":  times["sunrise"],
                "sunset":   times["sunset"],
            }
            moon = self.lunar.get_phase()

            # ── NUEVO: pantalla de noche con luna por fases ──────────────────
            if sun_info["period"] == "night":
                return self.ui_round.render_night(now, moon, self.alarm, sun_info)
            # ─────────────────────────────────────────────────────────────────

            # Enriquecer weather con temp_max/min del forecast del día 0
            current = self.weather.get_current()
            forecast = self.weather.get_forecast()
            if forecast:
                today = forecast[0]
                current.setdefault("temp_max", today.get("temp_max"))
                current.setdefault("temp_min", today.get("temp_min"))

            return self.ui_round.render(now, current, sun_info, moon,
                                        self.alarm, self.status)

        if self.state == State.MENU:
            key, label = MENU_ITEMS[self.menu_index]
            val = ""
            if key == "alarm_clock":
                st = "ON" if self.alarm.get("enabled") else "OFF"
                label = f"{st} {self.alarm.get('hour',7):02d}:{self.alarm.get('minute',0):02d}"
            return self.ui_round.render_focus(label, "Gira y pulsa", kind=key, value=val)

        if self.state == State.ALARM:
            value = f"{self.alarm.get('hour', 7):02d}:{self.alarm.get('minute', 0):02d}"
            sub   = "ON" if self.alarm.get("enabled") else "OFF"
            return self.ui_round.render_focus("Alarma", sub, "alarm_clock", value)

        if self.state == State.BRIGHTNESS:
            value = (f"{self.brightness_round}%"
                     if self.brightness_target == "round"
                     else f"{self.brightness_rect}%")
            title = ("Brillo redonda" if self.brightness_target == "round"
                     else "Brillo rect")
            return self.ui_round.render_focus(
                title, "Pulsar cambia pantalla", "brightness", value)

        if self.state == State.WIFI_SCAN:
            sub   = "Buscando" if self.wifi_scanning else "Elige red"
            value = (self.wifi_networks[self.wifi_index]["ssid"]
                     if self.wifi_networks else "")
            return self.ui_round.render_focus("WiFi", sub, "wifi", value[:16])

        if self.state == State.WIFI_PASSWORD:
            return self.ui_round.render_focus(
                "Contrasena", self.wifi_ssid[:16], "wifi",
                "*" * min(len(self.wifi_password), 8))

        if self.state == State.LOCATION:
            postal_str = "".join(str(d) for d in self.location_digits)
            sub = ("Confirmar" if self.location_digit_idx == 4
                   else f"Digito {self.location_digit_idx + 1}/5")
            return self.ui_round.render_focus(
                "Ubicacion", sub, "location", postal_str)

        if self.state == State.ALARM_RINGING:
            return self.ui_round.render_alarm_ringing()

        return None

    def _render_rect(self, now):
        if self.state == State.CLOCK:
            return self.ui_rect.render_forecast(self._forecast_for_ui())
        if self.state == State.MENU:
            dynamic_items = []
            for key, label in MENU_ITEMS:
                if key == "alarm_clock":
                    st = "ON" if self.alarm.get("enabled") else "OFF"
                    label = f"{st} {self.alarm.get('hour',7):02d}:{self.alarm.get('minute',0):02d}"
                dynamic_items.append((key, label))
            return self.ui_rect.render_menu(dynamic_items, self.menu_index)
        if self.state == State.ALARM:
            return self.ui_rect.render_alarm(self.alarm, self.alarm_field)
        if self.state == State.BRIGHTNESS:
            return self.ui_rect.render_brightness(self.brightness_round, self.brightness_rect, self.brightness_target)
        if self.state == State.WIFI_SCAN:
            return self.ui_rect.render_wifi_scan(self.wifi_networks, self.wifi_index, self.wifi_scanning)
        if self.state == State.WIFI_PASSWORD:
            return self.ui_rect.render_wifi_keyboard(
                self.wifi_ssid,
                self.wifi_password,
                PASSWORD_GROUPS,
                self.password_group,
                self.password_char,
                self.password_level,
            )
        if self.state == State.LOCATION:
            return self.ui_rect.render_location(self.location_digits, self.location_digit_idx, self.location_updating)
        if self.state == State.ALARM_RINGING:
            return self.ui_rect.render_ringing("Despertador", self.ring_option)
        return None

    def _forecast_for_ui(self):
        forecast = []
        for index, day in enumerate(self.weather.get_forecast()[:7]):
            ts = day.get("dt", int(time.time()) + index * 86400)
            local = time.localtime(ts)
            forecast.append({
                "weekday": local.tm_wday,
                "description": day.get("description", day.get("main", "")),
                "temp_max": day.get("temp_max"),
                "temp_min": day.get("temp_min"),
            })
        return forecast

    def _process_events(self) -> None:
        while True:
            try:
                kind, payload = self.events.get_nowait()
            except queue.Empty:
                return

            if kind == "encoder_rotate":
                try:
                    delta = int(payload) if payload is not None else 0
                except Exception:
                    continue
                self._rotate(delta)
            elif kind == "encoder_press":
                self._handle_press()
            elif kind == "encoder_long_press":
                self._handle_long_press()

    def run(self):
        print("[Main] starting")
        last_render = 0.0
        last_weather_check = 0.0
        while self.running:
            self._process_events()
            now = time.time()
            if now - last_render >= 1.0:
                self._render()
                self.tick += 1
                last_render = now
            if now - last_weather_check >= 15.0:
                if not self.flags.disable_weather and self.weather.should_update():
                    threading.Thread(target=self._refresh_weather, daemon=True).start()
                if self.clock.should_sync():
                    threading.Thread(target=self.clock.sync_time, daemon=True).start()
                last_weather_check = now
            time.sleep(0.05)
        self.cleanup()

    def cleanup(self):
        print("[Main] cleanup")
        if self.audio:
            self.audio.stop()
        if self.encoder:
            self.encoder.cleanup()
        if self.displays:
            self.displays.cleanup()


if __name__ == "__main__":
    AlarmClockApp().run()
