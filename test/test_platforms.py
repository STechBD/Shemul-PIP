from __future__ import annotations

from shemul.platforms import (
    detect_os,
    magic_vars,
    normalize_os_key,
    resolve_interpreter,
)


def test_detect_os_windows(monkeypatch):
    monkeypatch.setattr("shemul.platforms.sys.platform", "win32")
    assert detect_os() == "windows"


def test_detect_os_macos(monkeypatch):
    monkeypatch.setattr("shemul.platforms.sys.platform", "darwin")
    assert detect_os() == "macos"


def test_detect_os_linux(monkeypatch):
    monkeypatch.setattr("shemul.platforms.sys.platform", "linux")
    assert detect_os() == "linux"


def test_resolve_interpreter_prefers_python(monkeypatch):
    monkeypatch.setattr("shemul.platforms.shutil.which", lambda name: "/usr/bin/python" if name == "python" else None)
    assert resolve_interpreter() == "python"


def test_resolve_interpreter_falls_back_to_python3(monkeypatch):
    monkeypatch.setattr("shemul.platforms.shutil.which", lambda name: "/usr/bin/python3" if name == "python3" else None)
    assert resolve_interpreter() == "python3"


def test_resolve_interpreter_default_when_none(monkeypatch):
    monkeypatch.setattr("shemul.platforms.shutil.which", lambda name: None)
    assert resolve_interpreter() == "python3"


def test_magic_vars_windows():
    mv = magic_vars("windows")
    assert mv["os"] == "windows"
    assert mv["shell"] == "powershell"
    assert mv["sep"] == "\\"
    assert "python" in mv and "arch" in mv and "home" in mv


def test_magic_vars_linux():
    mv = magic_vars("linux")
    assert mv["os"] == "linux"
    assert mv["shell"] == "sh"
    assert mv["sep"] == "/"


def test_normalize_os_key():
    assert normalize_os_key("win") == "windows"
    assert normalize_os_key("Windows") == "windows"
    assert normalize_os_key("darwin") == "macos"
    assert normalize_os_key("mac") == "macos"
    assert normalize_os_key("linux") == "linux"
    assert normalize_os_key("freebsd") == "freebsd"
