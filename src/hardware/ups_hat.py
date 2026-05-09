"""
ups_hat.py — Driver I2C para DFR0528 UPS HAT (Pi Zero W)

Dirección I2C por defecto: 0x10
Mapa de registros (DFR0528):
  0x01  PID      — Product ID (debe ser 0xDF para confirmar presencia)
  0x02  VERSION  — Firmware (0x10 = V1.0, 0x11 = V1.1, …)
  0x03  VCELL_H  — Voltaje bits 11:8
  0x04  VCELL_L  — Voltaje bits  7:0  (1 LSB = 1.25 mV)
  0x05  SOC_H    — State-of-Charge byte alto
  0x06  SOC_L    — State-of-Charge byte bajo (1 LSB = 0.003906 %)

Registros de control de energía (compatibles con dfups.c de DFRobot):
  0x09  FUNCTION — Flags de función (bits: 4=watchdog, 3=LED, 2=RGB, 1=shutdown, 0=powam)
  0x0D  TIMER_H  — Timer auto-arranque, byte alto (minutos)
  0x0E  TIMER_L  — Timer auto-arranque, byte bajo (minutos)
  0x0F  WATCHDOG — Latido del watchdog (escribir 0x14 cada ≤10s para mantener encendido)

Fórmulas:
  voltage_mv = ((VCELL_H << 8) | VCELL_L) * 1.25
  soc_pct    = ((SOC_H  << 8) | SOC_L)   * 0.003906   →  clamped [0, 100]
  timer_min  = (TIMER_H << 8) | TIMER_L

Auto-arranque tras corte de luz:
  Llamar set_auto_restart(minutes=1) antes de apagar. El MCU del HAT reiniciará
  la Pi automáticamente cuando la batería o la corriente externa se recupere.

Uso mínimo:
  hat = UPSHat()
  hat.open()                        # lanza RuntimeError si no hay hardware
  data = hat.read_all()             # {'voltage_mv': 3850.0, 'soc': 75.2, ...}
  hat.close()
"""

from __future__ import annotations

# ── Registro map ─────────────────────────────────────────────────────────────

REG_PID      = 0x01
REG_VERSION  = 0x02
REG_VCELL_H  = 0x03
REG_VCELL_L  = 0x04
REG_SOC_H    = 0x05
REG_SOC_L    = 0x06

# Registros de control de energía (del protocolo dfups.c de DFRobot)
REG_FUNCTION = 0x09   # flags: bit1=shutdown, bit4=watchdog
REG_TIMER_H  = 0x0D   # minutos para auto-arranque, byte alto
REG_TIMER_L  = 0x0E   # minutos para auto-arranque, byte bajo
REG_WATCHDOG = 0x0F   # latido: escribir 0x14 cada ≤10s

WATCHDOG_BEAT    = 0x14
FLAG_SHUTDOWN    = 0x02   # bit 1 del registro FUNCTION
FLAG_POWAM       = 0x01   # bit 0: alimentación externa presente (power from mains)

EXPECTED_PID  = 0xDF
DEFAULT_ADDR  = 0x10
DEFAULT_BUS   = 1        # I2C-1: SDA=GPIO2 (pin 3), SCL=GPIO3 (pin 5)


