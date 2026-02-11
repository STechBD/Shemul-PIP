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

## 4. Clean old build artifacts

```powershell
Remove-Item -Recurse -Force dist, build, shemul.egg-info -ErrorAction SilentlyContinue
```

## 5. Build package

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

## 6. Validate package metadata

```powershell
python -m twine check dist/*
```

Expected:

```text
Checking dist\shemul-<version>-py3-none-any.whl: PASSED
Checking dist\shemul-<version>.tar.gz: PASSED
```

## 7. Optional TestPyPI publish

```powershell
python -m twine upload --repository testpypi dist/*
```

## 8. Final pre-push sanity

```powershell
git status
```

Confirm only intended release files changed.
