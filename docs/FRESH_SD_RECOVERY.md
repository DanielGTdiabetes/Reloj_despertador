# Recuperacion desde microSD limpia

## Contexto recuperado de Obsidian

- Proyecto local: `D:\Reloj_despertador`.
- Proyecto en la Raspberry Pi: `/home/dani/reloj_despertador`.
- Servicio: `reloj.service`.
- La version estable usa dos pantallas:
  - GC9A01 redonda 240x240 en SPI0 CE0.
  - ST7789P3 rectangular 284x76 en SPI0 CE1.
- No activar SPI1: entra en conflicto con I2S/MAX98357A.
- ST7789P3 debe mantenerse en variante `E`: `MADCTL=0xA8`, `COLMOD=0x05`, `col_offset=18`, `row_offset=82`, SPI0.1 a 4 MHz.
- El encoder usa polling. No volver a `GPIO.add_event_detect`.
- No desplegar `config/config.json` pisando el bloque `wifi` remoto. `deploy_win.py` preserva `wifi` si ya existe en la Pi.

## Preparar Raspberry Pi Imager

Usa Raspberry Pi OS Lite para Pi Zero W y configura antes de grabar:

- Usuario: `dani`.
- SSH activado.
- WiFi configurado desde Imager.
- Locale/timezone: `Europe/Madrid`.
- Hostname recomendado: `reloj`.

Despues del primer arranque, busca la IP nueva en el router o prueba:

```powershell
ping reloj.local
```

## Desplegar desde Windows

Desde `D:\Reloj_despertador`:

```powershell
$env:PI_HOST="reloj.local"
$env:PI_USER="dani"
$env:PI_PASS="TU_PASSWORD_DE_LA_PI"
python deploy_win.py
```

Si conoces la IP, usa por ejemplo:

```powershell
$env:PI_HOST="192.168.0.204"
python deploy_win.py
```

El despliegue:

1. Empaqueta `src`, `config`, `scripts`, `requirements.txt` y `README.md`.
2. Copia el paquete a `/home/dani/reloj_despertador`.
3. Extrae la app.
4. Preserva el bloque `wifi` remoto si existe.
5. Ejecuta `scripts/bootstrap_fresh_pi.sh`.
6. Instala dependencias, activa SPI/I2S/MAX98357A, instala `reloj.service` y lo arranca.

## Validar en la Pi

```bash
sudo systemctl status reloj.service --no-pager -l
sudo journalctl -u reloj.service -n 80 --no-pager
```

Logs esperados:

```text
[HW] round display OK
[HW] rect display OK
[HW] encoder OK
[HW] audio OK
[Main] starting
```

Si el bootstrap acaba de activar SPI/I2S, reinicia una vez:

```bash
sudo reboot
```

## Configuracion de hardware esperada

En `/boot/firmware/config.txt` o `/boot/config.txt`:

```ini
dtparam=spi=on
dtparam=i2s=on
dtoverlay=max98357a
```

No usar:

```ini
dtparam=audio=on
dtoverlay=spi1-3cs
```
