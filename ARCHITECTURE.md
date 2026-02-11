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
5. Resolve command templates using merged `vars` + `env`.
6. Apply safety guards (`confirm`, `danger`).
7. Execute via shell runner.

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

### Initialization UX

- `shemul init <template>` initializes project config.
- `shemul init -g [template]` initializes global config.
- Running `init` on an existing config warns with path and opens the file for editing.
- `init -g` without template defaults to `none`.

### UX Layer

Rich provides structured output: tables, status messages, and clear errors. The CLI never hides errors, and always shows the resolved command when `--trace` is enabled.

### Configuration

`shemul.json` is validated via JSON Schema bundled with the package and can be printed using `shemul schema`.

### Repository Convention

- Tests live in `test/` (singular), not `tests/`.
