# UPS HAT DFR0528 — Documentación de integración

## Hardware

- **Módulo:** DFR0528 UPS HAT para Raspberry Pi Zero
- **Referencia:** https://wiki.dfrobot.com/dfr0528/docs/19883
- **Interfaz:** I2C bus 1 (SDA=GPIO2 pin 3, SCL=GPIO3 pin 5)
- **Dirección I2C:** `0x10` (16 decimal)
- **Batería compatible:** LiPo 3.7 V (conector JST)

---

## Cableado

El HAT se monta directamente sobre el header de 40 pines de la Pi Zero W.
**No requiere cableado adicional** — usa la alimentación y el I2C del header.

Los pines I2C ya están habilitados en `/boot/firmware/config.txt`:
```ini
dtparam=i2c_arm=on   ← ya presente, no tocar
```

---

## Registro map

### Lectura (monitoreo de batería)

| Registro | Nombre  | R/W | Descripción                         |
|----------|---------|-----|-------------------------------------|
| 0x00     | ADDR    | R/W | Dirección I2C esclavo (defecto 0x10)|
| 0x01     | PID     | R   | Product ID — debe ser 0xDF          |
| 0x02     | VERSION | R   | Firmware (0x10=V1.0, 0x11=V1.1…)   |
| 0x03     | VCELL_H | R   | Voltaje bits 11:8                   |
| 0x04     | VCELL_L | R   | Voltaje bits 7:0 (1 LSB = 1.25 mV) |
| 0x05     | SOC_H   | R   | State-of-Charge byte alto           |
| 0x06     | SOC_L   | R   | State-of-Charge byte bajo (LSB = 0.003906 %) |

**Fórmulas:**
```
voltage_mv = ((VCELL_H << 8) | VCELL_L) * 1.25
soc_pct    = ((SOC_H  << 8) | SOC_L)   * 0.003906   → clamp [0, 100]
```

### Control de energía (auto-arranque y watchdog)

