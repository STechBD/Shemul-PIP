from __future__ import annotations

import importlib.metadata as importlib_metadata
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from .util import is_truthy

MANIFEST_URL = "https://www.stechbd.net/product/Shemul-PIP/latest.json"
PYPI_URL = "https://pypi.org/pypi/shemul/json"
THROTTLE_SECONDS = 24 * 3600
HTTP_TIMEOUT = 1.5


@dataclass
class UpdateInfo:
    version: str
    version_code: Optional[int]
    min_supported_code: Optional[int]
    url: str
    notes: str


def update_check_enabled(config_raw: Optional[dict], no_update_flag: bool) -> bool:
    import os

    if no_update_flag:
        return False
    if is_truthy(os.environ.get("SHEMUL_NO_UPDATE_CHECK", "")):
        return False
    if config_raw is not None and config_raw.get("update_check") is False:
        return False
    return True


def _http_get_json(url: str, timeout: float) -> Optional[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "shemul-update-check"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (https only)
        return json.loads(resp.read().decode("utf-8"))


def _fetch_manifest(timeout: float = HTTP_TIMEOUT) -> Optional[UpdateInfo]:
    # Primary: Shemul manifest (carries the version code).
    try:
        data = _http_get_json(MANIFEST_URL, timeout)
        if data and data.get("version"):
            code = data.get("version_code")
            return UpdateInfo(
                version=str(data["version"]),
                version_code=int(code) if code is not None else None,
                min_supported_code=(
                    int(data["min_supported_code"]) if data.get("min_supported_code") is not None else None
                ),
                url=str(data.get("url", PYPI_URL)),
                notes=str(data.get("notes", "")),
            )
    except Exception:
        pass

    # Fallback: PyPI JSON API (no version code available).
    try:
        data = _http_get_json(PYPI_URL, timeout)
        version = (data or {}).get("info", {}).get("version")
        if version:
            return UpdateInfo(
                version=str(version),
                version_code=None,
                min_supported_code=None,
                url="https://pypi.org/project/shemul/",
                notes="",
            )
    except Exception:
        pass

    return None


def _read_cache(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_cache(path: Path, data: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
    except Exception:
        pass


def _is_throttled(cache: dict, now: float) -> bool:
    checked_at = cache.get("checked_at")
    if not isinstance(checked_at, (int, float)):
        return False
    return (now - checked_at) < THROTTLE_SECONDS


def _semver_tuple(version: str) -> tuple:
    parts = []
    for chunk in str(version).split("."):
        digits = ""
        for ch in chunk:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def _is_newer(info: UpdateInfo, current_code: int, current_version: str) -> bool:
    if info.version_code is not None and current_code is not None:
        return info.version_code > current_code
    return _semver_tuple(info.version) > _semver_tuple(current_version)


def _info_from_cache(cache: dict) -> Optional[UpdateInfo]:
    latest = cache.get("latest")
    if not isinstance(latest, dict) or not latest.get("version"):
        return None
    return UpdateInfo(
        version=str(latest["version"]),
        version_code=latest.get("version_code"),
        min_supported_code=latest.get("min_supported_code"),
        url=str(latest.get("url", PYPI_URL)),
        notes=str(latest.get("notes", "")),
    )


def latest_release(
    *,
    cache_path: Path,
    force: bool = False,
    fetcher: Callable[..., Optional[UpdateInfo]] = _fetch_manifest,
    now: Optional[float] = None,
) -> Optional[UpdateInfo]:
    """Return the latest known release (regardless of whether it is newer).

    Uses the cache when throttled (and not forced) so there is no network call.
    Never raises.
    """
    try:
        now = time.time() if now is None else now
        cache = _read_cache(cache_path)

        if not force and _is_throttled(cache, now):
            return _info_from_cache(cache)

        info = fetcher()
        if info is not None:
            _write_cache(
                cache_path,
                {
                    "checked_at": now,
                    "latest": {
                        "version": info.version,
                        "version_code": info.version_code,
                        "min_supported_code": info.min_supported_code,
                        "url": info.url,
                        "notes": info.notes,
                    },
                },
            )
            return info

        # Stamp the attempt so we honour the throttle window, then use cache.
        cache["checked_at"] = now
        _write_cache(cache_path, cache)
        return _info_from_cache(cache)
    except Exception:
        return None


def check_for_update(
    *,
    cache_path: Path,
    current_code: int,
    current_version: str,
    force: bool = False,
    fetcher: Callable[..., Optional[UpdateInfo]] = _fetch_manifest,
    now: Optional[float] = None,
) -> Optional[UpdateInfo]:
    """Return UpdateInfo when a newer release is available, else None.

    Never raises, never blocks beyond the fetcher's own timeout. When throttled
    (and not forced) it reports from cache without any network call.
    """
    try:
        info = latest_release(cache_path=cache_path, force=force, fetcher=fetcher, now=now)
        if info is None:
            return None
        return info if _is_newer(info, current_code, current_version) else None
    except Exception:
        return None


def about_status(
    *,
    cache_path: Path,
    current_code: int,
    current_version: str,
    force: bool = False,
    fetcher: Callable[..., Optional[UpdateInfo]] = _fetch_manifest,
    now: Optional[float] = None,
) -> "tuple[str, Optional[UpdateInfo]]":
    """Return an update status for the about screen.

    Status is one of: "current" (up to date), "outdated" (newer available),
    or "unknown" (could not determine, e.g. offline). Never raises.
    """
    info = latest_release(cache_path=cache_path, force=force, fetcher=fetcher, now=now)
    if info is None:
        return ("unknown", None)
    if _is_newer(info, current_code, current_version):
        return ("outdated", info)
    return ("current", info)


def spawn_background_check(
    *,
    cache_path: Path,
    current_code: int,
    current_version: str,
    result_box: List[Optional[UpdateInfo]],
    enabled: bool,
) -> Optional[threading.Thread]:
    if not enabled:
        return None

    def _worker() -> None:
        result_box.append(
            check_for_update(
                cache_path=cache_path,
                current_code=current_code,
                current_version=current_version,
                force=False,
            )
        )

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread


def is_editable_install() -> bool:
    """True when Shemul is installed in editable/development mode.

    Auto-update must never clobber a developer's editable checkout with a PyPI
    release, so it is skipped in that case.
    """
    try:
        dist = importlib_metadata.distribution("shemul")
        text = dist.read_text("direct_url.json")
        if not text:
            return False
        data = json.loads(text)
        return bool(data.get("dir_info", {}).get("editable"))
    except Exception:
        return False


def auto_update_already_attempted(cache_path: Path, version: str) -> bool:
    return _read_cache(cache_path).get("auto_update_version") == version


def mark_auto_update(cache_path: Path, version: str) -> None:
    cache = _read_cache(cache_path)
    cache["auto_update_version"] = version
    _write_cache(cache_path, cache)


def spawn_auto_update(
    *,
    runner: Optional[Callable[[List[str]], Optional[object]]] = None,
) -> bool:
    """Launch a detached `pip install -U shemul` in the background.

    Never blocks and never raises. Returns True when the process was launched.
    The new version takes effect on the next invocation of Shemul.
    """
    if is_editable_install():
        return False
    cmd = [sys.executable, "-m", "pip", "install", "-U", "shemul"]
    try:
        if runner is not None:
            runner(cmd)
            return True
        kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        if os.name == "nt":
            kwargs["creationflags"] = (
                getattr(subprocess, "DETACHED_PROCESS", 0)
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            )
        else:
            kwargs["start_new_session"] = True
        subprocess.Popen(cmd, **kwargs)
        return True
    except Exception:
        return False


def render_auto_update_notice(ui, info: UpdateInfo) -> None:
    ui.info(f"Shemul {info.version} available - updating in the background (pip install -U shemul).")
    ui.info("The new version takes effect on your next command.")


def render_notice(ui, info: UpdateInfo) -> None:
    lines = [f"Shemul {info.version} is available."]
    if info.notes:
        lines.append(info.notes)
    lines.append("Update:  pip install -U shemul")
    lines.append(f"Details: {info.url}")
    ui.panel("Update available", "\n".join(lines))
