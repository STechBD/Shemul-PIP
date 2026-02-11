from __future__ import annotations

from rich.prompt import Confirm


class Guard:
    def confirm(self, message: str) -> bool:
        return Confirm.ask(message, default=False)
