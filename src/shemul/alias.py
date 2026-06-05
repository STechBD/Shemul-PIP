from __future__ import annotations

import os
import shutil
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

MARKER = "# shemul-managed-alias v1"
WINDOWS_MARKER = "REM shemul-managed-alias v1"


@dataclass
class AliasStatus:
    state: str  # "free" | "ours" | "conflict"
    path: Optional[Path]
    detail: str


def user_bin_dir() -> Path:
    override = os.environ.get("SHEMUL_BIN_DIR")
    if override:
        return Path(override).expanduser()
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA")
        root = Path(base).expanduser() if base else (Path.home() / "AppData" / "Local")
        return root / "Shemul" / "bin"
    return Path.home() / ".local" / "bin"


def shim_path() -> Path:
    name = "s.cmd" if sys.platform.startswith("win") else "s"
    return user_bin_dir() / name


def shim_is_ours(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return False
    return MARKER in text or WINDOWS_MARKER in text


def detect(which: Callable[[str], Optional[str]] = shutil.which) -> AliasStatus:
    found = which("s")
    if not found:
        return AliasStatus("free", None, "`s` is available")
    found_path = Path(found)
    if shim_is_ours(found_path):
        return AliasStatus("ours", found_path, "`s` already points to Shemul")
    return AliasStatus("conflict", found_path, f"`s` already used by {found_path}")


def _shim_text() -> str:
    if sys.platform.startswith("win"):
        return f"@echo off\r\n{WINDOWS_MARKER}\r\nshemul %*\r\n"
    return f"#!/bin/sh\n{MARKER}\nexec shemul \"$@\"\n"


def _write_shim() -> Path:
    target = shim_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_shim_text(), encoding="utf-8")
    if not sys.platform.startswith("win"):
        mode = target.stat().st_mode
        target.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return target


def install(ui, which: Callable[[str], Optional[str]] = shutil.which) -> int:
    status = detect(which)
    if status.state == "ours":
        ui.info("Alias `s` already points to Shemul. Nothing to do.")
        return 0
    if status.state == "conflict":
        ui.warn(f"`s` is already installed at {status.path}.")
        ui.warn("Shemul will not override it to avoid breaking your system.")
        ui.info("Please continue using the full command:  shemul <command>")
        return 1
    target = _write_shim()
    ui.success("Alias enabled. You can now use:  s <command>   (same as shemul <command>)")
    ui.info(f"Created: {target}")
    ui.info(f"Ensure {target.parent} is on your PATH.")
    return 0


def remove(ui) -> int:
    target = shim_path()
    if not target.exists():
        ui.info("No Shemul-managed `s` alias found.")
        return 0
    if not shim_is_ours(target):
        ui.warn(f"{target} was not created by Shemul; leaving it untouched.")
        return 1
    try:
        target.unlink()
        ui.success(f"Removed alias shim: {target}")
        return 0
    except Exception as exc:  # pragma: no cover - filesystem edge
        ui.error(f"Could not remove {target}: {exc}")
        return 1


def status(ui, which: Callable[[str], Optional[str]] = shutil.which) -> int:
    state = detect(which)
    if state.state == "conflict":
        ui.warn(f"Alias `s`: {state.detail}. Use `shemul` instead.")
    else:
        ui.info(f"Alias `s`: {state.state} - {state.detail}")
    return 0


def handle(ui, action: str) -> int:
    action = (action or "status").lower()
    if action == "install":
        return install(ui)
    if action == "remove":
        return remove(ui)
    if action == "status":
        return status(ui)
    ui.error(f"Unknown alias action: {action}. Use install | status | remove.")
    return 1
