# AGENTS.md

This file is the local guide for AI/code agents working on Shemul. Keep it in sync with
[`README.md`](README.md) and [`ARCHITECTURE.md`](ARCHITECTURE.md) when behavior changes.

## Project Summary

- Package name: `shemul` — an advanced project-aware JSON task runner for PIP.
- Current version: **2.0.0** (Version Code `3`); requires **Python >= 3.9**.
- Python package layout: `src/`.
- CLI entrypoint: `shemul` -> `shemul.cli:main`.
- Primary config file: `shemul.json` (project) and an OS-native global config.
- Runtime dependencies: `rich`, `jsonschema`, `questionary` (test extra: `pytest`).

### Module Map

- Core: `cli.py` (parse + dispatch + update-check orchestration), `app.py` (state load, resolve,
  planner gate, plugin dispatch), `command.py` (resolution: `os`/templating/magic/`bin`/`runtime`),
  `executor.py` (shell default + opt-in arg-vector), `config.py` (load + validate + merge),
  `context.py` (upward project discovery).
- Cross-OS engine (2.0.0): `platforms.py` (OS/arch, magic vars, interpreter probing, recognized shells).
- Orchestration (2.0.0): `planner.py` (`needs`/`pre`/`post`/`parallel`, cycle detection),
  `plugins.py` (`shemul.plugins` registry + runner dispatch).
- Services (2.0.0): `updater.py` (PyPI/version-code check + background auto-update), `alias.py`
  (`s` shim), `settings.py` (preferences).
- Interactive UI (2.0.0): `interactive.py` (arrow-key prompts via `questionary`, non-TTY fallback).
- Support: `ui.py`, `guard.py`, `util.py`, `autocomplete.py`, `template.py`, `doctor.py`, `version.py`.
- Schema: `src/shemul/schema.json` (draft-07, `additionalProperties: false`, additive across releases).

### App Flow (condensed from ARCHITECTURE.md)

1. Discover the nearest `shemul.json` upward; resolve the OS-native global config path; load and
   validate both against the bundled schema; merge (global baseline, **project wins**).
