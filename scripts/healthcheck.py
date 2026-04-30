#!/usr/bin/env python3

from __future__ import annotations

import json
import time

from common import load_project_config

from display import DisplayManager
from hardware.audio import I2SAudio
from hardware.rotary_encoder import RotaryEncoder
from paths import CONFIG_PATH
from runtime_flags import RuntimeFlags
from services.weather import WeatherService


def main() -> int:
    flags = RuntimeFlags.from_env()
    cfg = load_project_config()

    report: dict[str, object] = {
        "flags": flags.summary(),
        "ok": True,
        "subsystems": {},
    }
    exit_code = 0

    # Displays (isolated)
    manager = None
    try:
        ui_cfg = cfg.get("ui", {})
        manager = DisplayManager(
            cfg,
            flags,
            brightness_round=int(ui_cfg.get("brightness_round", 80)),
            brightness_rect=int(ui_cfg.get("brightness_rect", 80)),
        )
        manager.init()
        display_status = manager.healthcheck()
        report["subsystems"] = {**report["subsystems"], "displays": display_status}

        for name, disabled in (("round", flags.disable_round), ("rect", flags.disable_rect)):
            if disabled:
                continue
            if not display_status.get(name, {}).get("present", False):
                exit_code = max(exit_code, 2)
    except Exception as exc:
        report["subsystems"] = {**report["subsystems"], "displays_error": str(exc)}
        exit_code = max(exit_code, 2)
    finally:
        if manager:
            manager.cleanup()

    # Encoder
    if flags.disable_encoder:
        report["subsystems"] = {**report["subsystems"], "encoder": {"disabled": True}}
    else:
        enc = None
        try:
            enc_cfg = cfg.get("encoder", {})
            enc = RotaryEncoder(
                clk_pin=enc_cfg.get("clk_pin", 5),
                dt_pin=enc_cfg.get("dt_pin", 6),
                sw_pin=enc_cfg.get("sw_pin", 13),
            )
            time.sleep(0.1)
            report["subsystems"] = {**report["subsystems"], "encoder": {"ok": True}}
        except Exception as exc:
            report["subsystems"] = {**report["subsystems"], "encoder": {"ok": False, "error": str(exc)}}
            exit_code = max(exit_code, 2)
        finally:
            if enc:
                enc.cleanup()

    # Audio
    audio_cfg = cfg.get("audio", {})
    if flags.disable_audio or not audio_cfg.get("enabled", True):
        report["subsystems"] = {**report["subsystems"], "audio": {"disabled": True}}
    else:
        audio = None
        try:
            audio = I2SAudio(device=audio_cfg.get("device", "max98357a"))
            report["subsystems"] = {**report["subsystems"], "audio": {"ok": True}}
        except Exception as exc:
            report["subsystems"] = {**report["subsystems"], "audio": {"ok": False, "error": str(exc)}}
            exit_code = max(exit_code, 2)
        finally:
            if audio:
                audio.stop()

    # Weather (no network call)
    if flags.disable_weather:
        report["subsystems"] = {**report["subsystems"], "weather": {"disabled": True}}
    else:
        try:
            weather = WeatherService(str(CONFIG_PATH))
            _ = weather.get_current()
            report["subsystems"] = {**report["subsystems"], "weather": {"ok": True}}
        except Exception as exc:
            report["subsystems"] = {**report["subsystems"], "weather": {"ok": False, "error": str(exc)}}
            exit_code = max(exit_code, 1)

    report["ok"] = exit_code == 0
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
