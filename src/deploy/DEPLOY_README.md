# Despliegue — Instrucciones

## Archivos a copiar a la Pi

### Archivos NUEVOS (no existían antes):
```
deploy/src/ui/weather_icons.py          →  src/ui/weather_icons.py
deploy/src/assets/menu_icons/alarm.png  →  src/assets/menu_icons/alarm.png
deploy/src/assets/menu_icons/wifi.png   →  src/assets/menu_icons/wifi.png
deploy/src/assets/menu_icons/sync.png   →  src/assets/menu_icons/sync.png
deploy/src/assets/menu_icons/weather.png→  src/assets/menu_icons/weather.png
deploy/src/assets/menu_icons/location.png→ src/assets/menu_icons/location.png
```

### Archivos a REEMPLAZAR:
```
deploy/src/ui/round_home.py     →  src/ui/round_home.py
deploy/src/ui/rect_ui.py        →  src/ui/rect_ui.py
deploy/src/ui/theme.py          →  src/ui/theme.py
```

### Parche en app.py (NO reemplazar el archivo completo):
El archivo `deploy/PATCH_app_py.py` contiene el método `_render_round()` actualizado.
Abrir `src/app.py` y reemplazar SOLO el método `_render_round()` con el que aparece en el parche.
El cambio es mínimo: añade 4 líneas con la condición de noche y enriquece current con temp_max/min.

---

## Secuencia de despliegue segura

```bash
# 1. Hacer backup (ya tienes uno, pero por si acaso)
cd /home/pi/Reloj_despertador
tar czf backup_antes_ui_$(date +%Y%m%d).tar.gz src/ui/

# 2. Copiar archivos nuevos
cp deploy/src/ui/weather_icons.py src/ui/
cp deploy/src/ui/round_home.py    src/ui/
cp deploy/src/ui/rect_ui.py       src/ui/
cp deploy/src/ui/theme.py         src/ui/
mkdir -p src/assets/menu_icons
cp deploy/src/assets/menu_icons/*.png src/assets/menu_icons/
echo "Archivos copiados OK"

# 3. Editar app.py — reemplazar _render_round()
# (ver deploy/PATCH_app_py.py)
nano src/app.py

# 4. Test rápido sin hardware
python3 -c "from ui.weather_icons import render_weather_icon; render_weather_icon('lluvia').save('/tmp/test.png'); print('OK')"

# 5. Reiniciar servicio
sudo systemctl restart reloj.service
sudo journalctl -u reloj.service -f
```

---

## Qué cambia visualmente

| Pantalla | Antes | Después |
|----------|-------|---------|
| Redonda — día | Iconos PNG bitmap pequeños | Iconos PNG 3D alta calidad, arco solar con progreso |
| Redonda — noche | Igual que día | Luna por fases, estrellas, pulso nocturno |
| Redonda — foco | Iconos dibujados simples | Iconos coloridos por categoría |
| Rect — pronóstico | 4 días (incluyendo hoy) | 4 días siguientes (sin hoy) |
| Rect — menú | 4 ítems | 5 ítems (+ Ubicación) |
| Rect — ubicación | No existía | 5 cajas de dígito con CP activo resaltado |

---

## Novedades funcionales

- **Pantalla de noche**: cuando `SunService.get_time_of_day()` devuelve `"night"`,
  la pantalla redonda muestra la luna con su fase real (calculada por `LunarService`).
- **Código postal**: Menú → Ubicación → introduce 5 dígitos con el encoder →
  llama a OWM Geocoding API → actualiza lat/lon en config.json → recarga el tiempo.
- **Temp min/max**: se muestra en la pantalla de día (tomado del forecast día 0).
- **Badge alarma**: campana reconocible + hora + días activos (L-V, S-D, etc).
- **Arco solar**: el arco exterior muestra el progreso del día en tiempo real.

---

## Dependencias — sin cambios

No se añade ninguna dependencia Python nueva.
`weather_icons.py` usa solo `PIL` (Pillow), que ya está instalado.
