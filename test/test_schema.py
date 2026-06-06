from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

_SCHEMA = json.loads(Path("src/shemul/schema.json").read_text(encoding="utf-8"))


def _validate(instance):
    jsonschema.validate(instance=instance, schema=_SCHEMA)


def test_legacy_101_config_still_validates():
    cfg = {
        "name": "demo",
        "version": "1.0.0",
        "runtime": "python",
        "vars": {"NAME": "x"},
        "env": {"local": {"compose": "docker-compose.yml"}},
        "commands": {
            "dev": {"run": "echo dev", "desc": "d", "group": "core", "confirm": True, "danger": False},
        },
    }
    _validate(cfg)


def test_new_keys_validate():
    cfg = {
        "requires": ">=2.0.0",
        "update_check": False,
        "bin": {"py": {"windows": "python", "default": "python3"}},
        "commands": {
            "run": {
                "run": "{{bin.py}} app.py",
                "os": {"windows": "python app.py"},
                "shell": False,
                "exec": ["python3", "app.py"],
                "needs": ["build"],
                "pre": ["lint"],
                "post": ["notify"],
                "parallel": True,
                "runner": "docker",
            },
            "build": {"run": "echo build"},
            "lint": {"run": "echo lint"},
            "notify": {"run": "echo notify"},
        },
    }
    _validate(cfg)


def test_bad_needs_type_rejected():
    cfg = {"commands": {"c": {"run": "x", "needs": "build"}}}
    with pytest.raises(jsonschema.ValidationError):
        _validate(cfg)


def test_bad_parallel_type_rejected():
    cfg = {"commands": {"c": {"run": "x", "parallel": "yes"}}}
    with pytest.raises(jsonschema.ValidationError):
        _validate(cfg)


def test_unknown_command_key_rejected():
    cfg = {"commands": {"c": {"run": "x", "bogus": 1}}}
    with pytest.raises(jsonschema.ValidationError):
        _validate(cfg)
