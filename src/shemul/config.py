from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import jsonschema

from .util import read_json


@dataclass
class ShemulConfig:
    raw: Dict[str, Any]
    path: Path

    @property
    def name(self) -> str:
        return str(self.raw.get("name", ""))

    @property
    def commands(self) -> Dict[str, Any]:
        return dict(self.raw.get("commands", {}))

    @property
    def vars(self) -> Dict[str, Any]:
        return dict(self.raw.get("vars", {}))

    @property
    def envs(self) -> Dict[str, Any]:
        return dict(self.raw.get("env", {}))


class ConfigLoader:
    def __init__(self, schema_path: Path) -> None:
        self.schema_path = schema_path

    def load(self, path: Path) -> ShemulConfig:
        raw = read_json(path)
        schema = read_json(self.schema_path)
        jsonschema.validate(instance=raw, schema=schema)
        return ShemulConfig(raw=raw, path=path)

    def schema_text(self) -> str:
        return self.schema_path.read_text(encoding="utf-8")

    def merge(self, project: Optional[ShemulConfig], global_cfg: Optional[ShemulConfig]) -> Optional[ShemulConfig]:
        if project and not global_cfg:
            return project
        if global_cfg and not project:
            return global_cfg
        if not project and not global_cfg:
            return None

        assert project is not None and global_cfg is not None

        merged = dict(global_cfg.raw)
        merged["vars"] = {**global_cfg.vars, **project.vars}
        merged["env"] = {**global_cfg.envs, **project.envs}
        merged["commands"] = {**global_cfg.commands, **project.commands}
        merged["name"] = project.name or global_cfg.name
        merged_path = project.path
        return ShemulConfig(raw=merged, path=merged_path)
