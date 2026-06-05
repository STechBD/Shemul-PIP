from __future__ import annotations

from pathlib import Path

import pytest

from shemul.config import ShemulConfig
from shemul.planner import CycleError, Planner, has_planner_keys


class _UI:
    def error(self, m):
        pass


class FakeApp:
    def __init__(self, codes=None):
        self.ran = []
        self.codes = codes or {}
        self.ui = _UI()

    def _run_single(self, config, name, *, dry, trace, extra_args):
        self.ran.append(name)
        return self.codes.get(name, 0)


def _config(commands):
    return ShemulConfig(raw={"commands": commands}, path=Path("x"))


def test_has_planner_keys():
    assert has_planner_keys({"run": "x", "needs": ["a"]})
    assert not has_planner_keys({"run": "x"})


def test_needs_pre_main_post_order():
    config = _config(
        {
            "main": {"run": "m", "needs": ["b"], "pre": ["p"], "post": ["q"]},
            "b": {"run": "b"},
            "p": {"run": "p"},
            "q": {"run": "q"},
        }
    )
    app = FakeApp()
    result = Planner(app).run(config, "main")
    assert result.return_code == 0
    assert app.ran == ["b", "p", "main", "q"]


def test_cycle_detection():
    config = _config(
        {
            "a": {"run": "a", "needs": ["b"]},
            "b": {"run": "b", "needs": ["a"]},
        }
    )
    with pytest.raises(CycleError):
        Planner(FakeApp()).run(config, "a")


def test_nonzero_need_aborts_main():
    config = _config(
        {
            "main": {"run": "m", "needs": ["bad"]},
            "bad": {"run": "bad"},
        }
    )
    app = FakeApp(codes={"bad": 2})
    result = Planner(app).run(config, "main")
    assert result.return_code == 2
    assert "main" not in app.ran


def test_nonzero_main_skips_post():
    config = _config(
        {
            "main": {"run": "m", "post": ["q"]},
            "q": {"run": "q"},
        }
    )
    app = FakeApp(codes={"main": 3})
    result = Planner(app).run(config, "main")
    assert result.return_code == 3
    assert "q" not in app.ran


def test_parallel_runs_all_needs():
    config = _config(
        {
            "main": {"run": "m", "needs": ["n1", "n2"], "parallel": True},
            "n1": {"run": "n1"},
            "n2": {"run": "n2"},
        }
    )
    app = FakeApp()
    result = Planner(app).run(config, "main")
    assert result.return_code == 0
    assert set(app.ran) == {"n1", "n2", "main"}


def test_dedup_runs_shared_dep_once():
    config = _config(
        {
            "main": {"run": "m", "needs": ["a", "b"]},
            "a": {"run": "a", "needs": ["shared"]},
            "b": {"run": "b", "needs": ["shared"]},
            "shared": {"run": "s"},
        }
    )
    app = FakeApp()
    Planner(app).run(config, "main")
    assert app.ran.count("shared") == 1
