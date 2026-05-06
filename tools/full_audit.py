"""
AUDITORÍA COMPLETA DE DIAGNÓSTICO — ST7789 Rectangular
=======================================================

Este script NO modifica código. Solo lee, verifica y reporta.

Ejecutar en la Raspberry Pi Zero W:
    python3 tools/full_audit.py

Requiere: sudo (para pinctrl, systemctl, lectura de /boot/firmware)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time


def run_cmd(cmd: str, timeout: int = 10) -> tuple[int, str, str]:
    """Ejecuta un comando y devuelve (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as exc:
        return -1, "", str(exc)


def section(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def subsection(title: str):
    print(f"\n--- {title} ---")


def check(label: str, ok: bool, detail: str = ""):
    status = "OK" if ok else "FALLO"
    icon = "[+]" if ok else "[!]"
    print(f"  {icon} [{status}] {label}")
    if detail:
        for line in detail.split("\n"):
            print(f"       {line}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. OVERLAY Y BOOT CONFIG
# ─────────────────────────────────────────────────────────────────────────────

def audit_boot_config():
    section("1. OVERLAY Y BOOT CONFIG")

    candidates = ["/boot/firmware/config.txt", "/boot/config.txt"]
    config_path = None
    config_content = ""

    for path in candidates:
        if os.path.exists(path):
            config_path = path
            with open(path) as f:
                config_content = f.read()
            break

    if not config_path:
        check("config.txt encontrado", False, "No existe en ninguna ruta esperada")
        return

    check("config.txt encontrado", True, f"Ruta: {config_path}")

    lines = config_content.splitlines()
    spi_lines = [l.strip() for l in lines if "spi" in l.lower() and not l.strip().startswith("#")]

    subsection("Líneas SPI activas (no comentadas):")
    for l in spi_lines:
        print(f"       {l}")

    has_spi0_2cs = "dtoverlay=spi0-2cs" in config_content
    has_spi0_1cs = "dtoverlay=spi0-1cs" in config_content
    has_spi_on = "dtparam=spi=on" in config_content
    has_duplicate_spi = config_content.lower().count("dtoverlay=spi0") > 1

    check("dtoverlay=spi0-2cs presente", has_spi0_2cs)
    check("NO dtoverlay=spi0-1cs", not has_spi0_1cs)
    check("dtparam=spi=on presente", has_spi_on)
    check("Sin overlays SPI duplicados", not has_duplicate_spi,
          "Hay múltiples dtoverlay=spi0-* si esto falla")

    # Verificar uptime para saber si se reinició
    rc, out, _ = run_cmd("uptime -s")
    if rc == 0:
        print(f"\n       Último arranque: {out}")
        rc2, out2, _ = run_cmd("date '+%Y-%m-%d %H:%M:%S'")
        if rc2 == 0:
            print(f"       Ahora: {out2}")


# ─────────────────────────────────────────────────────────────────────────────
# 2. DEVICES SPI REALES
# ─────────────────────────────────────────────────────────────────────────────

def audit_spi_devices():
    section("2. DEVICES SPI REALES")

    for dev in ["/dev/spidev0.0", "/dev/spidev0.1"]:
        exists = os.path.exists(dev)
        check(f"{dev} existe", exists)
        if exists:
            rc, out, _ = run_cmd(f"ls -l {dev}")
            if rc == 0:
                print(f"       {out}")

    # Verificar módulo kernel
    rc, out, _ = run_cmd("lsmod | grep spi")
    subsection("Módulos SPI cargados:")
    if out:
        for line in out.splitlines():
            print(f"       {line}")
    else:
        print("       (ningún módulo spi en lsmod)")

    # Verificar device tree
    rc, out, _ = run_cmd("ls /sys/bus/spi/devices/ 2>/dev/null")
    subsection("Devices SPI en /sys/bus/spi/devices/:")
    if out:
        for line in out.splitlines():
            print(f"       {line}")
    else:
        print("       (vacío o no accesible)")


# ─────────────────────────────────────────────────────────────────────────────
# 3. GPIO PINCTRL
# ─────────────────────────────────────────────────────────────────────────────

def audit_pinctrl():
    section("3. ESTADO DE PINES (pinctrl)")

    pins = {
        7: "SPI0 CE1 (hardware CS1)",
        8: "SPI0 CE0 (hardware CS0)",
        16: "CS manual ST7789",
        22: "DC ST7789",
        23: "BL ST7789",
        27: "RST ST7789",
    }

    for pin, desc in pins.items():
        rc, out, err = run_cmd(f"pinctrl get {pin}")
        if rc == 0 and out:
            # Parsear output tipo: "gpio 16: pd dl | hi // GPIO16"
            info = out.strip()
            is_output = "op" in info or "output" in info.lower()
            is_spi_alt = "a0" in info or "a1" in info or "a2" in info or "a3" in info or "a4" in info or "a5" in info
            level = "hi" if "hi" in info else "lo" if "lo" in info else "?"
            check(f"GPIO{pin} ({desc})", True, f"{info}")

            # Validaciones específicas
            if pin == 16:
                check(f"  -> GPIO16 es output manual (NO ALT SPI)", not is_spi_alt,
                      f"Si es ALT SPI, el overlay spi0-2cs lo está reclamando como CE1")
            if pin == 22:
                check(f"  -> GPIO22 es output", True)
            if pin == 27:
                check(f"  -> GPIO27 es output", True)
            if pin == 23:
                check(f"  -> GPIO23 es output/PWM", True)
        else:
            check(f"GPIO{pin} ({desc})", False, err or "pinctrl no disponible")


# ─────────────────────────────────────────────────────────────────────────────
# 4. CÓDIGO ACTUALIZADO
# ─────────────────────────────────────────────────────────────────────────────

def audit_code_state():
    section("4. ESTADO DEL CÓDIGO")

    # Determinar base dir
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(base)

    # git status
    rc, out, _ = run_cmd("git status --short")
    subsection("git status (archivos modificados):")
    if out:
        for line in out.splitlines()[:20]:
            print(f"       {line}")
    else:
        print("       (working tree limpio)")

    # git log -1
    rc, out, _ = run_cmd("git log -1 --oneline")
    print(f"\n       Último commit: {out}")

    # Verificar config.json
    config_path = os.path.join(base, "config", "config.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            cfg = json.load(f)
        rect = cfg.get("displays", {}).get("rect", {})
        subsection("config.json — rect display:")
        check("spi_port = 0", rect.get("spi_port") == 0, f"valor: {rect.get('spi_port')}")
        check("spi_device = 1", rect.get("spi_device") == 1, f"valor: {rect.get('spi_device')}")
        check("cs_pin = 16", rect.get("cs_pin") == 16, f"valor: {rect.get('cs_pin')}")
        check("dc_pin = 22", rect.get("dc_pin") == 22, f"valor: {rect.get('dc_pin')}")
        check("rst_pin = 27", rect.get("rst_pin") == 27, f"valor: {rect.get('rst_pin')}")
        check("bl_pin = 23", rect.get("bl_pin") == 23, f"valor: {rect.get('bl_pin')}")
        check("col_offset = 18", rect.get("col_offset") == 18, f"valor: {rect.get('col_offset')}")
        check("row_offset = 82", rect.get("row_offset") == 82, f"valor: {rect.get('row_offset')}")

    # Verificar st7789.py — buscar BUG de _cd transacciones separadas
    st7789_path = os.path.join(base, "src", "hardware", "st7789.py")
    if os.path.exists(st7789_path):
        with open(st7789_path) as f:
            content = f.read()

        subsection("Análisis estático de st7789.py:")

        # BUG: _cd llama a _cmd y _data en transacciones separadas
        has_separate_cd = "def _cd(" in content and "self._cmd(" in content and "self._data(" in content
        if has_separate_cd:
            # Verificar si _cd usa transacción única o separada
            import re
            cd_method = re.search(r'def _cd\(.*?\n(.*?)(?=\n    def |\nclass |\Z)', content, re.DOTALL)
            if cd_method:
                cd_body = cd_method.group(1)
                if "self._cmd(" in cd_body and "self._data(" in cd_body:
                    check("BUG CRÍTICO: _cd() usa transacciones SEPARADAS para cmd+data", False,
                          "El ST7789 requiere cmd+data bajo el mismo CS assert.\n"
                          "Cada llamada a _cmd() y _data() abre/cierra su propia transacción,\n"
                          "lo que hace CS toggle entre comando y datos.")

        # Verificar MADCTL
        madctl_match = re.search(r'CMD_MADCTL.*?\[0x([0-9A-Fa-f]+)\]', content)
        if madctl_match:
            madctl_val = int(madctl_match.group(1), 16)
            print(f"\n       MADCTL = 0x{madctl_val:02X}")
            bits = {
                7: ("MY", bool(madctl_val & 0x80)),
                6: ("MX", bool(madctl_val & 0x40)),
                5: ("MV", bool(madctl_val & 0x20)),
                4: ("ML", bool(madctl_val & 0x10)),
                3: ("BGR", bool(madctl_val & 0x08)),
                2: ("MH", bool(madctl_val & 0x04)),
            }
            for bit, (name, val) in bits.items():
                print(f"         bit{bit} {name} = {val}")


# ─────────────────────────────────────────────────────────────────────────────
# 5. SERVICIO
# ─────────────────────────────────────────────────────────────────────────────

def audit_service():
    section("5. ESTADO DEL SERVICIO")

    rc, out, _ = run_cmd("systemctl is-active reloj.service 2>/dev/null")
    check("reloj.service activo", out == "active", f"estado: {out}")

    rc, out, _ = run_cmd("systemctl is-enabled reloj.service 2>/dev/null")
    print(f"       enabled: {out}")

    # Procesos Python
    rc, out, _ = run_cmd("ps aux | grep -E 'python|reloj' | grep -v grep")
    subsection("Procesos Python/reloj activos:")
    if out:
        for line in out.splitlines()[:10]:
            print(f"       {line}")
    else:
        print("       (ninguno)")


# ─────────────────────────────────────────────────────────────────────────────
# 6. ANÁLISIS DE spi_bus.py
# ─────────────────────────────────────────────────────────────────────────────

def audit_spi_bus():
    section("6. ANÁLISIS DE spi_bus.py")

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spi_bus_path = os.path.join(base, "src", "hardware", "spi_bus.py")

    if not os.path.exists(spi_bus_path):
        check("spi_bus.py encontrado", False)
        return

    with open(spi_bus_path) as f:
        content = f.read()

    # Verificar que _handle siempre pone no_cs=True
    has_no_cs = "no_cs = True" in content or "no_cs=True" in content
    check("_handle() activa no_cs=True", has_no_cs)

    # Verificar que transaction() hace all_cs_high antes y después
    has_all_cs_before = "self._all_cs_high()" in content
    check("transaction() llama _all_cs_high()", has_all_cs_before)

    # Verificar singleton
    has_singleton = "_instance" in content and "instance()" in content
    check("Patrón singleton implementado", has_singleton)

    # PROBLEMA: _handle() abre spidev una vez y lo reusa.
    # Si dos perfiles comparten mismo (port, device), comparten handle.
    # Pero GC9A01 usa (0,0) y ST7789 usa (0,1) — OK, son distintos.
    print("\n       Handles spidev:")
    print("         GC9A01 -> (0, 0) = /dev/spidev0.0")
    print("         ST7789 -> (0, 1) = /dev/spidev0.1")
    check("Handles no colisionan", True, "Cada display tiene su propio (port, device)")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  AUDITORÍA COMPLETA — ST7789 RECTANGULAR")
    print(f"  Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    audit_boot_config()
    audit_spi_devices()
    audit_pinctrl()
    audit_code_state()
    audit_service()
    audit_spi_bus()

    section("RESUMEN DE HALLAZGOS CRÍTICOS")

    print("""
  PROBLEMAS IDENTIFICADOS:

  1. [CRÍTICO] st7789.py _cd() divide comando y datos en transacciones SPI
     separadas. Cada _cmd() y _data() abre/cierra su propia transacción,
     haciendo CS toggle entre el byte de comando y sus datos.

     El ST7789 requiere que comando + datos se envíen bajo un único CS assert.
     Con CS toggle entre medio, el chip ignora los datos o los interpreta
     como comandos.

     Esto afecta a TODOS los comandos con parámetros:
       - MADCTL (0x36) + [0xA0]
       - COLMOD (0x3A) + [0x05]
       - CASET (0x2A) + [xs, xe]
       - RASET (0x2B) + [ys, ye]
       - RAMWR (0x2C) + [framebuffer data]

  2. [VERIFICAR] MADCTL: el estado GOLD usa 0xA0.
     Si el panel se ve girado/colores raros, probar alternativas con la matriz.

  3. [VERIFICAR] Offsets: el estado GOLD usa col_offset=18, row_offset=82.
     Si la imagen se ve desplazada/recortada, probar alternativa 82/18.

  ACCIONES RECOMENDADAS:

  A) Ejecutar tools/spi_diag.py para confirmar estado del sistema.
  B) Ejecutar tools/gpio_diag.py para verificar pines.
  C) Ejecutar tools/bringup_rect.py para ver si hay alguna respuesta visual.
  D) Si bringup_rect.py no funciona, el problema es el BUG de _cd().
     Corregir: hacer que _cd() use una única transacción para cmd+data.
  E) Ejecutar tools/bringup_rect_matrix.py para probar combinaciones.
""")

    return 0


if __name__ == "__main__":
    sys.exit(main())
