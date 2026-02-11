# Publish Troubleshooting

## Error: `InvalidConfigError` about license classifiers

If GitHub Actions fails at `python -m build` with:

`License classifiers have been superseded by license expressions`

then fix `pyproject.toml`:

1. Keep SPDX license expression:
   - `license = "MIT"`
2. Remove deprecated classifier from `[project].classifiers`:
   - `License :: OSI Approved :: MIT License`

## Why this happens

Recent `setuptools` versions enforce PEP 639 behavior and reject legacy license classifiers when using license expressions.

## Verify locally before pushing

Run this exact sequence:

```powershell
.\.venv\Scripts\python -m pytest -q
Remove-Item -Recurse -Force dist, build, shemul.egg-info -ErrorAction SilentlyContinue
.\.venv\Scripts\python -m build
.\.venv\Scripts\python -m twine check dist/*
```

If all pass, your publish workflow should pass the build step on GitHub Actions.

## Error: `No module named build`

Symptom:

```text
python.exe: No module named build
```

Fix:

```powershell
python -m pip install --upgrade pip
python -m pip install --upgrade build twine
```

Expected:

```text
Successfully installed build-... twine-...
```

## Known-good local sequence (verified)

```powershell
python -m pip install --upgrade pip
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

Expected key results:

1. `python -m build` ends with:
   - `Successfully built shemul-<version>.tar.gz and shemul-<version>-py3-none-any.whl`
2. `python -m twine check dist/*` ends with:
   - `Checking dist\shemul-<version>-py3-none-any.whl: PASSED`
   - `Checking dist\shemul-<version>.tar.gz: PASSED`

## Quick diagnosis table

1. `No module named build`
   - Cause: `build` not installed in current interpreter/venv
   - Fix: `python -m pip install --upgrade build`
2. `License classifiers have been superseded by license expressions`
   - Cause: deprecated license classifier still present in `pyproject.toml`
   - Fix: remove `License :: OSI Approved :: MIT License` and keep `license = "MIT"`
3. `twine check` fails
   - Cause: broken metadata/readme
   - Fix: read exact `twine check` error, then correct `pyproject.toml` or `README.md`, rebuild, re-check

## Important: GitHub Release uses tag snapshot

If local build passes but GitHub Release publish fails with old metadata, the release tag likely points to an older commit.

Check locally:

```powershell
git fetch --tags
git show <tag>:pyproject.toml
```

If that file still contains deprecated classifier, create a new tag from the fixed commit and publish a new release.
