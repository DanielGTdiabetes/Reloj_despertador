"""
GC9A01 Display Driver - 240x240 Circular Display
Uses spidev for direct SPI communication
"""

import spidev
import RPi.GPIO as GPIO
import time
from PIL import Image, ImageDraw, ImageFont


class GC9A01:
    """Driver for GC9A01 240x240 circular LCD display"""

    WIDTH  = 240
    HEIGHT = 240

    # Commands
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
    CMD_RGBCTRL  = 0xB1
    CMD_PORCTRL  = 0xB2
    CMD_GCTRL    = 0xB7
    CMD_VCOMS    = 0xBB
    CMD_LCMCTRL  = 0xC0
    CMD_VDVVRHEN = 0xC2
    CMD_VRHS     = 0xC3
    CMD_VDVSET   = 0xC4
    CMD_FRCTR2   = 0xC6
    CMD_PWCTRL1  = 0xD0
    CMD_INTERRE1 = 0xFE
    CMD_INTERRE2 = 0xEF

    def __init__(self, spi_port=0, spi_device=0, dc_pin=25, rst_pin=26, bl_pin=None):
        self.dc_pin  = dc_pin
        self.rst_pin = rst_pin
        self.bl_pin  = bl_pin   # None si la pantalla no tiene pin BL (backlight fijo)

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.dc_pin,  GPIO.OUT)
        GPIO.setup(self.rst_pin, GPIO.OUT)
        if self.bl_pin is not None:
            GPIO.setup(self.bl_pin, GPIO.OUT)
            GPIO.output(self.bl_pin, GPIO.HIGH)

        self.spi = spidev.SpiDev()
        self.spi.open(spi_port, spi_device)
        self.spi.max_speed_hz = 20_000_000   # 20 MHz, seguro para Pi Zero W
        self.spi.mode = 0b00

        self.framebuffer = Image.new("RGB", (self.WIDTH, self.HEIGHT), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.framebuffer)

        self._init_display()

    # ── SPI helpers ──────────────────────────────────────────────────────────

    def _cmd(self, cmd):
        GPIO.output(self.dc_pin, GPIO.LOW)
        self.spi.writebytes([cmd])

    def _dat(self, data):
        GPIO.output(self.dc_pin, GPIO.HIGH)
        if isinstance(data, int):
            self.spi.writebytes([data])
        else:
            # spidev limita a 4096 bytes por llamada
            for i in range(0, len(data), 4096):
                self.spi.writebytes(list(data[i:i+4096]))

    def _cd(self, cmd, data=None):
        self._cmd(cmd)
        if data is not None:
            self._dat(data if isinstance(data, (list, bytes)) else [data])

    # ── Init ─────────────────────────────────────────────────────────────────

    def _init_display(self):
        # Hard reset
        GPIO.output(self.rst_pin, GPIO.HIGH); time.sleep(0.01)
        GPIO.output(self.rst_pin, GPIO.LOW);  time.sleep(0.01)
        GPIO.output(self.rst_pin, GPIO.HIGH); time.sleep(0.12)

        self._cmd(self.CMD_SWRESET); time.sleep(0.12)

        # Secuencia de init completa para GC9A01
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

        self._cd(0xB6, [0x00, 0x00])           # Display function control
        self._cd(self.CMD_MADCTL,   [0x48])    # MY MX MV ML BGR MH — ajustar si imagen girada
        self._cd(self.CMD_COLMOD,   [0x05])    # 16 bits por pixel
        self._cd(0x90, [0x08, 0x08, 0x08, 0x08])
        self._cd(0xBD, [0x06])
        self._cd(0xBC, [0x00])
        self._cd(0xFF, [0x60, 0x01, 0x04])
        self._cd(self.CMD_PWCTRL1,  [0x13])
        self._cd(0xC1,              [0x13])
        self._cd(0xC2,              [0x13])
        self._cd(0xC3,              [0x22])
        self._cd(0xBE,              [0x11])
        self._cd(0xE1,              [0x10, 0x0E])
        self._cd(0xDF, [0x21, 0x0C, 0x02])
        # Gamma positiva
        self._cd(0xF0, [0x45, 0x09, 0x08, 0x08, 0x26, 0x2A])
        # Gamma negativa
        self._cd(0xF1, [0x43, 0x70, 0x72, 0x36, 0x37, 0x6F])
        self._cd(0xF2, [0x45, 0x09, 0x08, 0x08, 0x26, 0x2A])
        self._cd(0xF3, [0x43, 0x70, 0x72, 0x36, 0x37, 0x6F])
        self._cd(0xED, [0x1B, 0x0B])
        self._cd(0xAE, [0x77])
        self._cd(0xCD, [0x63])
        self._cd(0x70, [0x07, 0x07, 0x04, 0x0E, 0x0F, 0x09, 0x07, 0x08, 0x03])
        self._cd(self.CMD_FRCTR2,   [0x34])
        self._cd(0x62, [0x18, 0x0D, 0x71, 0xED, 0x70, 0x70,
                        0x18, 0x0F, 0x71, 0xEF, 0x70, 0x70])
        self._cd(0x63, [0x18, 0x11, 0x71, 0xF1, 0x70, 0x70,
                        0x18, 0x13, 0x71, 0xF3, 0x70, 0x70])
        self._cd(0x64, [0x28, 0x29, 0xF1, 0x01, 0xF1, 0x00, 0x07])
        self._cd(0x66, [0x3C, 0x00, 0xCD, 0x67, 0x45, 0x45, 0x10, 0x00, 0x00, 0x00])
        self._cd(0x67, [0x00, 0x3C, 0x00, 0x00, 0x00, 0x01, 0x54, 0x10, 0x32, 0x98])
        self._cd(0x74, [0x10, 0x85, 0x80, 0x00, 0x00, 0x4E, 0x00])
        self._cd(0x98, [0x3E, 0x07])

        self._cmd(self.CMD_INVON)               # ← inversión de color necesaria
        self._cmd(self.CMD_SLPOUT); time.sleep(0.12)
        self._cmd(self.CMD_DISPON); time.sleep(0.02)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_brightness(self, percent):
        """Solo aplica si bl_pin está definido."""
        if self.bl_pin is not None:
            GPIO.output(self.bl_pin, GPIO.HIGH if percent > 0 else GPIO.LOW)

    def display(self, image=None):
        if image is not None:
            if image.size != (self.WIDTH, self.HEIGHT):
                # Usar NEAREST para no añadir blur en resize de emergencia
                image = image.resize((self.WIDTH, self.HEIGHT), Image.NEAREST)
            self.framebuffer = image.convert("RGB")

        self._cd(self.CMD_CASET, [0x00, 0x00, 0x00, 0xEF])   # cols 0‥239
        self._cd(self.CMD_RASET, [0x00, 0x00, 0x00, 0xEF])   # rows 0‥239
        self._cmd(self.CMD_RAMWR)

        pixels = self.framebuffer.getdata()
        buf = bytearray(self.WIDTH * self.HEIGHT * 2)
        idx = 0
        for r, g, b in pixels:
            c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            buf[idx]     = (c >> 8) & 0xFF
            buf[idx + 1] = c & 0xFF
            idx += 2

        GPIO.output(self.dc_pin, GPIO.HIGH)
        # Intentar envío monolítico para evitar artefactos entre chunks
        try:
            self.spi.writebytes2(buf)
        except Exception:
            mv = memoryview(buf)
            for i in range(0, len(buf), 16384):
                self.spi.writebytes2(mv[i:i + 16384])

    def clear(self, color=(0, 0, 0)):
        self.framebuffer = Image.new("RGB", (self.WIDTH, self.HEIGHT), color)

    def cleanup(self):
        self._cmd(self.CMD_SLPIN)
        pins = [self.dc_pin, self.rst_pin]
        if self.bl_pin is not None:
            pins.append(self.bl_pin)
        GPIO.cleanup(pins)
        self.spi.close()
