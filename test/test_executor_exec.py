from __future__ import annotations

from shemul.executor import Executor


class _FakeCompleted:
    def __init__(self, code=0):
        self.returncode = code


def _patch_run(monkeypatch):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return _FakeCompleted(0)

    monkeypatch.setattr("shemul.executor.subprocess.run", fake_run)
    return calls


def test_default_path_uses_shell_true(monkeypatch):
    calls = _patch_run(monkeypatch)
    result = Executor().run("echo hi")
    cmd, kwargs = calls[-1]
    assert cmd == "echo hi"
    assert kwargs["shell"] is True
    assert result.return_code == 0


def test_exec_argv_uses_shell_false(monkeypatch):
    calls = _patch_run(monkeypatch)
    result = Executor().run("ignored", exec_argv=["echo", "hi"])
    cmd, kwargs = calls[-1]
    assert cmd == ["echo", "hi"]
    assert kwargs["shell"] is False
    assert result.command == "echo hi"
    assert result.return_code == 0


def test_shell_false_uses_shell_false(monkeypatch):
    calls = _patch_run(monkeypatch)
    Executor().run("echo hi", shell=False)
    cmd, kwargs = calls[-1]
    assert cmd == "echo hi"
    assert kwargs["shell"] is False


def test_dry_does_not_execute(monkeypatch):
    calls = _patch_run(monkeypatch)
    result = Executor().run("echo hi", dry=True)
    assert calls == []
    assert result.return_code == 0


def test_pick_shell():
    ex = Executor()
    assert ex.pick_shell("windows") == "powershell"
    assert ex.pick_shell("linux") == "/bin/sh"
