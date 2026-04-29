# Reloj Despertador - Raspberry Pi Zero W

Reloj despertador con doble pantalla y interfaz meteorológica para Raspberry Pi Zero W.

## Hardware

- **Raspberry Pi Zero W** con microSD 8GB
- **Pantalla A (Redonda)**: GC9A01, 240x240 píxeles, SPI0
- **Pantalla B (Rectangular)**: ST7789, 76x284 píxeles, SPI1
- **Encoder Rotatorio**: 5 pines (A, B, SW, VCC, GND)
- **Altavoz**: MAX98357A (I2S)

## Pantalla Rectangular (76x284)
- Previsión meteorológica de 5 días en formato de tarjetas.
- Tarjetas redondeadas con gradientes de color distintivos (Estilo "Smart Display").
- Temperatura máxima/mínima e iconos del tiempo para cada día.
- Menús y ajustes secundarios.

## Pantalla Redonda (240x240)
- Reloj principal con diseño premium.
- Anillo circular de progreso (segundero) con gradiente dinámico.
- Hora en formato grande y centrado.
- Fecha actual y pronóstico inmediato (temperatura, descripción, icono).
- Interfaz circular para la configuración de alarmas, WiFi y brillo.

## Cableado

### GC9A01 (SPI0)
| Pin | GPIO | BCM |
|-----|------|-----|
| MOSI | GPIO10 | 10 |
| SCK | GPIO11 | 11 |
| CS0 | GPIO8 | 8 |
| DC | GPIO25 | 25 |
| RST | GPIO26 | 26 |
| BL | GPIO12 | 12 |

### ST7789 (SPI1)
| Pin | GPIO | BCM |
|-----|------|-----|
| MOSI | GPIO20 | 20 |
| SCK | GPIO21 | 21 |
| CS0 | GPIO18 | 18 |
| DC | GPIO22 | 22 |
| RST | GPIO27 | 27 |
| BL | GPIO23 | 23 |

### Encoder Rotatorio
| Pin | GPIO | BCM |
|-----|------|-----|
| CLK | GPIO5 | 5 |
| DT | GPIO6 | 6 |
| SW | GPIO13 | 13 |

### MAX98357A (I2S)
| Pin | GPIO | BCM |
|-----|------|-----|
| BCLK | GPIO18 | 18 |
| LRCLK | GPIO19 | 19 |
| DIN | GPIO21 | 21 |

## Instalación

1. Instalar Raspberry Pi OS Lite (64-bit)
2. Ejecutar script de setup:
   ```bash
   bash scripts/setup_pi.sh
   ```
3. Configurar WiFi y API key en `config/config.json`
4. Ejecutar:
   ```bash
   python3 src/main.py
   ```

## Uso del Encoder

- **Girar**: Navegar arriba/abajo en menús
- **Pulsar**: Seleccionar/confirmar
- **Pulsación larga (2s)**: Volver atrás

## API Meteorológica

OpenWeatherMap - `bc0fbcb8537c4c41d664f7ec6b0d6133`
Ubicación: Vila-real, Castellón (39.94°N, 0.10°W)
