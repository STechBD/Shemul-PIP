from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from shemul.app import App
from shemul.cli import _handle_init
from shemul.config import ConfigLoader, ShemulConfig
from shemul.util import global_config_path


def _temp_dir(prefix: str) -> Path:
    base = Path(".tmp_test") / f"{prefix}_{uuid.uuid4().hex}"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _mute_ui(app: App) -> None:
    app.ui.success = lambda message: None
    app.ui.info = lambda message: None
    app.ui.warn = lambda message: None
    app.ui.error = lambda message: None
    app.ui.table = lambda title, columns, rows: None
    app.ui.panel = lambda title, body: None


def test_global_config_path_uses_appdata_on_windows(monkeypatch):
    temp = _temp_dir("appdata_windows")
    try:
        monkeypatch.setattr("shemul.util.sys.platform", "win32")
        monkeypatch.setenv("APPDATA", str(temp / "Roaming"))
        assert global_config_path() == temp / "Roaming" / "Shemul" / "shemul.json"
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def test_global_config_path_uses_library_on_macos(monkeypatch):
    temp = _temp_dir("mac_home")
    try:
        monkeypatch.setattr("shemul.util.sys.platform", "darwin")
        monkeypatch.setattr("shemul.util.Path.home", lambda: temp)
        assert global_config_path() == temp / "Library" / "Application Support" / "Shemul" / "shemul.json"
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def test_global_config_path_uses_xdg_on_linux(monkeypatch):
    temp = _temp_dir("xdg_linux")
    try:
        monkeypatch.setattr("shemul.util.sys.platform", "linux")
        monkeypatch.setenv("XDG_CONFIG_HOME", str(temp / "xdg"))
        assert global_config_path() == temp / "xdg" / "shemul" / "shemul.json"
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def test_global_config_path_uses_shemul_config_home_override(monkeypatch):
    temp = _temp_dir("config_home_override")
    try:
        monkeypatch.setenv("SHEMUL_CONFIG_HOME", str(temp / "cfg"))
        assert global_config_path() == temp / "cfg" / "shemul" / "shemul.json"
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def test_global_config_path_uses_explicit_path_override(monkeypatch):
    temp = _temp_dir("explicit_global_path")
    try:
        target = temp / "custom" / "global.json"
        monkeypatch.setenv("SHEMUL_GLOBAL_CONFIG_PATH", str(target))
        assert global_config_path() == target
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def test_config_merge_prioritizes_project_commands():
    schema_path = Path("src/shemul/schema.json")
    loader = ConfigLoader(schema_path)

    global_cfg = ShemulConfig(
        raw={
            "commands": {
                "hello": {"run": "echo global"},
                "global-only": {"run": "echo global-only"},
            },
            "vars": {"NAME": "global"},
        },
        path=Path("global.json"),
    )
    project_cfg = ShemulConfig(
        raw={
            "commands": {
                "hello": {"run": "echo project"},
                "project-only": {"run": "echo project-only"},
            },
            "vars": {"NAME": "project"},
        },
        path=Path("project.json"),
    )

    merged = loader.merge(project_cfg, global_cfg)
    assert merged is not None
    assert merged.commands["hello"]["run"] == "echo project"
    assert "global-only" in merged.commands
    assert "project-only" in merged.commands
    assert merged.vars["NAME"] == "project"


def test_init_global_creates_default_and_opens_editor(monkeypatch):
    temp = _temp_dir("init_global_create")
    opened: list[Path] = []
    try:
        monkeypatch.setenv("SHEMUL_GLOBAL_CONFIG_PATH", str(temp / "global" / "shemul.json"))
        monkeypatch.setattr("shemul.cli.open_in_editor", lambda path: opened.append(path) or True)

        app = App()
        _mute_ui(app)
        _handle_init(app, temp, ["-g"])

        target = temp / "global" / "shemul.json"
        assert target.exists()
        raw = json.loads(target.read_text(encoding="utf-8"))
        assert raw["name"] == "global"
        assert "example" in raw["commands"]
        assert opened == [target]
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def test_init_global_existing_warns_and_opens(monkeypatch):
    temp = _temp_dir("init_global_existing")
    messages: list[str] = []
    opened: list[Path] = []
    try:
        target = temp / "global" / "shemul.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('{"commands":{"keep":{"run":"echo keep"}}}\n', encoding="utf-8")

        monkeypatch.setenv("SHEMUL_GLOBAL_CONFIG_PATH", str(target))
        monkeypatch.setattr("shemul.cli.open_in_editor", lambda path: opened.append(path) or True)

        app = App()
        _mute_ui(app)
        app.ui.warn = lambda message: messages.append(message)
        _handle_init(app, temp, ["-g"])

        assert "already initialized" in messages[0].lower()
        assert opened == [target]
        assert '"keep"' in target.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def test_init_project_existing_warns_and_opens(monkeypatch):
    temp = _temp_dir("init_project_existing")
    messages: list[str] = []
    opened: list[Path] = []
    try:
        target = temp / "shemul.json"
        target.write_text('{"commands":{"keep":{"run":"echo keep"}}}\n', encoding="utf-8")
        monkeypatch.setattr("shemul.cli.open_in_editor", lambda path: opened.append(path) or True)

        app = App()
        _mute_ui(app)
        app.ui.warn = lambda message: messages.append(message)
        _handle_init(app, temp, ["none"])

        assert "already initialized" in messages[0].lower()
        assert opened == [target]
        assert '"keep"' in target.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def test_app_load_state_uses_global_when_project_missing(monkeypatch):
    temp = _temp_dir("state_global_only")
    try:
        g_path = temp / "global" / "shemul.json"
        g_path.parent.mkdir(parents=True, exist_ok=True)
        g_path.write_text(
            json.dumps({"name": "global", "commands": {"hello": {"run": "echo global"}}}) + "\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("SHEMUL_GLOBAL_CONFIG_PATH", str(g_path))

        app = App()
        state = app.load_state(temp)
        assert state.context is None
        assert state.global_config is not None
        assert state.config is not None
        assert state.config.commands["hello"]["run"] == "echo global"
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def test_app_load_state_prioritizes_project_on_conflict(monkeypatch):
    temp = _temp_dir("state_project_priority")
    try:
        g_path = temp / "global" / "shemul.json"
        g_path.parent.mkdir(parents=True, exist_ok=True)
        g_path.write_text(
            json.dumps(
                {
                    "name": "global",
                    "commands": {
                        "hello": {"run": "echo global"},
                        "gonly": {"run": "echo gonly"},
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )

        project = temp / "project"
        project.mkdir(parents=True, exist_ok=True)
        (project / "shemul.json").write_text(
            json.dumps(
                {
                    "name": "project",
                    "commands": {
                        "hello": {"run": "echo project"},
                        "ponly": {"run": "echo ponly"},
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )

        monkeypatch.setenv("SHEMUL_GLOBAL_CONFIG_PATH", str(g_path))

        app = App()
        state = app.load_state(project)
        assert state.config is not None
        assert state.config.commands["hello"]["run"] == "echo project"
        assert "gonly" in state.config.commands
        assert "ponly" in state.config.commands
    finally:
        shutil.rmtree(temp, ignore_errors=True)
