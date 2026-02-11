from __future__ import annotations

from typing import List


def complete(words: List[str], candidates: List[str]) -> List[str]:
    if not words:
        return sorted(candidates)
    current = words[-1]
    return sorted([c for c in candidates if c.startswith(current)])
