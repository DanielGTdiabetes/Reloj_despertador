from __future__ import annotations

import traceback
from typing import Any

from runtime_flags import RuntimeFlags

from .rect_display import RectDisplay
from .round_display import RoundDisplay


class DisplayManager:
    def __init__(self, config: dict[str, Any], flags: RuntimeFlags, *, brightness_round: int = 80, brightness_rect: int = 80) -> None:
        self._config = config
        self._flags = flags
        self.round: RoundDisplay | None = None
        self.rect: RectDisplay | None = None
        self._brightness_round = brightness_round
        self._brightness_rect = brightness_rect
        self._round_error = ""
        self._rect_error = ""

    def _validate(self) -> None:
        round_cfg = self._config["displays"]["round"]
        rect_cfg = self._config["displays"]["rect"]
        if (rect_cfg.get("width"), rect_cfg.get("height")) != (284, 76):
            raise ValueError("[ST7789] dims must be 284x76")
        if len({round_cfg.get("dc_pin"), round_cfg.get("rst_pin"), rect_cfg.get("dc_pin"), rect_cfg.get("rst_pin"), rect_cfg.get("cs_pin")}) < 5:
            raise ValueError("[BOOT] duplicated display control pins")
        if rect_cfg.get("cs_pin") in (2, 3):
            raise ValueError("[BOOT] GPIO2/GPIO3 reserved for I2C UPS")

    def init(self) -> None:
        self._validate()
        boot_cfg = self._config.get("boot", {})
        if boot_cfg.get("diag_only_rect", False):
            print("[BOOT] diag_only_rect enabled")
            self._init_rect()
            return
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
            print("[GC9A01] init OK")
        except Exception as exc:
            self.round = None
            self._round_error = str(exc)
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
            print("[ST7789] init OK")
        except Exception as exc:
            self.rect = None
            self._rect_error = str(exc)
            traceback.print_exc()

    def set_brightness(self, *, round_percent: int | None = None, rect_percent: int | None = None) -> None:
        if round_percent is not None and self.round:
            self.round.set_brightness(round_percent)
        if rect_percent is not None and self.rect:
            self.rect.set_brightness(rect_percent)

    def submit(self, *, round_image: Any | None = None, rect_image: Any | None = None) -> None:
        if round_image is not None and self.round is not None:
            self.round.render(round_image)
        if rect_image is not None and self.rect is not None:
            self.rect.render(rect_image)

    def cleanup(self) -> None:
        if self.round:
            self.round.cleanup()
        if self.rect:
            self.rect.cleanup()
