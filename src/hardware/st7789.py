"""
ST7789 Display Driver — ST7789P3 rect 76×284 landscape
SPI0 CE1 (GPIO7) — shares bus with GC9A01 on CE0 (GPIO8).

Config correcta (GRAM 240×320 estándar, landscape via MV):
- MADCTL 0x68 (MV+MX+BGR), INVON, col_offset=18, row_offset=82
- CS GPIO7 manual (no_cs=True), BL activo LOW, SPI 10MHz
"""

import spidev
import RPi.GPIO as GPIO
import time
from PIL import Image, ImageDraw


class ST7789Display:
    """Driver for ST7789P3 284x76 rectangular LCD (landscape)"""

    WIDTH  = 284
    HEIGHT = 76

    # Offsets dentro del GRAM 320×240 (landscape-nativo)
    COL_OFFSET = 18
    ROW_OFFSET = 82

    CMD_SWRESET  = 0x01
    CMD_SLPIN    = 0x10
    CMD_SLPOUT   = 0x11
    CMD_NORON    = 0x13
    CMD_INVOFF   = 0x20
    CMD_INVON    = 0x21
    CMD_DISPOFF  = 0x28
    CMD_DISPON   = 0x29
    CMD_CASET    = 0x2A
    CMD_RASET    = 0x2B
    CMD_RAMWR    = 0x2C
    CMD_MADCTL   = 0x36
    CMD_COLMOD   = 0x3A
    CMD_PORCTRL  = 0xB2
    CMD_GCTRL    = 0xB7
    CMD_VCOMS    = 0xBB
    CMD_LCMCTRL  = 0xC0
    CMD_VDVVRHEN = 0xC2
    CMD_VRHS     = 0xC3
    CMD_VDVSET   = 0xC4
    CMD_FRCTR2   = 0xC6
    CMD_PWCTRL1  = 0xD0

    def __init__(self, spi_port=0, spi_device=1, cs_pin=7,
                 dc_pin=22, rst_pin=27, bl_pin=23,
                 col_offset=18, row_offset=82):
        self.cs_pin     = cs_pin
        self.dc_pin     = dc_pin
        self.rst_pin    = rst_pin
        self.bl_pin     = bl_pin
        self.col_offset = col_offset
        self.row_offset = row_offset

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.cs_pin,  GPIO.OUT)
        GPIO.setup(self.dc_pin,  GPIO.OUT)
        GPIO.setup(self.rst_pin, GPIO.OUT)
        GPIO.setup(self.bl_pin,  GPIO.OUT)
        GPIO.output(self.cs_pin, GPIO.HIGH)
        GPIO.output(self.bl_pin, GPIO.HIGH)  # BL off (activo LOW)

        self.spi = spidev.SpiDev()
        self.spi.open(spi_port, spi_device)
        self.spi.max_speed_hz = 10_000_000
        self.spi.mode = 0b00
        self.spi.no_cs = True  # CS controlado manualmente via GPIO

        self.framebuffer = Image.new("RGB", (self.WIDTH, self.HEIGHT), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.framebuffer)

        self._init_display()

    # ── SPI helpers ─────────────────────────────────────────────────────────

    def _write_command(self, cmd):
        GPIO.output(self.dc_pin, GPIO.LOW)
        GPIO.output(self.cs_pin, GPIO.LOW)
        self.spi.writebytes([cmd])
        GPIO.output(self.cs_pin, GPIO.HIGH)

    def _write_data(self, data):
        GPIO.output(self.dc_pin, GPIO.HIGH)
        GPIO.output(self.cs_pin, GPIO.LOW)
        if isinstance(data, int):
            self.spi.writebytes([data])
        else:
            self.spi.writebytes(list(data))
        GPIO.output(self.cs_pin, GPIO.HIGH)

    def _write_cmd_data(self, cmd, data=None):
        self._write_command(cmd)
        if data:
            self._write_data(data)

    # ── Init ────────────────────────────────────────────────────────────────

    def _init_display(self):
        GPIO.output(self.rst_pin, GPIO.HIGH); time.sleep(0.01)
        GPIO.output(self.rst_pin, GPIO.LOW);  time.sleep(0.01)
        GPIO.output(self.rst_pin, GPIO.HIGH); time.sleep(0.12)

        self._write_cmd_data(self.CMD_SWRESET); time.sleep(0.15)
        self._write_cmd_data(self.CMD_SLPOUT);  time.sleep(0.12)

        # MADCTL 0x68 = MV+MX+BGR → landscape real 284×76 (swap row/col en GRAM 240×320)
        self._write_cmd_data(self.CMD_MADCTL,   [0x68])
        self._write_cmd_data(self.CMD_COLMOD,   [0x55])   # 16-bit color
        self._write_cmd_data(self.CMD_PORCTRL,  [0x0C, 0x0C, 0x00, 0x33, 0x33])
        self._write_cmd_data(self.CMD_GCTRL,    [0x35])
        self._write_cmd_data(self.CMD_VCOMS,    [0x2B])
        self._write_cmd_data(self.CMD_LCMCTRL,  [0x0C])
        self._write_cmd_data(self.CMD_VDVVRHEN, [0x01])
        self._write_cmd_data(self.CMD_VRHS,     [0x15])
        self._write_cmd_data(self.CMD_VDVSET,   [0x20])
        self._write_cmd_data(self.CMD_FRCTR2,   [0x0F])
        self._write_cmd_data(self.CMD_PWCTRL1,  [0xA4, 0xA1])

        self._write_cmd_data(self.CMD_INVON)
        self._write_cmd_data(self.CMD_NORON)
        self._write_cmd_data(self.CMD_DISPON)
        time.sleep(0.1)

        self.set_brightness(80)

    # ── Window helpers ───────────────────────────────────────────────────────

    def _set_window(self):
        xs = self.col_offset
        xe = self.col_offset + self.WIDTH  - 1   # 18+284-1 = 301 (dentro de 0-319 con MV)
        ys = self.row_offset
        ye = self.row_offset + self.HEIGHT - 1   # 82+76-1  = 157 (dentro de 0-239 con MV)
        self._write_cmd_data(self.CMD_CASET, [xs >> 8, xs & 0xFF, xe >> 8, xe & 0xFF])
        self._write_cmd_data(self.CMD_RASET, [ys >> 8, ys & 0xFF, ye >> 8, ye & 0xFF])

    # ── Public API ───────────────────────────────────────────────────────────

    def clear(self, color=(0, 0, 0)):
        self.framebuffer = Image.new("RGB", (self.WIDTH, self.HEIGHT), color)
        self.draw = ImageDraw.Draw(self.framebuffer)

    def display(self, image=None):
        if image is not None:
            if image.size != (self.WIDTH, self.HEIGHT):
                image = image.resize((self.WIDTH, self.HEIGHT), Image.LANCZOS)
            self.framebuffer = image.convert("RGB")
            self.draw = ImageDraw.Draw(self.framebuffer)

        self._set_window()
        self._write_command(self.CMD_RAMWR)

        pixels = self.framebuffer.getdata()
        buf = bytearray(self.WIDTH * self.HEIGHT * 2)
        idx = 0
        for r, g, b in pixels:
            c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            buf[idx]     = (c >> 8) & 0xFF
            buf[idx + 1] = c & 0xFF
            idx += 2

        GPIO.output(self.dc_pin, GPIO.HIGH)
        GPIO.output(self.cs_pin, GPIO.LOW)
        try:
            self.spi.writebytes2(buf)
        except Exception:
            for i in range(0, len(buf), 4096):
                self.spi.writebytes(list(buf[i:i + 4096]))
        GPIO.output(self.cs_pin, GPIO.HIGH)

    def set_brightness(self, percent):
        """BL activo LOW"""
        GPIO.output(self.bl_pin, GPIO.LOW if percent > 0 else GPIO.HIGH)

    def cleanup(self):
        self._write_cmd_data(self.CMD_SLPIN)
        GPIO.cleanup([self.cs_pin, self.dc_pin, self.rst_pin, self.bl_pin])
        self.spi.close()
