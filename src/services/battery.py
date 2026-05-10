"""
battery.py — Servicio de monitoreo de batería para DFR0528 UPS HAT

Responsabilidades:
  - Lectura periódica en hilo daemon (cada POLL_INTERVAL segundos en estado normal,
    cada CRITICAL_INTERVAL en estado crítico/apagado).
  - Clasificación del nivel de batería: ok | warning | critical | shutdown.
  - Callbacks configurables:
      on_low_battery(level, pct)   → llamado en warning/critical
      on_shutdown_required()       → llamado una sola vez cuando SOC ≤ shutdown_threshold
  - Apagado seguro real: tras SHUTDOWN_DELAY segundos ejecuta "sudo shutdown -h now".

Si enabled=False (configuración por defecto hasta tener el hardware), el servicio
no intenta abrir el bus I2C y todos los getters devuelven None. La aplicación
funciona con normalidad sin mostrar nada en pantalla.
"""

from __future__ import annotations

import logging
import subprocess
import threading
import time

log = logging.getLogger(__name__)

# ── Constantes de comportamiento ─────────────────────────────────────────────

POLL_INTERVAL      = 10    # segundos entre lecturas en estado normal
CRITICAL_INTERVAL  =  5    # segundos en estado crítico / shutdown
WARNING_THRESHOLD  = 20.0  # %  — nivel "warning" (aviso visual + status)
CRITICAL_THRESHOLD = 15.0  # %  — nivel "critical" (aviso urgente)
SHUTDOWN_THRESHOLD = 12.0  # %  — nivel "shutdown" (apagado seguro inmediato)
SHUTDOWN_DELAY     = 10    # segundos de margen antes de ejecutar shutdown

# ── Detección de alimentación externa ────────────────────────────────────────
# El voltaje tiene separación clara entre modos (datos reales):
#   • En red:     > 4100 mV  (típico: 4150–4200 mV, float-charging)
#   • En batería: < 4050 mV  (típico: 3990–4040 mV)
# Banda de histéresis 4050–4100 mV: mantiene estado anterior para evitar
# oscilaciones en el límite. Detección en la primera lectura (~30 s).
VOLT_MAINS_MV = 4130   # por encima -> en red/cargando
VOLT_BATT_MV  = 4100   # por debajo -> en bateria
SOC_TREND_EPS = 0.03   # cambio minimo de SOC para considerar tendencia real


