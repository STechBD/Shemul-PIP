from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Dict, Optional


def detect_os() -> str:
    """Return the current OS as one of "windows", "macos", "linux".

    Mirrors the sys.platform branching in util.global_config_path so tests can
    monkeypatch shemul.platforms.sys.platform the same way.
    """
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def detect_arch() -> str:
    """Return a normalized CPU architecture: amd64, arm64, or the raw value."""
    if hasattr(os, "uname"):
        machine = os.uname().machine
    else:
        machine = os.environ.get("PROCESSOR_ARCHITECTURE", "")
    machine = machine.lower()
    if machine in {"x86_64", "amd64", "x64"}:
        return "amd64"
    if machine in {"arm64", "aarch64"}:
        return "arm64"
    return machine or "unknown"


def resolve_interpreter(name: str = "python") -> str:
    """Resolve a portable Python interpreter command for the current machine.

    Probes python -> py -3 -> python3 and returns the first available. Falls
    back to "python3" (the most cross-platform name) when none are found.
    """
    if name not in {"python", "python3", "py"}:
        # Non-python interpreters: return as-is if present, else the name.
        return name if shutil.which(name) else name
    for candidate in ("python", "py -3", "python3"):
        exe = candidate.split()[0]
        if shutil.which(exe):
            return candidate
    return "python3"


def magic_vars(current_os: Optional[str] = None) -> Dict[str, str]:
    """Build the table of auto-injected platform variables."""
    current_os = current_os or detect_os()
    return {
        "os": current_os,
        "arch": detect_arch(),
        "python": resolve_interpreter(),
        "shell": "powershell" if current_os == "windows" else "sh",
        "sep": "\\" if current_os == "windows" else "/",
        "home": str(Path.home()),
    }


# Shell names that a top-level `runtime` may select as the default interpreter.
RECOGNIZED_SHELLS = {"sh", "bash", "zsh", "fish", "dash", "ksh", "powershell", "pwsh", "cmd"}


def normalize_os_key(key: str) -> str:
    """Normalize an OS key from a config os{} map to a canonical value."""
    value = key.strip().lower()
    if value in {"windows", "win", "win32"}:
        return "windows"
    if value in {"macos", "mac", "darwin", "osx"}:
        return "macos"
    if value in {"linux", "unix"}:
        return "linux"
    return value
