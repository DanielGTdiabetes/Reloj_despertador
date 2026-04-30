from __future__ import annotations

import traceback
from typing import Any

from runtime_flags import RuntimeFlags

from .rect_display import RectDisplay
from .round_display import RoundDisplay


class DisplayManager:
    """
    Render síncrono. Sin workers, sin colas.

    Toda la serialización SPI la garantiza `SpiBus` (lock global y
    reconfiguración por transacción). Llamamos a `display.render()`
    directamente desde el bucle principal.
    """

    def __init__(
        self,
        config: dict[str, Any],
        flags: RuntimeFlags,
        *,
        brightness_round: int = 80,
        brightness_rect: int = 80,
    ) -> None:
        self._config = config
        self._flags = flags

        self.round: RoundDisplay | None = None
        self.rect: RectDisplay | None = None

        self._brightness_round = brightness_round
        self._brightness_rect = brightness_rect

        self._round_error = ""
        self._rect_error = ""

    def init(self) -> None:
        self._init_round()
        self._init_rect()

    def _init_round(self) -> None:
        if self._flags.disable_round:
            print("[HW] round display disabled by env")
            return

        try:
            cfg = self._config["displays"]["round"]
            self.round = RoundDisplay(cfg)
            self.round.init()
            self.round.set_brightness(self._brightness_round)
            print("[HW] round display OK")
        except Exception as exc:
            self.round = None
            self._round_error = str(exc)
            print(f"[HW] round display failed: {exc}")
            traceback.print_exc()

    def _init_rect(self) -> None:
        if self._flags.disable_rect:
            print("[HW] rect display disabled by env")
            return

        try:
            cfg = self._config["displays"]["rect"]
            self.rect = RectDisplay(cfg)
            self.rect.init()
            self.rect.set_brightness(self._brightness_rect)
            print("[HW] rect display OK")
        except Exception as exc:
            self.rect = None
            self._rect_error = str(exc)
            print(f"[HW] rect display failed: {exc}")
            traceback.print_exc()

    def set_brightness(
        self, *, round_percent: int | None = None, rect_percent: int | None = None
    ) -> None:
        if round_percent is not None:
            self._brightness_round = round_percent
            if self.round:
                self.round.set_brightness(round_percent)
        if rect_percent is not None:
            self._brightness_rect = rect_percent
            if self.rect:
                self.rect.set_brightness(rect_percent)

    def submit(
        self, *, round_image: Any | None = None, rect_image: Any | None = None
    ) -> None:
        if round_image is not None and self.round is not None:
            try:
                self.round.render(round_image)
                self._round_error = ""
            except Exception as exc:
                self._round_error = str(exc)
                print(f"[Display:round] render failed: {exc}")
                traceback.print_exc()

        if rect_image is not None and self.rect is not None:
            try:
                self.rect.render(rect_image)
                self._rect_error = ""
            except Exception as exc:
                self._rect_error = str(exc)
                print(f"[Display:rect] render failed: {exc}")
                traceback.print_exc()

    def healthcheck(self) -> dict[str, Any]:
        return {
            "round": {"present": self.round is not None, "error": self._round_error},
            "rect": {"present": self.rect is not None, "error": self._rect_error},
        }

    def cleanup(self) -> None:
        if self.round:
            try:
                self.round.cleanup()
            except Exception:
                traceback.print_exc()
        if self.rect:
            try:
                self.rect.cleanup()
            except Exception:
                traceback.print_exc()
