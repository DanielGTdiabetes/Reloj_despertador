from __future__ import annotations

from typing import Any


class RectDisplay:
    def __init__(self, cfg: dict[str, Any]) -> None:
        self._cfg = cfg
        self._display = None

    def init(self) -> None:
        from hardware.st7789 import ST7789Display

        self._display = ST7789Display(
            spi_port=self._cfg.get("spi_port", 0),
            spi_device=self._cfg.get("spi_device", 1),
            cs_pin=self._cfg.get("cs_pin", 16),
            dc_pin=self._cfg.get("dc_pin", 22),
            rst_pin=self._cfg.get("rst_pin", 27),
            bl_pin=self._cfg.get("bl_pin", 23),
            col_offset=self._cfg.get("col_offset", 82),
            row_offset=self._cfg.get("row_offset", 18),
        )

    def set_brightness(self, percent: int) -> None:
        if self._display:
            self._display.set_brightness(percent)

    def clear(self) -> None:
        if self._display:
            self._display.clear()

    def render(self, image: Any) -> None:
        if not self._display:
            raise RuntimeError("rect display not initialized")
        self._display.display(image)

    def healthcheck(self) -> bool:
        return self._display is not None

    def cleanup(self) -> None:
        if self._display:
            self._display.cleanup()

