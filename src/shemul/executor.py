from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional

from .platforms import detect_os


@dataclass
class ExecutionResult:
    command: str
    return_code: int


class Executor:
    def pick_shell(self, os_name: Optional[str] = None) -> str:
        os_name = os_name or detect_os()
        return "powershell" if os_name == "windows" else "/bin/sh"

    def run(
        self,
        command: str,
        env: Dict[str, str] | None = None,
        dry: bool = False,
        shell: bool | str = True,
        exec_argv: Optional[List[str]] = None,
    ) -> ExecutionResult:
        if dry:
            display = " ".join(exec_argv) if exec_argv is not None else command
            return ExecutionResult(command=display, return_code=0)

        # Opt-in safe execution: arg-vector or shell explicitly disabled.
        if exec_argv is not None or shell is False:
            argv = exec_argv if exec_argv is not None else command
            completed = subprocess.run(argv, shell=False, check=False, env=env)
            display = " ".join(exec_argv) if exec_argv is not None else command
            return ExecutionResult(command=display, return_code=completed.returncode)

        # A named shell (string) selects the interpreter on POSIX via `executable`.
        # On Windows or when the shell is not found, fall back to the default shell.
        executable = None
        if isinstance(shell, str) and shell and not sys.platform.startswith("win"):
            executable = shutil.which(shell)

        # Default path — identical to 1.0.1 behaviour when executable is None.
        completed = subprocess.run(command, shell=True, check=False, env=env, executable=executable)
        return ExecutionResult(command=command, return_code=completed.returncode)
