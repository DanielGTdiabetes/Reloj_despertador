# Estado de Restauración: Niebla
Fecha: 2026-05-01

Este documento registra la configuración exacta que permitió recuperar la actividad en ambas pantallas (Redonda OK, Rectangular con Niebla/Ruido).

## Referencia Git
- **Commit**: `a2aa28f`
- **Mensaje**: "checkpoint: reached 'niebla' state with correct physical pin mapping and forced backlight"

## Configuración de Hardware (Pines BCM)
### Bus SPI0 (Pines Físicos 19, 21, 23, 24, 26)
| Periférico | CS (Pin) | DC (Pin) | RST (Pin) | BL (Pin) |
| :--- | :--- | :--- | :--- | :--- |
| **Redonda (GC9A01)** | 8 (24) | 25 (22) | 26 (37) | N/A |
| **Rectangular (ST7789)** | 7 (26) | 22 (15) | 27 (13) | 23 (16) |

## Configuración de Pantalla Rectangular (ST7789)
- **Bus**: SPI 0, Device 1.
- **Offsets**: `col_offset=82`, `row_offset=18`.
- **Inversion**: `False` (`CMD_INVOFF`).
- **Rotation**: `270` (`MADCTL=0xA8`).
- **Backlight**: Activo-LOW (0 = ON). Forzado a ON en el driver para diagnóstico.

## Notas de Diagnóstico
- La "niebla" en la pantalla rectangular confirma que:
  1. El cableado es correcto (llega reloj y datos).
  2. El bus SPI0 está correctamente compartido.
  3. La inicialización básica está ocurriendo.
  4. El backlight está operativo.
