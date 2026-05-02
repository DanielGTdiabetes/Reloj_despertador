# Estado de Éxito: Pantallas Duales Operativas
Fecha última actualización: 2026-05-02

## Referencia Git
- **Tag**: `v1.0-coldboot-fix`
- **Estado**: Funcional. Cold boot resuelto definitivamente.

## Resumen del fix de cold boot (2026-05-02)

El CS del ST7789 se movió de GPIO7 (pin físico 26, CE1 hardware) a **GPIO16 (pin físico 36, GPIO normal)**.

**Causa del bug**: `dtparam=spi=on` hace que el kernel configure GPIO7 como CE1 hardware al boot. Ese pin puede quedar en LOW brevemente durante la inicialización del overlay, enviando una señal espuria al CS del display antes de que Python arranque. El chip queda en estado parcial.

**Fix**: GPIO16 es un GPIO normal que el kernel no toca. Con `dtoverlay=spi0-1cs` en config.txt (solo CE0), `/dev/spidev0.1` ya no existe y GPIO7 queda libre.

## Configuración de Hardware Definitiva

### Bus SPI0
| Pin Físico | Función | BCM / GPIO | Nota |
| :--- | :--- | :--- | :--- |
| **19** | MOSI | 10 | Compartido |
| **23** | SCLK | 11 | Compartido |
| **24** | CE0 (CS redonda) | 8 | Kernel CE0 |
| **36** | CS rectangular | 16 | GPIO normal — NO CE hardware |

### Otros pines de control
| Periférico | Función | Pin Físico | BCM / GPIO |
| :--- | :--- | :--- | :--- |
| Redonda | DC | 22 | 25 |
| Redonda | RST | 37 | 26 |
| Rectangular | DC | 15 | 22 |
| Rectangular | RST | 13 | 27 |
| Rectangular | BL | 16 | 23 |

## Configuración Software Validada

### config.json displays
```json
{
  "round": {
    "spi_port": 0, "spi_device": 0,
    "cs_pin": 8, "dc_pin": 25, "rst_pin": 26, "bl_pin": null
  },
  "rect": {
    "spi_port": 0, "spi_device": 0,
    "cs_pin": 16, "dc_pin": 22, "rst_pin": 27, "bl_pin": 23,
    "col_offset": 18, "row_offset": 82
  }
}
```

### /boot/firmware/config.txt
```ini
dtoverlay=spi0-1cs
dtparam=i2c_arm=on
dtoverlay=max98357a
camera_auto_detect=0
display_auto_detect=0
```

### ST7789 parámetros validados
- MADCTL: `0xA8` | COLMOD: `0x05` | INVOFF
- col_offset: 18, row_offset: 82
- Backlight activo-LOW en GPIO23
