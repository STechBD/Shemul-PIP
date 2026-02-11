from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from shemul.template import resolve_template_key, write_template_file


def test_template_alias_resolution():
    assert resolve_template_key("docker fastapi backend") == "docker-fastapi-backend"
    assert resolve_template_key("next.js frontend") == "nextjs-frontend"
    assert resolve_template_key("none") == "none"


def test_write_template_file_creates_valid_shape():
    temp_dir = Path(".tmp_test") / f"template_{uuid.uuid4().hex}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    try:
        target = temp_dir / "shemul.json"
        write_template_file("fastapi-backend", target, "demo")
        text = target.read_text(encoding="utf-8")
        assert '"name": "demo"' in text
        assert '"commands"' in text
        assert '"dev"' in text
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_write_template_file_respects_force_flag():
    temp_dir = Path(".tmp_test") / f"template_{uuid.uuid4().hex}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    try:
        target = temp_dir / "shemul.json"
        write_template_file("none", target, "demo")
        failed = False
        try:
            write_template_file("none", target, "demo")
        except FileExistsError:
            failed = True
        assert failed is True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
