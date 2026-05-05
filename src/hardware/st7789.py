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

    def __init__(self, spi_port=0, spi_device=1, cs_pin=16, dc_pin=22, rst_pin=27, bl_pin=23, col_offset=82, row_offset=18):
        self.spi_port = spi_port
        self.spi_device = spi_device
        self.cs_pin = cs_pin
        self.dc_pin = dc_pin
        self.rst_pin = rst_pin
        self.bl_pin = bl_pin
        self.col_offset = col_offset
        self.row_offset = row_offset
        self._bus = SpiBus.instance()
        self._bus.register_device(SpiDeviceProfile(self.SPI_NAME, spi_port, spi_device, cs_pin, init_speed_hz=4_000_000, frame_speed_hz=24_000_000))

        GPIO.setup(self.dc_pin, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.rst_pin, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.bl_pin, GPIO.OUT, initial=GPIO.HIGH)
        self._pwm = GPIO.PWM(self.bl_pin, 200)
        self._pwm.start(100)
        self._first_frame_ok = False

        self.framebuffer = Image.new("RGB", (self.WIDTH, self.HEIGHT), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.framebuffer)

        self._init_with_retry()

    def _cmd(self, cmd: int, *, init_phase: bool = False) -> None:
        with self._bus.transaction(self.SPI_NAME, init_phase=init_phase) as spi:
            GPIO.output(self.dc_pin, GPIO.LOW)
            spi.writebytes([cmd])

    def _data(self, data, *, init_phase: bool = False) -> None:
        payload = [data] if isinstance(data, int) else data
        with self._bus.transaction(self.SPI_NAME, init_phase=init_phase) as spi:
            GPIO.output(self.dc_pin, GPIO.HIGH)
            spi.writebytes2(payload if isinstance(payload, (bytes, bytearray, list)) else list(payload))

    def _cd(self, cmd: int, data=None, *, init_phase: bool = False) -> None:
        self._cmd(cmd, init_phase=init_phase)
        if data is not None:
            self._data(data, init_phase=init_phase)

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
        GPIO.output(self.bl_pin, GPIO.HIGH)
        GPIO.output(self.rst_pin, GPIO.HIGH); time.sleep(0.02)
        GPIO.output(self.rst_pin, GPIO.LOW); time.sleep(0.12)
        GPIO.output(self.rst_pin, GPIO.HIGH); time.sleep(0.2)
        self._cmd(self.CMD_SWRESET, init_phase=True); time.sleep(0.18)
        self._cmd(self.CMD_SLPOUT, init_phase=True); time.sleep(0.15)
        self._cd(self.CMD_MADCTL, [0xA8], init_phase=True)
        self._cd(self.CMD_COLMOD, [0x05], init_phase=True)
        self._cmd(0x21, init_phase=True)
        self._cmd(self.CMD_NORON, init_phase=True)
        self._cmd(self.CMD_DISPON, init_phase=True)
        time.sleep(0.1)

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
        self._set_window(); self._cmd(self.CMD_RAMWR)
        self._data(rgb565.astype(">u2").tobytes())
        if not self._first_frame_ok:
            self._first_frame_ok = True
            self._pwm.ChangeDutyCycle(20)

    def clear(self, color=(0, 0, 0)):
        self.framebuffer = Image.new("RGB", (self.WIDTH, self.HEIGHT), color)
        self.draw = ImageDraw.Draw(self.framebuffer)

    def set_brightness(self, percent: int):
        self._pwm.ChangeDutyCycle(100 - max(0, min(95, percent)))

    def cleanup(self):
        try:
            self._cmd(self.CMD_DISPOFF, init_phase=True)
            self._cmd(self.CMD_SLPIN, init_phase=True)
        finally:
            self._pwm.ChangeDutyCycle(100)
            self._pwm.stop()
