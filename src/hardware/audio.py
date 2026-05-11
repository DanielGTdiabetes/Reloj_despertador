"""
USB Audio Driver - UGREEN USB Sound Card (ALC4030)
Handles alarm sounds and audio playback via ALSA/aplay.
"""

import subprocess
import os
import threading
import time


class I2SAudio:
    def __init__(self, device="USB Audio"):
        self.device = device
        self._alsa_device, self._card_num = self._resolve_alsa_device(device)
        self._playing = False
        self._current_process = None
        self._volume = 80

    def _resolve_alsa_device(self, name):
        """Return (aplay -D spec, card_num).

        Prefers the 'ugreen' named device from ~/.asoundrc (stereo→mono mix for
        single-speaker setups). Falls back to plughw:{card},0 if not found.
        """
        try:
            listed = subprocess.check_output(["aplay", "-L"], stderr=subprocess.DEVNULL, text=True)
            if "ugreen" in listed.lower():
                # Named device from .asoundrc handles mono mix
                out = subprocess.check_output(["aplay", "-l"], stderr=subprocess.DEVNULL, text=True)
                for line in out.splitlines():
                    if name.lower() in line.lower() and line.startswith("card"):
                        card_num = line.split(":")[0].replace("card", "").strip()
                        return "ugreen", card_num
        except Exception:
            pass
        try:
            out = subprocess.check_output(["aplay", "-l"], stderr=subprocess.DEVNULL, text=True)
            for line in out.splitlines():
                if name.lower() in line.lower() and line.startswith("card"):
                    card_num = line.split(":")[0].replace("card", "").strip()
                    return f"plughw:{card_num},0", card_num
        except Exception:
            pass
        return "plughw:0,0", "0"

    def set_volume(self, percent):
        self._volume = max(0, min(100, percent))
        v = self._volume
        # KT USB Audio uses a non-simple control — must use cset numid=3
        try:
            subprocess.run(
                ["amixer", "-c", self._card_num, "cset", "numid=3", f"{v},{v}"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
            )
            return
        except subprocess.CalledProcessError:
            pass
        # Fallback for other cards with simple controls
        for control in ("PCM", "Speaker", "Master", "Headphone"):
            try:
                subprocess.run(
                    ["amixer", "-c", self._card_num, "sset", control, f"{v}%"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
                )
                break
            except subprocess.CalledProcessError:
                continue

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

    def is_playing(self):
        return self._playing
