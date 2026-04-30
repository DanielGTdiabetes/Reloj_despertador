"""
Polling rotary encoder driver.

The previous event-detect version can fail under systemd on this Pi.
Polling is fast enough for a menu encoder and avoids edge permission issues.
"""

import threading
import time

import RPi.GPIO as GPIO


class RotaryEncoder:
    def __init__(self, clk_pin=5, dt_pin=6, sw_pin=13, poll_interval=0.003):
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.sw_pin = sw_pin
        self.poll_interval = poll_interval
        self._position = 0
        self._running = True
        self._callbacks = {
            "rotate_cw": [],
            "rotate_ccw": [],
            "button_press": [],
            "button_long_press": [],
        }
        self._long_press_threshold = 1.1

        GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.sw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def on(self, event, callback):
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def get_position(self):
        return self._position

    def reset_position(self):
        self._position = 0

    def cleanup(self):
        self._running = False
        if self._thread.is_alive():
            self._thread.join(timeout=0.2)
        GPIO.cleanup([self.clk_pin, self.dt_pin, self.sw_pin])

    def _emit(self, event, *args):
        for callback in self._callbacks[event]:
            try:
                callback(*args)
            except TypeError:
                callback()
            except Exception as exc:
                print(f"[Encoder] callback error: {exc}")

    def _poll_loop(self):
        last_clk = GPIO.input(self.clk_pin)
        last_sw = GPIO.input(self.sw_pin)
        pressed_at = None
        long_fired = False
        last_rotate = 0.0

        while self._running:
            clk = GPIO.input(self.clk_pin)
            dt = GPIO.input(self.dt_pin)
            sw = GPIO.input(self.sw_pin)
            now = time.time()

            if clk != last_clk and clk == GPIO.LOW and now - last_rotate > 0.025:
                last_rotate = now
                if dt != clk:
                    self._position += 1
                    self._emit("rotate_cw", self._position)
                else:
                    self._position -= 1
                    self._emit("rotate_ccw", self._position)
            last_clk = clk

            if sw != last_sw:
                if sw == GPIO.LOW:
                    pressed_at = now
                    long_fired = False
                else:
                    if pressed_at is not None and not long_fired:
                        self._emit("button_press")
                    pressed_at = None
            last_sw = sw

            if pressed_at is not None and not long_fired:
                if now - pressed_at >= self._long_press_threshold:
                    long_fired = True
                    self._emit("button_long_press")

            time.sleep(self.poll_interval)

