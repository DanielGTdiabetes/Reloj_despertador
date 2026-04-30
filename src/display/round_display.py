from __future__ import annotations

from typing import Any


class RoundDisplay:
    def __init__(self, cfg: dict[str, Any]) -> None:
        self._cfg = cfg
        self._display = None

    def init(self) -> None:
        from hardware.gc9a01 import GC9A01

        self._display = GC9A01(
            spi_port=self._cfg.get("spi_port", 0),
            spi_device=self._cfg.get("spi_device", 0),
            cs_pin=self._cfg.get("cs_pin", 8),
            dc_pin=self._cfg.get("dc_pin", 25),
            rst_pin=self._cfg.get("rst_pin", 26),
            bl_pin=self._cfg.get("bl_pin"),
        )

    def set_brightness(self, percent: int) -> None:
        if self._display:
            self._display.set_brightness(percent)

    def clear(self) -> None:
        if self._display:
            self._display.clear()

    def render(self, image: Any) -> None:
        if not self._display:
            raise RuntimeError("round display not initialized")
        self._display.display(image)

    def healthcheck(self) -> bool:
        return self._display is not None

    def cleanup(self) -> None:
        if self._display:
            self._display.cleanup()

