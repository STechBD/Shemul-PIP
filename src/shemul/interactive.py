from __future__ import annotations

import os
import sys
from typing import Dict, List, Optional, Sequence

from .util import is_truthy

try:  # questionary is optional at runtime; we degrade gracefully without it.
    import questionary
except Exception:  # pragma: no cover - import guard
    questionary = None


def interactive_enabled() -> bool:
    """True only when an arrow-key UI can actually work.

    Disabled by `SHEMUL_NO_INTERACTIVE`, when questionary is missing, or when
    stdin/stdout is not a TTY (CI, pipes, test runners).
    """
    if is_truthy(os.environ.get("SHEMUL_NO_INTERACTIVE", "")):
        return False
    if questionary is None:
        return False
    try:
        return bool(sys.stdin.isatty() and sys.stdout.isatty())
    except Exception:
        return False


def confirm(message: str, default: bool = False) -> bool:
    """Yes/No prompt. Interactive arrow-key selection when possible.

    Falls back to rich's typed confirm (and then to `default`) when not
    interactive, so CI and tests never block.
    """
    if interactive_enabled():
        try:
            choice = questionary.select(
                message,
                choices=["Yes", "No"],
                default="Yes" if default else "No",
                instruction="(use arrow keys, then Enter)",
            ).ask()
            if choice is None:  # cancelled (Ctrl-C / Esc)
                return default
            return choice == "Yes"
        except Exception:
            pass

    try:
        from rich.prompt import Confirm

        return Confirm.ask(message, default=default)
    except Exception:
        return default


def select_one(
    message: str,
    choices: Sequence[str],
    default: Optional[str] = None,
) -> Optional[str]:
    """Pick one option with arrow keys; returns `default` when non-interactive."""
    options = list(choices)
    if not options:
        return None
    if interactive_enabled():
        try:
            picked = questionary.select(
                message,
                choices=options,
                default=default if default in options else None,
                instruction="(use arrow keys, then Enter)",
            ).ask()
            return picked
        except Exception:
            pass
    if default is not None:
        return default
    return options[0]


def toggle_settings(message: str, items: Dict[str, bool]) -> Optional[Dict[str, bool]]:
    """Checkbox UI for boolean settings.

    Returns the new mapping, or None when non-interactive / cancelled (caller
    should keep the existing values in that case).
    """
    if not items or not interactive_enabled():
        return None
    try:
        choices = [questionary.Choice(title=name, checked=bool(val)) for name, val in items.items()]
        selected: Optional[List[str]] = questionary.checkbox(message, choices=choices).ask()
        if selected is None:
            return None
        return {name: (name in selected) for name in items}
    except Exception:
        return None
