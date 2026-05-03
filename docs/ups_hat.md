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

---

## Archivos del proyecto

| Archivo | Función |
|---------|---------|
| `src/hardware/ups_hat.py` | Driver I2C de bajo nivel |
| `src/services/battery.py` | Servicio de monitoreo (hilo daemon) |
| `src/ui/round_home.py` | Indicador visual en pantalla redonda |
| `src/app.py` | Integración con la app principal |
| `config/config.json` → sección `ups` | Configuración (ON/OFF, umbrales) |

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
3. Tras **10 segundos** el servicio ejecuta `sudo shutdown -h now`
4. La Pi se apaga limpiamente sin corrupción de SD

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

| Síntoma | Causa probable | Solución |
|---------|---------------|----------|
| `smbus2 no instalado` | Falta pip | `pip install smbus2` en la Pi |
| `UPS HAT no encontrado en I2C bus=1 addr=0x10` | HAT no conectado o I2C no habilitado | Verificar físicamente; `i2cdetect -y 1` |
| `PID inesperado: 0xXX` | Dirección I2C incorrecta | Revisar `i2c_address` en config |
| No aparece indicador en pantalla | `enabled: false` en config | Cambiar a `true` |
| SOC siempre 0% | HAT sin batería conectada | Conectar LiPo al conector JST |
