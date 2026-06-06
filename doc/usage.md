# Shemul Usage & Examples

A hands-on guide to every Shemul feature, each with **1–3 small examples** you can copy.
New to Shemul? Read top to bottom. Already know the basics? Jump to
[New in 2.0.0](#part-2--new-in-200).

- Core features (1.0.x): the building blocks every project uses.
- New in 2.0.0: cross-OS commands, update notifier, the `s` alias, task pipelines, plugins.

> Flag order: global options come **before** the command —
> `shemul --dry build`, not `shemul build --dry`. Anything after the command name is
> passed through to the command itself.

> Interactive UI: on a real terminal, prompts (confirm, `shemul settings`, the `init` template
> chooser, "did you mean?") use **arrow keys** to select — no typing required. In CI, pipes, or when
> `SHEMUL_NO_INTERACTIVE=1` is set, Shemul falls back to plain typed prompts so nothing blocks.

## Table of Contents

- [Part 1 — Core features (1.0.x)](#part-1--core-features-10x)
  - [1. Initialize a project config](#1-initialize-a-project-config)
  - [2. Initialize a global config](#2-initialize-a-global-config)
  - [3. List commands](#3-list-commands)
  - [4. Run a command](#4-run-a-command)
  - [5. Variables (`vars`)](#5-variables-vars)
  - [6. Environment presets (`env`)](#6-environment-presets-env)
  - [7. Groups and descriptions](#7-groups-and-descriptions)
  - [8. Confirm and danger guards](#8-confirm-and-danger-guards)
  - [9. Dry-run and trace](#9-dry-run-and-trace)
  - [10. Pass extra arguments](#10-pass-extra-arguments)
  - [11. Info, help, doctor, schema](#11-info-help-doctor-schema)
  - [12. Templates](#12-templates)
  - [13. Project-over-global precedence](#13-project-over-global-precedence)
- [Part 2 — New in 2.0.0](#part-2--new-in-200)
  - [14. Cross-OS commands (`os`)](#14-cross-os-commands-os)
  - [15. Interpreter maps (`bin`)](#15-interpreter-maps-bin)
  - [16. Magic variables](#16-magic-variables)
  - [17. Default shell via `runtime`](#17-default-shell-via-runtime)
  - [18. Safe execution (`shell` / `exec`)](#18-safe-execution-shell--exec)
  - [19. Task dependencies (`needs`)](#19-task-dependencies-needs)
  - [20. Pre/post hooks](#20-prepost-hooks)
  - [21. Parallel dependencies (`parallel`)](#21-parallel-dependencies-parallel)
  - [22. Update notifier and `shemul update`](#22-update-notifier-and-shemul-update)
  - [23. Version codes (`version --code`)](#23-version-codes-version---code)
  - [24. The `s` alias](#24-the-s-alias)
  - [25. Plugins (`runner`)](#25-plugins-runner)
  - [26. Require a minimum version (`requires`)](#26-require-a-minimum-version-requires)

---

## Part 1 — Core features (1.0.x)

### 1. Initialize a project config

Creates a `shemul.json` in the current directory.

```bash
# Example 1: blank starter config
shemul init

# Example 2: from a template
shemul init fastapi-backend

# Example 3: overwrite an existing config
shemul init nextjs-frontend --force
```

### 2. Initialize a global config

A global config makes commands runnable from any directory.

```bash
# Example 1: create the global config (OS-native location)
shemul init -g

# Example 2: seed the global config from a template
shemul init -g fastapi-backend

# Example 3: list available templates first
shemul init --list
```

Global config locations:

- Windows: `%APPDATA%\Shemul\shemul.json`
- macOS: `~/Library/Application Support/Shemul/shemul.json`
- Linux: `$XDG_CONFIG_HOME/shemul/shemul.json` (fallback `~/.config/shemul/shemul.json`)

### 3. List commands

```bash
# Example 1: list everything (project + global), grouped
shemul ls

# Example 2: see one group's commands
shemul help quality

# Example 3: inspect a single command's resolved details
shemul help test
```

### 4. Run a command

Given this `shemul.json`:

```json
{
  "name": "demo",
  "commands": {
    "dev":  { "run": "uvicorn app.main:app --reload" },
    "test": { "run": "pytest -q" }
  }
}
```

```bash
# Example 1: run the dev server
shemul dev

# Example 2: run the tests
shemul test

# Example 3: see what would run without running it
shemul --dry dev
```

> System vs your commands: a **bare** name prefers *your* project/global command when one exists, so
> you can safely define commands named `init`, `test`, `build`, etc. To run the built-in explicitly,
> prefix it with a **slash**: `shemul /init`, `shemul /settings`, `shemul /about`. See
> [System commands](#system-commands-slash) below.

### 5. Variables (`vars`)

Reusable values, referenced as `{{NAME}}`.

```json
{
  "vars": { "API": "api", "PORT": "8000" },
  "commands": {
    "logs": { "run": "docker compose logs -f {{API}}" },
    "serve": { "run": "python -m http.server {{PORT}}" }
  }
}
```

```bash
# Example 1
shemul logs        # -> docker compose logs -f api

# Example 2
shemul serve       # -> python -m http.server 8000

# Example 3: confirm substitution with a dry-run
shemul --dry logs
```

### 6. Environment presets (`env`)

Named bundles of values, referenced as `{{env.key}}`. A command selects one with `"env"`.

```json
{
  "env": {
    "local": { "compose": "docker-compose.yml" },
    "prod":  { "compose": "docker-compose.prod.yml" }
  },
  "commands": {
    "up":      { "run": "docker compose -f {{env.compose}} up", "env": "local" },
    "prod:up": { "run": "docker compose -f {{env.compose}} up -d", "env": "prod" }
  }
}
```

```bash
# Example 1: uses the local compose file
shemul up

# Example 2: uses the prod compose file
shemul prod:up

# Example 3: verify the resolved file
shemul --dry prod:up
```

### 7. Groups and descriptions

`group` organizes `shemul ls`; `desc` documents a command.

```json
{
  "commands": {
    "test":   { "run": "pytest -q", "group": "quality", "desc": "Run tests" },
    "lint":   { "run": "ruff check .", "group": "quality", "desc": "Lint source" },
    "deploy": { "run": "./deploy.sh", "group": "release", "desc": "Ship it" }
  }
}
```

```bash
# Example 1: grouped listing
shemul ls

# Example 2: show one group
shemul help quality

# Example 3: show one command's description + resolved run
shemul help deploy
```

### 8. Confirm and danger guards

`confirm` prompts before running; `danger` shows a stronger warning. On a terminal the prompt is an
arrow-key **Yes / No** selector (default **No**); pipe input or set `SHEMUL_NO_INTERACTIVE=1` for a
typed `[y/n]` prompt.

```json
{
  "commands": {
    "migrate": { "run": "alembic upgrade head", "confirm": true },
    "reset":   { "run": "dropdb app && createdb app", "danger": true }
  }
}
```

```bash
# Example 1: prompts "Are you sure...?"
shemul migrate

# Example 2: prompts with a stronger "dangerous" warning
shemul reset

# Example 3: preview without prompting or running
shemul --dry reset
```

### 9. Dry-run and trace

```bash
# Example 1: print the resolved command, do not execute
shemul --dry deploy

# Example 2: show the resolved command AND its env context
shemul --trace up

# Example 3: combine with any command
shemul --dry test
```

### 10. Pass extra arguments

Anything after the command name is appended to the command.

```json
{ "commands": { "test": { "run": "pytest -q" } } }
```

```bash
# Example 1: run a single test file
shemul test tests/test_api.py

# Example 2: pass pytest flags
shemul test -k login -x

# Example 3: preview the full command
shemul --dry test -k login
```

### 11. Info, help, doctor, schema

```bash
# Example 1: where are my configs and what's active?
shemul info

# Example 2: full help / a command's help
shemul help
shemul help test

# Example 3: environment readiness + bundled JSON Schema
shemul doctor
shemul schema
```

### System commands (slash)

Built-in (system) commands can be invoked explicitly with a **leading slash**, so they never clash
with a project/global command of the same name. Bare names prefer *your* command; the slash always
means the built-in.

System commands: `/init`, `/ls`, `/info`, `/help`, `/doctor`, `/schema`, `/alias`, `/update`,
`/settings`, `/version`, `/about`.

`shemul /about` shows a styled panel with the version + version code, a live **update-status** line
(up to date / update available / offline), and project links.

```bash
# Example 1: you define your own `init` in shemul.json
shemul init         # runs YOUR command
shemul /init        # runs Shemul's initializer

# Example 2: any built-in works with a slash
shemul /doctor
shemul /version --code

# Example 3 (Git Bash / MSYS2 on Windows only): escape the leading slash
shemul //doctor     # MSYS rewrites a single leading slash into a path
```

> Most shells (PowerShell, cmd, bash, zsh) pass `/init` through unchanged. Only Git Bash / MSYS2 on
> Windows rewrites a single leading slash into a path — there, use `//init`, or just use the bare name.

### 12. Templates

Built-in starting points for `shemul init`:
`docker-fastapi-backend`, `fastapi-backend`, `django-drf-backend`, `expressjs-backend`,
`nestjs-backend`, `react-native-expo-app`, `nextjs-frontend`, `none`.

```bash
# Example 1: list templates with aliases
shemul init --list

# Example 2: aliases work ("fastapi" == "fastapi-backend")
shemul init fastapi

# Example 3: multi-word aliases are fine
shemul init docker fastapi backend
```

### 13. Project-over-global precedence

When a project and global config both define a command of the same name, **project wins**.

```bash
# Example 1: global has `deploy`; run it from anywhere
cd ~/anywhere && shemul deploy

# Example 2: a project that redefines `deploy` overrides the global one
cd ~/my-project && shemul deploy

# Example 3: confirm which scopes are active
shemul info
```

---

## Part 2 — New in 2.0.0

### 14. Cross-OS commands (`os`)

Give a command per-OS variants. Lookup order: current OS → `default` → the base `run`.
Keys accept `windows`/`win`, `macos`/`mac`/`darwin`, `linux`.

```json
{
  "commands": {
    "open":  { "run": "xdg-open .", "os": { "windows": "start .", "macos": "open ." } },
    "clear": { "run": "clear", "os": { "windows": "cls" } }
  }
}
```

```bash
# Example 1 (Windows): resolves to `start .`
shemul --dry open

# Example 2 (macOS): resolves to `open .`
shemul --dry open

# Example 3 (Linux): falls back to the base run `xdg-open .`
shemul --dry open
```

### 15. Interpreter maps (`bin`)

Define a tool once per OS, reuse it everywhere. Reference it as `{{NAME}}` or `{{bin.NAME}}`.

```json
{
  "bin": { "py": { "windows": "python", "default": "python3" } },
  "commands": {
    "run":  { "run": "{{py}} app.py" },
    "test": { "run": "{{bin.py}} -m pytest -q" }
  }
}
```

```bash
# Example 1 (Windows): {{py}} -> python
shemul --dry run        # python app.py

# Example 2 (Linux/macOS): {{py}} -> python3
shemul --dry run        # python3 app.py

# Example 3: the namespaced form works too
shemul --dry test       # python -m pytest -q  (Windows)
```

### 16. Magic variables

Auto-injected, no config needed:

| Variable | Windows | Linux / macOS |
|---|---|---|
| `{{os}}` | `windows` | `linux` / `macos` |
| `{{arch}}` | `amd64` / `arm64` | `amd64` / `arm64` |
| `{{python}}` | `python` (or `py -3`) | `python3` |
| `{{shell}}` | `powershell` | `sh` |
| `{{sep}}` | `\` | `/` |
| `{{home}}` | home dir | home dir |

```json
{
  "commands": {
    "whoami": { "run": "echo running on {{os}}/{{arch}}" },
    "serve":  { "run": "{{python}} -m http.server" },
    "path":   { "run": "echo build{{sep}}out" }
  }
}
```

```bash
# Example 1
shemul --dry whoami     # echo running on windows/amd64

# Example 2: portable Python without declaring a bin map
shemul --dry serve      # python3 -m http.server  (Linux)

# Example 3: a user var named the same wins over the magic value
#   with vars: { "os": "custom" }, {{os}} resolves to "custom"
shemul --dry whoami
```

### 17. Default shell via `runtime`

A top-level `runtime` naming a shell (`sh`, `bash`, `zsh`, `fish`, `powershell`, `pwsh`, `cmd`)
sets the default shell for commands that don't specify their own. Descriptive values like
`docker`/`python`/`node` are ignored for execution (backward compatible).

```json
{
  "runtime": "bash",
  "commands": {
    "greet": { "run": "echo hello from $0" },
    "win":   { "run": "Write-Host hi", "shell": "powershell" }
  }
}
```

```bash
# Example 1: `greet` runs under bash (on POSIX, when bash is installed)
shemul greet

# Example 2: a per-command shell overrides the runtime default
shemul win

# Example 3: runtime: "docker" stays descriptive — commands run with the default shell
shemul --dry greet
```

### 18. Safe execution (`shell` / `exec`)

By default commands run through the shell (so `&&`, pipes, `>`, globs work). For commands that
take untrusted input, opt into argument-vector execution — no shell parsing.

```json
{
  "commands": {
    "piped": { "run": "cat data.txt | sort | uniq" },
    "safe":  { "exec": ["python3", "tool.py", "--name", "value"] },
    "nosh":  { "run": "git status", "shell": false }
  }
}
```

```bash
# Example 1: default shell execution (pipes work)
shemul piped

# Example 2: exec runs argv directly, no shell involved
shemul safe

# Example 3: shell:false runs the run string as a single argv (no shell features)
shemul nosh
```

### 19. Task dependencies (`needs`)

`needs` runs other commands first. Shared dependencies run once; cycles are detected and reported.

```json
{
  "commands": {
    "install": { "run": "npm ci" },
    "build":   { "run": "npm run build", "needs": ["install"] },
    "deploy":  { "run": "./deploy.sh", "needs": ["build"] }
  }
}
```

```bash
# Example 1: runs install -> build
shemul build

# Example 2: runs install -> build -> deploy
shemul deploy

# Example 3: preview the chain (each step shown)
shemul --dry deploy
```

### 20. Pre/post hooks

`pre` runs before the command; `post` runs only if the command succeeds.

```json
{
  "commands": {
    "fmt":     { "run": "ruff format ." },
    "test":    { "run": "pytest -q" },
    "notify":  { "run": "echo done" },
    "release": { "run": "python -m build", "pre": ["fmt", "test"], "post": ["notify"] }
  }
}
```

```bash
# Example 1: fmt -> test -> build -> notify
shemul release

# Example 2: if `test` fails, build and notify never run
shemul release

# Example 3: preview the full pipeline
shemul --dry release
```

Run order for any command: `needs` → `pre` → the command → `post`.

### 21. Parallel dependencies (`parallel`)

With `parallel: true`, a command's `needs` run concurrently.

```json
{
  "commands": {
    "lint":  { "run": "ruff check ." },
    "types": { "run": "mypy ." },
    "test":  { "run": "pytest -q" },
    "ci":    { "run": "echo all green", "needs": ["lint", "types", "test"], "parallel": true }
  }
}
```

```bash
# Example 1: lint, types, test run together, then `ci`
shemul ci

# Example 2: any failing dependency aborts with its exit code
shemul ci

# Example 3: preview which commands participate
shemul --dry ci
```

### 22. Update notifier and `shemul update`

Shemul checks PyPI at most once per 24h, in the background, and prints a one-line notice **after**
your command when a newer release exists. It never blocks or slows your command.

```bash
# Example 1: force a check right now
shemul update

# Example 2: disable the check for a single run
shemul --no-update-check build

# Example 3: disable it permanently (env, or per config)
#   export SHEMUL_NO_UPDATE_CHECK=1
#   or add  "update_check": false  to shemul.json
shemul build
```

#### Auto-update and settings (`shemul settings`)

Opt in to have Shemul update **itself**: when the background check finds a newer release, Shemul
launches a detached `pip install -U shemul` and the new version takes effect on your next command.
It is **off by default**, never blocks your command, and is skipped automatically for editable
(`pip install -e`) development checkouts.

```bash
# Example 1: see current settings (and the settings file path)
shemul settings

# Example 2: enable / disable background auto-update
shemul settings auto-update on
shemul settings auto-update off

# Example 3: reset all settings to defaults
shemul settings reset
```

Notes:

- On a terminal, `shemul settings` (no arguments) opens an interactive checkbox editor — toggle with
  Space, save with Enter. The `auto-update on|off` form is always available for scripts/CI.
- Settings live in `settings.json` next to your global config (override with `SHEMUL_SETTINGS_PATH`).
- `shemul doctor` reports whether auto-update is enabled (and if it is skipped for an editable install).
- Auto-update respects the same off switches as the notifier (`--no-update-check`,
  `SHEMUL_NO_UPDATE_CHECK`, `update_check: false`): if the check doesn't run, nothing updates.

### 23. Version codes (`version --code`)

Each release has a monotonic integer **version code** (1.0.0 = 1, 1.0.1 = 2, 2.0.0 = 3) used for
fast update comparisons.

```bash
# Example 1: plain version
shemul --version          # 2.0.0

# Example 2: version with code
shemul version --code     # 2.0.0 (code 3)

# Example 3: the same code drives `shemul update` and `shemul doctor`
shemul doctor
```

### 24. The `s` alias

Type `s` instead of `shemul`. The installer **refuses to clobber** an existing `s` on your system.

```bash
# Example 1: check what `s` currently resolves to
shemul alias status

# Example 2: install the shim (only if `s` is free)
shemul alias install
#   then:  s build   ==   shemul build

# Example 3: remove the shim (only removes Shemul's own)
shemul alias remove
```

If `s` is already taken, install prints a clear message and changes nothing — keep using `shemul`.

### 25. Plugins (`runner`)

Third-party packages can register custom runners under the `shemul.plugins` entry-point group. A
command opts in with `"runner": "<name>"`. If the runner is missing or errors, Shemul falls back to
normal execution.

```json
{
  "commands": {
    "deploy": { "run": "deploy --env prod", "runner": "k8s" }
  }
}
```

A plugin package registers the runner:

```python
# my_shemul_plugin/__init__.py
def register(registry):
    registry.register_runner("k8s", lambda resolved: my_deploy(resolved.command))
```

```toml
# the plugin's pyproject.toml
[project.entry-points."shemul.plugins"]
k8s = "my_shemul_plugin:register"
```

```bash
# Example 1: with the plugin installed, `deploy` dispatches to the k8s runner
shemul deploy

# Example 2: without the plugin, the same config just runs the `run` string
shemul deploy

# Example 3: a failing runner falls back to default execution (never crashes the CLI)
shemul deploy
```

### 26. Require a minimum version (`requires`)

Declare the minimum Shemul a config needs. Older Shemul versions show an upgrade hint instead of a
cryptic schema error.

```json
{
  "requires": ">=2.0.0",
  "bin": { "py": { "windows": "python", "default": "python3" } },
  "commands": { "run": { "run": "{{py}} app.py" } }
}
```

```bash
# Example 1: on Shemul >= 2.0.0 everything works
shemul run

# Example 2: on older Shemul, you are told to upgrade
#   "This config needs Shemul >= 2.0.0. Run: pip install -U shemul"

# Example 3: keep tooling current
pip install -U shemul
```

---

## A complete example

```json
{
  "name": "demo",
  "requires": ">=2.0.0",
  "runtime": "bash",
  "bin": { "py": { "windows": "python", "default": "python3" } },
  "vars": { "PORT": "8000" },
  "env": { "prod": { "host": "0.0.0.0" } },
  "commands": {
    "install": { "run": "{{py}} -m pip install -r requirements.txt", "group": "setup" },
    "lint":    { "run": "ruff check .", "group": "quality" },
    "test":    { "run": "{{py}} -m pytest -q", "group": "quality", "needs": ["install"] },
    "serve":   { "run": "{{py}} -m http.server {{PORT}}", "desc": "Static server" },
    "open":    { "run": "xdg-open .", "os": { "windows": "start .", "macos": "open ." } },
    "ci":      { "run": "echo green", "needs": ["lint", "test"], "parallel": true },
    "deploy":  { "run": "{{py}} deploy.py --host {{env.host}}", "env": "prod", "danger": true }
  }
}
```

```bash
shemul ls                 # see everything grouped
shemul --dry ci           # preview the parallel pipeline
shemul test               # installs first, then tests
shemul version --code     # 2.0.0 (code 3)
```