class UPSHat:
    """Driver mínimo para el DFR0528 UPS HAT.

    Requiere el paquete smbus2:
        pip install smbus2
    Y que I2C esté habilitado en /boot/firmware/config.txt:
        dtparam=i2c_arm=on   ← ya presente en este proyecto
    """

    def __init__(self, bus: int = DEFAULT_BUS, address: int = DEFAULT_ADDR) -> None:
        self._bus_id  = bus
        self._address = address
        self._bus     = None          # SMBus, se abre en open()

    # ── Ciclo de vida ────────────────────────────────────────────────────────

    def open(self) -> None:
        """Abre el bus I2C y verifica el PID del dispositivo.

        Raises:
            RuntimeError: si smbus2 no está instalado, el HAT no responde,
                          o el PID no coincide.
        """
        try:
            import smbus2
            self._bus = smbus2.SMBus(self._bus_id)
        except ImportError:
            raise RuntimeError(
                "smbus2 no instalado — ejecuta: pip install smbus2"
            )
        except Exception as exc:
            raise RuntimeError(f"No se puede abrir I2C bus {self._bus_id}: {exc}") from exc

        try:
            pid = self._bus.read_byte_data(self._address, REG_PID)
        except OSError as exc:
            self._bus.close()
            self._bus = None
            raise RuntimeError(
                f"UPS HAT no encontrado en I2C bus={self._bus_id} "
                f"addr=0x{self._address:02X}: {exc}"
            ) from exc

        if pid != EXPECTED_PID:
            self._bus.close()
            self._bus = None
            raise RuntimeError(
                f"PID inesperado: 0x{pid:02X} (esperado 0x{EXPECTED_PID:02X}). "
                f"¿Dirección I2C incorrecta?"
            )

    def close(self) -> None:
        """Cierra el bus I2C."""
        if self._bus is not None:
            try:
                self._bus.close()
            except Exception:
                pass
            self._bus = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *_):
        self.close()

    # ── Lecturas ─────────────────────────────────────────────────────────────

    def read_voltage_mv(self) -> float:
        """Voltaje de la batería en mV. Rango típico: 3000–4200 mV."""
        h = self._bus.read_byte_data(self._address, REG_VCELL_H)
        l = self._bus.read_byte_data(self._address, REG_VCELL_L)
        raw = (h << 8) | l
        return raw * 1.25

    def read_soc(self) -> float:
        """State of Charge en porcentaje, 0.0–100.0."""
        h = self._bus.read_byte_data(self._address, REG_SOC_H)
        l = self._bus.read_byte_data(self._address, REG_SOC_L)
        raw = (h << 8) | l
        return min(100.0, max(0.0, raw * 0.003906))

    def read_version(self) -> str:
        """Versión de firmware, p.ej. 'V1.0'."""
        v = self._bus.read_byte_data(self._address, REG_VERSION)
        major = (v >> 4) & 0xF
        minor = v & 0xF
        return f"V{major}.{minor}"

    def read_all(self) -> dict:
        """Devuelve un dict con voltage_mv, soc y version en una sola llamada."""
        return {
            "voltage_mv": self.read_voltage_mv(),
            "soc":        self.read_soc(),
            "version":    self.read_version(),
        }

    # ── Control de energía ───────────────────────────────────────────────────

    def set_auto_restart(self, minutes: int = 1) -> None:
        """Configura el MCU del HAT para reiniciar la Pi automáticamente.

        El HAT arrancará la Pi transcurridos `minutes` minutos tras detectar
        que el sistema se ha apagado (latido del watchdog ausente). Esto también
        persiste en la memoria no volátil del MCU, por lo que funciona incluso
        tras un corte de batería completo cuando vuelve la corriente externa.

        Args:
            minutes: Minutos de espera antes del arranque automático (mínimo 1).
        """
        if minutes < 1:
            minutes = 1
        minutes = min(minutes, 0x7FFF)
        hi = (minutes >> 8) & 0xFF
        lo = minutes & 0xFF
        self._bus.write_byte_data(self._address, REG_TIMER_H, hi)
        self._bus.write_byte_data(self._address, REG_TIMER_L, lo)

    def read_auto_restart(self) -> int:
        """Lee el timer de auto-arranque configurado actualmente (en minutos)."""
        hi = self._bus.read_byte_data(self._address, REG_TIMER_H)
        lo = self._bus.read_byte_data(self._address, REG_TIMER_L)
        return (hi << 8) | lo

    def send_watchdog(self) -> None:
        """Envía un latido al MCU del HAT para mantenerlo activo.

        Debe llamarse cada ≤10 segundos mientras el sistema está encendido.
        Si el latido se detiene, el MCU lo interpreta como que el sistema se
        apagó y pone en marcha el timer de auto-arranque.
        """
        self._bus.write_byte_data(self._address, REG_WATCHDOG, WATCHDOG_BEAT)

    def read_function(self) -> int:
        """Lee el registro FUNCTION (0x09) — bits: 4=watchdog, 3=LED, 2=RGB, 1=shutdown, 0=powam."""
        return self._bus.read_byte_data(self._address, REG_FUNCTION)

    def is_on_mains(self) -> bool:
        """True si hay alimentación externa (corriente de red), False si solo batería.
        POWAM=1 indica modo batería activo (sin corriente externa), de ahí la negación.
        NOTA: este bit no es fiable en todos los firmware del DFR0528.
        Se recomienda usar detección por tendencia de voltaje en battery.py."""
        return not bool(self.read_function() & FLAG_POWAM)

    def signal_shutdown(self) -> None:
        """Notifica al MCU que el sistema va a apagarse intencionalmente."""
        flag = self._bus.read_byte_data(self._address, REG_FUNCTION)
        self._bus.write_byte_data(self._address, REG_FUNCTION, flag | FLAG_SHUTDOWN)
