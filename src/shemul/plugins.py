from __future__ import annotations

import importlib.metadata as importlib_metadata
from dataclasses import dataclass, field
from typing import Callable, Dict, List

ENTRY_POINT_GROUP = "shemul.plugins"


@dataclass
class PluginRegistry:
    resolvers: Dict[str, Callable] = field(default_factory=dict)
    runners: Dict[str, Callable] = field(default_factory=dict)

    def register_resolver(self, name: str, fn: Callable) -> None:
        self.resolvers[str(name)] = fn

    def register_runner(self, name: str, fn: Callable) -> None:
        self.runners[str(name)] = fn


def _iter_entry_points(group: str) -> List:
    try:
        eps = importlib_metadata.entry_points()
    except Exception:
        return []
    # Python 3.10+ selectable API.
    select = getattr(eps, "select", None)
    if callable(select):
        try:
            return list(select(group=group))
        except Exception:
            return []
    # Python 3.9 dict-style API.
    try:
        return list(eps.get(group, []))  # type: ignore[attr-defined]
    except Exception:
        return []


def discover(registry: PluginRegistry | None = None) -> PluginRegistry:
    """Discover and load plugins from the shemul.plugins entry-point group.

    Each entry point is expected to load a callable that takes the registry and
    registers resolvers/runners. Failures in any single plugin are ignored so a
    broken plugin never blocks the CLI.
    """
    registry = registry or PluginRegistry()
    for ep in _iter_entry_points(ENTRY_POINT_GROUP):
        try:
            hook = ep.load()
            hook(registry)
        except Exception:
            continue
    return registry
