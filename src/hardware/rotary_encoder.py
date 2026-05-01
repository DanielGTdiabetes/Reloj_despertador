
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
        }
        
        GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.sw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self._thread = threading.Thread(target=self._state_machine_poll, daemon=True)
        self._thread.start()

    def on(self, event, callback):
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _emit(self, event):
        for callback in self._callbacks[event]:
            try:
                callback()
            except Exception as e:
                print(f"[Encoder] Callback error: {e}")

    def _state_machine_poll(self):
        # Máquina de estados robusta para evitar rebotes
        # 00 -> 01 -> 11 -> 10 -> 00  (Sentido A)
        # 00 -> 10 -> 11 -> 01 -> 00  (Sentido B)
        
        last_state = (GPIO.input(self.clk_pin) << 1) | GPIO.input(self.dt_pin)
        last_sw = GPIO.input(self.sw_pin)
        pressed_at = None
        long_fired = False
        
        # Tabla de verdad para la máquina de estados
        # 1 = CW, -1 = CCW, 0 = Sin movimiento
        # Basado en (estado_anterior << 2) | estado_actual
        TRANSITIONS = [
            0, -1,  1,  0,  # 00 -> 00, 01, 10, 11
            1,  0,  0, -1,  # 01 -> 00, 01, 10, 11
           -1,  0,  0,  1,  # 10 -> 00, 01, 10, 11
            0,  1, -1,  0   # 11 -> 00, 01, 10, 11
        ]
        
        counter = 0
        
        while self._running:
            # Leer pines
            clk = GPIO.input(self.clk_pin)
            dt = GPIO.input(self.dt_pin)
            sw = GPIO.input(self.sw_pin)
            
            current_state = (clk << 1) | dt
            
            if current_state != last_state:
                # Calcular movimiento según la transición
                idx = (last_state << 2) | current_state
                move = TRANSITIONS[idx]
                counter += move
                
                # Cada 4 micro-pasos (un ciclo completo del encoder), disparamos un evento
                if counter >= 4:
                    self._emit("rotate_cw")
                    counter = 0
                elif counter <= -4:
                    self._emit("rotate_ccw")
                    counter = 0
                
                last_state = current_state

            # Lógica del botón (sin cambios, ya funcionaba bien)
            now = time.time()
            if sw != last_sw:
                if sw == GPIO.LOW:
                    pressed_at = now
                    long_fired = False
                else:
                    if pressed_at is not None and not long_fired:
                        self._emit("button_press")
                    pressed_at = None
            
            if pressed_at is not None and not long_fired:
                if now - pressed_at >= 1.1:
                    long_fired = True
                    self._emit("button_long_press")
            
            last_sw = sw
            time.sleep(0.001) # Muestreo ultra-rápido de 1ms para no perder transiciones

    def cleanup(self):
        self._running = False
        GPIO.cleanup([self.clk_pin, self.dt_pin, self.sw_pin])
