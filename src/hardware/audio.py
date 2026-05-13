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

    def _max_out_cset_volumes(self):
        """Set all hardware volume controls to their maximum raw value via cset."""
        try:
            out = subprocess.check_output(
                ["amixer", "-c", self._card_num, "contents"],
                stderr=subprocess.DEVNULL, text=True,
            )
        except Exception:
            return
        import re
        current_numid = None
        max_val = None
        is_volume = False
        for line in out.splitlines():
            m = re.match(r"numid=(\d+).*name='(.+)'", line)
            if m:
                current_numid = m.group(1)
                name = m.group(2).lower()
                is_volume = "volume" in name and "capture" not in name
                max_val = None
            elif is_volume and "min=" in line:
                m2 = re.search(r"max=(\d+)", line)
                if m2:
                    max_val = m2.group(1)
            elif is_volume and max_val and line.strip().startswith(": values="):
                vals = line.strip()[len(": values="):]
                count = len(vals.split(","))
                raw = ",".join([max_val] * count)
                try:
                    subprocess.run(
                        ["amixer", "-c", self._card_num, "cset",
                         f"numid={current_numid}", raw],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                except Exception:
                    pass

    def set_volume(self, percent):
        self._volume = max(0, min(100, percent))
        v = self._volume
        # Max out every hardware control regardless of chip — works for any USB DAC
        for control in ("PCM Playback Volume", "Headphone Playback Volume",
                        "Speaker", "Master", "Headphone", "PCM"):
            try:
                subprocess.run(
                    ["amixer", "-c", self._card_num, "sset", control, "100%"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
                )
            except subprocess.CalledProcessError:
                pass
        # Some USB DACs use non-TLV controls only settable via cset with raw values
        self._max_out_cset_volumes()

        # Actual volume via softvol "PCM Boost" (.asoundrc); created on first device open
        try:
            subprocess.run(
                ["amixer", "-c", self._card_num, "sset", "PCM Boost", f"{v}%"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
            )
        except subprocess.CalledProcessError:
            pass

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
