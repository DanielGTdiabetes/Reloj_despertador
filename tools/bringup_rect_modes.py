import sys
import os
import time
from PIL import Image, ImageDraw

# Asegurar que el modulo principal sea accesible
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.hardware.st7789 import ST7789Display
from src.hardware.spi_bus import SpiBus

INIT_MODES = [False, True]
COLMODS = [0x05, 0x55]
MADCTLS = [0xA8, 0x70, 0x00, 0x60]
OFFSETS = [(18, 82), (82, 18), (0, 0)]

SPI_PORT = 0
SPI_DEVICE = 1
CS_PIN = 16

def test_config(init_ext, colmod, madctl, offset):
    print("=" * 60)
    print(f"Probando configuración:")
    print(f"  init_extended : {init_ext} (Falso = Mínima, Verdadero = Extendida)")
    print(f"  colmod        : 0x{colmod:02X}")
    print(f"  madctl        : 0x{madctl:02X}")
    print(f"  col_offset    : {offset[0]}")
    print(f"  row_offset    : {offset[1]}")
    print(f"  spi_device    : {SPI_DEVICE}")
    print(f"  cs_pin        : {CS_PIN}")
    print(f"  velocidad SPI : 24MHz (frame) / 4MHz (init)")
    print("-" * 60)

    try:
        # Forzar un bus limpio
        SpiBus.instance().close()
        time.sleep(0.1)

        display = ST7789Display(
            spi_port=SPI_PORT,
            spi_device=SPI_DEVICE,
            cs_pin=CS_PIN,
            col_offset=offset[0],
            row_offset=offset[1],
            init_extended=init_ext,
            madctl_val=madctl,
            colmod_val=colmod
        )

        # Crear imagen de prueba (Rectángulo con bordes y cruz para comprobar offsets y orientación)
        img = Image.new("RGB", (ST7789Display.WIDTH, ST7789Display.HEIGHT), "black")
        draw = ImageDraw.Draw(img)
        
        # Borde rojo para verificar que no esté cortado
        draw.rectangle((0, 0, ST7789Display.WIDTH-1, ST7789Display.HEIGHT-1), outline="red", width=2)
        
        # Cruz central verde para verificar orientación
        draw.line((0, 0, ST7789Display.WIDTH-1, ST7789Display.HEIGHT-1), fill="green", width=1)
        draw.line((0, ST7789Display.HEIGHT-1, ST7789Display.WIDTH-1, 0), fill="green", width=1)
        
        # Textos informativos
        draw.text((10, 10), f"MADCTL: 0x{madctl:02X}", fill="white")
        draw.text((10, 30), f"EXT: {init_ext}", fill="white")
        draw.text((10, 50), f"OFF: {offset[0]},{offset[1]}", fill="white")

        display.display(img)
        display.set_brightness(50)
        
        print(">>> Observa la pantalla.")
        print(">>> Presiona ENTER para probar la siguiente combinación, o 'q' + ENTER para salir...")
        cmd = input().strip().lower()
        
        display.cleanup()
        SpiBus.instance().close()
        
        if cmd == 'q':
            return False
        return True
        
    except Exception as e:
        print(f"ERROR al inicializar o probar: {e}")
        try:
            SpiBus.instance().close()
        except:
            pass
        print(">>> Presiona ENTER para continuar a pesar del error, o 'q' para salir...")
        cmd = input().strip().lower()
        if cmd == 'q':
            return False
        return True

def main():
    print("Iniciando herramienta interactiva de prueba ST7789...")
    print("Se iterará por todas las combinaciones.")
    
    for ext in INIT_MODES:
        for cm in COLMODS:
            for md in MADCTLS:
                for off in OFFSETS:
                    if not test_config(ext, cm, md, off):
                        print("Pruebas canceladas por el usuario.")
                        return
                        
    print("Todas las combinaciones han sido probadas.")

if __name__ == "__main__":
    main()
