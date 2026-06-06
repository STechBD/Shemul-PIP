# Architecture

## Goals

- Project-aware CLI with safe-by-default execution.
- Global-scope command support across directories.
- Clear separation of configuration, context discovery, and execution.
- Deterministic precedence: project commands override global conflicts.

## Design Overview

### App Flow

1. Discover project context by walking upward for `shemul.json`.
2. Resolve OS-native global config path:
   - Windows: `%APPDATA%\\Shemul\\shemul.json`
   - macOS: `~/Library/Application Support/Shemul/shemul.json`
   - Linux: `$XDG_CONFIG_HOME/shemul/shemul.json` (fallback: `~/.config/shemul/shemul.json`)
3. Load and validate available config files with bundled JSON Schema.
4. Merge project + global config into effective runtime config.
5. (2.0.0) Start a non-blocking background update check (best-effort, daemon thread).
6. Select the command base string by OS: `os[current]` → `os["default"]` → `run`.
7. Resolve command templates: `vars` + `env`, then magic variables, then `bin` interpreter maps.
8. (2.0.0) If the command declares `needs`/`pre`/`post`/`parallel`, run it through the planner;
   otherwise run it directly.
9. Apply safety guards (`confirm`, `danger`).
10. (2.0.0) If the command names a plugin `runner`, dispatch to it; otherwise execute via the
    shell/exec runner.
11. (2.0.0) After the command returns, print the update notice if a newer release is available.

### Module Map

| Module | Responsibility |
|---|---|
| `cli.py` | Argument parsing, dispatch, update-check orchestration, new subcommands |
| `app.py` | Orchestration, state load, resolve, planner gate, plugin dispatch |
| `command.py` | Command resolution: `os` selection, templating, magic vars, `bin`, `runtime` shell |
| `executor.py` | Shell execution (default) and opt-in arg-vector / named-shell execution |
| `config.py` | Load + JSON Schema validation + project/global merge |
| `context.py` | Project discovery by walking upward for `shemul.json` |
| `platforms.py` | OS/arch detection, magic-var table, interpreter probing, recognized shells |
| `planner.py` | Dependency graph: `needs`/`pre`/`post`/`parallel`, cycle detection |
| `plugins.py` | `shemul.plugins` entry-point discovery and runner/resolver registry |
| `updater.py` | PyPI/manifest check, 24h cache, throttle, version-code comparison, background auto-update |
| `alias.py` | `s` shim install/status/remove with conflict detection |
| `settings.py` | User preferences store (`settings.json`) and the `shemul settings` command |
| `interactive.py` | Arrow-key prompts (confirm, select, checkbox) with non-TTY fallbacks |
| `doctor.py` | Readiness checks: OS, interpreters, alias, docker, update reachability |
| `template.py` | Built-in `init` templates |
| `ui.py`, `guard.py`, `util.py`, `autocomplete.py` | Output, prompts, paths, completion |
| `version.py` | `__version__`, `VERSION_CODE`, `version_info` |

### Cross-OS Resolution (2.0.0)

A command can carry an `os` map (`windows`/`macos`/`linux`/`default`); the matching key wins,
falling back to the base `run`. Top-level `bin` maps define named interpreters per OS, referenced
as `{{name}}` or `{{bin.name}}`. Magic variables (`{{os}}`, `{{arch}}`, `{{python}}`, `{{shell}}`,
`{{sep}}`, `{{home}}`) are injected automatically. Expansion order is user `vars`/`env` → magic →
`bin`, so user values can override the auto-injected ones. All of this is additive: a config with
none of these keys resolves exactly as in 1.0.x.

### Planner (2.0.0)

`Planner` reads `needs`/`pre`/`post`/`parallel` from the raw command config and runs the graph in
the order `needs → pre → main → post`. Dependencies are deduplicated (a shared dependency runs
once), cycles raise `CycleError`, and the first non-zero exit code aborts the run. `parallel: true`
executes a node's `needs` concurrently with a thread pool guarded by a lock.

### Plugins (2.0.0)

`plugins.discover()` loads the `shemul.plugins` entry-point group into a `PluginRegistry`. A command
with a `runner` key dispatches to the matching registered runner; a missing or failing runner falls
back to default execution, so a broken plugin never crashes the CLI.

### Update Notifier (2.0.0)

