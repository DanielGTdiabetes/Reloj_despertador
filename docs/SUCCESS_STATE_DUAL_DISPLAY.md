# Estado de Éxito: Pantallas Duales Operativas
Fecha: 2026-05-01

Este documento registra la configuración final y validada que permite el funcionamiento simultáneo de la pantalla redonda y la rectangular compartiendo el bus SPI0 en una Raspberry Pi Zero.

## Referencia Git
- **Commit**: `[PENDIENTE TRAS EL PRÓXIMO COMMIT]`
- **Estado**: Funcional al 100% (Imagen clara en ambas pantallas).

## Configuración de Hardware Definitiva
### Bus SPI0 (Pines Físicos del Pi Zero)
| Pin Físico | Función SPI | BCM / GPIO | Nota |
| :--- | :--- | :--- | :--- |
| **19** | MOSI (SDA) | 10 | Compartido |
| **23** | SCLK (SCL) | 11 | Compartido |
| **24** | CE0 (CS) | 8 | Redonda |
| **26** | CE1 (CS) | 7 | Rectangular |

### Otros Pines de Control
| Periférico | Función | Pin Físico | BCM / GPIO |
| :--- | :--- | :--- | :--- |
| **Redonda** | DC | 22 | 25 |
| **Redonda** | RST | 37 | 26 |
| **Rectangular** | DC | 15 | 22 |
| **Rectangular** | RST | 13 | 27 |
| **Rectangular** | BL | 16 | 23 |

## Configuración de Software Validada (ST7789)
- **Controlador**: `st7789.py` (Versión con bus compartido y bloqueo global).
- **Offsets**: `col_offset=18`, `row_offset=82`.
- **MADCTL**: `0xA8` (Rotación 270 / BGR).
- **Color Inversion**: `False` (`CMD_INVOFF`).
- **SPI Speed**: 4 MHz (Para máxima estabilidad en bus compartido).

## Notas Técnicas
- El problema original de la "niebla" se solucionó intercambiando los offsets (originalmente se pensaba que eran 82/18 y resultaron ser 18/82 para esta variante de panel).
- El backlight está configurado como activo-LOW (0 = ON).
