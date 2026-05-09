from __future__ import annotations

import time
from typing import Optional

import numpy as np
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw

from .spi_bus import SpiBus, SpiDeviceProfile


class ST7789Display:
    WIDTH = 284
    HEIGHT = 76
    SPI_NAME = "st7789"

    CMD_SWRESET = 0x01
    CMD_RDDID = 0x04
    CMD_SLPIN = 0x10
    CMD_SLPOUT = 0x11
    CMD_NORON = 0x13
    CMD_DISPOFF = 0x28
    CMD_DISPON = 0x29
    CMD_CASET = 0x2A
    CMD_RASET = 0x2B
    CMD_RAMWR = 0x2C
    CMD_MADCTL = 0x36
    CMD_COLMOD = 0x3A

    def __init__(self, spi_port=0, spi_device=1, cs_pin=16, dc_pin=22, rst_pin=27, bl_pin=23,
                 col_offset=18, row_offset=82,
                 init_extended=False, madctl_val=0xA0, colmod_val=0x05):
        self.spi_port = spi_port
        self.spi_device = spi_device
        self.cs_pin = cs_pin
        self.dc_pin = dc_pin
        self.rst_pin = rst_pin
        self.bl_pin = bl_pin
        self.col_offset = col_offset
        self.row_offset = row_offset
        self.init_extended = init_extended
        self.madctl_val = madctl_val
        self.colmod_val = colmod_val
        self._bus = SpiBus.instance()
        self._bus.register_device(SpiDeviceProfile(self.SPI_NAME, spi_port, spi_device, cs_pin, init_speed_hz=4_000_000, frame_speed_hz=16_000_000))

        GPIO.setup(self.dc_pin, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.rst_pin, GPIO.OUT, initial=GPIO.HIGH)
        # BL pin: control directo GPIO sin PWM para evitar parpadeo en Pi Zero W.
        # El pin es activo-bajo: LOW = encendido, HIGH = apagado.
        GPIO.setup(self.bl_pin, GPIO.OUT, initial=GPIO.HIGH)
        self._bl_on = False
        self._first_frame_ok = False

        self.framebuffer = Image.new("RGB", (self.WIDTH, self.HEIGHT), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.framebuffer)

        self._init_with_retry()

    def _write_cmd_data(self, cmd: int, data=None, *, init_phase: bool = False) -> None:
        """Envía comando y datos en UNA sola transacción SPI (CS continuo)."""
        with self._bus.transaction(self.SPI_NAME, init_phase=init_phase) as spi:
            GPIO.output(self.dc_pin, GPIO.LOW)
            spi.writebytes([cmd])

            if data is not None:
                GPIO.output(self.dc_pin, GPIO.HIGH)
                if isinstance(data, int):
                    payload = [data]
                else:
                    payload = list(data)

                spi.writebytes2(bytes(payload))

    def _cmd(self, cmd: int, *, init_phase: bool = False) -> None:
        self._write_cmd_data(cmd, None, init_phase=init_phase)

    def _cd(self, cmd: int, data=None, *, init_phase: bool = False) -> None:
        self._write_cmd_data(cmd, data, init_phase=init_phase)

    def _init_with_retry(self) -> None:
        for attempt in (1, 2):
            try:
                self._init_display()
                print(f"[ST7789] init OK at attempt {attempt}")
                return
            except Exception as exc:
                print(f"[ST7789] init failed attempt {attempt}: {exc}")
                time.sleep(0.2)
        raise RuntimeError("[ST7789] init failed after retries")

    def _init_display(self) -> None:
        GPIO.output(self.rst_pin, GPIO.HIGH); time.sleep(0.02)
        GPIO.output(self.rst_pin, GPIO.LOW); time.sleep(0.12)
        GPIO.output(self.rst_pin, GPIO.HIGH); time.sleep(0.2)

        self._cmd(self.CMD_SWRESET, init_phase=True); time.sleep(0.18)
        self._cmd(self.CMD_SLPOUT, init_phase=True); time.sleep(0.15)

        if self.init_extended:
            self._cd(0xB2, [0x0C, 0x0C, 0x00, 0x33, 0x33], init_phase=True) # PORCTRL
            self._cd(0xB7, [0x35], init_phase=True) # GCTRL
            self._cd(0xBB, [0x1F], init_phase=True) # VCOMS
            self._cd(0xC0, [0x2C], init_phase=True) # LCMCTRL
            self._cd(0xC2, [0x01], init_phase=True) # VDVVRHEN
            self._cd(0xC3, [0x12], init_phase=True) # VRHS
            self._cd(0xC4, [0x20], init_phase=True) # VDVS
            self._cd(0xC6, [0x0F], init_phase=True) # FRCTRL2
            self._cd(0xD0, [0xA4, 0xA1], init_phase=True) # PWCTRL1

        self._cd(self.CMD_MADCTL, [self.madctl_val], init_phase=True)
        self._cd(self.CMD_COLMOD, [self.colmod_val], init_phase=True)
        self._cmd(0x20, init_phase=True) # INVOFF
        self._cmd(self.CMD_NORON, init_phase=True); time.sleep(0.01)
        self._cmd(self.CMD_DISPON, init_phase=True); time.sleep(0.1)

    def _set_window(self) -> None:
        xs, ys = self.col_offset, self.row_offset
        xe, ye = xs + self.WIDTH - 1, ys + self.HEIGHT - 1
        self._cd(self.CMD_CASET, [xs >> 8, xs & 0xFF, xe >> 8, xe & 0xFF])
        self._cd(self.CMD_RASET, [ys >> 8, ys & 0xFF, ye >> 8, ye & 0xFF])

    def display(self, image: Optional[Image.Image] = None) -> None:
        if image is not None:
            self.framebuffer = image.resize((self.WIDTH, self.HEIGHT), Image.LANCZOS).convert("RGB")
        arr = np.asarray(self.framebuffer, dtype=np.uint8)
        rgb565 = (((arr[..., 0].astype(np.uint16) & 0xF8) << 8) | ((arr[..., 1].astype(np.uint16) & 0xFC) << 3) | (arr[..., 2].astype(np.uint16) >> 3))

        self._set_window()

        with self._bus.transaction(self.SPI_NAME, init_phase=False) as spi:
            GPIO.output(self.dc_pin, GPIO.LOW)
            spi.writebytes([self.CMD_RAMWR])
            GPIO.output(self.dc_pin, GPIO.HIGH)
            spi.writebytes2(rgb565.astype(">u2").tobytes())

        if not self._first_frame_ok:
            self._first_frame_ok = True
            if self._bl_on:
                GPIO.output(self.bl_pin, GPIO.LOW)

    def clear(self, color=(0, 0, 0)):
        self.framebuffer = Image.new("RGB", (self.WIDTH, self.HEIGHT), color)
        self.draw = ImageDraw.Draw(self.framebuffer)

    def set_brightness(self, percent: int):
        self._bl_on = percent > 0
        if self._first_frame_ok:
            GPIO.output(self.bl_pin, GPIO.LOW if self._bl_on else GPIO.HIGH)

    def cleanup(self):
        try:
            self._cmd(self.CMD_DISPOFF, init_phase=True)
            self._cmd(self.CMD_SLPIN, init_phase=True)
        finally:
            GPIO.output(self.bl_pin, GPIO.HIGH)
