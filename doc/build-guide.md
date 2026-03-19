# Build Guide

This guide explains how to regenerate metadata and build distribution artifacts on Windows and Linux.

## Prerequisites

1. Python 3.9+ installed
2. Virtual environment created (recommended)

## Activate Virtual Environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux (bash/zsh):

```bash
source .venv/bin/activate
```

## Regenerate `src/shemul.egg-info`

Use this when project metadata changes (like Python requirements or classifiers).

Windows PowerShell:

```powershell
Remove-Item -Recurse -Force src\shemul.egg-info -ErrorAction SilentlyContinue
python -m pip install --upgrade pip
python -m pip install -e .
```

Linux (bash/zsh):

```bash
rm -rf src/shemul.egg-info
python -m pip install --upgrade pip
python -m pip install -e .
```

## Test From Source (No Install)

Use this to run the CLI directly from the repo without installing the package.

Note: Prefer `PYTHONPATH=src python -m shemul.cli`. If you see blank output for `--help` or `info` on Windows, use the fallback `python -m src.shemul.cli` instead.

Windows PowerShell:

```powershell
$env:PYTHONPATH="src" && python -m shemul.cli --help
$env:PYTHONPATH="src" && python -m shemul.cli info
$env:PYTHONPATH="src" && python -m shemul.cli init
```

Fallback (Windows PowerShell):

```powershell
python -m src.shemul.cli --help
python -m src.shemul.cli info
python -m src.shemul.cli init
```

Linux (bash/zsh):

```bash
PYTHONPATH=src python -m shemul.cli --help
PYTHONPATH=src python -m shemul.cli info
PYTHONPATH=src python -m shemul.cli init
```

## Clean Build Artifacts

Windows PowerShell:

```powershell
Remove-Item -Recurse -Force dist, build, src\shemul.egg-info -ErrorAction SilentlyContinue
```

Linux (bash/zsh):

```bash
rm -rf dist build src/shemul.egg-info
```

## Build sdist and wheel

Windows PowerShell:

```powershell
python -m pip install --upgrade pip
python -m pip install --upgrade build twine
python -m build
```

Linux (bash/zsh):

```bash
python -m pip install --upgrade pip
python -m pip install --upgrade build twine
python -m build
```

Expected output (key lines):

```text
* Creating isolated environment: venv+pip...
* Building sdist...
* Building wheel...
Successfully built shemul-<version>.tar.gz and shemul-<version>-py3-none-any.whl
```

Expected files:

1. `dist/shemul-<version>.tar.gz`
2. `dist/shemul-<version>-py3-none-any.whl`

## Validate Package Metadata

Windows PowerShell:

```powershell
python -m twine check dist/*
```

Linux (bash/zsh):

```bash
python -m twine check dist/*
```

Expected:

```text
Checking dist/shemul-<version>-py3-none-any.whl: PASSED
Checking dist/shemul-<version>.tar.gz: PASSED
```
