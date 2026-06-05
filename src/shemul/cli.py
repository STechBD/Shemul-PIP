from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from . import alias as alias_mod
from . import interactive
from . import settings as settings_mod
from . import updater
from .app import App
from .doctor import Doctor
from .template import list_templates, resolve_template_key, template_aliases, write_template_file
from .util import global_cache_path, global_config_path, open_in_editor
from .version import VERSION_CODE, __version__


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="shemul", add_help=False)
    parser.add_argument("-v", "--v", "--version", dest="version", action="store_true", help="show version")
    parser.add_argument("--dry", action="store_true", help="print resolved command only")
    parser.add_argument("--trace", action="store_true", help="show resolved vars and env")
    parser.add_argument("-h", "--h", "--help", dest="help", action="store_true", help="show help")
    parser.add_argument("--no-update-check", dest="no_update_check", action="store_true", help="disable the update check for this run")
    parser.add_argument("command", nargs="?", help="command to run")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    return parser


def _about_box(app: App) -> None:
    body = (
        "Built by S Technologies\n"
        "Website: https://www.stechbd.net/product/Shemul-PIP\n"
        "Repository: https://github.com/STechBD/Shemul-PIP"
    )
    app.ui.panel("About", body)


def _show_about(app: App, force: bool = False) -> int:
    """Render a styled About panel with version, version code, and update status."""
    from rich.console import Group
    from rich.table import Table
    from rich.text import Text

    status, info = updater.about_status(
        cache_path=global_cache_path(),
        current_code=VERSION_CODE,
        current_version=__version__,
        force=force,
    )

    if status == "outdated" and info is not None:
        update_line = Text.assemble(
            ("Update available: ", "bold yellow"),
            (info.version, "bold white"),
            ("   run ", "yellow"),
            ("pip install -U shemul", "bold cyan"),
        )
    elif status == "current":
        update_line = Text("You are on the latest version", style="bold green")
    else:
        update_line = Text("Update status unavailable (offline)", style="dim")

    grid = Table.grid(padding=(0, 3))
    grid.add_column(justify="right", style="bold cyan", no_wrap=True)
    grid.add_column(style="white")
    grid.add_row("Version", Text.assemble((__version__, "bold white"), (f"   (code {VERSION_CODE})", "dim")))
    grid.add_row("Status", update_line)
    grid.add_row("Built by", "S Technologies (STechBD.Net)")
    grid.add_row("Website", Text("https://www.stechbd.net/product/Shemul-PIP", style="underline blue"))
    grid.add_row("Repository", Text("https://github.com/STechBD/Shemul-PIP", style="underline blue"))
    grid.add_row("PyPI", Text("https://pypi.org/project/shemul", style="underline blue"))
    grid.add_row("License", "MIT")

    header = Text.assemble(
        ("Shemul", "bold magenta"),
        ("  -  ", "dim"),
        ("Project-aware JSON task runner", "italic white"),
    )

    description = Text(
        "Shemul is an advanced project-aware CLI tool for task automation based on JSON "
        "configuration for PIP. It is a free and open-source CLI that centralizes repetitive "
        "development commands in shemul.json and runs them with safety controls, supporting both "
        "project-local and user-global command scopes.",
        style="white",
    )

    panel = box_panel(Group(header, Text(""), description, Text(""), grid))
    app.ui.console.print(panel)
    return 0


def box_panel(renderable):
    from rich import box
    from rich.panel import Panel

    return Panel(
        renderable,
        title="[bold]About Shemul[/bold]",
        subtitle="[dim]thanks for using Shemul[/dim]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 3),
    )


def _show_help(app: App, state) -> None:
    ui = app.ui
    ui.panel("Shemul", f"Shemul is an advanced project-aware CLI tool for task automation based on JSON configuration for PIP.\nVersion: {__version__}")
    _about_box(app)
    ui.info("Usage: shemul (options) <command> (args)")
    ui.info("Usage: shemul (options)  # show this help")

    option_rows = [
        ["-h, --h, --help", "Show help"],
        ["-v, --v, --version", "Show version"],
        ["--dry", "Print resolved command only"],
        ["--trace", "Show resolved vars and env"],
    ]
    ui.table("Global Options", ["option", "description"], option_rows)

    global_rows = [
        ["init [template]", "Create project shemul.json from a template (default: none)"],
        ["init -g [template]", "Create/edit global shemul.json in OS-native user config"],
        ["ls", "List configured commands (project + global)"],
        ["info", "Show detected project and active config"],
        ["help [name|group]", "Show command/group help or full help"],
        ["doctor", "Run system readiness checks"],
        ["schema", "Print built-in JSON schema"],
        ["alias [install|status|remove]", "Manage the `s` shortcut alias (same as shemul)"],
        ["update", "Check PyPI for a newer Shemul release"],
        ["settings [auto-update on|off]", "View or change Shemul settings"],
        ["about", "Show information about Shemul"],
    ]
    ui.table("Global Commands", ["command", "description"], global_rows)
    ui.info("Tip: prefix a system command with '/' (e.g. `shemul /init`) to bypass a project command of the same name.")

    if not state.config:
        ui.warn("No config found. Run `shemul init -g` to initialize global commands.")
        return

    rows = []
    for name in sorted(state.config.commands.keys()):
        cfg = state.config.commands[name]
        group = str(cfg.get("group", "core"))
        desc = str(cfg.get("desc", "")).strip() or "-"
        rows.append([name, group, desc])
    ui.table("Available Commands", ["command", "group", "description"], rows)


