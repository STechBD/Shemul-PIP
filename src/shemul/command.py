from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ResolvedCommand:
    name: str
    command: str
    env: Dict[str, Any]
    confirm: bool
    danger: bool
    desc: str
    group: str


class Command:
    def __init__(self, name: str, config: Dict[str, Any], vars_map: Dict[str, Any], envs: Dict[str, Any]) -> None:
        self.name = name
        self.config = config
        self.vars_map = vars_map
        self.envs = envs

    def resolve(self) -> ResolvedCommand:
        run = str(self.config["run"])
        env_name = self.config.get("env")
        env_data = {}
        if env_name:
            env_data = dict(self.envs.get(env_name, {}))

        template_vars = {**self.vars_map, "env": env_data}
        resolved = self._template(run, template_vars)

        return ResolvedCommand(
            name=self.name,
            command=resolved,
            env=env_data,
            confirm=bool(self.config.get("confirm", False)),
            danger=bool(self.config.get("danger", False)),
            desc=str(self.config.get("desc", "")),
            group=str(self.config.get("group", "core")),
        )

    def _template(self, text: str, vars_map: Dict[str, Any]) -> str:
        result = text
        for key, value in vars_map.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    token = "{{" + f"{key}.{sub_key}" + "}}"
                    result = result.replace(token, str(sub_value))
            else:
                token = "{{" + f"{key}" + "}}"
                result = result.replace(token, str(value))
        return result
