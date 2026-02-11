from __future__ import annotations

from dataclasses import dataclass
import difflib
from pathlib import Path
from typing import Dict, List, Optional

from .autocomplete import complete
from .command import Command
from .config import ConfigLoader, ShemulConfig
from .context import ContextDiscovery, ProjectContext
from .executor import Executor
from .guard import Guard
from .ui import UI
from .util import global_config_path


@dataclass
class AppState:
    context: Optional[ProjectContext]
    project_config: Optional[ShemulConfig]
    global_config: Optional[ShemulConfig]
    config: Optional[ShemulConfig]


class App:
    def __init__(self) -> None:
        self.ui = UI()
        self.guard = Guard()
        self.executor = Executor()
        self.schema_path = Path(__file__).parent / "schema.json"

    def load_state(self, start: Path) -> AppState:
        loader = ConfigLoader(self.schema_path)

        context = ContextDiscovery(start).discover()
        project_config: Optional[ShemulConfig] = None
        if context:
            project_config = loader.load(context.config_path)

        g_path = global_config_path()
        global_cfg: Optional[ShemulConfig] = None
        if g_path.exists():
            global_cfg = loader.load(g_path)

        config = loader.merge(project_config, global_cfg)
        return AppState(context=context, project_config=project_config, global_config=global_cfg, config=config)

    def list_commands(self, config: ShemulConfig) -> Dict[str, List[str]]:
        grouped: Dict[str, List[str]] = {}
        for name, cfg in config.commands.items():
            group = str(cfg.get("group", "core"))
            grouped.setdefault(group, []).append(name)
        for key in grouped:
            grouped[key] = sorted(grouped[key])
        return dict(sorted(grouped.items()))

    def command_names(self, config: ShemulConfig) -> List[str]:
        return sorted(config.commands.keys())

    def resolve(self, config: ShemulConfig, name: str):
        cmd_cfg = config.commands[name]
        cmd = Command(name, cmd_cfg, config.vars, config.envs)
        return cmd.resolve()

    def run_command(self, config: ShemulConfig, name: str, dry: bool, trace: bool, extra_args: List[str]) -> int:
        resolved = self.resolve(config, name)

        if extra_args:
            resolved = resolved.__class__(
                name=resolved.name,
                command=resolved.command + " " + " ".join(extra_args),
                env=resolved.env,
                confirm=resolved.confirm,
                danger=resolved.danger,
                desc=resolved.desc,
                group=resolved.group,
            )

        if trace:
            env_text = "\n".join([f"{k}={v}" for k, v in resolved.env.items()]) or "(none)"
            self.ui.panel("Trace", f"Command: {resolved.command}\nEnv: {env_text}")

        if resolved.danger:
            if not self.guard.confirm("This command is marked as dangerous. Continue?"):
                self.ui.warn("Aborted.")
                return 1

        if resolved.confirm:
            if not self.guard.confirm("Are you sure you want to run this command?"):
                self.ui.warn("Aborted.")
                return 1

        if dry:
            self.ui.info(resolved.command)
            return 0

        result = self.executor.run(resolved.command, env=None, dry=False)
        if result.return_code == 0:
            self.ui.success("Command completed")
        else:
            self.ui.error(f"Command failed with exit code {result.return_code}")
        return result.return_code

    def help_for(self, config: ShemulConfig, name_or_group: str) -> bool:
        if name_or_group in config.commands:
            resolved = self.resolve(config, name_or_group)
            body = f"Run: {resolved.command}\nGroup: {resolved.group}\nConfirm: {resolved.confirm}\nDanger: {resolved.danger}"
            self.ui.panel(f"Help: {name_or_group}", body)
            return True
        grouped = self.list_commands(config)
        if name_or_group in grouped:
            rows = [[name] for name in grouped[name_or_group]]
            self.ui.table(f"Group: {name_or_group}", ["Command"], rows)
            return True
        return False

    def completion(self, config: ShemulConfig, words: List[str]) -> List[str]:
        builtins = ["init", "ls", "info", "help", "doctor", "schema", "_complete"]
        candidates = list(set(builtins + self.command_names(config)))
        return complete(words, candidates)

    def suggest(self, config: ShemulConfig, name: str) -> List[str]:
        candidates = self.command_names(config)
        return difflib.get_close_matches(name, candidates, n=3, cutoff=0.5)