def _show_init_help(app: App) -> None:
    rows = []
    for item in list_templates():
        aliases = ", ".join(template_aliases(item["key"])[:2])
        rows.append([item["key"], item["desc"], aliases or "-"])
    app.ui.table("Init Templates", ["template", "description", "aliases"], rows)
    app.ui.info("Usage: shemul init [template] [--force]")
    app.ui.info("Usage: shemul init -g [template] [--force]")
    app.ui.info("Usage: shemul init --list")
    app.ui.info("Example: shemul init docker fastapi backend")
    app.ui.info("Example: shemul init -g")
    app.ui.info("Example: shemul init nextjs-frontend")


def _open_config_for_edit(app: App, target: Path) -> None:
    if open_in_editor(target):
        app.ui.info(f"Opened {target}")
    else:
        app.ui.warn(f"Could not open editor automatically. Edit this file manually: {target}")


def _handle_init(app: App, cwd: Path, args: list[str]) -> None:
    flags = {arg for arg in args if arg.startswith("-")}
    force = "--force" in flags or "-f" in flags
    list_only = "--list" in flags or "-l" in flags
    global_scope = "--global" in flags or "-g" in flags
    template_tokens = [arg for arg in args if not arg.startswith("-")]

    if list_only:
        _show_init_help(app)
        return

    target = global_config_path() if global_scope else (cwd / "shemul.json")
    if target.exists() and not force:
        scope_label = "Global" if global_scope else "Project"
        app.ui.warn(f"{scope_label} config already initialized at {target}")
        _open_config_for_edit(app, target)
        return

    if not template_tokens:
        template_key = "none"
        if interactive.interactive_enabled():
            keys = [item["key"] for item in list_templates()]
            chosen = interactive.select_one("Pick a template", keys, default="none")
            template_key = chosen or "none"
    else:
        template_input = " ".join(template_tokens).strip()
        template_key = resolve_template_key(template_input)
        if not template_key:
            app.ui.error(f"Unknown template: {template_input}")
            _show_init_help(app)
            return

    target.parent.mkdir(parents=True, exist_ok=True)
    project_name = "global" if global_scope else cwd.name
    write_template_file(template_key=template_key, target_path=target, project_name=project_name, force=force)

    scope_label = "global" if global_scope else "project"
    app.ui.success(f"Created {scope_label} config: {target}")
    app.ui.info(f"Template: {template_key}")
    app.ui.info("Next: run `shemul ls` to inspect commands.")
    _open_config_for_edit(app, target)


def _handle_update(app: App) -> int:
    info = updater.check_for_update(
        cache_path=global_cache_path(),
        current_code=VERSION_CODE,
        current_version=__version__,
        force=True,
    )
    if info is not None:
        updater.render_notice(app.ui, info)
    else:
        app.ui.success(f"Shemul is up to date ({__version__}).")
    return 0


# System (built-in) commands. Invoke explicitly with a leading slash, e.g.
# `shemul /init`, to distinguish them from project/global commands of the same name.
SYSTEM_COMMANDS = [
    "init", "ls", "info", "help", "doctor", "schema",
    "alias", "update", "settings", "version", "about",
]


def _print_version(ns) -> int:
    if "--code" in ns.args:
        print(f"{__version__} (code {VERSION_CODE})")
    else:
        print(__version__)
    return 0


