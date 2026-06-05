from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


class CycleError(Exception):
    """Raised when command dependencies form a cycle."""


PLANNER_KEYS = ("needs", "pre", "post", "parallel")


@dataclass
class PlanResult:
    return_code: int
    ran: List[str] = field(default_factory=list)


def has_planner_keys(cmd_cfg: dict) -> bool:
    return any(key in cmd_cfg for key in PLANNER_KEYS)


class Planner:
    def __init__(self, app) -> None:
        self.app = app
        self._visited: set = set()
        self._lock = threading.Lock()

    def _deps(self, config, name: str) -> Tuple[List[str], List[str], List[str], bool]:
        cfg = config.commands.get(name, {})
        needs = list(cfg.get("needs", []) or [])
        pre = list(cfg.get("pre", []) or [])
        post = list(cfg.get("post", []) or [])
        parallel = bool(cfg.get("parallel", False))
        return needs, pre, post, parallel

    def run(
        self,
        config,
        name: str,
        *,
        dry: bool = False,
        trace: bool = False,
        extra_args: Optional[List[str]] = None,
        _stack: Tuple[str, ...] = (),
    ) -> PlanResult:
        if name in _stack:
            raise CycleError(" -> ".join([*_stack, name]))
        if name not in config.commands:
            self.app.ui.error(f"Unknown command: {name}")
            return PlanResult(1, [])

        ran: List[str] = []
        needs, pre, post, parallel = self._deps(config, name)
        new_stack = (*_stack, name)

        code = self._run_group(config, needs, parallel, dry, trace, new_stack, ran)
        if code != 0:
            return PlanResult(code, ran)

        code = self._run_group(config, pre, False, dry, trace, new_stack, ran)
        if code != 0:
            return PlanResult(code, ran)

        with self._lock:
            already = name in self._visited
        if not already:
            code = self.app._run_single(config, name, dry=dry, trace=trace, extra_args=list(extra_args or []))
            ran.append(name)
            if code != 0:
                return PlanResult(code, ran)
            with self._lock:
                self._visited.add(name)

        code = self._run_group(config, post, False, dry, trace, new_stack, ran)
        if code != 0:
            return PlanResult(code, ran)

        return PlanResult(0, ran)

    def _run_group(self, config, names, parallel, dry, trace, stack, ran) -> int:
        if not names:
            return 0

        if parallel and len(names) > 1:
            results: List[PlanResult] = []
            with ThreadPoolExecutor(max_workers=min(len(names), 8)) as pool:
                futures = [
                    pool.submit(self.run, config, n, dry=dry, trace=trace, extra_args=None, _stack=stack)
                    for n in names
                ]
                for future in futures:
                    res = future.result()
                    results.append(res)
            for res in results:
                ran.extend(res.ran)
            for res in results:
                if res.return_code != 0:
                    return res.return_code
            return 0

        for n in names:
            res = self.run(config, n, dry=dry, trace=trace, extra_args=None, _stack=stack)
            ran.extend(res.ran)
            if res.return_code != 0:
                return res.return_code
        return 0
