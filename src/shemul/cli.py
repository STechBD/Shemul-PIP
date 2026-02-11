from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .app import App
from .doctor import Doctor
from .template import list_templates, resolve_template_key, template_aliases, write_template_file
from .util import global_config_path, open_in_editor
from .version import __version__


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="shemul", add_help=False)
    parser.add_argument("-v", "--v", "--version", dest="version", action="store_true", help="show version")
    parser.add_argument("--dry", action="store_true", help="print resolved command only")
    parser.add_argument("--trace", action="store_true", help="show resolved vars and env")
    parser.add_argument("-h", "--h", "--help", dest="help", action="store_true", help="show help")
    parser.add_argument("command", nargs="?", help="command to run")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    return parser


def _show_help(app: App, state) -> None:
    ui = app.ui
    ui.panel("Shemul", f"Shemul is an advanced, project-aware task runner.\nVersion: {__version__}")
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
        ["init <template>", "Create project shemul.json from a template"],
        ["init -g [template]", "Create/edit global shemul.json in OS-native user config"],
        ["ls", "List configured commands (project + global)"],
        ["info", "Show detected project and active config"],
        ["help [name|group]", "Show command/group help or full help"],
        ["doctor", "Run system readiness checks"],
        ["schema", "Print built-in JSON schema"],
    ]
    ui.table("Global Commands", ["command", "description"], global_rows)

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
    app.ui.info("Usage: shemul init <template> [--force]")
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
        if global_scope:
            template_key = "none"
        else:
            _show_init_help(app)
            return
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


def main() -> None:
    parser = _build_parser()
    ns = parser.parse_args()

    app = App()
    ui = app.ui
    state = app.load_state(Path.cwd())

    if ns.version:
        print(__version__)
        return

    if ns.help:
        _show_help(app, state)
        return

    if not ns.command:
        _show_help(app, state)
        return

    if ns.command == "init":
        _handle_init(app, Path.cwd(), ns.args)
        return

    if ns.command == "doctor":
        checks = Doctor().run()
        rows = []
        for check in checks:
            status = "ok" if check.ok else "fail"
            rows.append([status, check.name, check.detail])
        ui.table("Doctor", ["status", "check", "detail"], rows)
        return

    if ns.command == "schema":
        print(app.schema_path.read_text(encoding="utf-8"))
        return

    if ns.command == "_complete":
        words = [w for w in ns.args if not w.startswith("-")]
        if not state.config:
            for item in ["init", "ls", "info", "help", "doctor", "schema", "_complete"]:
                print(item)
            return
        for item in app.completion(state.config, words):
            print(item)
        return

    if not state.config:
        if ns.command in {"info", "ls", "help"}:
            _show_help(app, state)
            return
        ui.error("No shemul config found. Run `shemul init -g` to create a global config.")
        return

    if ns.command == "info":
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
        return

    if ns.command == "ls":
        grouped = app.list_commands(state.config)
        rows = []
        for group, names in grouped.items():
            for name in names:
                rows.append([group, name])
        ui.table("Commands", ["group", "command"], rows)
        return

    if ns.command == "help":
        if not ns.args:
            _show_help(app, state)
            return
        target = ns.args[0]
        if not app.help_for(state.config, target):
            ui.error(f"Unknown command or group: {target}")
        return

    if ns.command not in state.config.commands:
        ui.error(f"Unknown command: {ns.command}")
        suggestions = app.suggest(state.config, ns.command)
        if suggestions:
            ui.info("Did you mean?")
            for item in suggestions:
                ui.info(f"  {item}")
        if not state.global_config:
            ui.info("Tip: initialize global commands with `shemul init -g`.")
        return

    sys.exit(app.run_command(state.config, ns.command, dry=ns.dry, trace=ns.trace, extra_args=ns.args))


if __name__ == "__main__":
    main()
