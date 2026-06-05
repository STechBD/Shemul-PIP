from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .util import global_settings_path, is_truthy

DEFAULTS: Dict[str, Any] = {
    # Auto-update is opt-in: running pip on the user's behalf is invasive.
    "auto_update": False,
}

# Accepted aliases that map onto a canonical settings key.
_KEY_ALIASES = {
    "auto_update": "auto_update",
    "auto-update": "auto_update",
    "autoupdate": "auto_update",
}

_FALSY = {"0", "false", "no", "n", "off", "disable", "disabled"}


def _normalize_key(key: str) -> Optional[str]:
    return _KEY_ALIASES.get(str(key).strip().lower())


def _parse_bool(value: str) -> Optional[bool]:
    text = str(value).strip().lower()
    if is_truthy(text) or text in {"enable", "enabled"}:
        return True
    if text in _FALSY:
        return False
    return None


def load(path: Optional[Path] = None) -> Dict[str, Any]:
    path = path or global_settings_path()
    data = dict(DEFAULTS)
    try:
        stored = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(stored, dict):
            data.update({k: v for k, v in stored.items() if k in DEFAULTS})
    except Exception:
        pass
    return data


def save(data: Dict[str, Any], path: Optional[Path] = None) -> None:
    path = path or global_settings_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        keep = {k: v for k, v in data.items() if k in DEFAULTS}
        path.write_text(json.dumps(keep, indent=2) + "\n", encoding="utf-8")
    except Exception:
        pass


def get(key: str, default: Any = None, path: Optional[Path] = None) -> Any:
    canonical = _normalize_key(key) or key
    return load(path).get(canonical, default)


def set_value(key: str, value: Any, path: Optional[Path] = None) -> None:
    canonical = _normalize_key(key) or key
    data = load(path)
    data[canonical] = value
    save(data, path)


def handle(ui, args: List[str]) -> int:
    args = list(args or [])

    if not args:
        return _interactive_or_show(ui)

    head = args[0].strip().lower()

    if head == "reset":
        save(dict(DEFAULTS))
        ui.success("Settings reset to defaults.")
        return _show(ui)

    if head == "set" and len(args) >= 3:
        return _set(ui, args[1], args[2])

    canonical = _normalize_key(head)
    if canonical is None:
        ui.error(f"Unknown setting: {args[0]}. Known settings: {', '.join(sorted(DEFAULTS))}.")
        return 1

    if len(args) >= 2:
        return _set(ui, head, args[1])

    # No value given -> show current value for that setting.
    ui.info(f"{canonical} = {get(canonical)}")
    return 0


def _set(ui, key: str, raw_value: str) -> int:
    canonical = _normalize_key(key)
    if canonical is None:
        ui.error(f"Unknown setting: {key}. Known settings: {', '.join(sorted(DEFAULTS))}.")
        return 1
    parsed = _parse_bool(raw_value)
    if parsed is None:
        ui.error(f"Invalid value '{raw_value}' for {canonical}. Use on/off (true/false).")
        return 1
    set_value(canonical, parsed)
    ui.success(f"{canonical} = {parsed}")
    return 0


def _interactive_or_show(ui) -> int:
    from . import interactive

    if interactive.interactive_enabled():
        current = load()
        items = {k: bool(current.get(k)) for k in sorted(DEFAULTS)}
        updated = interactive.toggle_settings(
            "Shemul settings (space to toggle, Enter to save)", items
        )
        if updated is not None:
            data = load()
            data.update(updated)
            save(data)
            ui.success("Settings saved.")
    return _show(ui)


def _show(ui) -> int:
    data = load()
    rows = [[k, str(data.get(k))] for k in sorted(DEFAULTS)]
    ui.table("Settings", ["setting", "value"], rows)
    ui.info("Toggle with: shemul settings auto-update on|off")
    ui.info(f"Settings file: {global_settings_path()}")
    return 0
