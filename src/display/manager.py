from __future__ import annotations

import threading
from typing import Any

from runtime_flags import RuntimeFlags

from .rect_display import RectDisplay
from .round_display import RoundDisplay
from .worker import DisplayWorker


class DisplayManager:
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
        self._spi_lock = threading.Lock()

        self.round = None
        self.rect = None
        self._round_worker = None
        self._rect_worker = None

        self._brightness_round = brightness_round
        self._brightness_rect = brightness_rect

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
            self._round_worker = DisplayWorker("round", self.round, spi_lock=self._spi_lock)
            self._round_worker.start()
            print("[HW] round display OK (worker)")
        except Exception as exc:
            self.round = None
            self._round_worker = None
            print(f"[HW] round display failed: {exc}")

    def _init_rect(self) -> None:
        if self._flags.disable_rect:
            print("[HW] rect display disabled by env")
            return

        try:
            cfg = self._config["displays"]["rect"]
            self.rect = RectDisplay(cfg)
            self.rect.init()
            self.rect.set_brightness(self._brightness_rect)
            self._rect_worker = DisplayWorker("rect", self.rect, spi_lock=self._spi_lock)
            self._rect_worker.start()
            print("[HW] rect display OK (worker)")
        except Exception as exc:
            self.rect = None
            self._rect_worker = None
            print(f"[HW] rect display failed: {exc}")

    def set_brightness(self, *, round_percent: int | None = None, rect_percent: int | None = None) -> None:
        if round_percent is not None:
            self._brightness_round = round_percent
            if self.round:
                self.round.set_brightness(round_percent)
        if rect_percent is not None:
            self._brightness_rect = rect_percent
            if self.rect:
                self.rect.set_brightness(rect_percent)

    def submit(self, *, round_image: Any | None = None, rect_image: Any | None = None) -> None:
        if round_image is not None and self._round_worker:
            self._round_worker.submit(round_image)
        if rect_image is not None and self._rect_worker:
            self._rect_worker.submit(rect_image)

    def healthcheck(self) -> dict[str, Any]:
        return {
            "round": {
                "present": self.round is not None,
                "healthy": bool(self._round_worker and self._round_worker.healthy),
                "error": getattr(self._round_worker, "last_error", ""),
            },
            "rect": {
                "present": self.rect is not None,
                "healthy": bool(self._rect_worker and self._rect_worker.healthy),
                "error": getattr(self._rect_worker, "last_error", ""),
            },
        }

    def cleanup(self) -> None:
        if self._round_worker:
            self._round_worker.cleanup()
        if self._rect_worker:
            self._rect_worker.cleanup()

