from __future__ import annotations

from shemul.command import Command


def _resolve(cfg, vars_map=None, bin_map=None, current_os="linux", runtime=""):
    return Command(
        "c", cfg, vars_map or {}, {}, bin_map=bin_map or {}, current_os=current_os, runtime=runtime
    ).resolve()


def test_os_override_selects_current_os():
    cfg = {"run": "base", "os": {"windows": "winc", "linux": "linc"}}
    assert _resolve(cfg, current_os="windows").command == "winc"
    assert _resolve(cfg, current_os="linux").command == "linc"


def test_os_override_normalizes_keys():
    cfg = {"run": "base", "os": {"win": "winc", "mac": "macc"}}
    assert _resolve(cfg, current_os="windows").command == "winc"
    assert _resolve(cfg, current_os="macos").command == "macc"


def test_os_default_fallback():
    cfg = {"run": "base", "os": {"default": "defc"}}
    assert _resolve(cfg, current_os="macos").command == "defc"


def test_absent_os_uses_run_unchanged():
    # Regression: a 1.0.1-style command with no os map behaves identically.
    cfg = {"run": "echo hello"}
    assert _resolve(cfg, current_os="windows").command == "echo hello"


def test_magic_var_os_and_sep():
    assert _resolve({"run": "echo {{os}}"}, current_os="linux").command == "echo linux"
    assert _resolve({"run": "a{{sep}}b"}, current_os="windows").command == "a\\b"


def test_bin_expansion_per_os():
    cfg = {"run": "{{bin.py}} app.py"}
    bin_map = {"py": {"windows": "python", "default": "python3"}}
    assert _resolve(cfg, bin_map=bin_map, current_os="windows").command == "python app.py"
    assert _resolve(cfg, bin_map=bin_map, current_os="linux").command == "python3 app.py"


def test_bin_bare_token_form():
    # The docs headline example uses the bare {{py}} form too.
    cfg = {"run": "{{py}} app.py"}
    bin_map = {"py": {"windows": "python", "default": "python3"}}
    assert _resolve(cfg, bin_map=bin_map, current_os="windows").command == "python app.py"
    assert _resolve(cfg, bin_map=bin_map, current_os="linux").command == "python3 app.py"


def test_user_var_overrides_magic():
    # vars expand before magic, so a user-defined {{os}} wins.
    assert _resolve({"run": "{{os}}"}, vars_map={"os": "custom"}, current_os="linux").command == "custom"


def test_shell_and_exec_fields():
    r = _resolve({"run": "x", "shell": False, "exec": ["echo", "hi"]})
    assert r.shell is False
    assert r.exec_argv == ["echo", "hi"]
    default = _resolve({"run": "x"})
    assert default.shell is True
    assert default.exec_argv is None


def test_runtime_sets_default_shell():
    # A top-level runtime naming a shell becomes the command's default shell.
    assert _resolve({"run": "x"}, runtime="bash").shell == "bash"
    # An explicit per-command shell wins over runtime.
    assert _resolve({"run": "x", "shell": False}, runtime="bash").shell is False
    # A descriptive runtime (docker/python/node) is ignored for execution.
    assert _resolve({"run": "x"}, runtime="docker").shell is True
