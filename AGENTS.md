# AGENTS.md

This file is the local guide for AI/code agents working on Shemul.

## Project Summary

- Package name: `shemul`
- Python package layout: `src/`
- CLI entrypoint: `shemul` -> `shemul.cli:main`
- Primary config file: `shemul.json`

## Scope Rules

- Project config path: nearest `shemul.json` found upward from current directory.
- Global config path (OS-native):
  - Windows: `%APPDATA%\\Shemul\\shemul.json`
  - macOS: `~/Library/Application Support/Shemul/shemul.json`
  - Linux: `$XDG_CONFIG_HOME/shemul/shemul.json` (fallback: `~/.config/shemul/shemul.json`)
- Merge behavior: global baseline, project override.
- Command conflict behavior: project command wins over global command with same name.

## Init Rules

- `shemul init <template>`: initialize project config.
- `shemul init -g [template]`: initialize global config.
- `shemul init -g` defaults to `none` template if omitted.
- If target config already exists and `--force` is not used:
  - warn user with exact file path
  - open file for editing

## Testing Convention

- Use `test/` (singular) for all tests.
- Do not introduce a `tests/` directory in this repository.
- Run test suite with:

```bash
python -m pytest -q
```

## Packaging and Release

- Build metadata is in `pyproject.toml`.
- Keep versions aligned:
  - `pyproject.toml` `[project].version`
  - `src/shemul/version.py` `__version__`
- Publish flow is documented in `PUBLISHING.md`.

## Editing Guidelines for Agents

- Prefer minimal, focused changes.
- Keep behavior backward-compatible unless explicitly changing UX.
- Add tests for any behavior changes (especially scope resolution and init flow).
- Update `README.md` and `ARCHITECTURE.md` when behavior changes.