2. Start a non-blocking background update check (daemon thread; best-effort, never blocks).
3. Dispatch (see [Command dispatch](#command-dispatch)).
4. For a user command, `command.py` selects the base by `os[current]` -> `os["default"]` -> `run`,
   then expands `vars`/`env` -> magic vars -> `bin`; `runtime` may set the default shell.
5. If the command declares `needs`/`pre`/`post`/`parallel`, run it through `planner.py`
   (order `needs -> pre -> main -> post`; deduped; cycles raise `CycleError`; first non-zero aborts).
6. Apply safety guards (`confirm`/`danger`) via the interactive Yes/No prompt.
7. If a registered plugin `runner` is named, dispatch to it; otherwise execute via `executor.py`
   (`shell=True` default, or opt-in `shell:false`/`exec` arg-vector).
8. After the command returns, print the update notice (or run opt-in auto-update).

### Command dispatch

- System (built-in) commands: `init`, `ls`, `info`, `help`, `doctor`, `schema`, `update`, `alias`,
  `version`, `settings`, `about` (plus the internal `_complete`).
- **A leading slash (`shemul /init`) always runs the system command** — this is the canonical,
  unambiguous way to invoke a built-in. A **bare** name prefers a project/global command of the same
  name, falling back to the system command. Dispatch lives in `cli._dispatch` / `cli._run_system`.
- Notes: `version --code` -> `2.0.0 (code 3)`; `about` renders a styled panel with version, version
  code, and a live update-status line; `alias install|status|remove`; `settings [auto-update on|off]`
  (interactive checkbox editor on a TTY); global flag `--no-update-check`.
- This repo's own `shemul.json` defines dev commands (group `dev`): `cli`, `test`, `build`, `check`
  (run the source CLI / tests / build / twine check before publishing).
- Env vars: `SHEMUL_GLOBAL_CONFIG_PATH`, `SHEMUL_CONFIG_HOME`, `SHEMUL_GLOBAL_CACHE_PATH`,
  `SHEMUL_SETTINGS_PATH`, `SHEMUL_BIN_DIR`, `SHEMUL_NO_UPDATE_CHECK`, `SHEMUL_NO_INTERACTIVE`,
  `SHEMUL_EDITOR` (also honors `VISUAL`/`EDITOR`).

### Config keys

- 1.0.x: `name`, `version`, `runtime`, `vars`, `env`, and per-command `run`/`desc`/`env`/`group`/`confirm`/`danger`.
- 2.0.0 (all optional, additive): top-level `bin`, `requires`, `update_check`; per-command
  `os`, `shell`, `exec`, `needs`, `pre`, `post`, `parallel`, `runner`. Magic vars: `{{os}}`,
  `{{arch}}`, `{{python}}`, `{{shell}}`, `{{sep}}`, `{{home}}`.

See `doc/usage.md` for examples of every feature.

## Scope Rules

- Project config path: nearest `shemul.json` found upward from the current directory.
- Global config path (OS-native):
  - Windows: `%APPDATA%\\Shemul\\shemul.json`
  - macOS: `~/Library/Application Support/Shemul/shemul.json`
  - Linux: `$XDG_CONFIG_HOME/shemul/shemul.json` (fallback: `~/.config/shemul/shemul.json`)
- Merge behavior: global baseline, project override (applies to `vars`, `env`, `bin`, `runtime`,
  `commands`).
- Command conflict behavior: project command wins over a global command with the same name.

## Execution & Safety Model

- Default execution is `subprocess.run(..., shell=True)`, preserving shell features (`&&`, pipes,
  redirection, globbing). Opt into arg-vector execution with `shell: false` or `exec: [...]`.
- A top-level `runtime` naming a shell (`sh`/`bash`/`powershell`/…) sets the default shell for
  commands that don't set their own; descriptive values (`docker`/`python`/`node`) are ignored for
  execution and stay backward compatible.
- `confirm` prompts before running; `danger` shows a stronger warning. Prompts are arrow-key Yes/No
  on a TTY (default **No**), and fall back to a typed prompt under non-TTY / `SHEMUL_NO_INTERACTIVE`.
- The update notifier is opt-out (`--no-update-check`, `SHEMUL_NO_UPDATE_CHECK`, `update_check:false`);
  background auto-update is **opt-in** via settings and is skipped for editable installs.

## Init Rules

- `shemul init <template>`: initialize project config; `shemul init -g [template]`: global config.
- Without a template, `init` uses `none` non-interactively; on a TTY it offers an interactive
  template picker.
- If the target config already exists and `--force` is not used: warn with the exact file path and
  open the file for editing.

## Testing Convention

- Use `test/` (singular) for all tests. Do not introduce a `tests/` directory.
- Install test deps with `python -m pip install -e ".[test]"`.
- Run the suite with:

```bash
python -m pytest -q
```

- Tests import modules directly (no subprocess), use `monkeypatch` for env/platform, and inject
  fakes for network/`shutil.which`/`questionary` (never hit the network, real PyPI, or a real TTY).
- Create temp dirs under the **system temp** (`tempfile.mkdtemp`), not under the repo — the repo
  ships its own `shemul.json`, which `find_upward` would otherwise discover and break
  project-discovery tests.
- CI runs `.github/workflows/test.yml` on Ubuntu/Windows/macOS across Python 3.9–3.13.

## Packaging and Release

- Build metadata is in `pyproject.toml`.
- Keep versions aligned on every release:
  - `pyproject.toml` `[project].version`
  - `src/shemul/version.py` `__version__` and `version_info`
  - `src/shemul/version.py` `VERSION_CODE` (bump by exactly 1)
  - `CHANGELOG.md` `Version Code:` line (must match `VERSION_CODE`) and the dated section header
  - `README.md` changelog header date (e.g. `### Version 2.0.0 (June 6, 2026)`)
- The **version code counts published releases** and is independent of the semver name
  (1.0.0 = 1, 1.0.1 = 2, 2.0.0 = 3 — there is no 1.1.0). The update checker compares codes.
- Publish the `latest.json` manifest (with `version` + `version_code`) when releasing so the update
  checker lines up.
- Build/release flow is documented in `doc/` (`build-guide.md`, `local-release-checklist.md`,
  `publish-troubleshooting.md`).

## Editing Guidelines for Agents

- Prefer minimal, focused changes.
- Keep behavior backward-compatible. Schema changes must stay **additive** (new optional keys only);
  never change existing key types. A truly breaking default change is reserved for a future major (v3.0.0).
- Add tests for any behavior change (especially scope resolution, dispatch precedence, and init flow).
- When behavior or features change, update `README.md`, `ARCHITECTURE.md`, `doc/usage.md`, and
  `CHANGELOG.md`.
- ASCII-only content in CLI output strings (the Windows legacy console is cp1252); rely on `rich`
  styles/box-drawing rather than decorative Unicode glyphs.

## Repository Convention

- Tests live in `test/` (singular), not `tests/`.
