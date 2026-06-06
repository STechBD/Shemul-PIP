from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from shemul import updater
from shemul.updater import UpdateInfo, check_for_update, update_check_enabled


def _tmp_cache() -> Path:
    base = Path(tempfile.mkdtemp(prefix=f"updater_{uuid.uuid4().hex}_"))
    return base / "update-cache.json"


def _info(version="1.2.0", code=4):
    return UpdateInfo(version=version, version_code=code, min_supported_code=1, url="u", notes="n")


def test_update_check_enabled_default(monkeypatch):
    monkeypatch.delenv("SHEMUL_NO_UPDATE_CHECK", raising=False)
    assert update_check_enabled(None, False) is True


def test_update_check_disabled_by_flag():
    assert update_check_enabled(None, True) is False


def test_update_check_disabled_by_env(monkeypatch):
    monkeypatch.setenv("SHEMUL_NO_UPDATE_CHECK", "1")
    assert update_check_enabled(None, False) is False


def test_update_check_disabled_by_config():
    assert update_check_enabled({"update_check": False}, False) is False


def test_newer_by_version_code():
    cache = _tmp_cache()
    out = check_for_update(
        cache_path=cache, current_code=3, current_version="1.1.0", force=True,
        fetcher=lambda: _info(code=4), now=1000.0,
    )
    assert out is not None and out.version == "1.2.0"


def test_not_newer_same_code():
    cache = _tmp_cache()
    out = check_for_update(
        cache_path=cache, current_code=4, current_version="1.2.0", force=True,
        fetcher=lambda: _info(code=4), now=1000.0,
    )
    assert out is None


def test_semver_fallback_when_no_code():
    cache = _tmp_cache()
    out = check_for_update(
        cache_path=cache, current_code=3, current_version="1.1.0", force=True,
        fetcher=lambda: UpdateInfo("1.2.0", None, None, "u", ""), now=1000.0,
    )
    assert out is not None


def test_throttle_uses_cache_without_fetch():
    cache = _tmp_cache()
    # First call writes cache at t=1000.
    check_for_update(
        cache_path=cache, current_code=3, current_version="1.1.0", force=True,
        fetcher=lambda: _info(code=4), now=1000.0,
    )

    called = []

    def boom():
        called.append(True)
        raise AssertionError("fetcher should not be called when throttled")

    out = check_for_update(
        cache_path=cache, current_code=3, current_version="1.1.0", force=False,
        fetcher=boom, now=1000.0 + 60,  # within 24h window
    )
    assert called == []
    assert out is not None and out.version == "1.2.0"


def test_force_bypasses_throttle():
    cache = _tmp_cache()
    check_for_update(
        cache_path=cache, current_code=3, current_version="1.1.0", force=True,
        fetcher=lambda: _info(version="1.2.0", code=4), now=1000.0,
    )
    out = check_for_update(
        cache_path=cache, current_code=3, current_version="1.1.0", force=True,
        fetcher=lambda: _info(version="1.3.0", code=5), now=1000.0 + 60,
    )
    assert out is not None and out.version == "1.3.0"


def test_fetcher_none_returns_none():
    cache = _tmp_cache()
    out = check_for_update(
        cache_path=cache, current_code=3, current_version="1.1.0", force=True,
        fetcher=lambda: None, now=1000.0,
    )
    assert out is None


def test_fetcher_raising_never_raises():
    cache = _tmp_cache()

    def boom():
        raise RuntimeError("network down")

    # Whole call is guarded; must return None, not raise.
    out = check_for_update(
        cache_path=cache, current_code=3, current_version="1.1.0", force=True,
        fetcher=boom, now=1000.0,
    )
    assert out is None


def test_global_cache_path_override(monkeypatch):
    target = _tmp_cache()
    monkeypatch.setenv("SHEMUL_GLOBAL_CACHE_PATH", str(target))
    from shemul.util import global_cache_path

    assert global_cache_path() == target


def test_spawn_auto_update_skips_editable(monkeypatch):
    monkeypatch.setattr("shemul.updater.is_editable_install", lambda: True)
    called = []
    assert updater.spawn_auto_update(runner=lambda cmd: called.append(cmd)) is False
    assert called == []


def test_spawn_auto_update_runs_when_installed(monkeypatch):
    import sys

    monkeypatch.setattr("shemul.updater.is_editable_install", lambda: False)
    called = []
    assert updater.spawn_auto_update(runner=lambda cmd: called.append(cmd)) is True
    assert called and called[0][:5] == [sys.executable, "-m", "pip", "install", "-U"]


def test_auto_update_marker_roundtrip():
    cache = _tmp_cache()
    assert updater.auto_update_already_attempted(cache, "1.2.0") is False
    updater.mark_auto_update(cache, "1.2.0")
    assert updater.auto_update_already_attempted(cache, "1.2.0") is True
    assert updater.auto_update_already_attempted(cache, "1.3.0") is False


def test_latest_release_returns_latest_regardless_of_newer():
    cache = _tmp_cache()
    out = updater.latest_release(cache_path=cache, force=True, fetcher=lambda: _info("1.5.0", 9), now=1000.0)
    assert out is not None and out.version == "1.5.0"


def test_about_status_outdated():
    cache = _tmp_cache()
    status, info = updater.about_status(
        cache_path=cache, current_code=3, current_version="1.1.0", force=True,
        fetcher=lambda: _info("1.2.0", 4), now=1000.0,
    )
    assert status == "outdated" and info.version == "1.2.0"


def test_about_status_current():
    cache = _tmp_cache()
    status, _ = updater.about_status(
        cache_path=cache, current_code=4, current_version="1.2.0", force=True,
        fetcher=lambda: _info("1.2.0", 4), now=1000.0,
    )
    assert status == "current"


def test_about_status_unknown_when_offline():
    cache = _tmp_cache()
    status, info = updater.about_status(
        cache_path=cache, current_code=3, current_version="1.1.0", force=True,
        fetcher=lambda: None, now=1000.0,
    )
    assert status == "unknown" and info is None