`updater` performs a best-effort, time-throttled (24h) check against the Shemul manifest with a PyPI
fallback, comparing monotonic **version codes** (semver fallback). It runs on a daemon thread, never
blocks the command, never raises, and is disabled by `--no-update-check`, the
`SHEMUL_NO_UPDATE_CHECK` env var, or `update_check: false`.

### Auto-update and Settings (2.0.0)

Preferences live in a `settings.json` file next to the global config and are read/written by
`settings.py` (managed via `shemul settings`). When the `auto_update` setting is enabled **and** the
background check finds a newer release, the CLI launches a **detached** `pip install -U shemul`
(`updater.spawn_auto_update`) and the upgrade takes effect on the next invocation. Auto-update is
opt-in (default off), records the attempted version in the cache so it does not re-spawn for the same
target, never blocks or raises, and is skipped for editable installs (`updater.is_editable_install`)
so a developer's checkout is never clobbered.

### Command Dispatch (2.0.0)

Commands resolve through `cli._dispatch`:

- A **leading slash** (`shemul /init`) always invokes the system/built-in command via
  `cli._run_system` — never a project command.
- A **bare name** (`shemul init`) prefers a project/global command of that name when one exists, and
  otherwise falls back to the system command. This lets users define commands named like built-ins
  (`init`, `test`, `build`) and still reach the built-in via the slash form.
- System commands: `init`, `ls`, `info`, `help`, `doctor`, `schema`, `alias`, `update`, `settings`,
  `version`, `about` (plus the internal `_complete`). Completion offers both bare and slash forms.

### Scope Resolution

- Project scope: nearest `shemul.json` found upward from current directory.
- Global scope: OS-native per-user config path (platform dependent).
- Merge rule: global is baseline, project overrides conflicting keys.
- Conflict rule for commands: project command with same name always wins.
- If only global exists, commands are runnable from any directory.

### OOP Command Model

The `Command` class owns resolution and execution metadata. This enables dry-run, trace output, and future composition strategies without changing CLI parsing logic.

### Safety Model

`confirm` triggers a prompt for any command.
`danger` shows a stronger warning with explicit confirmation.

By default commands run through the shell (`shell=True`), preserving shell features (`&&`, pipes,
redirection, globbing). Commands can opt into safer argument-vector execution with `shell: false` or
an explicit `exec: [...]` argument vector, which bypasses the shell entirely. A top-level `runtime`
naming a shell (`sh`/`bash`/`powershell`/…) selects the default interpreter for commands that do not
set their own; descriptive values (`docker`/`python`/`node`) are ignored for execution and remain
backward compatible.

### Initialization UX

- `shemul init [template]` initializes project config (defaults to `none`).
- `shemul init -g [template]` initializes global config (defaults to `none`).
- Running `init` on an existing config warns with path and opens the file for editing.
- `init -g` without template defaults to `none`.

### UX Layer

Rich provides structured output: tables, status messages, and clear errors. The CLI never hides errors, and always shows the resolved command when `--trace` is enabled.

Interactive prompts (2.0.0) live in `interactive.py` and are powered by `questionary`. `confirm`,
`danger`, `shemul settings`, the `init` template chooser, and the "did you mean?" suggestion picker
use arrow-key selection on a real terminal. The layer detects when interactivity is unavailable —
no TTY (CI, pipes, test runners), `questionary` missing, or `SHEMUL_NO_INTERACTIVE` set — and falls
back to the typed `rich` prompt or a safe default, so automated environments never block.

### Configuration

`shemul.json` is validated via JSON Schema bundled with the package and can be printed using
`shemul schema`. The schema is **additive across releases**: new keys (`os`, `bin`, `runtime`, `shell`,
`exec`, `needs`, `pre`, `post`, `parallel`, `runner`, `requires`, `update_check`) are optional, and
their absence reproduces 1.0.x behaviour. A config may declare `requires` (e.g. `">=2.0.0"`); older
Shemul versions surface an upgrade hint instead of a cryptic schema error.

### Versioning

Each release carries a monotonic integer **version code** in `version.py` (`VERSION_CODE`) that
matches the `Version Code` line in `CHANGELOG.md` (1.0.0 = 1, 1.0.1 = 2, 2.0.0 = 3). The update
checker compares codes rather than parsing semver. Surface it with `shemul version --code`.

### Repository Convention

- Tests live in `test/` (singular), not `tests/`.
