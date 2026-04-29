"""
GC9A01 Display Driver - 240x240 Circular Display
Uses spidev for direct SPI communication with high-quality rendering via Pillow
"""

import spidev
import RPi.GPIO as GPIO
import time
from PIL import Image, ImageDraw, ImageFont

class GC9A01:
    """Driver for GC9A01 240x240 circular LCD display"""

    WIDTH = 240
    HEIGHT = 240

    # Command definitions
    CMD_SWRESET = 0x01
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
    CMD_RAMCTRL = 0xB0
    CMD_RGBCTRL = 0xB1
    CMD_PORCTRL = 0xB2
    CMD_GCTRL = 0xB7
    CMD_VCOMS = 0xBB
    CMD_LCMCTRL = 0xC0
    CMD_VDVVRHEN = 0xC2
    CMD_VRHS = 0xC3
    CMD_VDVSET = 0xC4
    CMD_FRCTR2 = 0xC6
    CMD_PWCTRL1 = 0xD0
    CMD_VREG1A = 0xD3
    CMD_VREG1B = 0xD6
    CMD_PWCTRL2 = 0xE4
    CMD_INTERRE1 = 0xFE
    CMD_INTERRE2 = 0xEF

    def __init__(self, spi_port=0, spi_device=0, dc_pin=25, rst_pin=26, bl_pin=12):
        self.dc_pin = dc_pin
        self.rst_pin = rst_pin
        self.bl_pin = bl_pin

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.dc_pin, GPIO.OUT)
        GPIO.setup(self.rst_pin, GPIO.OUT)
        if self.bl_pin is not None:
            GPIO.setup(self.bl_pin, GPIO.OUT)

        self.spi = spidev.SpiDev()
        self.spi.open(spi_port, spi_device)
        self.spi.max_speed_hz = 40000000
        self.spi.mode = 0b00

        self.framebuffer = Image.new("RGB", (self.WIDTH, self.HEIGHT), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.framebuffer)

        self._init_display()

    def _write_command(self, cmd):
        GPIO.output(self.dc_pin, GPIO.LOW)
        self.spi.writebytes([cmd])

    def _write_data(self, data):
        GPIO.output(self.dc_pin, GPIO.HIGH)
        if isinstance(data, int):
            self.spi.writebytes([data])
        else:
            self.spi.writebytes(data)

    def _write_cmd_data(self, cmd, data=None):
        self._write_command(cmd)
        if data:
            self._write_data(data)

    def _init_display(self):
        GPIO.output(self.rst_pin, GPIO.HIGH)
        time.sleep(0.01)
        GPIO.output(self.rst_pin, GPIO.LOW)
        time.sleep(0.01)
        GPIO.output(self.rst_pin, GPIO.HIGH)
        time.sleep(0.1)

        self._write_cmd_data(self.CMD_SWRESET)
        time.sleep(0.1)

        self._write_cmd_data(self.CMD_INTERRE2, [0xEB, 0x14])
        self._write_cmd_data(self.CMD_INTERRE1)
        self._write_cmd_data(self.CMD_INTERRE2, [0xEB, 0x14])
        self._write_cmd_data(self.CMD_PORCTRL, [0x39, 0x3C, 0x68, 0x0A, 0x32])
        self._write_cmd_data(self.CMD_GCTRL, [0x35])
        self._write_cmd_data(self.CMD_VCOMS, [0x19])
        self._write_cmd_data(self.CMD_LCMCTRL, [0x2C])
        self._write_cmd_data(self.CMD_VDVVRHEN, [0x01])
        self._write_cmd_data(self.CMD_VRHS, [0x12])
        self._write_cmd_data(self.CMD_VDVSET, [0x20])
        self._write_cmd_data(self.CMD_FRCTR2, [0x0F])
        self._write_cmd_data(self.CMD_PWCTRL1, [0xA4, 0xA1])
        self._write_cmd_data(self.CMD_MADCTL, [0x48])
        self._write_cmd_data(self.CMD_COLMOD, [0x55])
        self._write_cmd_data(self.CMD_RGBCTRL, [0x80, 0x0A])
        self._write_cmd_data(self.CMD_PORCTRL, [0x0A, 0x12, 0x1A, 0x32, 0x3C])

        self._write_cmd_data(self.CMD_SLPOUT)
        time.sleep(0.1)
        self._write_cmd_data(self.CMD_DISPON)
        time.sleep(0.1)

        self.set_brightness(80)

    def set_brightness(self, percent):
        percent = max(0, min(100, percent))
        if self.bl_pin is not None:
            GPIO.output(self.bl_pin, GPIO.HIGH if percent > 0 else GPIO.LOW)

    def clear(self, color=(0, 0, 0)):
        self.framebuffer = Image.new("RGB", (self.WIDTH, self.HEIGHT), color)
        self.draw = ImageDraw.Draw(self.framebuffer)

    def display(self, image=None):
        if image is not None:
            if image.size != (self.WIDTH, self.HEIGHT):
                image = image.resize((self.WIDTH, self.HEIGHT), Image.LANCZOS)
            self.framebuffer = image.convert("RGB")
            self.draw = ImageDraw.Draw(self.framebuffer)

        pixels = list(self.framebuffer.getdata())
        buf = []
        for r, g, b in pixels:
            color = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            buf.append((color >> 8) & 0xFF)
            buf.append(color & 0xFF)

        self._write_cmd_data(self.CMD_CASET, [0x00, 0x00, 0x00, 0xEF])
        self._write_cmd_data(self.CMD_RASET, [0x00, 0x00, 0x00, 0xEF])
        self._write_command(self.CMD_RAMWR)

        GPIO.output(self.dc_pin, GPIO.HIGH)
        try:
            self.spi.writebytes2(bytearray(buf))
        except Exception:
            chunk_size = 4096
            for i in range(0, len(buf), chunk_size):
                self.spi.writebytes(buf[i:i+chunk_size])

    def apply_circular_mask(self):
        mask = Image.new("L", (self.WIDTH, self.HEIGHT), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, self.WIDTH-1, self.HEIGHT-1), fill=255)
        bg = Image.new("RGB", (self.WIDTH, self.HEIGHT), (0, 0, 0))
        self.framebuffer.paste(bg, mask=Image.new("L", (self.WIDTH, self.HEIGHT), 0))
        self.framebuffer = Image.composite(self.framebuffer, bg, mask)

    def cleanup(self):
        self._write_cmd_data(self.CMD_SLPIN)
        pins = [self.dc_pin, self.rst_pin]
        if self.bl_pin is not None:
            pins.append(self.bl_pin)
        GPIO.cleanup(pins)
        self.spi.close()
