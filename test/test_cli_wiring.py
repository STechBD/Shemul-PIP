from __future__ import annotations

from pathlib import Path

from shemul.app import App, AppState
from shemul.cli import _build_parser, _dispatch
from shemul.config import ShemulConfig


def _state_with_commands(commands):
    config = ShemulConfig(raw={"commands": commands}, path=Path("x"))
    return AppState(context=None, project_config=config, global_config=None, config=config)


def _mute(app):
    app.ui.success = lambda m: None
    app.ui.error = lambda m: None
    app.ui.info = lambda m: None
    app.ui.warn = lambda m: None
    app.ui.panel = lambda title, body: None
    app.ui.table = lambda title, columns, rows: None


def test_version_code(capsys):
    app = App()
    state = app.load_state(Path.cwd())
    ns = _build_parser().parse_args(["version", "--code"])
    code = _dispatch(app, state, ns)
    out = capsys.readouterr().out
    assert code == 0
    assert "2.0.0" in out and "code 3" in out


def test_version_plain(capsys):
    app = App()
    state = app.load_state(Path.cwd())
    ns = _build_parser().parse_args(["version"])
    _dispatch(app, state, ns)
    out = capsys.readouterr().out.strip()
    assert out == "2.0.0"


def test_completion_includes_new_subcommands():
    app = App()
    config = ShemulConfig(raw={"commands": {"c": {"run": "x"}}}, path=Path("x"))
    candidates = app.completion(config, [])
    assert "alias" in candidates
    assert "update" in candidates


def test_update_subcommand_forces_check(monkeypatch):
    app = App()
    _mute(app)
    seen = {}
    monkeypatch.setattr("shemul.cli.updater.check_for_update", lambda **k: seen.update(k) or None)

    state = app.load_state(Path.cwd())
    ns = _build_parser().parse_args(["update"])
    code = _dispatch(app, state, ns)

    assert code == 0
    assert seen.get("force") is True


def test_alias_subcommand_routes(monkeypatch):
    app = App()
    _mute(app)
    seen = {}
    monkeypatch.setattr("shemul.cli.alias_mod.handle", lambda ui, action: seen.update({"action": action}) or 0)

    state = app.load_state(Path.cwd())
    ns = _build_parser().parse_args(["alias", "install"])
    code = _dispatch(app, state, ns)

    assert code == 0
    assert seen["action"] == "install"


def test_settings_subcommand_routes(monkeypatch):
    app = App()
    _mute(app)
    seen = {}
    monkeypatch.setattr("shemul.cli.settings_mod.handle", lambda ui, args: seen.update({"args": args}) or 0)

    state = app.load_state(Path.cwd())
    ns = _build_parser().parse_args(["settings", "auto-update", "on"])
    code = _dispatch(app, state, ns)

    assert code == 0
    assert seen["args"] == ["auto-update", "on"]


def test_completion_includes_settings():
    app = App()
    config = ShemulConfig(raw={"commands": {"c": {"run": "x"}}}, path=Path("x"))
    assert "settings" in app.completion(config, [])


def test_completion_includes_slash_forms():
    app = App()
    config = ShemulConfig(raw={"commands": {"c": {"run": "x"}}}, path=Path("x"))
    cands = app.completion(config, [])
    assert "/init" in cands and "/settings" in cands


def test_slash_forces_system_command(capsys):
    app = App()
    state = app.load_state(Path.cwd())
    ns = _build_parser().parse_args(["/version", "--code"])
    code = _dispatch(app, state, ns)
    out = capsys.readouterr().out
    assert code == 0 and "code 3" in out


def test_bare_name_prefers_user_command(monkeypatch):
    app = App()
    _mute(app)
    state = _state_with_commands({"doctor": {"run": "echo mine"}})
    calls = []
    monkeypatch.setattr(app, "run_command", lambda cfg, name, **k: calls.append(name) or 0)

    ns = _build_parser().parse_args(["doctor"])
    code = _dispatch(app, state, ns)

    assert code == 0
    assert calls == ["doctor"]  # the user command ran, not the system doctor


def test_slash_runs_system_even_when_user_shadows(monkeypatch):
    app = App()
    _mute(app)
    state = _state_with_commands({"version": {"run": "echo mine"}})
    ran = []
    monkeypatch.setattr(app, "run_command", lambda *a, **k: ran.append(1) or 0)

    ns = _build_parser().parse_args(["/version"])
    code = _dispatch(app, state, ns)

    assert code == 0
    assert ran == []  # system version printed; the user command was NOT run


def test_unknown_slash_command_errors():
    app = App()
    _mute(app)
    state = app.load_state(Path.cwd())
    ns = _build_parser().parse_args(["/bogus"])
    assert _dispatch(app, state, ns) == 1


def test_about_command_renders(monkeypatch):
    from shemul.updater import UpdateInfo

    app = App()
    state = app.load_state(Path.cwd())
    # No network: force the "outdated" branch so the update line renders.
    monkeypatch.setattr(
        "shemul.cli.updater.about_status",
        lambda **k: ("outdated", UpdateInfo("9.9.9", 99, 1, "https://pypi.org/project/shemul", "")),
    )
    ns = _build_parser().parse_args(["/about"])
    assert _dispatch(app, state, ns) == 0
