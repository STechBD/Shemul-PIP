# Local Release Checklist

Use this checklist before pushing release changes to GitHub.

## 1. Activate virtual environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Expected:

```text
(.venv) ...>
```

## 2. Keep version aligned

Update both files with the same version:

1. `pyproject.toml` -> `[project].version`
2. `src/shemul/version.py` -> `__version__`

## 3. Run tests

```powershell
python -m pytest -q
```

Expected:

```text
... passed
```

## 4. Smoke test CLI from source (no install)

Windows PowerShell:

```powershell
$env:PYTHONPATH="src"
python -m shemul.cli --help
python -m shemul.cli info
```

Linux (bash/zsh):

```bash
PYTHONPATH=src python -m shemul.cli --help
PYTHONPATH=src python -m shemul.cli info
```

Expected:

```text
Usage: shemul (options) <command> (args)
... Info panel ...
```

## 5. Clean old build artifacts

```powershell
Remove-Item -Recurse -Force dist, build, shemul.egg-info -ErrorAction SilentlyContinue
```

## 6. Build package

```powershell
python -m pip install --upgrade pip
python -m pip install --upgrade build twine
python -m build
```

Expected install output (sample):

```text
Requirement already satisfied: pip ...
Successfully installed build-... twine-...
```

Expected build output (key lines):

```text
* Creating isolated environment: venv+pip...
* Building sdist...
* Building wheel...
Successfully built shemul-<version>.tar.gz and shemul-<version>-py3-none-any.whl
```

Expected files:

1. `dist/shemul-<version>.tar.gz`
2. `dist/shemul-<version>-py3-none-any.whl`

## 7. Validate package metadata

```powershell
python -m twine check dist/*
```

Expected:

```text
Checking dist\shemul-<version>-py3-none-any.whl: PASSED
Checking dist\shemul-<version>.tar.gz: PASSED
```

## 8. Optional TestPyPI publish

```powershell
python -m twine upload --repository testpypi dist/*
```

## 9. Final pre-push sanity

```powershell
git status
```

Confirm only intended release files changed.
