from __future__ import annotations

import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

import RPi.GPIO as GPIO
import spidev


@dataclass(frozen=True)
class SpiDeviceProfile:
    name: str
    port: int
    device: int
    cs_pin: int
    mode: int = 0
    bits_per_word: int = 8
    init_speed_hz: int = 4_000_000
    frame_speed_hz: int = 24_000_000


class SpiBus:
    _instance: "SpiBus | None" = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._handles: dict[tuple[int, int], spidev.SpiDev] = {}
        self._profiles: dict[str, SpiDeviceProfile] = {}

    @classmethod
    def instance(cls) -> "SpiBus":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def register_device(self, profile: SpiDeviceProfile) -> None:
        self._profiles[profile.name] = profile
        GPIO.setup(profile.cs_pin, GPIO.OUT, initial=GPIO.HIGH)
        print(f"[SPI] registered {profile.name} spi{profile.port}.{profile.device} CS={profile.cs_pin}")

    def _all_cs_high(self) -> None:
        for profile in self._profiles.values():
            GPIO.output(profile.cs_pin, GPIO.HIGH)

    def _handle(self, port: int, device: int) -> spidev.SpiDev:
        key = (port, device)
        spi = self._handles.get(key)
        if spi is None:
            spi = spidev.SpiDev()
            spi.open(port, device)
            try:
                spi.no_cs = True
            except Exception as exc:
                raise RuntimeError(
                    f"[SPI] no se pudo activar no_cs en spi{port}.{device}: {exc}"
                ) from exc
            self._handles[key] = spi
        return spi

    @contextmanager
    def transaction(self, name: str, *, init_phase: bool = False) -> Iterator[spidev.SpiDev]:
        if name not in self._profiles:
            raise ValueError(f"[SPI] unknown device profile: {name}")

        profile = self._profiles[name]
        speed = profile.init_speed_hz if init_phase else profile.frame_speed_hz

        with self._lock:
            spi = self._handle(profile.port, profile.device)
            self._all_cs_high()
            spi.mode = profile.mode
            spi.bits_per_word = profile.bits_per_word
            spi.max_speed_hz = speed
            GPIO.output(profile.cs_pin, GPIO.LOW)
            try:
                yield spi
            finally:
                GPIO.output(profile.cs_pin, GPIO.HIGH)
                self._all_cs_high()

    def close(self) -> None:
        with self._lock:
            self._all_cs_high()
            for spi in self._handles.values():
                try:
                    spi.close()
                except Exception:
                    pass
            self._handles.clear()
