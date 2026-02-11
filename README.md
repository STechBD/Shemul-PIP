# Shemul

**Shemul** is a simple and lightweight **project-aware** task runner for development workflows. It is a free and open-source CLI that centralizes repetitive development commands in `shemul.json` and runs them with safety controls, supporting both project-local and user-global command scopes.

## Table of Contents

- [Requirements](#requirements)
- [Features](#features)
- [Change log](#change-log)
- [Installation](#installation)
- [Usage](#usage)
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

- Python >= 3.14
- Optional: shell completion (bash, zsh, or fish) via scripts in `completion/`

## Features

- [x] Dual scope config: project and global
- [x] Deterministic precedence: project overrides global on command conflicts
- [x] Project discovery with `shemul.json`
- [x] Command model supporting `vars` and `env` templating
- [x] Safe execution controls: `confirm`, `danger`, `--dry`, `--trace`
- [x] Diagnostics via `shemul doctor`
- [x] Rich CLI output with grouped command lists and contextual help
- [x] Built-in template-based initialization (`shemul init`)
- [x] Global initializer: `shemul init -g`
- [x] JSON Schema validation for `shemul.json`
- [x] Friendly command listing, info, help, and suggestions
- [x] Shell completion scripts for bash, zsh, and fish

## Change log

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

- `shemul init <template>` creates project `shemul.json`.
- `shemul init -g [template]` creates global `shemul.json`; without template uses `none`.
- If config already exists, `init` warns with path and opens the file for editing.
- Use `--force` to overwrite existing config.

Available templates: `docker-fastapi-backend`, `fastapi-backend`, `django-drf-backend`, `expressjs-backend`, `nestjs-backend`, `react-native-expo-app`, `nextjs-frontend`, `none`.

### Common commands

```bash
shemul ls
shemul info
shemul help <name|group>
shemul doctor
shemul schema
shemul <command>
```

### Safety flags

- `confirm: true` in config prompts before run.
- `danger: true` prompts with stronger warning.
- `--dry` prints resolved command.
- `--trace` prints resolved command and env context.

### Configuration example

```json
{
  "$schema": "https://shemul.dev/schema.json",
  "name": "example-project",
  "version": "1.0",
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
- Run tests:

```bash
python -m pytest -q
```

## License

Shemul is open-sourced software licensed under the [MIT License](LICENSE).

## Security

If you discover any security-related issues, please email [product@stechbd.net](mailto:product@stechbd.net) instead of using the issue tracker.

## Future Plan

- [ ] Plugin/extensibility system for custom resolvers and runners
- [ ] More built-in templates and community template registry
- [ ] Better cross-platform editor/open behavior and UX polish
- [ ] Optional remote/team-shared config patterns
- [ ] Additional command introspection and diagnostics

## Author

- [Md. Ashraful Alam Shemul](https://github.com/AAShemul)

## Contributors

None yet.

## About S Technologies

**S Technologies** (**STechBD.Net**) is a research-based technology company in Bangladesh.
It was founded in 2013.
It provides services like domain registration, web hosting, web servers, software development, AI model development, software as a service (SaaS), UI/UX design, SEO, business solutions, etc.
**S Technologies** has been working in research of new technologies especially in artificial intelligence, and developing new products.
You'll find an overview of all our open source products [on our website](https://www.stechbd.net/open-source).

## Support

If you are having general issues with this package, feel free to contact us on [STechBD.Net/support](https://www.stechbd.net/support).

If you believe you have found an issue, please report it using the [GitHub issue tracker](https://github.com/STechBD/Shemul-PIP/issues), or better yet, fork the repository and submit a pull request.

- [Home Page](https://shemul.stechbd.net)
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
