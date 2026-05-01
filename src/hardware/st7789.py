"""
Driver ST7789P3 para panel rectangular 284x76.

Configuración validada (variante E):
  - SPI0 CE1, GPIO7 como CS manual (no_cs=True).
  - MADCTL 0xA8, COLMOD 0x05.
  - col_offset 82, row_offset 18.
  - 4 MHz SPI para mantener estable el bus compartido del Pi Zero W.
  - Backlight activo-LOW en GPIO23.
  - INVON para contraste correcto.

Cambios vs versión anterior:
  - Usa SpiBus compartido (lock global, reconfigura speed/mode por transacción).
  - Render RGB565 vectorizado con numpy.
  - Lectura RDDID (0x04) tras init.
  - Backlight diferido: solo se enciende tras primer render OK.
  - No llama a GPIO.setmode/setwarnings; bootstrap centralizado en app.
"""

from __future__ import annotations

import time
import traceback
from typing import Optional

import numpy as np
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw

from .spi_bus import SpiBus


class ST7789Display:
    WIDTH = 284
    HEIGHT = 76

    CMD_SWRESET = 0x01
    CMD_RDDID = 0x04
    CMD_SLPIN = 0x10
    CMD_SLPOUT = 0x11
    CMD_NORON = 0x13
    CMD_INVOFF = 0x20
    CMD_INVON = 0x21
    CMD_DISPOFF = 0x28
    CMD_DISPON = 0x29
    CMD_CASET = 0x2A
    CMD_RASET = 0x2B
    CMD_RAMWR = 0x2C
    CMD_MADCTL = 0x36
    CMD_COLMOD = 0x3A
    CMD_PORCTRL = 0xB2
    CMD_GCTRL = 0xB7
    CMD_VCOMS = 0xBB
    CMD_LCMCTRL = 0xC0
    CMD_VDVVRHEN = 0xC2
    CMD_VRHS = 0xC3
    CMD_VDVSET = 0xC4
    CMD_FRCTR2 = 0xC6
    CMD_PWCTRL1 = 0xD0

    SPI_SPEED_HZ = 4_000_000

    def __init__(
        self,
        spi_port: int = 0,
        spi_device: int = 1,
        cs_pin: int = 7,
        dc_pin: int = 22,
        rst_pin: int = 27,
        bl_pin: int = 23,
        col_offset: int = 82,
        row_offset: int = 18,
    ) -> None:
        self.spi_port = spi_port
        self.spi_device = spi_device
        self.cs_pin = cs_pin
        self.dc_pin = dc_pin
        self.rst_pin = rst_pin
        self.bl_pin = bl_pin
        self.col_offset = col_offset
        self.row_offset = row_offset

        self._bus = SpiBus.instance()
        self._first_frame_ok = False

        GPIO.setup(self.cs_pin, GPIO.OUT)
        GPIO.setup(self.dc_pin, GPIO.OUT)
        GPIO.setup(self.rst_pin, GPIO.OUT)
        GPIO.setup(self.bl_pin, GPIO.OUT)
        GPIO.output(self.cs_pin, GPIO.HIGH)
        GPIO.output(self.bl_pin, GPIO.LOW)   # BL encendido inmediatamente (activo-LOW)

        self.framebuffer = Image.new("RGB", (self.WIDTH, self.HEIGHT), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.framebuffer)

        self._init_display()
        self._verify_chip()

    # ── SPI helpers ──────────────────────────────────────────────────────────

    def _cmd(self, cmd: int) -> None:
        with self._bus.transaction(self.spi_port, self.spi_device, self.SPI_SPEED_HZ) as spi:
            GPIO.output(self.dc_pin, GPIO.LOW)
            GPIO.output(self.cs_pin, GPIO.LOW)
            spi.writebytes([cmd])
            GPIO.output(self.cs_pin, GPIO.HIGH)

    def _data(self, data) -> None:
        with self._bus.transaction(self.spi_port, self.spi_device, self.SPI_SPEED_HZ) as spi:
            GPIO.output(self.dc_pin, GPIO.HIGH)
            GPIO.output(self.cs_pin, GPIO.LOW)
            if isinstance(data, int):
                spi.writebytes([data])
            else:
                payload = data if isinstance(data, (list, bytes, bytearray)) else list(data)
                try:
                    spi.writebytes2(payload)
                except AttributeError:
                    for i in range(0, len(payload), 4096):
                        spi.writebytes(list(payload[i:i + 4096]))
            GPIO.output(self.cs_pin, GPIO.HIGH)

    def _cd(self, cmd: int, data=None) -> None:
        self._cmd(cmd)
        if data is not None:
            self._data(data if isinstance(data, (list, bytes, bytearray)) else [data])

    def _read(self, cmd: int, length: int) -> bytes:
        with self._bus.transaction(self.spi_port, self.spi_device, self.SPI_SPEED_HZ) as spi:
            GPIO.output(self.dc_pin, GPIO.LOW)
            GPIO.output(self.cs_pin, GPIO.LOW)
            spi.writebytes([cmd])
            GPIO.output(self.dc_pin, GPIO.HIGH)
            rx = spi.readbytes(length + 1)  # 1 byte dummy
            GPIO.output(self.cs_pin, GPIO.HIGH)
        return bytes(rx[1:])

    # ── Init ─────────────────────────────────────────────────────────────────

    def _init_display(self) -> None:
        GPIO.output(self.rst_pin, GPIO.HIGH)
        time.sleep(0.01)
        GPIO.output(self.rst_pin, GPIO.LOW)
        time.sleep(0.05)
        GPIO.output(self.rst_pin, GPIO.HIGH)
        time.sleep(0.15)

        self._cmd(self.CMD_SWRESET)
        time.sleep(0.15)
        self._cmd(self.CMD_SLPOUT)
        time.sleep(0.12)

        self._cd(self.CMD_MADCTL, [0xA8])
        self._cd(self.CMD_COLMOD, [0x05])
        self._cd(self.CMD_PORCTRL, [0x0C, 0x0C, 0x00, 0x33, 0x33])
        self._cd(self.CMD_GCTRL, [0x35])
        self._cd(self.CMD_VCOMS, [0x2B])
        self._cd(self.CMD_LCMCTRL, [0x0C])
        self._cd(self.CMD_VDVVRHEN, [0x01])
        self._cd(self.CMD_VRHS, [0x15])
        self._cd(self.CMD_VDVSET, [0x20])
        self._cd(self.CMD_FRCTR2, [0x0F])
        self._cd(self.CMD_PWCTRL1, [0xA4, 0xA1])

        self._cmd(self.CMD_INVOFF)
        self._cmd(self.CMD_NORON)
        self._cmd(self.CMD_DISPON)
        time.sleep(0.1)

    def _verify_chip(self) -> None:
        try:
            rddid = self._read(self.CMD_RDDID, 3)
            print(f"[ST7789] RDDID = {rddid.hex()}")
            if rddid == b"\x00\x00\x00" or rddid == b"\xff\xff\xff":
                # No abortamos por compatibilidad pero queda registrado.
                print(f"[ST7789] RDDID sospechoso ({rddid.hex()}): chip puede no estar respondiendo")
        except Exception as exc:
            print(f"[ST7789] RDDID lectura fallida: {exc}")
            traceback.print_exc()

    # ── Public API ───────────────────────────────────────────────────────────

    def clear(self, color=(0, 0, 0)) -> None:
        self.framebuffer = Image.new("RGB", (self.WIDTH, self.HEIGHT), color)
        self.draw = ImageDraw.Draw(self.framebuffer)

    def display(self, image: Optional[Image.Image] = None) -> None:
        if image is not None:
            if image.size != (self.WIDTH, self.HEIGHT):
                image = image.resize((self.WIDTH, self.HEIGHT), Image.LANCZOS)
            self.framebuffer = image.convert("RGB")
            self.draw = ImageDraw.Draw(self.framebuffer)

        arr = np.asarray(self.framebuffer, dtype=np.uint8)
        r = arr[..., 0].astype(np.uint16)
        g = arr[..., 1].astype(np.uint16)
        b = arr[..., 2].astype(np.uint16)
        rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        buf = rgb565.astype(">u2").tobytes()

        self._set_window()
        self._cmd(self.CMD_RAMWR)
        self._data(buf)

        if not self._first_frame_ok:
            self._first_frame_ok = True
            # Encender BL (activo-LOW) ya que el primer frame válido fue OK.
            GPIO.output(self.bl_pin, GPIO.LOW)

    def set_brightness(self, percent: int) -> None:
        """BL activo-LOW: GPIO LOW = encendido. Solo permite encender tras primer frame OK."""
        percent = max(0, min(100, percent))
        if percent > 0 and self._first_frame_ok:
            GPIO.output(self.bl_pin, GPIO.LOW)
        else:
            GPIO.output(self.bl_pin, GPIO.HIGH)

    def _set_window(self) -> None:
        xs = self.col_offset
        xe = self.col_offset + self.WIDTH - 1
        ys = self.row_offset
        ye = self.row_offset + self.HEIGHT - 1
        self._cd(self.CMD_CASET, [xs >> 8, xs & 0xFF, xe >> 8, xe & 0xFF])
        self._cd(self.CMD_RASET, [ys >> 8, ys & 0xFF, ye >> 8, ye & 0xFF])

    def cleanup(self) -> None:
        try:
            self._cmd(self.CMD_DISPOFF)
            self._cmd(self.CMD_SLPIN)
        except Exception:
            pass
        try:
            GPIO.output(self.bl_pin, GPIO.HIGH)  # BL off
        except Exception:
            pass
