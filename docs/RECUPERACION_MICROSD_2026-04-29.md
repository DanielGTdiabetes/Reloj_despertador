# Recuperacion microSD limpia - 2026-04-29

## Contexto aplicado

Esta preparacion parte de la memoria de Obsidian y del estado local del proyecto
tras la incidencia de la pantalla rectangular.

Reglas criticas:

- No volver a SPI1. Entra en conflicto con I2S/MAX98357A.
- Mantener la ST7789P3 rectangular en variante E.
- No desplegar un `config/config.json` que borre el bloque `wifi` remoto.
- No seguir ajustando el encoder hasta recuperar visualmente la ST7789.

## Configuracion buena de pantalla rectangular

- Panel: ST7789P3 284x76.
- SPI: `spi0.1`, 4 MHz.
- CS: `GPIO7`, controlado por software.
- DC: `GPIO22`.
- RST: `GPIO27`.
- BL: `GPIO23`, activo LOW.
- `MADCTL=0xA8`.
- `COLMOD=0x05`.
- `col_offset=18`.
- `row_offset=82`.

## Flujo cuando la microSD este lista

1. Arrancar la Raspberry Pi Zero W con la microSD nueva.
2. Confirmar que tiene red y SSH activo.
3. Localizar la IP si cambia respecto a `192.168.0.204`.
4. Ejecutar desde Windows:

```powershell
$env:PI_HOST="192.168.0.204"
python .\deploy_win.py
```

Si la IP es distinta, cambiar `PI_HOST`.

El despliegue:

- Empaqueta `src`, `config`, `scripts`, `requirements.txt` y `README.md`.
- Excluye `__pycache__` y `.pyc`.
- Copia el paquete a `/home/dani/reloj_despertador`.
- Ejecuta `scripts/bootstrap_fresh_pi.sh` si existe.
- Instala dependencias de sistema.
- Activa SPI0 e I2S/MAX98357A.
- Desactiva SPI1 si estaba presente.
- Instala y reinicia `reloj.service`.

## Validacion esperada

En los logs deben aparecer estas lineas:

```text
[HW] round display OK
[HW] rect display OK
[HW] encoder OK
[HW] audio OK
```

Comandos utiles en la Pi:

```bash
sudo systemctl status reloj.service --no-pager -l
sudo journalctl -u reloj.service -n 80 --no-pager
ls -l /dev/spidev0.*
```

## Si la pantalla rectangular sigue en blanco

1. Parar y no ajustar encoder.
2. Cortar alimentacion fisica completa de Raspberry y pantallas durante 20-30 s.
3. Revisar cable RST de la ST7789P3.
4. Confirmar que existen `/dev/spidev0.0` y `/dev/spidev0.1`.
5. Revisar logs antes de tocar codigo.
