from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config_loader import load_config  # noqa: E402
from paths import CONFIG_PATH  # noqa: E402


def load_project_config() -> dict:
    return load_config(str(CONFIG_PATH))

