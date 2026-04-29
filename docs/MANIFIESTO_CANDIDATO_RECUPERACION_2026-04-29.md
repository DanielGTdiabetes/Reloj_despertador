# Manifiesto candidato recuperacion - 2026-04-29

Este manifiesto fija la version local candidata antes de probar la microSD
limpia. Si el hardware funciona, usar esta lista como referencia para limpiar
copias, scripts temporales y versiones antiguas.

## Criterio

- ST7789P3 rectangular en variante E.
- Offsets rectangulares `col_offset=18`, `row_offset=82`.
- SPI0.1 para rectangular, SPI0.0 para redonda.
- SPI1 desactivado.
- Encoder por polling.
- Despliegue con preservacion del bloque `wifi` remoto.

## Archivos criticos

| Archivo | Bytes | Modificado | SHA256 |
|---|---:|---|---|
| `src/main.py` | 23197 | 2026-04-29 14:10:16 | `86e5831cec48516850da42f1a05b44dde68698934f9fa766c3687ef085ce0444` |
| `src/hardware/st7789.py` | 5820 | 2026-04-29 06:07:34 | `bc03cce141f373a69c036c0ce8b4ece3ed1c2b2f0bdf90e07f0494ddd35f6c08` |
| `src/hardware/gc9a01.py` | 7747 | 2026-04-29 06:07:34 | `5e903cd32c15c0a28557fc15aa135f96a141fb993e964b9fe1faf2a85154de82` |
| `src/hardware/rotary_encoder.py` | 3996 | 2026-04-29 06:07:34 | `8daebf9877e50db3d9b793a6d6f5d064f98090be0d1df764f3c0215adcee08a4` |
| `src/hardware/audio.py` | 2296 | 2026-04-29 06:07:34 | `cb5a5355571089a1f332da3681401e10be3ac23d0873f66ab783b37ed78a658e` |
| `src/ui/rect_ui.py` | 15667 | 2026-04-29 06:07:34 | `650f4517aa5088fb24fa6f80a7c07c88dc8d3b431378921fe0226376980d00d1` |
| `src/ui/round_home.py` | 8796 | 2026-04-29 06:07:34 | `a0425002e6dea11b3970ddb869240dee8d661d25b857a13158e21a14073dac78` |
| `src/graphics/icons.py` | 9262 | 2026-04-29 06:07:34 | `e587d5fcb25b79411fec0164f748a4f4b5db0c3f60130f0e2e7551ea2a76c644` |
| `src/services/weather.py` | 7840 | 2026-04-29 06:07:34 | `2f07dd91e26bf9017a97a56ea118c3a24c637b2d347e1550c25f16355f233163` |
| `config/config.json` | 2015 | 2026-04-29 06:07:34 | `0046b8910e99219a3e8e1b734caa40ad288a462be54b391c0b5a7ea8333dd404` |
| `scripts/bootstrap_fresh_pi.sh` | 2276 | 2026-04-29 04:55:34 | `fad5c5cdbed964af227dc3c6ce344f0740b45c13c8687a45e9ab34aad7723eb1` |
| `scripts/reloj.service` | 329 | 2026-04-29 06:07:34 | `f176fbf17c72c9ffc711e5470c5dcdba343862baf8b0fc2a985db456483c1605` |
| `requirements.txt` | 197 | 2026-04-29 06:07:34 | `414986ea9ec82fe5cda5f27f2121fb315a3cd3dfc78c24f7251fcc02d72ee660` |
| `README.md` | 4702 | 2026-04-29 06:07:34 | `d179893ef3552aea0a4dc5b1c3495f90d0697da3203346329f1aaaa5b6036496` |

## Paquete generado

- `project_updated.tar`
- Entradas: 52
- `__pycache__` incluido: no
- `.pyc` incluido: no

## Limpieza pendiente si funciona

- Crear una rama o commit estable con este manifiesto.
- Eliminar o mover a archivo historico scripts temporales de debug/fix.
- Eliminar copias extraidas antiguas como `_tar_extract`, `project_updated`,
  `project_updated_downloaded` si ya no hacen falta.
- Regenerar un README minimo de operacion y dejar la recuperacion documentada.