Registros compatibles con el protocolo `dfups.c` de DFRobot ([raspberrypi_ups](https://github.com/DFRobot/raspberrypi_ups)):

| Registro | Nombre   | R/W | Descripción                                           |
|----------|----------|-----|-------------------------------------------------------|
| 0x09     | FUNCTION | R/W | Flags: bit4=watchdog, bit3=LED, bit2=RGB, bit1=shutdown, bit0=powam |
| 0x0D     | TIMER_H  | R/W | Timer auto-arranque, byte alto (minutos)              |
| 0x0E     | TIMER_L  | R/W | Timer auto-arranque, byte bajo (minutos)              |
| 0x0F     | WATCHDOG | W   | Latido del MCU: escribir `0x14` cada ≤ 10 s           |

```python
# Leer/escribir timer (minutos):
timer = (TIMER_H << 8) | TIMER_L
```

---

## Archivos del proyecto

| Archivo | Función |
|---------|---------|
| `src/hardware/ups_hat.py` | Driver I2C de bajo nivel + control de energía |
| `src/services/battery.py` | Servicio de monitoreo (hilo daemon) + shutdown seguro |
| `src/ui/round_home.py` | Indicador visual en pantalla redonda |
| `src/app.py` | Integración con la app principal |
| `config/config.json` → sección `ups` | Configuración (ON/OFF, umbrales) |
| `scripts/ups_watchdog.py` | Daemon de latido I2C + configuración auto-arranque al boot |
| `scripts/ups-watchdog.service` | Servicio systemd del watchdog |
| `scripts/ups_auto_start.py` | Herramienta de diagnóstico y configuración puntual |
| `scripts/install_ups_auto_start.sh` | Instalador del servicio watchdog |
| `scripts/deploy_ups_auto_start.py` | Script de deploy desde el PC al Pi |

---

## Configuración (`config/config.json`)

```json
"ups": {
    "enabled": false,          ← cambiar a true al instalar el HAT
    "i2c_bus": 1,
    "i2c_address": 16,         ← 0x10 en decimal
    "warning_threshold": 20,   ← % para aviso "batería baja"
    "shutdown_threshold": 2    ← % para apagado seguro
}
```

---

## Auto-arranque tras corte de corriente

> [!NOTE]
> Problema resuelto: cuando la batería se agotaba completamente y volvía la electricidad, la Pi no arrancaba sola — había que pulsar el botón del HAT manualmente.

### Causa

El MCU del DFR0528 arranca en modo **"espera botón"** por defecto. Para que cambie a modo **"arranque automático"** hay que escribir un timer en los registros `0x0D-0x0E`. El MCU almacena este valor en **memoria no volátil (flash)**, por lo que persiste aunque la batería se agote del todo.

### Mecanismo

```
Pi arranca
   └─► ups-watchdog.service inicia
         └─► Escribe timer = 1 min en el MCU  (persiste en flash)
         └─► Envía latido I2C cada 5 s

Corte de corriente → batería se agota → Pi se apaga
   └─► battery.py llama set_auto_restart(1) + signal_shutdown() antes de shutdown

MCU pierde corriente → flash conserva timer = 1 min

Vuelve la electricidad
   └─► MCU arranca, lee timer almacenado (1 min)
   └─► Espera 1 minuto
   └─► Enciende la Pi automáticamente ✓
```

### Instalación en la Pi (primera vez)

```bash
# Desde el PC de desarrollo:
python3 scripts/deploy_ups_auto_start.py

# O manualmente en la Pi:
sudo bash /home/dani/reloj_despertador/scripts/install_ups_auto_start.sh
```

### Verificar que funciona

```bash
# En la Pi:
sudo systemctl status ups-watchdog.service

# Ver logs en tiempo real:
sudo journalctl -u ups-watchdog.service -f

# Comprobar timer configurado:
python3 /home/dani/reloj_despertador/scripts/ups_auto_start.py --info
```

Salida esperada:
```
[UPS] HAT V1.0 — SOC=85%
[UPS] Auto-arranque configurado: 1 min tras corte de corriente
```

### Ajustar el tiempo de espera

Por defecto: **1 minuto** (suficiente para que la batería se estabilice).

Para cambiarlo, editar `AUTO_RESTART_MINUTES` en `scripts/ups_watchdog.py` y reiniciar:
```bash
sudo systemctl restart ups-watchdog.service
```

---

## Pasos para activar (cuando llegue el HAT)

### 1. Instalar dependencia en la Pi

```bash
ssh dani@192.168.0.204
pip install smbus2
```

O añadirlo a `requirements.txt` antes de hacer deploy:
```
smbus2
```

### 2. Verificar detección I2C (opcional, diagnóstico)

```bash
i2cdetect -y 1
# Debe aparecer 0x10 en la tabla
```

### 3. Activar en config

En `config/config.json` cambiar:
```json
"ups": {
    "enabled": true,    ← ESTE cambio activa todo
    ...
}
```

### 4. Deploy

```bash
cd D:\Reloj_despertador
python deploy_win.py
```

### 5. Verificar logs

```bash
ssh dani@192.168.0.204
sudo journalctl -u reloj.service -f
```

Debe aparecer:
```
[Battery] UPS HAT OK — firmware V1.0
```

Si falla:
```
[Battery] HAT no disponible: UPS HAT no encontrado en I2C bus=1 addr=0x10
```

---

## Comportamiento en producción

### Indicador visual (pantalla redonda, 240×240)

Posición: X=177, Y=148 — lado derecho, simétrico al icono de alarma.

```
┌──────────────────┬──┐
│ relleno SOC %    │+ │  ← cuerpo 22×12px + polo +
└──────────────────┴──┘
        85%              ← porcentaje centrado debajo
```

**Código de colores:**

| Nivel       | % batería  | Color            | Efecto        |
|-------------|-----------|------------------|---------------|
| `ok`        | > 20%     | Verde (60,200,80)| Estático      |
| `warning`   | 10–20%    | Amarillo         | Estático      |
| `critical`  | 2–10%     | Naranja          | Estático      |
| `shutdown`  | ≤ 2%      | Rojo             | Parpadeo      |

El indicador aparece en modo **día, amanecer, atardecer y noche**.
Si el HAT no está instalado (`enabled: false`) no se dibuja nada.

### Alertas de texto (`self.status`)

- **Batería baja (warning):** `"Batería baja 18% — conecta cargador"`
- **Crítico (critical):**  `"BATERÍA CRÍTICA 8%"`
- **Apagado inminente:**  `"BATERÍA AGOTADA — APAGANDO"`

### Apagado seguro

Cuando SOC ≤ `shutdown_threshold` (2% por defecto):

1. Se activa `_on_battery_shutdown()` en la app
2. La pantalla muestra `"BATERÍA AGOTADA — APAGANDO"`
3. Tras **10 segundos**, `battery.py` llama a:
   - `hat.set_auto_restart(minutes=1)` → graba timer en flash del MCU
   - `hat.signal_shutdown()` → notifica al MCU que el apagado es intencional
4. El servicio ejecuta `sudo shutdown -h now`
5. La Pi se apaga limpiamente sin corrupción de SD
6. Cuando vuelva la corriente (o la batería se recupere), el MCU arrancará la Pi automáticamente en 1 minuto

---

## Polling y rendimiento

| Estado    | Intervalo de lectura |
|-----------|---------------------|
| Normal    | 30 s                |
| Critical  | 5 s                 |
| Shutdown  | 5 s (hasta apagar)  |

El hilo de batería es **daemon** — no bloquea el shutdown de la app.
El bus I2C es independiente del SPI de las pantallas; no hay conflicto.

---

## Solución de problemas

### Monitoreo de batería

| Síntoma | Causa probable | Solución |
|---------|---------------|----------|
| `smbus2 no instalado` | Falta pip | `pip install smbus2` en la Pi |
| `UPS HAT no encontrado en I2C bus=1 addr=0x10` | HAT no conectado o I2C no habilitado | Verificar físicamente; `i2cdetect -y 1` |
| `PID inesperado: 0xXX` | Dirección I2C incorrecta | Revisar `i2c_address` en config |
| No aparece indicador en pantalla | `enabled: false` en config | Cambiar a `true` |
| SOC siempre 0% | HAT sin batería conectada | Conectar LiPo al conector JST |

### Auto-arranque

| Síntoma | Causa probable | Solución |
|---------|---------------|----------|
| Pi no arranca sola tras corte | `ups-watchdog.service` no instalado | `sudo bash scripts/install_ups_auto_start.sh` |
| Timer muestra 0 min | Registros de control no accesibles en este firmware | Ver nota abajo |
| `ups-watchdog.service` en estado `failed` | HAT no presente al arrancar | Normal si el HAT no está conectado; el servicio sale limpiamente |
| Pi arranca pero watchdog no aparece en logs | systemd no habilitó el servicio | `sudo systemctl enable --now ups-watchdog.service` |

> [!WARNING]
> **Nota sobre compatibilidad de registros:** El mapa de registros de control de energía (0x09, 0x0D-0x0F) está documentado en el `dfups.c` de DFRobot para el modelo original (dirección I2C 0x18). El DFR0528 usa dirección 0x10; si los registros de control no responden, puede ser necesario también probar con address=0x18 en `ups_watchdog.py`. Verificar con `i2cdetect -y 1` si aparece `0x18` además de `0x10`.
