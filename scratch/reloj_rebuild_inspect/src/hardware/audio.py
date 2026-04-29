"""
I2S Audio Driver - MAX98357A Amplifier
Handles alarm sounds and audio playback via I2S
"""

import subprocess
import os
import threading
import time

class I2SAudio:
    """Driver for MAX98357A I2S audio amplifier"""

    def __init__(self, device="max98357a"):
        self.device = device
        self._playing = False
        self._current_process = None
        self._volume = 80

    def set_volume(self, percent):
        self._volume = max(0, min(100, percent))

    def play_file(self, filepath, loop=False):
        if not os.path.exists(filepath):
            print(f"Audio file not found: {filepath}")
            return

        self._playing = True

        def _play():
            while self._playing:
                cmd = [
                    "aplay",
                    "-D", f"plughw:CARD={self.device}",
                    "-q",
                    filepath
                ]
                try:
                    self._current_process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    self._current_process.wait()
                except Exception as e:
                    print(f"Audio playback error: {e}")
                    time.sleep(1)

                if not loop:
                    break

        thread = threading.Thread(target=_play, daemon=True)
        thread.start()

    def stop(self):
        self._playing = False
        if self._current_process:
            self._current_process.terminate()
            self._current_process = None

    def is_playing(self):
        return self._playing

    def generate_beep(self, filepath, frequency=800, duration=0.5):
        try:
            import numpy as np
            import scipy.io.wavfile as wav

            sample_rate = 44100
            t = np.linspace(0, duration, int(sample_rate * duration))
            tone = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)

            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            wav.write(filepath, sample_rate, tone)
            return True
        except ImportError:
            return False