class BatteryService:
    """Gestiona la lectura y supervisión del DFR0528 UPS HAT.

    Uso típico en app.py:

        self.battery = BatteryService(
            enabled=cfg.get("ups", {}).get("enabled", False),
            bus=cfg.get("ups", {}).get("i2c_bus", 1),
            address=cfg.get("ups", {}).get("i2c_address", 0x10),
            on_low_battery=self._on_battery_low,
            on_shutdown_required=self._on_battery_shutdown,
        )
        self.battery.start()      # no-op si enabled=False o HAT no presente

        # En render:
        state = self.battery.get_state()   # None si no disponible
    """

    def __init__(
        self,
        enabled: bool = False,
        bus: int = 1,
        address: int = 0x10,
        warning_threshold: float  = WARNING_THRESHOLD,
        critical_threshold: float = CRITICAL_THRESHOLD,
        shutdown_threshold: float = SHUTDOWN_THRESHOLD,
        on_low_battery=None,        # callable(level: str, pct: float) | None
        on_shutdown_required=None,  # callable() | None
    ) -> None:
        self.enabled  = enabled
        self._bus_id  = bus
        self._address = address

        self._warn_thr  = warning_threshold
        self._crit_thr  = critical_threshold
        self._shut_thr  = shutdown_threshold

        self._on_low  = on_low_battery
        self._on_shut = on_shutdown_required

        # Estado interno (protegido por _lock)
        self._lock     = threading.Lock()
        self._soc: float | None   = None
        self._volts: float | None = None   # mV
        self._level: str          = "unknown"
        self._on_mains: bool = True   # asumir red en arranque
        self._last_soc: float | None = None

        self._hat     = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._shutdown_triggered = False

    # ── Ciclo de vida ────────────────────────────────────────────────────────

    def start(self) -> bool:
        """Inicia el hilo de monitoreo.

        Returns:
            True  — HAT encontrado, monitoreo activo.
            False — desactivado por config o HAT no presente (no es un error fatal).
        """
        if not self.enabled:
            log.info("[Battery] servicio desactivado por config (ups.enabled=false)")
            return False

        try:
            from hardware.ups_hat import UPSHat
            hat = UPSHat(bus=self._bus_id, address=self._address)
            hat.open()
            ver = hat.read_version()
            self._hat = hat
            print(f"[Battery] UPS HAT OK — firmware {ver}", flush=True)
        except Exception as exc:
            print(f"[Battery] HAT no disponible: {exc}", flush=True)
            return False

        self._running = True
        self._thread  = threading.Thread(
            target=self._loop, daemon=True, name="battery-monitor"
        )
        self._thread.start()
        return True

    def stop(self) -> None:
        """Detiene el hilo de monitoreo y cierra el bus I2C."""
        self._running = False
        if self._hat is not None:
            try:
                self._hat.close()
            except Exception:
                pass

    # ── Getters thread-safe ──────────────────────────────────────────────────

    @property
    def available(self) -> bool:
        """True si el HAT está presente y el hilo de monitoreo activo."""
        return self._hat is not None

    @property
    def soc(self) -> float | None:
        """Porcentaje de carga, o None si no disponible."""
        with self._lock:
            return self._soc

    @property
    def voltage_mv(self) -> float | None:
        """Voltaje de batería en mV, o None si no disponible."""
        with self._lock:
            return self._volts

    @property
    def level(self) -> str:
        """Nivel actual: 'ok' | 'warning' | 'critical' | 'shutdown' | 'unknown'."""
        with self._lock:
            return self._level

    def get_state(self) -> dict | None:
        """Snapshot thread-safe del estado de batería.

        Returns:
            dict con claves 'soc', 'voltage_mv', 'level', 'on_mains', o None si no disponible.
        """
        if not self.available:
            return None
        with self._lock:
            if self._soc is None:
                return None
            return {
                "soc":        self._soc,
                "voltage_mv": self._volts,
                "level":      self._level,
                "on_mains":   self._on_mains,
            }

    # ── Loop interno ─────────────────────────────────────────────────────────

    def _loop(self) -> None:
        """Hilo daemon: lee batería periódicamente y gestiona alertas."""
        while self._running:
            try:
                soc   = self._hat.read_soc()
                volts = self._hat.read_voltage_mv()
                level = self._classify(soc)

                try:
                    hardware_mains = self._hat.is_on_mains()
                except Exception:
                    hardware_mains = None

                on_mains = self._update_mains_state(soc, volts, hardware_mains)
                with self._lock:
                    self._soc      = soc
                    self._volts    = volts
                    self._level    = level
                    self._on_mains = on_mains

                print(f"[Battery] SOC={soc:.1f}%  V={volts:.0f}mV  level={level}  mains={on_mains}", flush=True)
                self._handle_level(level, soc)

            except Exception as exc:
                print(f"[Battery] error de lectura I2C: {exc}", flush=True)

            # Reducir intervalo cuando la batería está baja
            interval = (
                CRITICAL_INTERVAL
                if self._level in ("critical", "shutdown")
                else POLL_INTERVAL
            )

            # Enviar latido al watchdog del HAT cada ciclo para que sepa que la Pi está viva
            elapsed = 0.0
            while self._running and elapsed < interval:
                try:
                    self._hat.send_watchdog()
                except Exception:
                    pass
                time.sleep(5.0)
                elapsed += 5.0

    def _update_mains_state(self, soc: float, volts: float, hardware_mains: bool | None = None) -> bool:
        """Detecta alimentacion externa combinando SOC, voltaje y bit del HAT.

        La senal mas fiable en este montaje es la tendencia del SOC: si baja,
        esta consumiendo bateria; si sube, esta cargando. Cuando el SOC esta
        clavado al 100%, usamos voltaje y el bit POWAM del HAT como apoyo.
        """
        trend_mains = None
        if self._last_soc is not None:
            delta = soc - self._last_soc
            if delta <= -SOC_TREND_EPS:
                trend_mains = False
            elif delta >= SOC_TREND_EPS:
                trend_mains = True
        self._last_soc = soc
        if trend_mains is not None:
            self._on_mains = trend_mains
            return self._on_mains

        if volts >= VOLT_MAINS_MV:
            self._on_mains = True
        elif volts <= VOLT_BATT_MV:
            self._on_mains = False
        elif hardware_mains is not None:
            self._on_mains = hardware_mains

        return self._on_mains

    def _classify(self, soc: float) -> str:
        if soc <= self._shut_thr:
            return "shutdown"
        if soc <= self._crit_thr:
            return "critical"
        if soc <= self._warn_thr:
            return "warning"
        return "ok"

    def _handle_level(self, level: str, soc: float) -> None:
        # Notificar nivel bajo (warning / critical)
        if level in ("warning", "critical") and self._on_low:
            try:
                self._on_low(level, soc)
            except Exception as exc:
                log.debug("[Battery] callback on_low_battery falló: %s", exc)

        # Apagado seguro — se dispara una sola vez
        if level == "shutdown" and not self._shutdown_triggered:
            self._shutdown_triggered = True
            log.critical(
                "[Battery] SOC=%.1f%% ≤ %.1f%% — apagado seguro en %ds",
                soc, self._shut_thr, SHUTDOWN_DELAY,
            )
            if self._on_shut:
                try:
                    self._on_shut()
                except Exception as exc:
                    log.debug("[Battery] callback on_shutdown_required falló: %s", exc)
            threading.Thread(
                target=self._do_shutdown, daemon=True, name="battery-shutdown"
            ).start()

    def _do_shutdown(self) -> None:
        """Espera SHUTDOWN_DELAY segundos y ejecuta el apagado del sistema."""
        time.sleep(SHUTDOWN_DELAY)
        self._prepare_auto_restart()
        log.critical("[Battery] ejecutando: sudo shutdown -h now")
        try:
            subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
        except Exception as exc:
            log.error("[Battery] shutdown falló: %s", exc)

    def _prepare_auto_restart(self) -> None:
        """Configura el HAT para auto-arrancar cuando vuelva la corriente.

        Escribe el timer de 1 minuto y la señal de shutdown en el MCU del HAT
        antes de que el sistema se apague, de forma que el HAT reinicie la Pi
        automáticamente en cuanto la batería o la corriente externa se recupere.
        """
        if self._hat is None:
            return
        try:
            self._hat.set_auto_restart(minutes=1)
            self._hat.signal_shutdown()
            log.info("[Battery] HAT configurado para auto-arranque en 1 min tras apagado")
        except Exception as exc:
            log.warning("[Battery] no se pudo configurar auto-arranque en el HAT: %s", exc)
