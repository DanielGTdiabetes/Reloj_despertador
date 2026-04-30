from __future__ import annotations

from dataclasses import dataclass
import os


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_flag(name: str, default: bool = False) -> bool:
    if name not in os.environ:
        return default
    return _is_truthy(os.environ.get(name))


@dataclass(frozen=True)
class RuntimeFlags:
    safe_mode: bool
    disable_round: bool
    disable_rect: bool
    disable_encoder: bool
    disable_audio: bool
    disable_weather: bool

    @classmethod
    def from_env(cls) -> "RuntimeFlags":
        safe_mode = env_flag("SAFE_MODE", False)
        return cls(
            safe_mode=safe_mode,
            disable_round=env_flag("DISABLE_ROUND", False),
            disable_rect=env_flag("DISABLE_RECT", False),
            disable_encoder=env_flag("DISABLE_ENCODER", False),
            disable_audio=env_flag("DISABLE_AUDIO", safe_mode),
            disable_weather=env_flag("DISABLE_WEATHER", safe_mode),
        )

    def summary(self) -> str:
        parts = []
        if self.safe_mode:
            parts.append("SAFE_MODE")
        if self.disable_round:
            parts.append("DISABLE_ROUND")
        if self.disable_rect:
            parts.append("DISABLE_RECT")
        if self.disable_encoder:
            parts.append("DISABLE_ENCODER")
        if self.disable_audio:
            parts.append("DISABLE_AUDIO")
        if self.disable_weather:
            parts.append("DISABLE_WEATHER")
        return ", ".join(parts) if parts else "default"

