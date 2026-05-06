
import sys
import os

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    from hardware.ups_hat import UPSHat
    print("[DIAG] Intentando abrir UPS HAT en I2C bus 1, addr 0x10...")
    hat = UPSHat(bus=1, address=0x10)
    hat.open()
    print(f"[DIAG] HAT detectado!")
    print(f"[DIAG] Versión: {hat.read_version()}")
    print(f"[DIAG] Voltaje: {hat.read_voltage_mv()} mV")
    print(f"[DIAG] SOC:     {hat.read_soc()}%")
    hat.close()
except Exception as e:
    print(f"[DIAG] ERROR al acceder al HAT: {e}")

try:
    import smbus2
    print("[DIAG] smbus2 está instalado.")
except ImportError:
    print("[DIAG] ERROR: smbus2 NO está instalado.")

print("[DIAG] Verificando i2c-tools...")
os.system("i2cdetect -y 1")
