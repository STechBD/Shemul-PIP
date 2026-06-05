from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .platforms import RECOGNIZED_SHELLS, detect_os, magic_vars, normalize_os_key


@dataclass
class ResolvedCommand:
    name: str
    command: str
    env: Dict[str, Any]
    confirm: bool
    danger: bool
    desc: str
    group: str
    shell: bool | str = True
    exec_argv: Optional[List[str]] = None
    runner: str = ""


class Command:
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        vars_map: Dict[str, Any],
        envs: Dict[str, Any],
        bin_map: Optional[Dict[str, Any]] = None,
        current_os: Optional[str] = None,
        runtime: str = "",
    ) -> None:
        self.name = name
        self.config = config
        self.vars_map = vars_map
        self.envs = envs
        self.bin_map = bin_map or {}
        self.current_os = current_os or detect_os()
        self.runtime = runtime or ""

    def resolve(self) -> ResolvedCommand:
        base = self._select_base()

        env_name = self.config.get("env")
        env_data = {}
        if env_name:
            env_data = dict(self.envs.get(env_name, {}))

        # Expansion order: user vars/env first, then magic vars, then bin map,
        # so user-defined values can override the auto-injected ones.
        template_vars = {**self.vars_map, "env": env_data}
        resolved = self._template(base, template_vars)
        resolved = self._template(resolved, magic_vars(self.current_os))
        bin_for_os = self._bin_for_os()
        # Support both the namespaced {{bin.py}} and the bare {{py}} forms.
        resolved = self._template(resolved, {"bin": bin_for_os})
        resolved = self._template(resolved, bin_for_os)

        if "shell" in self.config:
            shell_val = self.config.get("shell")
        elif self.runtime and self.runtime.lower() in RECOGNIZED_SHELLS:
            shell_val = self.runtime.lower()
        else:
            shell_val = True
        exec_cfg = self.config.get("exec")
        exec_argv = list(exec_cfg) if exec_cfg else None

        return ResolvedCommand(
            name=self.name,
            command=resolved,
            env=env_data,
            confirm=bool(self.config.get("confirm", False)),
            danger=bool(self.config.get("danger", False)),
            desc=str(self.config.get("desc", "")),
            group=str(self.config.get("group", "core")),
            shell=shell_val,
            exec_argv=exec_argv,
            runner=str(self.config.get("runner", "")),
        )

    def _select_base(self) -> str:
        os_map = self.config.get("os") or {}
        if os_map:
            normalized = {normalize_os_key(k): v for k, v in os_map.items()}
            if self.current_os in normalized:
                return str(normalized[self.current_os])
            if "default" in normalized:
                return str(normalized["default"])
        return str(self.config["run"])

    def _bin_for_os(self) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for key, per_os in self.bin_map.items():
            if isinstance(per_os, dict):
                normalized = {normalize_os_key(k): v for k, v in per_os.items()}
                out[key] = str(normalized.get(self.current_os, normalized.get("default", "")))
            else:
                out[key] = str(per_os)
        return out

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
