"""
PARCHE app.py — solo _render_round()
=====================================
Reemplaza ÚNICAMENTE el método _render_round() en AlarmClockApp.
Todo lo demás de app.py permanece INTACTO.

CAMBIO: añade la condición de noche para llamar a render_night()
cuando sun_info["period"] == "night".
"""

# ── Método completo listo para pegar ──────────────────────────────────────────

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
            return self.ui_round.render_focus(label, "Gira y pulsa", kind=key)

        if self.state == State.ALARM:
            value = f"{self.alarm.get('hour', 7):02d}:{self.alarm.get('minute', 0):02d}"
            sub   = "Activa" if self.alarm.get("enabled") else "Desactivada"
            return self.ui_round.render_focus("Alarma", sub, "alarm", value)

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
