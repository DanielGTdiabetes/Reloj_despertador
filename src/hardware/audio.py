"""
I2S Audio Driver - MAX98357A Amplifier
Handles alarm sounds and audio playback via I2S
"""

import subprocess
import os
import threading
import time

class I2SAudio:
    def __init__(self, device="MAX98357A"):
        self.device = device
        self._alsa_device = self._resolve_alsa_device(device)
        self._playing = False
        self._current_process = None
        self._volume = 80

    def _resolve_alsa_device(self, name):
        """Return a working aplay -D spec, falling back to plughw:0 if needed."""
        try:
            out = subprocess.check_output(["aplay", "-l"], stderr=subprocess.DEVNULL, text=True)
            for line in out.splitlines():
                # Match case-insensitively
                if name.lower() in line.lower() and line.startswith("card"):
                    card_num = line.split(":")[0].replace("card", "").strip()
                    return f"plughw:{card_num},0"
        except Exception:
            pass
        return "plughw:0,0"

    def set_volume(self, percent):
        # MAX98357A gain is hardware-controlled; store value for reference only
        self._volume = max(0, min(100, percent))

    def play_file(self, filepath, loop=False):
        if not os.path.exists(filepath):
            print(f"[Audio] file not found: {filepath}")
            return

        self.stop()
        self._playing = True

        def _play():
            while self._playing:
                cmd = ["aplay", "-D", self._alsa_device, "-q", filepath]
                try:
                    self._current_process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                    )
                    _, err = self._current_process.communicate()
                    if err and self._playing:
                        print(f"[Audio] aplay: {err.decode(errors='replace').strip()}")
                except Exception as e:
                    print(f"[Audio] playback error: {e}")
                    time.sleep(1)
                if not loop:
                    break

        threading.Thread(target=_play, daemon=True).start()

    def stop(self):
        self._playing = False
        if self._current_process:
            try:
                self._current_process.terminate()
            except Exception:
                pass
            self._current_process = None

    def stop(self):
        self._playing = False
        if self._current_process:
            self._current_process.terminate()
            self._current_process = None

    def is_playing(self):
        return self._playing
