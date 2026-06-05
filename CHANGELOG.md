# Changelog of Shemul

All notable changes to this project will be documented in this file.

## Table of Contents

- [Version 2.0.0](#version-200)
- [Version 1.0.1](#version-101)
- [Version 1.0.0](#version-100)

## Version 2.0.0

Version 2.0.0 is a major release of Shemul that roughly doubles the feature set. Almost every new capability is additive (an optional `shemul.json` key or subcommand), so existing 1.0.1 configs keep working. It is a major release because command dispatch changed: bare built-in names now defer to a same-named project command (reachable explicitly via the slash form, e.g. `shemul /init`), and a new runtime dependency (`questionary`) was added.

- Release Date: June 6, 2026
- Version Code: 3
- Release type: Major
- Stability: Stable

> Note on version codes: the version *code* (3) counts published releases (1.0.0=1, 1.0.1=2, 2.0.0=3) and is independent of the semver name. There is no 1.1.0 release; this work ships as 2.0.0.

### Requirements

- Python Version: 3.9 or higher

### Breaking changes

- **Command dispatch precedence.** A bare built-in name (`init`, `ls`, `info`, `help`, `doctor`, `schema`) now runs your project/global command of that name when one exists, instead of always running the built-in. Use the slash form (`shemul /init`) to force the built-in. Configs that did not define commands with these names are unaffected.
- **New runtime dependency:** `questionary` (for interactive prompts). Installed automatically by pip.

### Changes

- Cross-OS command engine: per-command `os` overrides, top-level `bin` interpreter maps, and magic variables (`{{os}}`, `{{arch}}`, `{{python}}`, `{{shell}}`, `{{sep}}`, `{{home}}`).
- Update notifier: non-blocking PyPI/manifest version check with 24h cache and opt-out controls; `shemul update` and `shemul version --code`.
- Optional background auto-update: when enabled, a detached `pip install -U shemul` runs after an update is found (opt-in, skipped for editable installs).
- Settings store and `shemul settings` command to enable/disable preferences such as `auto_update`.
- Interactive CLI UI: arrow-key Yes/No for `confirm`/`danger` prompts, a checkbox `shemul settings`
  editor, an `init` template picker, and a "did you mean?" command picker. Falls back to the typed
  prompt automatically when there is no TTY (CI/pipes) or when `SHEMUL_NO_INTERACTIVE` is set.
- System vs project commands: a leading slash runs the built-in explicitly (`shemul /init`,
  `/settings`, `/about`, …). Bare names now prefer a project/global command of the same name, so you
  can define your own `init`/`test`/etc. and still reach the built-in via `/name`.
- New `about` screen (`shemul /about`): a styled panel with the version, version code, a live
  update-status line (up to date / update available / offline), and project links.
- Version codes: monotonic integer release code for easy update checks.
- `s` short alias via opt-in installer (`shemul alias install|status|remove`) with conflict detection.
- Task orchestration: `needs` dependencies, `pre`/`post` hooks, and `parallel` groups.
- Active `runtime` awareness and opt-in safe execution (`shell: false` / `exec: [...]`).
- Plugin API via the `shemul.plugins` entry-point group with a custom `runner` per command.
- Extended `shemul doctor` checks (OS, interpreters, alias, update reachability).

### Affected Files

- `src/shemul/*` (new: `platforms.py`, `planner.py`, `plugins.py`, `updater.py`, `alias.py`, `settings.py`)
- `src/shemul/schema.json`
- `pyproject.toml`
- `README.md`, `ARCHITECTURE.md`, `AGENTS.md`, `doc/*`
- `CHANGELOG.md`

## Version 1.0.1

Version 1.0.1 is a patch release of Shemul for updating python dependency and organizing the codebase.

- Release Date: March 20, 2026
- Version Code: 2
- Release type: Patch
- Stability: Stable

### Requirements

- Python Version: 3.9 or higher

### Changes

- Fixed Python version requirement to >= 3.9.
- Organized codebase.

### Affected Files

- `pyproject.toml`
- `README.md`
- `CHANGELOG.md`

## Version 1.0.0

Version 1.0.0 is the initial release of Shemul.

- Release Date: February 11, 2026
- Version Code: 1
- Release type: Major
- Stability: Stable

### Requirements

- Python Version: 3.9 or higher

### Changes

- Initial release.

### Affected Files

- Not applicable.
