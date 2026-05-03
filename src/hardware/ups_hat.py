"""
ups_hat.py — Driver I2C para DFR0528 UPS HAT (Pi Zero W)

Dirección I2C por defecto: 0x10
Mapa de registros:
  0x01  PID      — Product ID (debe ser 0xDF para confirmar presencia)
  0x02  VERSION  — Firmware (0x10 = V1.0, 0x11 = V1.1, …)
  0x03  VCELL_H  — Voltaje bits 11:8
  0x04  VCELL_L  — Voltaje bits  7:0  (1 LSB = 1.25 mV)
  0x05  SOC_H    — State-of-Charge byte alto
  0x06  SOC_L    — State-of-Charge byte bajo (1 LSB = 0.003906 %)

Fórmulas:
  voltage_mv = ((VCELL_H << 8) | VCELL_L) * 1.25
  soc_pct    = ((SOC_H  << 8) | SOC_L)   * 0.003906   →  clamped [0, 100]

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
