"""
Bus SPI compartido y serializado.

Los dos displays (GC9A01 redonda y ST7789P3 rect) comparten físicamente MOSI/SCK
en SPI0. Cada uno usa un device distinto (CE0/CE1) con velocidades y modos
diferentes. Tener handles `spidev` abiertos en paralelo y alternar entre ellos
sin reconfigurar el controlador deja el bus en estado inconsistente.

`SpiBus` resuelve eso:
  - Singleton con lock global.
  - Mantiene un handle `spidev.SpiDev` por device, abierto perezosamente.
  - El context manager `transaction()` adquiere el lock y reaplica
    `max_speed_hz` y `mode` del device pedido antes de cada uso. Así nunca se
    asume que la configuración persiste entre llamadas.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Iterator

import spidev


class SpiBus:
    _instance: "SpiBus | None" = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._handles: dict[tuple[int, int], spidev.SpiDev] = {}

    @classmethod
    def instance(cls) -> "SpiBus":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _handle(self, port: int, device: int) -> spidev.SpiDev:
        key = (port, device)
        spi = self._handles.get(key)
        if spi is None:
            spi = spidev.SpiDev()
            spi.open(port, device)
            try:
                spi.no_cs = True
            except Exception:
                # Algunos kernels no exponen no_cs; ignoramos y delegamos en CS manual.
                pass
            self._handles[key] = spi
        return spi

    @contextmanager
    def transaction(
        self,
        port: int,
        device: int,
        speed_hz: int,
        mode: int = 0,
    ) -> Iterator[spidev.SpiDev]:
        """Toma el lock global y reconfigura el handle del device antes de usarlo."""
        with self._lock:
            spi = self._handle(port, device)
            spi.max_speed_hz = speed_hz
            spi.mode = mode
            yield spi

    def close(self) -> None:
        with self._lock:
            for spi in self._handles.values():
                try:
                    spi.close()
                except Exception:
                    pass
            self._handles.clear()
