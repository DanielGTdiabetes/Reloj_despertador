# Backup base microSD - 2026-04-30

## Identificacion

- Ubicacion en BMAX: `/home/dani/backups/reloj_despertador/baseline_sd_20260430_043028`
- Origen: microSD de la Raspberry Pi Zero W, leida offline desde el BMAX.
- Ruta del proyecto en la imagen: `/home/dani/reloj_despertador`
- Hostname de la Raspberry en la imagen: `despertador`
- Estado de red al capturar: la Raspberry no conectaba por WiFi ni respondia en `192.168.0.204`.

## Estado funcional que representa

Esta copia debe tratarse como base de recuperacion de codigo y hardware de pantallas,
no como una imagen completa plenamente funcional de red.

- Pantallas: base considerada buena. La configuracion valida es GC9A01 redonda en SPI0 CE0 y ST7789P3 rectangular en SPI0 CE1, variante `E`.
- ST7789P3: `MADCTL=0xA8`, `COLMOD=0x05`, `col_offset=18`, `row_offset=82`, SPI0.1 a 4 MHz.
- Audio: MAX98357A por I2S.
- Encoder: polling, no `GPIO.add_event_detect`.
- WiFi: roto/no operativo en el momento del backup. No usar esta copia como prueba de conectividad.

## Contenido guardado

El directorio del backup contiene:

- `pi_home_reloj_despertador.tar.gz`: copia del codigo desplegado en la Raspberry.
- `pi_bootfs_config.tar.gz`: `config.txt`, `cmdline.txt`, `network-config` y `meta-data` de la particion boot.
- `pi_system_wifi_service_snapshot.tar.gz`: snapshot de hostname, hosts, fstab, servicio `reloj.service`, NetworkManager/wpa_supplicant y logs disponibles.
- `project_file_manifest.tsv`: manifiesto de archivos del proyecto en la microSD.
- `SHA256SUMS.txt`: hashes de los tarballs.
- `WIFI_FIX_APPLIED.txt`: nota del arreglo posterior de WiFi aplicado offline.

## Arreglo posterior al backup

Despues de crear el backup se aplico un arreglo offline minimo en la misma microSD:

- Se creo `/etc/NetworkManager/system-connections/MOVISTAR_PLUS_6_2.nmconnection`.
- La configuracion se extrajo de `bootfs/network-config`.
- Permisos del perfil: `root:root`, modo `0600`.
- No se modifico codigo de la app.
- No se modifico `config.txt`.

## Regla de uso

Para rollback de codigo, usar primero `pi_home_reloj_despertador.tar.gz`.
Para diagnostico de red, recordar que el estado original del backup no tenia WiFi operativo;
si se restaura literalmente, puede ser necesario reaplicar o revisar el perfil de NetworkManager.
