# Shemul

Shemul is an advanced project-aware CLI tool for task automation based on JSON configuration for PIP. It is a free and open-source CLI that centralizes repetitive development commands in `shemul.json` and runs them with safety controls, supporting both project-local and user-global command scopes.

## Table of Contents

- [Requirements](#requirements)
- [Features](#features)
- [Change log](#change-log)
- [Installation](#installation)
- [Usage](#usage)
- [FAQs](#faqs)
- [License](#license)
- [Security](#security)
- [Future Plan](#future-plan)
- [Author](#author)
- [Contributors](#contributors)
- [About S Technologies](#about-s-technologies)
- [Support](#support)
- [Hire Us](#hire-us)
- [Contribute](#contribute)
- [More](#more)
- [Copyright](#copyright)

## Requirements

- Python >= 3.9
- Dependencies (installed automatically): `rich`, `jsonschema`, `questionary`
- Optional: shell completion (bash, zsh, or fish) via scripts in `completion/`
- Interactive arrow-key prompts activate on a real terminal; set `SHEMUL_NO_INTERACTIVE=1`
  (or pipe input / run in CI) to use plain typed prompts instead.

## Features

- [x] Dual scope config: project and global
- [x] Deterministic precedence: project overrides global on command conflicts
- [x] Project discovery with `shemul.json`
- [x] Command model supporting `vars` and `env` templating
- [x] Safe execution controls: `confirm`, `danger`, `--dry`, `--trace`
- [x] Diagnostics via `shemul doctor`
- [x] Rich CLI output with grouped command lists and contextual help
- [x] Built-in template-based initialization (`shemul init [template]`)
- [x] Global initializer: `shemul init -g`
- [x] JSON Schema validation for `shemul.json`
- [x] Friendly command listing, info, help, and suggestions
- [x] Shell completion scripts for bash, zsh, and fish
- [x] Cross-OS commands — one command, per-OS variants via `os` (`v2.0.0`)
- [x] Interpreter maps (`bin`) and magic variables (`{{os}}`, `{{python}}`, …) (`v2.0.0`)
- [x] Default shell selection via top-level `runtime` (`v2.0.0`)
- [x] Opt-in safe execution with `shell: false` / `exec: [...]` (`v2.0.0`)
- [x] Task pipelines: `needs` dependencies, `pre`/`post` hooks, `parallel` groups (`v2.0.0`)
- [x] Update notifier + version codes (`shemul update`, `shemul version --code`) (`v2.0.0`)
- [x] Optional background auto-update + `shemul settings` (enable/disable) (`v2.0.0`)
- [x] Interactive prompts — arrow-key Yes/No, settings, and pickers (TTY only) (`v2.0.0`)
- [x] System commands via slash (`shemul /init`) so your own commands can shadow built-ins (`v2.0.0`)
- [x] `s` short alias with conflict detection (`shemul alias install`) (`v2.0.0`)
- [x] Plugin API via the `shemul.plugins` entry-point group and per-command `runner` (`v2.0.0`)

> New to Shemul, or want copy-paste examples for every feature?
> See **[doc/usage.md](doc/usage.md)** — examples for each feature, old and new.

## Change log

### Version 2.0.0 (June 6, 2026)

- **Breaking:** bare built-in names (`init`, `ls`, `info`, …) now defer to a same-named project command; use the slash form (`shemul /init`) for the built-in. New runtime dependency `questionary`. See the [migration guide](doc/migration-1.0.1-to-2.0.0.md).
- Cross-OS command engine: per-command `os` overrides, `bin` interpreter maps, and magic variables.
- Default shell selection via top-level `runtime`.
- Opt-in safe execution (`shell: false` / `exec: [...]`).
- Task pipelines: `needs`, `pre`/`post`, and `parallel`.
- Update notifier with version codes; `shemul update` and `shemul version --code`.
- Optional background auto-update (opt-in) and a `shemul settings` command to toggle it.
- Interactive prompts: arrow-key Yes/No confirms, settings editor, and pickers (with non-TTY fallback).
- `s` short alias via opt-in installer (`shemul alias install|status|remove`).
- Plugin API (`shemul.plugins` entry-point group; per-command `runner`).
- Extended `shemul doctor` (OS, interpreters, alias, update reachability).

### Version 1.0.1 (March 20, 2026)

- Fixed Python version requirement to >= 3.9 across package metadata and docs.

### Version 1.0.0 (February 11, 2026)

- Initial release.
- Project and global scope config.
- Template-based init and safety controls.

Please see [CHANGELOG](CHANGELOG.md) for more information on what has changed recently.

## Installation

Shemul can be installed using pip:

```bash
pip install shemul
```

## Usage

### Scope model

Shemul supports two config scopes:

- **Project scope:** `<project>/shemul.json`
- **Global scope** (OS-native):
  - Windows: `%APPDATA%\Shemul\shemul.json`
  - macOS: `~/Library/Application Support/Shemul/shemul.json`
  - Linux: `$XDG_CONFIG_HOME/shemul/shemul.json` (fallback: `~/.config/shemul/shemul.json`)

If both scopes define the same command, project scope wins. If no config exists, Shemul suggests running `shemul init -g`.

### Initialize global config

```bash
shemul init -g
```

### Initialize project config

```bash
shemul init --list
shemul init fastapi-backend
```

### List and run commands

```bash
shemul ls
shemul <command>
```

### Init behavior

- `shemul init [template]` creates project `shemul.json`; without template uses `none`.
- `shemul init -g [template]` creates global `shemul.json`; without template uses `none`.
- If config already exists, `init` warns with path and opens the file for editing.
- Use `--force` to overwrite existing config.

Available templates: `docker-fastapi-backend`, `fastapi-backend`, `django-drf-backend`, `expressjs-backend`, `nestjs-backend`, `react-native-expo-app`, `nextjs-frontend`, `none`.

### Common commands

Run your own project/global commands from `shemul.json`:

```bash
shemul <command>            # run a command
shemul --dry <command>      # preview the resolved command without running it
shemul <command> [args]     # tokens after the name are passed through to the command
```

System (built-in) commands. **Prefix with a leading slash** so they never clash with a project
command of the same name — `shemul /ls` always means the built-in:

```bash
shemul /ls                  # list configured commands
shemul /info                # detected project + active config/scopes
shemul /help <name|group>   # help for a command or group
shemul /doctor              # environment readiness checks
shemul /schema              # print the bundled JSON Schema
shemul /init [template]     # create project shemul.json (add -g for global)
shemul /update              # check PyPI for a newer release now
shemul /version --code      # 2.0.0 (code 3)
shemul /alias status        # what does `s` resolve to?
shemul /alias install       # enable the `s` shortcut (if free)
shemul /settings            # view / edit settings (interactive on a TTY)
shemul /settings auto-update on   # auto-run `pip install -U shemul` in the background
shemul /about               # styled About panel: version, version code, update status
shemul --no-update-check <command>   # skip the update check for one run
```

> Flag order: global options come **before** the command — `shemul --dry build`, not
> `shemul build --dry`. Tokens after the command name are passed through to the command.

> Slash vs bare: the slash form (`shemul /init`) **always** runs the built-in. The bare form
> (`shemul init`) also works, but if your `shemul.json` defines a command with that name the bare
> form runs **your** command — so the slash is the unambiguous way to reach a system command. (Git
> Bash/MSYS2 on Windows rewrites a single leading slash into a path — use `//init` there, or any
> other shell.)

### Safety flags

- `confirm: true` in config prompts before run.
- `danger: true` prompts with stronger warning.
- `--dry` prints resolved command.
- `--trace` prints resolved command and env context.

### What's new in 2.0.0 (quick reference)

Cross-OS, portable commands:

```json
{
  "bin": { "py": { "windows": "python", "default": "python3" } },
  "commands": {
    "run":  { "run": "{{py}} app.py" },
    "open": { "run": "xdg-open .", "os": { "windows": "start .", "macos": "open ." } },
    "info": { "run": "echo {{os}}/{{arch}}" }
  }
}
```

Task pipelines:

```json
{
  "commands": {
    "install": { "run": "npm ci" },
    "lint":    { "run": "npm run lint" },
    "test":    { "run": "npm test", "needs": ["install"] },
    "ci":      { "run": "echo green", "needs": ["lint", "test"], "parallel": true },
    "release": { "run": "npm publish", "pre": ["ci"], "post": ["echo done"] }
  }
}
```

New config keys (all optional, all backward compatible):

| Key | Scope | Purpose |
|---|---|---|
| `os` | command | Per-OS `run` override (`windows`/`macos`/`linux`/`default`) |
| `bin` | top-level | Named per-OS interpreters, used as `{{name}}` or `{{bin.name}}` |
| `runtime` | top-level | Default shell (`sh`/`bash`/`powershell`/…) when a command sets none |
| `shell` | command | `false` for arg-vector exec, or a shell name |
| `exec` | command | Argument vector to run without a shell |
| `needs` | command | Commands to run first (deduped, cycle-checked) |
| `pre` / `post` | command | Run before / after (post only on success) |
| `parallel` | command | Run this command's `needs` concurrently |
| `runner` | command | Dispatch to a plugin runner (`shemul.plugins`) |
| `requires` | top-level | Minimum Shemul version, e.g. `">=2.0.0"` |
| `update_check` | top-level | Set `false` to disable the update notifier |

Magic variables (no config needed): `{{os}}`, `{{arch}}`, `{{python}}`, `{{shell}}`, `{{sep}}`, `{{home}}`.

Full walkthrough with 1–3 examples per feature: **[doc/usage.md](doc/usage.md)**.

### Configuration example

```json
{
	"name": "example-project",
	"version": "1.0.0",
	"runtime": "docker",
	"env": {
		"local": {
			"compose": "docker-compose.yml"
		}
	},
	"vars": {
		"API": "api"
	},
	"commands": {
		"up": {
			"run": "docker compose up --build",
			"env": "local",
			"desc": "Start stack"
		},
		"migrate:up": {
			"run": "docker compose exec {{API}} alembic upgrade head",
			"confirm": true
		}
	}
}
```

### Development

- Source layout uses `src/`. Tests are in `test/`.
- Install with test extras, then run tests:

```bash
python -m pip install -e ".[test]"
python -m pytest -q
```

- CI runs the suite on Ubuntu, Windows, and macOS across Python 3.9–3.13
  (`.github/workflows/test.yml`).
- The repo's own `shemul.json` defines dev commands (group `dev`) for testing before publishing:

```bash
shemul cli /version --code   # run the source CLI (python -m shemul.cli) with any args
shemul test                  # python -m pytest -q
shemul build                 # python -m build
shemul check                 # python -m twine check dist/*
```

## FAQs

### What is Shemul?

Shemul is an advanced project-aware CLI tool for task automation based on JSON configuration for PIP.

### What is `shemul.json`?

It is the project or global JSON config that defines your commands, variables, and environment presets.

### Do I need both global and project configs?

No. You can use either. If both exist, project commands override global commands with the same name.

### How do I create a blank Shemul config?

Run `shemul init` to create a minimal config using the `none` template.

### How do I see the built-in schema for Shemul?

Run `shemul schema` to print the bundled JSON Schema.

### Where is the global config stored?

Windows: `%APPDATA%\Shemul\shemul.json`  
macOS: `~/Library/Application Support/Shemul/shemul.json`  
Linux: `$XDG_CONFIG_HOME/shemul/shemul.json` (fallback: `~/.config/shemul/shemul.json`)

### How is Shemul different from Make / a Makefile?

Make is a **build system**: it tracks file timestamps to rebuild targets, uses a tab-sensitive DSL,
and is POSIX-centric. Shemul is a **task runner**: it centralizes named commands in JSON (no DSL),
runs the same command across operating systems (`os`/`bin`/magic vars), and adds safety gates
(`confirm`/`danger`), dual project **+ global** scope, and an update notifier. Reach for Make when you
need incremental artifact builds; reach for Shemul when you want portable, safe, named project
commands. They compose — a Shemul command can call `make`.

### How is Shemul different from Just?

Just is an excellent command runner with a `justfile` DSL and `[os]` recipe attributes. Shemul meets
the same per-OS need via `os`/`bin`/magic vars but uses **JSON** (machine-editable, schema-validated),
and adds **global** user-wide commands, **safety prompts**, an **update notifier + auto-update**,
**interactive** arrow-key prompts, **slash system commands**, the **`s`** alias, and a **plugin API**.
Pick Just for a single-binary DSL; pick Shemul for JSON-first, safety-focused, pip-native workflows.

### How is Shemul different from Task (go-task)?

Task uses YAML and ships its own built-in cross-platform shell interpreter. Shemul uses JSON and runs
through the system shell (with **opt-in** arg-vector exec for safety/portability). Both do
dependencies and parallelism; Shemul differentiates with safety gates, project **+ global** scope,
interactive UI, version codes, and background auto-update.

### How is Shemul different from npm scripts?

npm scripts live in `package.json` and assume a Node project. Shemul is **language-agnostic**, works
in any repository (and globally across repositories), and adds per-OS commands, dependencies /
pre-post / parallel, safety gates, schema validation, and a richer CLI UX.

### Why JSON instead of a Makefile/justfile DSL or YAML?

JSON is universal and trivially generated/edited by tools, and Shemul ships a **JSON Schema** so
editors give you validation and autocomplete out of the box. You get structure without learning a
bespoke language. (Comment support — JSONC — is being considered for a future release.)

### Is Shemul a build system?

No. Shemul runs and orchestrates **tasks**; it does not do incremental, file-hash-based rebuilds.
That is a deliberate non-goal — it composes alongside Make/CMake/etc. rather than replacing them.

### Can I use Shemul together with Make, Just, or npm?

Yes. Shemul commands are ordinary shell commands, so a Shemul command can call `make`, `just`,
`npm run`, `docker compose`, and so on. Many teams use Shemul as the friendly, safe front door to
existing tooling.

### Does Shemul phone home?

Only an opt-out update check: a single best-effort GET to the Shemul manifest (PyPI fallback) at most
once per 24 hours, cached locally, with **no telemetry or identifiers**. Disable it with
`SHEMUL_NO_UPDATE_CHECK=1`, `--no-update-check`, or `"update_check": false`. Background auto-update is
**off by default** and opt-in via `shemul /settings`.

## License

Shemul is open-sourced software licensed under the [MIT License](LICENSE).

## Security

If you discover any security-related issues, please email [product@stechbd.net](mailto:product@stechbd.net) instead of using the issue tracker.

## Future Plan

Ideas under consideration for future releases (all additive unless noted):

- [ ] Watch mode, matrix commands, conditional `when`/`unless`, retry/timeout
- [ ] Config composition (`extends`/includes), profiles/contexts, dotenv & secrets
- [ ] TUI command launcher, `shemul graph` (DAG view), completion auto-install, themes
- [ ] Community template registry and remote/team-shared configs
- [ ] Richer plugin API (lifecycle hooks, custom resolvers) and update channels
- [ ] (v3.0.0, breaking) Safe-by-default execution — arg-vector exec as the default

## Author

- [Md. Ashraful Alam Shemul](https://github.com/AAShemul)

## Contributors

None yet.

## About S Technologies

**S Technologies** (**STechBD.Net**) is a research-based technology company in Bangladesh. It was founded in 2013. It provides services like domain registration, web hosting, web servers, software development, AI model development, software as a service (SaaS), UI/UX design, SEO, business solutions, etc. **S Technologies** has been working in research of new technologies especially in artificial intelligence, and developing new products. You'll find an overview of all our open source products [on our website](https://www.stechbd.net/open-source).

## Support

If you are having general issues with this package, feel free to contact us on [STechBD.Net/support](https://www.stechbd.net/support).

If you believe you have found an issue, please report it using the [GitHub issue tracker](https://github.com/STechBD/Shemul-PIP/issues), or better yet, fork the repository and submit a pull request.

- [Home Page](https://www.stechbd.net/product/Shemul-PIP)
- [GitHub Repository](https://github.com/STechBD/Shemul-PIP)
- [GitHub Issues](https://github.com/STechBD/Shemul-PIP/issues)
- [PyPI Package](https://pypi.org/project/shemul/)
- [Email](mailto:product@stechbd.net)
- [Support Page](https://www.stechbd.net/support)
- [Contact Form](https://www.stechbd.net/contact)
- [Facebook](https://www.facebook.com/STechBD.Net)
- [X (Twitter)](https://twitter.com/STechBD_Net)
- [LinkedIn](https://www.linkedin.com/company/STechBD)
- [Instagram](https://www.instagram.com/STechBD.Net)
- [YouTube](https://www.youtube.com/channel/STechBD)

## Hire Us

- [AI App Development](https://www.stechbd.net/ai-development)
- [Web App Development](https://www.stechbd.net/web-development)
- [Android App Development](https://www.stechbd.net/android-app-development)
- [iOS App Development](https://www.stechbd.net/ios-app-development)

## Contribute

- [GitHub](https://github.com/STechBD/Shemul-PIP)

## More

- [Privacy Policy](https://www.stechbd.net/privacy)
- [Terms & Conditions](https://www.stechbd.net/terms)
- [Refund Policy](https://www.stechbd.net/refund-policy)
- [Software License Agreement](https://www.stechbd.net/software-license-agreement)

## Copyright

© 2013–26 **[S Technologies](https://www.stechbd.net)**. All rights reserved.
