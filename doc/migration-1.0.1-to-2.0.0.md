# Migrating from Shemul 1.0.1 to 2.0.0

## TL;DR

**For almost everyone, there is nothing to do.** Shemul 2.0.0 roughly doubles the feature set, but
the `shemul.json` config format is **backward compatible** — every 1.0.1 config keeps working
unchanged, because every new capability is an *optional* key.

2.0.0 is a *major* release for two reasons only:

1. A change to **command dispatch precedence** (affects you only if your config defines a command
   named like a built-in — see below).
2. A new **runtime dependency** (`questionary`), installed automatically by pip.

```bash
pip install -U shemul
shemul /version --code     # 2.0.0 (code 3)
```

> Version-code note: the version *code* counts releases (1.0.0 = 1, 1.0.1 = 2, 2.0.0 = 3). There is
> no 1.1.0 — this work shipped as 2.0.0.

---

## What stayed the same

- Your existing `shemul.json` (project and global) loads and runs identically.
- `vars`, `env`, `{{var}}` / `{{env.x}}` templating, `confirm`, `danger`, `--dry`, `--trace`,
  groups, `desc`, and project-over-global precedence all behave exactly as before.
- Default execution is still `shell=True` (so `&&`, pipes, `>`, globbing keep working).
- The bundled JSON Schema only **added** optional keys; nothing was removed or retyped.

---

## Breaking changes

### 1. Command dispatch precedence

In 1.0.1, a bare built-in name always ran the built-in. In 2.0.0, a **bare name prefers a
project/global command of the same name**, falling back to the built-in.

This changes behavior **only if your config defines a command named** `init`, `ls`, `info`, `help`,
`doctor`, or `schema` (these were unreachable in 1.0.1 — the built-in shadowed them). Now the bare
name runs *your* command.

To run the built-in explicitly, prefix it with a slash:

```bash
shemul /init        # always the built-in initializer
shemul /ls          # always the built-in command list
shemul /doctor      # always the built-in diagnostics
```

If you do **not** define commands with those names (the overwhelmingly common case), nothing changes
— `shemul ls`, `shemul doctor`, etc. work as before.

The subcommands new in 2.0.0 (`update`, `alias`, `version`, `settings`, `about`) follow the same
rule: a bare name runs your same-named command if you have one, otherwise the built-in. Use the slash
form (`shemul /update`) to be unambiguous.

> Git Bash / MSYS2 on Windows rewrites a single leading slash into a path. Use `//init` there, or run
> from PowerShell/cmd/another shell.

### 2. New dependency: `questionary`

2.0.0 adds `questionary` (for interactive arrow-key prompts). `pip install -U shemul` pulls it in
automatically. If you vendor dependencies or run in a locked environment, add `questionary>=2.0.0`.

---

## Things to check (CI and scripts)

These are **not** breaking, but are new behaviors worth knowing when automating Shemul:

- **Update check.** 2.0.0 runs a non-blocking, best-effort PyPI/manifest check (≤ once per 24h,
  cached, silent). To turn it off in CI or scripts:

  ```bash
  export SHEMUL_NO_UPDATE_CHECK=1      # or per-run: shemul --no-update-check <command>
  # or in config:  "update_check": false
  ```

- **Auto-update is OFF by default.** It only runs `pip install -U shemul` if you explicitly enable it
  (`shemul /settings auto-update on`) and is skipped for editable installs.

- **Interactive prompts.** On a real terminal, `confirm`/`danger` use an arrow-key Yes/No selector.
  In CI / pipes / non-TTY, Shemul falls back to the typed prompt automatically (same as 1.0.1). To
  force the plain typed prompt anywhere, set `SHEMUL_NO_INTERACTIVE=1`.

---

## Optional: adopt the new features

None of these are required, but they're why you upgraded. Add them incrementally:

- **Portable commands:** `bin` interpreter maps + magic vars (`{{python}}`, `{{os}}`, …) and
  per-command `os` overrides.
- **Pipelines:** `needs` dependencies, `pre`/`post` hooks, `parallel` groups.
- **Safety:** opt-in arg-vector execution (`shell: false` / `exec: [...]`).
- **Lifecycle:** `shemul /update`, `shemul /settings`, the `s` alias (`shemul /alias install`).

Declare the minimum version so older installs show a clear upgrade hint instead of a schema error:

```json
{ "requires": ">=2.0.0", "commands": { "run": { "run": "{{python}} app.py" } } }
```

See [usage.md](usage.md) for 1–3 examples of every feature, old and new.

---

## Need help?

- Full feature guide: [usage.md](usage.md)
- Changes list: [../CHANGELOG.md](../CHANGELOG.md)
- Issues: <https://github.com/STechBD/Shemul-PIP/issues>
