from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from .util import find_upward


@dataclass
class ProjectContext:
    root: Path
    config_path: Path
    project_type: str


class ContextDiscovery:
    def __init__(self, start: Path) -> None:
        self.start = start

    def discover(self) -> Optional[ProjectContext]:
        config_path = find_upward(self.start, "shemul.json")
        if not config_path:
            return None
        root = config_path.parent
        project_type = self._detect_type(root)
        return ProjectContext(root=root, config_path=config_path, project_type=project_type)

    def _detect_type(self, root: Path) -> str:
        has_docker = (root / "docker-compose.yml").exists() or (root / "compose.yml").exists()
        has_node = (root / "package.json").exists()
        has_python = (root / "pyproject.toml").exists() or (root / "requirements.txt").exists()

        types = []
        if has_docker:
            types.append("docker")
        if has_node:
            types.append("node")
        if has_python:
            types.append("python")

        if not types:
            return "unknown"
        if len(types) == 1:
            return types[0]
        return "mixed"
