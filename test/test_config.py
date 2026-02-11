from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from shemul.config import ConfigLoader


def test_schema_loads():
    temp_dir = Path(".tmp_test") / f"schema_{uuid.uuid4().hex}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    try:
        schema_path = temp_dir / "schema.json"
        schema_path.write_text('{"type":"object"}', encoding="utf-8")
        loader = ConfigLoader(schema_path)
        assert loader.schema_text().strip() == '{"type":"object"}'
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