def _run_system(app: App, state, ns, name: str) -> Optional[int]:
    """Run a built-in/system command by name.

    Returns the exit code, or None when `name` is not a system command.
    """
    ui = app.ui

    if name == "version":
        return _print_version(ns)

    if name == "about":
        return _show_about(app)

    if name == "init":
        _handle_init(app, Path.cwd(), ns.args)
        return 0

    if name == "update":
        return _handle_update(app)

    if name == "alias":
        action = ns.args[0] if ns.args else "status"
        return alias_mod.handle(app.ui, action)

    if name == "settings":
        return settings_mod.handle(app.ui, ns.args)

    if name == "doctor":
        checks = Doctor().run()
        rows = []
        for check in checks:
            status = "ok" if check.ok else "fail"
            rows.append([status, check.name, check.detail])
        ui.table("Doctor", ["status", "check", "detail"], rows)
        return 0

    if name == "schema":
        print(app.schema_path.read_text(encoding="utf-8"))
        return 0

    if name == "_complete":
        words = [w for w in ns.args if not w.startswith("-")]
        if not state.config:
            for item in app.completion(None, words):
                print(item)
            return 0
        for item in app.completion(state.config, words):
            print(item)
        return 0

    if name == "info":
        lines = []
        if state.context:
            lines.append(f"project root: {state.context.root}")
            lines.append(f"project config: {state.context.config_path}")
            lines.append(f"project type: {state.context.project_type}")
        else:
            lines.append("project config: (none)")

        if state.global_config:
            lines.append(f"global config: {state.global_config.path}")
        else:
            lines.append("global config: (none)")

        active = []
        if state.project_config:
            active.append("project")
        if state.global_config:
            active.append("global")
        lines.append(f"active scope: {' + '.join(active) if active else '(none)'}")
        ui.panel("Info", "\n".join(lines))
        _about_box(app)
        return 0

    if name == "ls":
        if not state.config:
            _show_help(app, state)
            return 0
        grouped = app.list_commands(state.config)
        rows = []
        for group, names in grouped.items():
            for cname in names:
                rows.append([group, cname])
        ui.table("Commands", ["group", "command"], rows)
        return 0

    if name == "help":
        if not ns.args:
            _show_help(app, state)
            return 0
        target = ns.args[0]
        if not (state.config and app.help_for(state.config, target)):
            ui.error(f"Unknown command or group: {target}")
            return 1
        return 0

    return None


def _dispatch(app: App, state, ns) -> int:
    ui = app.ui

    if ns.version:
        return _print_version(ns)

    if ns.help:
        _show_help(app, state)
        return 0

    if not ns.command:
        _show_help(app, state)
        return 0

    raw = ns.command

    # `shemul /init` etc. always runs the system command, never a user command.
    if raw.startswith("/"):
        code = _run_system(app, state, ns, raw[1:])
        if code is None:
            ui.error(f"Unknown system command: {raw}")
            ui.info("Available: " + ", ".join(f"/{c}" for c in SYSTEM_COMMANDS))
            return 1
        return code

    # Internal completion hook (used by shell completion scripts).
    if raw == "_complete":
        return _run_system(app, state, ns, "_complete") or 0

    # Bare name: a project/global command of the same name takes precedence,
    # so users can shadow built-ins (and reach the built-in via `/name`).
    if state.config and raw in state.config.commands:
        return app.run_command(state.config, raw, dry=ns.dry, trace=ns.trace, extra_args=ns.args)

    code = _run_system(app, state, ns, raw)
    if code is not None:
        return code

    # Neither a user command nor a system command.
    if not state.config:
        ui.error("No shemul config found. Run `shemul init -g` to create a global config.")
        return 1

    suggestions = app.suggest(state.config, raw)
    if suggestions and interactive.interactive_enabled():
        chosen = interactive.select_one(
            f"Unknown command '{raw}'. Did you mean?",
            [*suggestions, "(cancel)"],
            default=suggestions[0],
        )
        if chosen and chosen != "(cancel)":
            return app.run_command(state.config, chosen, dry=ns.dry, trace=ns.trace, extra_args=ns.args)
        return 1
    ui.error(f"Unknown command: {raw}")
    if suggestions:
        ui.info("Did you mean?")
        for item in suggestions:
            ui.info(f"  {item}")
    if not state.global_config:
        ui.info("Tip: initialize global commands with `shemul init -g`.")
    return 1


def main() -> None:
    parser = _build_parser()
    ns = parser.parse_args()

    app = App()
    state = app.load_state(Path.cwd())

    config_raw = state.config.raw if state.config else None
    cmd_name = ns.command[1:] if (ns.command and ns.command.startswith("/")) else ns.command
    skip_check = ns.version or cmd_name in {"_complete", "update", "version", "settings", "about"}
    enabled = updater.update_check_enabled(config_raw, ns.no_update_check) and not skip_check
    result_box: list = []
    thread = updater.spawn_background_check(
        cache_path=global_cache_path(),
        current_code=VERSION_CODE,
        current_version=__version__,
        result_box=result_box,
        enabled=enabled,
    )

    code = _dispatch(app, state, ns)

    if thread is not None:
        thread.join(timeout=0.1)
    if result_box and result_box[0] is not None:
        info = result_box[0]
        cache_path = global_cache_path()
        if settings_mod.get("auto_update") and not updater.auto_update_already_attempted(cache_path, info.version):
            if updater.spawn_auto_update():
                updater.mark_auto_update(cache_path, info.version)
                updater.render_auto_update_notice(app.ui, info)
            else:
                updater.render_notice(app.ui, info)
        else:
            updater.render_notice(app.ui, info)

    sys.exit(code)


if __name__ == "__main__":
    main()
