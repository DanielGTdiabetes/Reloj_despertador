
import threading
import time
import RPi.GPIO as GPIO

class RotaryEncoder:
    def __init__(self, clk_pin=5, dt_pin=6, sw_pin=13):
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.sw_pin = sw_pin
        
        self._running = True
        self._callbacks = {
            "rotate_cw": [],
            "rotate_ccw": [],
            "button_press": [],
            "button_long_press": [],
            "button_power_press": [],   # ≥ 5s → apagado
        }
        
        GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.sw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self._last_emit_time = 0
        self._thread = threading.Thread(target=self._state_machine_poll, daemon=True)
        self._thread.start()

    def on(self, event, callback):
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _emit(self, event):
        now = time.time()
        # Filtro de Cooldown optimizado: 80ms para mayor fluidez
        if "rotate" in event:
            if now - self._last_emit_time < 0.080:
                return
            self._last_emit_time = now
            
        for callback in self._callbacks[event]:
            try:
                callback()
            except Exception as e:
                print(f"[Encoder] Callback error: {e}")

    def _state_machine_poll(self):
        last_state = (GPIO.input(self.clk_pin) << 1) | GPIO.input(self.dt_pin)
        last_sw = GPIO.input(self.sw_pin)
        pressed_at = None
        long_fired = False
        power_fired = False
        
        # Tabla de verdad corregida e invertida
        TRANSITIONS = [
            0,  1, -1,  0,
           -1,  0,  0,  1,
            1,  0,  0, -1,
            0, -1,  1,  0
        ]
        
        counter = 0
        
        while self._running:
            clk = GPIO.input(self.clk_pin)
            dt = GPIO.input(self.dt_pin)
            sw = GPIO.input(self.sw_pin)
            
            current_state = (clk << 1) | dt
            
            if current_state != last_state:
                idx = (last_state << 2) | current_state
                move = TRANSITIONS[idx]
                counter += move
                
                # Umbral de 4: Un clic físico = Un movimiento
                if counter >= 4:
                    self._emit("rotate_cw")
                    counter = 0
                elif counter <= -4:
                    self._emit("rotate_ccw")
                    counter = 0
                
                last_state = current_state

            now = time.time()
            if sw != last_sw:
                if sw == GPIO.LOW:
                    pressed_at = now
                    long_fired = False
                    power_fired = False
                else:
                    if pressed_at is not None and not long_fired and not power_fired:
                        self._emit("button_press")
                    pressed_at = None

            if pressed_at is not None:
                held = now - pressed_at
                if not long_fired and held >= 1.1:
                    long_fired = True
                    self._emit("button_long_press")
                if not power_fired and held >= 5.0:
                    power_fired = True
                    self._emit("button_power_press")
            
            last_sw = sw
            time.sleep(0.001)

    def cleanup(self):
        self._running = False
        GPIO.cleanup([self.clk_pin, self.dt_pin, self.sw_pin])
