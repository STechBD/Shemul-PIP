from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Dict


@dataclass
class ExecutionResult:
    command: str
    return_code: int


class Executor:
    def run(self, command: str, env: Dict[str, str] | None = None, dry: bool = False) -> ExecutionResult:
        if dry:
            return ExecutionResult(command=command, return_code=0)

        completed = subprocess.run(command, shell=True, check=False, env=env)
        return ExecutionResult(command=command, return_code=completed.returncode)
