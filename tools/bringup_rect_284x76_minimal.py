import RPi.GPIO as GPIO
import spidev
import time
import sys

def main():
    print("[MINIMAL] Iniciando prueba mínima ST7789 284x76")
    
    # Pines
    CS_PIN = 16
    DC_PIN = 22
    RST_PIN = 27
    BL_PIN = 23
    
    print(f"[MINIMAL] Pines configurados: CS={CS_PIN}, DC={DC_PIN}, RST={RST_PIN}, BL={BL_PIN}")
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    GPIO.setup(CS_PIN, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(DC_PIN, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(RST_PIN, GPIO.OUT, initial=GPIO.HIGH)
    
    # Backlight ON (Active LOW)
    GPIO.setup(BL_PIN, GPIO.OUT, initial=GPIO.LOW)
    print("[MINIMAL] Backlight encendido (GPIO23 LOW)")
    
    # SPI
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 20_000_000
    spi.mode = 0
    spi.no_cs = True
    print("[MINIMAL] SPI abierto en /dev/spidev0.0 a 20MHz")
    
    def write_cmd(cmd, data=None):
        GPIO.output(CS_PIN, GPIO.LOW)
        GPIO.output(DC_PIN, GPIO.LOW)
        spi.writebytes([cmd])
        if data:
            GPIO.output(DC_PIN, GPIO.HIGH)
            spi.writebytes(list(data))
        GPIO.output(CS_PIN, GPIO.HIGH)
        # print(f"[MINIMAL] Comando 0x{cmd:02X} enviado" + (f" con {len(data)} bytes de datos" if data else ""))

    def set_window(x0, y0, x1, y1):
        print(f"[MINIMAL] Enviando set_window({x0}, {y0}, {x1}, {y1})")
        write_cmd(0x2A, [x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF])
        write_cmd(0x2B, [y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF])
    
    try:
        # Hardware Reset
        print("[MINIMAL] Ejecutando Hardware Reset")
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.02)
        GPIO.output(RST_PIN, GPIO.LOW)
        time.sleep(0.12)
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.2)
        
        # Init Sequence
        print("[MINIMAL] Enviando secuencia de inicialización...")
        print("[MINIMAL] SWRESET 0x01")
        write_cmd(0x01)
        time.sleep(0.18)
        
        print("[MINIMAL] SLPOUT 0x11")
        write_cmd(0x11)
        time.sleep(0.15)
        
        print("[MINIMAL] COLMOD 0x3A (0x55)")
        write_cmd(0x3A, [0x55])
        
        print("[MINIMAL] MADCTL 0x36 (0x00)")
        write_cmd(0x36, [0x00])
        
        print("[MINIMAL] INVON 0x21")
        write_cmd(0x21)
        
        print("[MINIMAL] NORON 0x13")
        write_cmd(0x13)
        time.sleep(0.01)
        
        print("[MINIMAL] DISPON 0x29")
        write_cmd(0x29)
        time.sleep(0.1)
        print("[MINIMAL] Inicialización completada.")
        
        WIDTH = 284
        HEIGHT = 76
        
        # Secuencia de colores: (Nombre, byte_high, byte_low) en RGB565
        colors = [
            ("Rojo", 0xF8, 0x00),
            ("Verde", 0x07, 0xE0),
            ("Azul", 0x00, 0x1F),
            ("Blanco", 0xFF, 0xFF),
            ("Negro", 0x00, 0x00),
        ]
        
        for name, hi, lo in colors:
            print(f"[MINIMAL] Dibujando color {name}...")
            set_window(0, 0, WIDTH - 1, HEIGHT - 1)
            
            # Preparar buffer
            pixels = WIDTH * HEIGHT
            # SPI writebytes2 espera bytes. Multiplicamos la pareja de bytes por el número de píxeles.
            pixel_data = bytes([hi, lo]) * pixels
            print(f"[MINIMAL] Enviando RAMWR 0x2C con {len(pixel_data)} bytes ({pixels} píxeles)")
            
            # RAMWR
            GPIO.output(CS_PIN, GPIO.LOW)
            GPIO.output(DC_PIN, GPIO.LOW)
            spi.writebytes([0x2C])
            GPIO.output(DC_PIN, GPIO.HIGH)
            # spi.writebytes2 is more efficient and safer for large payloads
            spi.writebytes2(pixel_data)
            GPIO.output(CS_PIN, GPIO.HIGH)
            
            time.sleep(1.0)
            
        print("[MINIMAL] Prueba finalizada correctamente.")
        
    except Exception as e:
        print(f"[MINIMAL] Error: {e}")
    finally:
        print("[MINIMAL] Limpiando recursos...")
        # Apagar backlight
        GPIO.output(BL_PIN, GPIO.HIGH)
        spi.close()
        GPIO.cleanup()
        print("[MINIMAL] Salida limpia.")

if __name__ == "__main__":
    main()
