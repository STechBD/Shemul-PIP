from __future__ import annotations

import platform as _platform
import shutil
import subprocess
from dataclasses import dataclass
from typing import List

from . import alias as alias_mod
from . import settings as settings_mod
from . import updater
from .platforms import detect_arch, detect_os


@dataclass
class DoctorCheck:
    name: str
    ok: bool
    detail: str


class Doctor:
    def run(self) -> List[DoctorCheck]:
        checks: List[DoctorCheck] = []

        checks.append(self._check_os())
        checks.extend(self._check_interpreters())
        checks.append(self._check_alias())

        docker = shutil.which("docker")
        if docker:
            checks.append(DoctorCheck("docker", True, "docker found"))
            checks.append(self._check_docker_running())
            checks.append(self._check_compose())
        else:
            checks.append(DoctorCheck("docker", False, "docker not found"))

        checks.append(self._check_update_manifest())
        checks.append(self._check_auto_update())
        return checks

    def _check_auto_update(self) -> DoctorCheck:
        enabled = bool(settings_mod.get("auto_update"))
        state = "enabled" if enabled else "disabled"
        if enabled and updater.is_editable_install():
            return DoctorCheck("auto-update", True, "enabled (skipped: editable install)")
        return DoctorCheck("auto-update", True, state)

    def _check_os(self) -> DoctorCheck:
        return DoctorCheck("os", True, f"{detect_os()} ({detect_arch()}, {_platform.system()})")

    def _check_interpreters(self) -> List[DoctorCheck]:
        results: List[DoctorCheck] = []
        for name in ("python", "python3", "node"):
            path = shutil.which(name)
            results.append(DoctorCheck(name, bool(path), path or f"{name} not found"))
        return results

    def _check_alias(self) -> DoctorCheck:
        status = alias_mod.detect()
        ok = status.state in {"free", "ours"}
        return DoctorCheck("alias s", ok, status.detail)

    def _check_update_manifest(self) -> DoctorCheck:
        try:
            info = updater._fetch_manifest()
        except Exception:
            info = None
        if info is not None:
            return DoctorCheck("update manifest", True, f"reachable (latest {info.version})")
        return DoctorCheck("update manifest", False, "unreachable")

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
