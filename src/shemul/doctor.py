from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import List


@dataclass
class DoctorCheck:
    name: str
    ok: bool
    detail: str


class Doctor:
    def run(self) -> List[DoctorCheck]:
        checks: List[DoctorCheck] = []

        docker = shutil.which("docker")
        if docker:
            checks.append(DoctorCheck("docker", True, "docker found"))
            checks.append(self._check_docker_running())
            checks.append(self._check_compose())
        else:
            checks.append(DoctorCheck("docker", False, "docker not found"))

        return checks

    def _check_docker_running(self) -> DoctorCheck:
        try:
            result = subprocess.run(["docker", "info"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return DoctorCheck("docker daemon", True, "docker is running")
            return DoctorCheck("docker daemon", False, "docker not running")
        except OSError:
            return DoctorCheck("docker daemon", False, "docker not running")

    def _check_compose(self) -> DoctorCheck:
        try:
            result = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return DoctorCheck("docker compose", True, "docker compose available")
            return DoctorCheck("docker compose", False, "docker compose unavailable")
        except OSError:
            return DoctorCheck("docker compose", False, "docker compose unavailable")
