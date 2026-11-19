"""Generic Loop-shaped AEW driver.

Shipped verbatim by harness-bootstrap into every generated harness that declares a
workflow with `"shape": "loop"` (`harness/drivers/loop_driver.py`) — not written per
harness. It runs the ordered step list of ``harness/workflows/<name>.json``: one fresh
agent session per `kind: "agent"` step, a deterministic check between steps, in the
order the plan declared (classify -> plan -> write_tests -> commit_tests -> red ->
implement -> green -> validate -> review -> commit, or any workflow shaped like it).

This module is pure control flow. Every harness-specific action — how to actually
invoke an agent, what a deterministic check actually runs (tests, `scripts/validate.sh`,
a git diff) — is injected by the caller, the same way `bootstrap/frame.py`'s
`run_frame` takes `ask_triage` / `ask_decompose` as parameters instead of hardcoding a
transport. Wiring `run_agent` to a real agent CLI (Kiro, Claude Code, ...) is a separate,
one-time integration a person writes for this harness; this module never guesses it.

No third-party imports, no dependency on `bootstrap` — this file runs standalone inside
whatever repository the generated harness targets.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

AgentRunner = Callable[[dict, dict], str]
CheckRunner = Callable[[dict, dict], Tuple[bool, str]]
HumanGate = Callable[[dict, dict], Tuple[bool, str]]


class LoopFailed(RuntimeError):
    """A step could not complete. ``step`` and ``detail`` say which and why."""

    def __init__(self, step: str, detail: str):
        super().__init__(f"{step}: {detail}")
        self.step = step
        self.detail = detail


@dataclass
class StepResult:
    name: str
    kind: str
    ok: bool
    detail: str = ""


def load_workflow(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        wf = json.load(fh)
    if wf.get("shape") != "loop":
        raise ValueError(f"{path}: shape is {wf.get('shape')!r}, not 'loop'")
    return wf


def _prompt_for(step: dict, context: dict) -> str:
    """Which prompt an agent step runs: its fixed `prompt`, or `prompt_map` keyed by the
    classification the workflow's own `classify` step already put in the context."""
    if step.get("prompt_map"):
        classification = context.get("classification")
        if not classification or classification not in step["prompt_map"]:
            raise LoopFailed(step["name"],
                              f"no prompt_map entry for classification {classification!r}")
        return step["prompt_map"][classification]
    if not step.get("prompt"):
        raise LoopFailed(step["name"], "agent step has neither `prompt` nor `prompt_map`")
    return step["prompt"]


def run_loop(workflow: dict, context: dict, run_agent: AgentRunner, run_check: CheckRunner,
             run_human: Optional[HumanGate] = None,
             log: Callable[[str], None] = lambda m: None) -> List[StepResult]:
    """Run every step of a loop-shaped workflow, in order.

    ``context`` is a plain dict the caller seeds (e.g. ``{"issue": ...}``); this function
    reads and writes it as steps run. The `classify` step's reply, once ``run_agent`` has
    parsed its envelope, is expected back as the bare classification token — this is what
    later `prompt_map` steps route on, stored under ``context["classification"]``.

    Every other agent step's reply is stashed under ``context[f"result:{step name}"]`` so
    later steps (and the caller, after the run) can see what happened. A deterministic or
    human step returning not-ok stops the run and raises `LoopFailed` — nothing here
    retries silently; the driver never tells a human a step passed when it did not.
    """
    if workflow.get("shape") != "loop":
        raise ValueError(f"run_loop given a workflow of shape {workflow.get('shape')!r}")
    results: List[StepResult] = []
    for step in workflow["steps"]:
        log(f"== {step['name']}")
        kind = step["kind"]
        if kind == "agent":
            prompt = _prompt_for(step, context)
            reply = run_agent({**step, "prompt": prompt}, context)
            context[f"result:{step['name']}"] = reply
            if step["name"] == "classify":
                context["classification"] = reply.strip()
            results.append(StepResult(step["name"], "agent", True, prompt))
        elif kind == "deterministic":
            ok, detail = run_check(step, context)
            results.append(StepResult(step["name"], "deterministic", ok, detail))
            if not ok:
                raise LoopFailed(step["name"], detail)
        elif kind == "human":
            if run_human is None:
                raise LoopFailed(step["name"], "workflow has a human step but no run_human was given")
            ok, detail = run_human(step, context)
            results.append(StepResult(step["name"], "human", ok, detail))
            if not ok:
                raise LoopFailed(step["name"], detail)
        else:
            raise LoopFailed(step["name"], f"unknown step kind {kind!r}")
    return results
