from __future__ import annotations

from pathlib import Path


def test_pyproject_does_not_use_deprecated_license_classifier():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'license = "MIT"' in pyproject
    assert "License :: OSI Approved :: MIT License" not in pyproject

