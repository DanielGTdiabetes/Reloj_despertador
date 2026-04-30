"""
Driver GC9A01 240x240 redondo.

Cambios vs versión anterior:
  - Usa SpiBus compartido (lock global, reconfigura speed/mode por transacción).
  - CS manual sobre GPIO8 (CE0) con `no_cs=True`, simétrico al ST7789.
  - Render RGB565 vectorizado con numpy.
  - Lectura de RDDID (0xDA) tras init para verificar que el chip responde.
  - Backlight diferido: solo se enciende tras un primer render OK.
  - No llama a GPIO.setmode/setwarnings; eso es responsabilidad del bootstrap.
"""

from __future__ import annotations

import time
import traceback
from typing import Optional

import numpy as np
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw

from .spi_bus import SpiBus


class GC9A01:
    WIDTH = 240
    HEIGHT = 240

    CMD_SWRESET = 0x01
    CMD_RDDID = 0xDA
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
    CMD_FRCTR2 = 0xC6
    CMD_PWCTRL1 = 0xD0
    CMD_INTERRE1 = 0xFE
    CMD_INTERRE2 = 0xEF

    SPI_SPEED_HZ = 20_000_000

    def __init__(
        self,
        spi_port: int = 0,
        spi_device: int = 0,
        cs_pin: int = 8,
        dc_pin: int = 25,
        rst_pin: int = 26,
        bl_pin: Optional[int] = None,
    ) -> None:
        self.spi_port = spi_port
        self.spi_device = spi_device
        self.cs_pin = cs_pin
        self.dc_pin = dc_pin
        self.rst_pin = rst_pin
        self.bl_pin = bl_pin

        self._bus = SpiBus.instance()
        self._initialized = False
        self._first_frame_ok = False

        GPIO.setup(self.cs_pin, GPIO.OUT)
        GPIO.setup(self.dc_pin, GPIO.OUT)
        GPIO.setup(self.rst_pin, GPIO.OUT)
        GPIO.output(self.cs_pin, GPIO.HIGH)
        if self.bl_pin is not None:
            GPIO.setup(self.bl_pin, GPIO.OUT)
            GPIO.output(self.bl_pin, GPIO.LOW)  # BL apagado hasta primer frame OK

        self.framebuffer = Image.new("RGB", (self.WIDTH, self.HEIGHT), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.framebuffer)

        self._init_display()
        self._verify_chip()
        self._initialized = True

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
                # spidev limita writebytes a 4096; usar writebytes2 si está disponible.
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
        # Hard reset
        GPIO.output(self.rst_pin, GPIO.HIGH)
        time.sleep(0.01)
        GPIO.output(self.rst_pin, GPIO.LOW)
        time.sleep(0.05)
        GPIO.output(self.rst_pin, GPIO.HIGH)
        time.sleep(0.15)

        self._cmd(self.CMD_SWRESET)
        time.sleep(0.15)

        # Secuencia de init GC9A01
        self._cd(self.CMD_INTERRE2, [0xEB, 0x14])
        self._cd(self.CMD_INTERRE1)
        self._cd(self.CMD_INTERRE2, [0xEB, 0x14])

        self._cd(0x84, [0x40])
        self._cd(0x85, [0xFF])
        self._cd(0x86, [0xFF])
        self._cd(0x87, [0xFF])
        self._cd(0x88, [0x0A])
        self._cd(0x89, [0x21])
        self._cd(0x8A, [0x00])
        self._cd(0x8B, [0x80])
        self._cd(0x8C, [0x01])
        self._cd(0x8D, [0x01])
        self._cd(0x8E, [0xFF])
        self._cd(0x8F, [0xFF])

        self._cd(0xB6, [0x00, 0x00])
        self._cd(self.CMD_MADCTL, [0x48])
        self._cd(self.CMD_COLMOD, [0x05])
        self._cd(0x90, [0x08, 0x08, 0x08, 0x08])
        self._cd(0xBD, [0x06])
        self._cd(0xBC, [0x00])
        self._cd(0xFF, [0x60, 0x01, 0x04])
        self._cd(self.CMD_PWCTRL1, [0x13])
        self._cd(0xC1, [0x13])
        self._cd(0xC2, [0x13])
        self._cd(0xC3, [0x22])
        self._cd(0xBE, [0x11])
        self._cd(0xE1, [0x10, 0x0E])
        self._cd(0xDF, [0x21, 0x0C, 0x02])
        self._cd(0xF0, [0x45, 0x09, 0x08, 0x08, 0x26, 0x2A])
        self._cd(0xF1, [0x43, 0x70, 0x72, 0x36, 0x37, 0x6F])
        self._cd(0xF2, [0x45, 0x09, 0x08, 0x08, 0x26, 0x2A])
        self._cd(0xF3, [0x43, 0x70, 0x72, 0x36, 0x37, 0x6F])
        self._cd(0xED, [0x1B, 0x0B])
        self._cd(0xAE, [0x77])
        self._cd(0xCD, [0x63])
        self._cd(0x70, [0x07, 0x07, 0x04, 0x0E, 0x0F, 0x09, 0x07, 0x08, 0x03])
        self._cd(self.CMD_FRCTR2, [0x34])
        self._cd(0x62, [0x18, 0x0D, 0x71, 0xED, 0x70, 0x70,
                        0x18, 0x0F, 0x71, 0xEF, 0x70, 0x70])
        self._cd(0x63, [0x18, 0x11, 0x71, 0xF1, 0x70, 0x70,
                        0x18, 0x13, 0x71, 0xF3, 0x70, 0x70])
        self._cd(0x64, [0x28, 0x29, 0xF1, 0x01, 0xF1, 0x00, 0x07])
        self._cd(0x66, [0x3C, 0x00, 0xCD, 0x67, 0x45, 0x45, 0x10, 0x00, 0x00, 0x00])
        self._cd(0x67, [0x00, 0x3C, 0x00, 0x00, 0x00, 0x01, 0x54, 0x10, 0x32, 0x98])
        self._cd(0x74, [0x10, 0x85, 0x80, 0x00, 0x00, 0x4E, 0x00])
        self._cd(0x98, [0x3E, 0x07])

        self._cmd(self.CMD_INVON)
        self._cmd(self.CMD_SLPOUT)
        time.sleep(0.12)
        self._cmd(self.CMD_DISPON)
        time.sleep(0.02)

    def _verify_chip(self) -> None:
        # Algunos GC9A01 no exponen RDDID de forma fiable (timing del dummy bit
        # vs byte). Lo registramos como diagnóstico, sin abortar.
        try:
            rddid = self._read(self.CMD_RDDID, 3)
            print(f"[GC9A01] RDDID = {rddid.hex()}")
        except Exception as exc:
            print(f"[GC9A01] RDDID lectura fallida: {exc}")

    # ── Public API ───────────────────────────────────────────────────────────

    def set_brightness(self, percent: int) -> None:
        if self.bl_pin is None:
            return
        # BL solo se permite encender una vez tenemos init OK + primer frame OK.
        if percent > 0 and self._first_frame_ok:
            GPIO.output(self.bl_pin, GPIO.HIGH)
        else:
            GPIO.output(self.bl_pin, GPIO.LOW)

    def display(self, image: Optional[Image.Image] = None) -> None:
        if image is not None:
            if image.size != (self.WIDTH, self.HEIGHT):
                image = image.resize((self.WIDTH, self.HEIGHT), Image.NEAREST)
            self.framebuffer = image.convert("RGB")

        # Conversión RGB565 vectorizada con numpy
        arr = np.asarray(self.framebuffer, dtype=np.uint8)
        r = arr[..., 0].astype(np.uint16)
        g = arr[..., 1].astype(np.uint16)
        b = arr[..., 2].astype(np.uint16)
        rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        # Big-endian
        buf = rgb565.astype(">u2").tobytes()

        self._cd(self.CMD_CASET, [0x00, 0x00, 0x00, 0xEF])
        self._cd(self.CMD_RASET, [0x00, 0x00, 0x00, 0xEF])
        self._cmd(self.CMD_RAMWR)
        self._data(buf)

        if not self._first_frame_ok:
            self._first_frame_ok = True
            if self.bl_pin is not None:
                GPIO.output(self.bl_pin, GPIO.HIGH)

    def clear(self, color=(0, 0, 0)) -> None:
        self.framebuffer = Image.new("RGB", (self.WIDTH, self.HEIGHT), color)
        self.draw = ImageDraw.Draw(self.framebuffer)

    def cleanup(self) -> None:
        try:
            self._cmd(self.CMD_DISPOFF)
            self._cmd(self.CMD_SLPIN)
        except Exception:
            pass
        if self.bl_pin is not None:
            try:
                GPIO.output(self.bl_pin, GPIO.LOW)
            except Exception:
                pass
