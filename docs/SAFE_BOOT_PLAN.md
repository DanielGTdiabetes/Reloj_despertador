# Safe boot + diagnóstico (Reloj_despertador)

Este documento describe el arranque por fases y el modo seguro para evitar que un fallo de hardware (pantallas, encoder, audio) o de servicios (clima/red) deje la Raspberry Pi en estado “ciego”.

## Objetivo

- Arrancar siempre (aunque falle una pantalla).
- Inicializar subsistemas de forma aislada y tolerante a fallos.
- Disponer de scripts de diagnóstico independientes sin arrancar toda la app.

## Variables de entorno (modo seguro)

El arranque admite flags por variables de entorno:

- `SAFE_MODE=1`: desactiva por defecto audio y actualizaciones remotas (clima) y evita tareas accesorias.
- `DISABLE_ROUND=1`: no inicializa la pantalla redonda.
- `DISABLE_RECT=1`: no inicializa la pantalla rectangular.
- `DISABLE_ENCODER=1`: no inicializa el encoder.
- `DISABLE_AUDIO=1`: no inicializa audio.
- `DISABLE_WEATHER=1`: no actualiza clima (usa fallback local).

Ejemplos:

- Probar pantallas sin red ni audio: `SAFE_MODE=1`
- Probar solo rectangular: `DISABLE_ROUND=1 DISABLE_WEATHER=1 DISABLE_AUDIO=1`
- Recuperación “a ciegas” sin encoder: `DISABLE_ENCODER=1`

## Ejecución

- App (systemd): `python3 -u src/main.py` (entrypoint mínimo, lógica en `src/app.py`)
- App (modo seguro): `SAFE_MODE=1 python3 -u src/main.py`

## Orden de arranque (fases)

1. Carga de config.
2. Logging.
3. Estado interno (sin hardware).
4. Inicialización pantalla redonda (aislada).
5. Inicialización pantalla rectangular (aislada).
6. Inicialización encoder.
7. Inicialización audio.
8. Servicios externos (clima, NTP).
9. Loop principal (eventos + render).

## Scripts de diagnóstico

Los scripts viven en `scripts/` y están pensados para ejecutarse en la Raspberry Pi desde el directorio del proyecto:

- `scripts/test_round_display.py`
- `scripts/test_rect_display.py`
- `scripts/test_both_displays.py`
- `scripts/test_encoder.py`
- `scripts/test_audio.py`
- `scripts/test_weather_assets.py`
- `scripts/healthcheck.py`

Cada script:

- carga `config/config.json`
- inicializa solo su subsistema
- imprime parámetros reales (SPI bus/device, pines, offsets)
- muestra un patrón visual o ejecuta una acción simple
- sale limpiamente (cleanup)
