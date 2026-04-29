# Reconstruccion 2026-04-28

## Objetivo

La app anterior estaba rota: ninguna de las dos pantallas renderizaba de forma
fiable. La reconstruccion busca una base mas simple, robusta y visualmente clara:

- Pantalla redonda como reloj principal.
- Pantalla rectangular como prediccion semanal y menu.
- Encoder rotatorio como unico control de usuario.
- Arranque resistente aunque fallen NTP, red o clima.
- Graficos coloridos, iconos detallados y buena legibilidad.

## Resultado Desplegado

Desplegado en Raspberry Pi Zero W el 2026-04-28.

Verificacion tras reiniciar `reloj.service`:

- Servicio: `active (running)`.
- Pantalla redonda GC9A01: inicializa OK.
- Pantalla rectangular ST7789P3: inicializa OK.
- Encoder: inicializa OK.
- Audio I2S: inicializa OK.
- NTP: sincroniza OK.
- Clima: OneCall devuelve 401, pero fallback clasico obtiene clima actual.

Backup creado antes del despliegue:

```text
/home/dani/reloj_despertador_backup_20260428_052038/
```

## Cambios Principales

### Controlador principal

Archivo: `src/main.py`

Se sustituyo el flujo anterior por una maquina de estados compacta:

- `clock`: reloj principal.
- `menu`: menu principal.
- `alarm`: configuracion de alarma.
- `brightness`: brillo de pantallas.
- `wifi_scan`: busqueda de redes.
- `wifi_password`: teclado WiFi.
- `alarm_ringing`: alarma sonando.

Las tareas lentas se lanzan en segundo plano:

- Sincronizacion NTP.
- Actualizacion meteorologica.
- Escaneo WiFi.
- Conexion WiFi.

Esto evita que la interfaz deje de refrescar por red lenta o API fallando.

### Interfaz redonda

Archivo: `src/ui/round_home.py`

Nueva pantalla principal:

- Hora grande centrada.
- Fecha y dia.
- Icono meteorologico actual.
- Temperatura, humedad y viento.
- Barra de progreso entre amanecer y anochecer.
- Estado lunar por la noche.
- Indicacion de alarma activa.

Tambien se usa como pantalla de foco en menu, alarma, brillo, WiFi y alarma
sonando.

### Interfaz rectangular

Archivo: `src/ui/rect_ui.py`

Nueva pantalla auxiliar:

- Prediccion de hasta 7 dias.
- Tarjetas compactas con gradientes.
- Iconos meteorologicos dibujados.
- Maxima y minima por dia.
- Menu principal.
- Pantalla de alarma.
- Pantalla de brillo.
- Lista de redes WiFi.
- Teclado compacto por grupos.

### Iconos y helpers graficos

Archivo: `src/graphics/icons.py`

Se centralizaron:

- Carga de fuentes.
- Ajuste de texto a ancho disponible.
- Gradientes.
- Mascara circular.
- Iconos de sol, nube, lluvia, tormenta, nieve, niebla, luna y parcialmente nublado.

### Driver ST7789P3

Archivo: `src/hardware/st7789.py`

Configuracion actual validada tras diagnostico de hardware y patrones:

- Tamano logico: `284x76`.
- SPI: `spi0.1`.
- Velocidad: 4 MHz.
- Secuencia de inicializacion tipo BuyDisplay / ER-TFTM2.25-1.
- `MADCTL=0xA8`.
- `COLMOD=0x05`.
- `col_offset=18`.
- `row_offset=82`.
- Backlight activo LOW.
- CS en `GPIO7` controlado por software (`spi.no_cs=True` cuando esta disponible).
- Envio con `writebytes2` y fallback por chunks.

### Driver GC9A01

Archivo: `src/hardware/gc9a01.py`

Cambios:

- Soporta `bl_pin=null` sin fallar.
- Usa `writebytes2` cuando esta disponible.
- Mantiene fallback por chunks.

### Encoder

Archivo: `src/hardware/rotary_encoder.py`

Se reemplazo el uso de `GPIO.add_event_detect` por polling.

Motivo:

- En systemd fallaba con `Failed to add edge detection`.
- El polling es suficiente para menus.
- Evita problemas de permisos o backend GPIO.

### Clima

Archivo: `src/services/weather.py`

Nuevo servicio con fallback:

1. Intenta OpenWeather OneCall 3.0.
2. Intenta OpenWeather OneCall 2.5.
3. Si falla, usa endpoints clasicos `weather` y `forecast`.
4. Si todo falla, devuelve datos de reserva para que la UI siga dibujando.

Estado observado:

- OneCall devuelve 401.
- Endpoint clasico funciona y devuelve clima actual.

Pendiente:

- Habilitar OneCall o cambiar de proveedor si se necesita prediccion diaria real
  de 7 dias.

### Reloj y sol

Archivos:

- `src/services/clock.py`
- `src/services/sun.py`

Cambios:

- NTP ya no bloquea el arranque.
- `ntplib` es opcional.
- Calculos de amanecer/anochecer devuelven horas locales.
- Si el calculo astronomico falla, hay fallback horario.

### Servicio systemd

Archivo: `scripts/reloj.service`

Estado final:

```ini
[Unit]
Description=Reloj Despertador
After=network.target

[Service]
User=dani
WorkingDirectory=/home/dani/reloj_despertador
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 -u src/main.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Se mantiene `User=dani` porque las dependencias Python instaladas estan
disponibles para ese usuario. El encoder ya no depende de interrupciones GPIO,
por lo que se evita el fallo anterior.

## Configuracion Actual

Archivo: `config/config.json`

Cambios importantes:

- `displays.round.bl_pin` pasa a `null`.
- `displays.rect.width` pasa a `284`.
- `displays.rect.height` pasa a `76`.
- `displays.rect.col_offset` pasa a `18`.
- `displays.rect.row_offset` pasa a `82`.
- Region y pais quedan en ASCII para evitar problemas de codificacion.

## Pruebas Realizadas

En local:

```bash
python -m py_compile ...
python test_ui.py
```

Con el runtime empaquetado se generaron:

- `test_clock_round.png`
- `test_forecast_rect.png`
- `test_menu_rect.png`
- `test_wifi_keyboard_rect.png`

Comprobacion automatica:

- `test_clock_round.png`: 240x240, no vacia.
- `test_forecast_rect.png`: 284x76, no vacia.
- `test_menu_rect.png`: 284x76, no vacia.
- `test_wifi_keyboard_rect.png`: 284x76, no vacia.

En la Pi:

```text
ACTIVE=active
[HW] round display OK
[HW] rect display OK
[HW] encoder OK
[HW] audio OK
[Main] starting
[Clock] NTP synced with pool.ntp.org
[Weather] updated: cielo claro
```

## Limitaciones Conocidas

- No se pudo verificar visualmente el hardware desde la sesion remota.
- OneCall no esta autorizado con la configuracion actual.
- La prediccion semanal puede ser limitada si se usa solo el endpoint clasico.
- El teclado WiFi es funcional pero basico: grupos de caracteres, OK y borrar.

## Proximos Pasos

1. Verificar fisicamente que ambas pantallas muestran la UI nueva.
2. Probar giro, pulsacion corta y pulsacion larga del encoder.
3. Probar menu de brillo en ambas pantallas.
4. Probar configuracion WiFi con una red real.
5. Probar alarma con audio.
6. Decidir proveedor para prediccion semanal real si OpenWeather OneCall no se habilita.
