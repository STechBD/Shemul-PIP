from __future__ import annotations

from . import interactive


class Guard:
    def confirm(self, message: str) -> bool:
        return interactive.confirm(message, default=False)
