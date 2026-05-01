
from PIL import Image, ImageOps
import os

def process_icon(input_path, output_path, color):
    # Abrir y convertir a escala de grises para usar como máscara
    img = Image.open(input_path).convert("L")
    
    # Invertir si el fondo es negro y el icono blanco
    # (El icono blanco tendrá valores altos, el fondo bajos)
    
    # Crear una nueva imagen del color deseado con transparencia
    colored_img = Image.new("RGBA", img.size, color)
    
    # Usar la imagen original como máscara de transparencia
    # Los pixeles blancos (icono) serán opacos, los negros (fondo) transparentes
    colored_img.putalpha(img)
    
    # Recortar bordes vacíos
    bbox = colored_img.getbbox()
    if bbox:
        colored_img = colored_img.crop(bbox)
    
    # Redimensionar a un tamaño estándar de icono (p.ej. 128x128) para que sean uniformes
    colored_img = colored_img.resize((128, 128), Image.LANCZOS)
    
    colored_img.save(output_path)
    print(f"Processed: {output_path}")

# Rutas de entrada
clock_in = r"C:\Users\danie\.gemini\antigravity\brain\8de439e2-3a7e-4f7b-9cb3-da7c62be6508\v2_alarm_clock_icon_1777656036365.png"
sun_in = r"C:\Users\danie\.gemini\antigravity\brain\8de439e2-3a7e-4f7b-9cb3-da7c62be6508\v2_brightness_icon_1777656055415.png"

# Rutas de salida
clock_out = r"d:\Reloj_despertador\src\assets\menu_icons\alarm_clock.png"
sun_out = r"d:\Reloj_despertador\src\assets\menu_icons\brightness.png"

# Colores (RGBA)
CYAN = (0, 255, 255, 255)
GOLD = (255, 190, 0, 255)

if __name__ == "__main__":
    process_icon(clock_in, clock_out, CYAN)
    process_icon(sun_in, sun_out, GOLD)
