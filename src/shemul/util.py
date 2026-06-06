from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_upward(start: Path, filename: str) -> Path | None:
    current = start
    while True:
        candidate = current / filename
        if candidate.exists():
            return candidate
        if current.parent == current:
            return None
        current = current.parent


def is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def global_config_path() -> Path:
    override = os.environ.get("SHEMUL_GLOBAL_CONFIG_PATH")
    if override:
        return Path(override).expanduser()

    config_home = os.environ.get("SHEMUL_CONFIG_HOME")
    if config_home:
        return Path(config_home).expanduser() / "shemul" / "shemul.json"

    if sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        base = Path(appdata).expanduser() if appdata else (Path.home() / "AppData" / "Roaming")
        return base / "Shemul" / "shemul.json"

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Shemul" / "shemul.json"

    xdg_home = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg_home).expanduser() if xdg_home else (Path.home() / ".config")
    return base / "shemul" / "shemul.json"


def global_cache_path() -> Path:
    override = os.environ.get("SHEMUL_GLOBAL_CACHE_PATH")
    if override:
        return Path(override).expanduser()

    config_home = os.environ.get("SHEMUL_CONFIG_HOME")
    if config_home:
        return Path(config_home).expanduser() / "shemul" / "update-cache.json"

    if sys.platform.startswith("win"):
        appdata = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        base = Path(appdata).expanduser() if appdata else (Path.home() / "AppData" / "Local")
        return base / "Shemul" / "update-cache.json"

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "Shemul" / "update-cache.json"

    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg_cache).expanduser() if xdg_cache else (Path.home() / ".cache")
    return base / "shemul" / "update-cache.json"


def global_settings_path() -> Path:
    override = os.environ.get("SHEMUL_SETTINGS_PATH")
    if override:
        return Path(override).expanduser()
    # Settings live next to the global config (user preferences, not a cache).
    return global_config_path().parent / "settings.json"


def open_in_editor(path: Path) -> bool:
    editor = os.environ.get("SHEMUL_EDITOR") or os.environ.get("VISUAL") or os.environ.get("EDITOR")
    if editor:
        command = editor
        if "{file}" in command:
            command = command.replace("{file}", str(path))
        else:
            command = f'{command} "{path}"'
        completed = subprocess.run(command, shell=True, check=False)
        return completed.returncode == 0

    try:
        os.startfile(str(path))  # type: ignore[attr-defined]
        return True
    except Exception:
        return False
