"""Run the `loop` shape for real: classify -> plan -> TDD -> validate -> review -> commit.

Shipped by harness-bootstrap into every generated harness that declares a `loop`-shaped
workflow (`harness/drivers/run_plan_build.py`) — the piece that was missing before: a
real, runnable entrypoint wiring `loop_driver.run_loop` to actual Kiro turns (via
`agents.invoke_kiro`) and this harness's own `scripts/validate.sh`, for the canonical
`classify -> plan -> write_tests -> commit_tests -> red -> implement -> green -> validate
-> review -> commit` step sequence `aew-pattern.md` requires and `validate.py` enforces.

Usage (run from the repo root, with `uv pip install -r harness/drivers/requirements.txt`
and `kiro-cli` on PATH)::

    uv run python harness/drivers/run_plan_build.py --issue "<issue text>" [--issue-id ST-42]
    uv run python harness/drivers/run_plan_build.py --issue-file path/to/issue.md

Every agent step's prompt takes one bare `$ARGUMENTS` input in this harness's own
convention (confirmed against the deployed prompts, not assumed): `classify`/`plan` get
the issue text; `write_tests`/`implement` get the plan file path this script wrote from
the `plan` step's `SPEC` envelope; `review` gets the issue plus that path; `commit`/
`commit_tests` get which files to stage, discovered from `git status` (never guessed from
an agent's own prose self-report) plus the issue's id/title/work type.

What this script does NOT invent: `red`/`green`/`validate` run this harness's own
`scripts/validate.sh` and check its exit code — if that script does not exist yet (an
empty validator, no codebase — the normal state for a requirements-only harness), they
report "skipped: no validator yet" rather than silently passing or failing, exactly as
`plan_harness.md` requires the plan's own `validate` step to say.

Every `scripts/validate.sh` invocation is bounded by `VALIDATOR_TIMEOUT` (default 300s,
override via env). A hung validator — a generated test recursively invoking the validator
or test runner itself, a stray network call, anything — fails that step cleanly instead of
hanging the whole driver forever; the timeout kills the *entire* process group `bash`
spawned, not just `bash`, so nothing it started is left running.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
from datetime import datetime, timezone
from typing import List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loop_driver  # noqa: E402
from agents import invoke_kiro, set_audit_sink  # noqa: E402
from audit import AuditSink  # noqa: E402

import prompts  # noqa: E402

PROMPTS_DIR = ".kiro/prompts"
WORKFLOW_PATH = "harness/workflows/plan_build.json"
VALIDATOR = "scripts/validate.sh"
# A hung validator (a generated test recursively invoking the validator/test runner itself,
# a stray network call, anything) must fail this step, not take the whole driver down
# indefinitely — this is what forced a manual `pkill` across a whole orphaned process tree
# during real use, before this existed.
VALIDATOR_TIMEOUT = float(os.getenv("VALIDATOR_TIMEOUT", "300"))


def _git(*args: str) -> Tuple[int, str]:
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def _changed_files() -> List[str]:
    """Every tracked-or-new path with uncommitted changes, via `git status`, never an
    agent's own self-report of what it touched."""
    code, out = _git("status", "--porcelain")
    if code != 0:
        return []
    return [line[3:].strip() for line in out.splitlines() if line.strip()]


def _run_validator_once() -> Tuple[int, str, str]:
    """Run VALIDATOR once, bounded by VALIDATOR_TIMEOUT. On timeout, kills the whole process
    GROUP (`start_new_session=True` + `killpg`), not just the direct `bash` child — a plain
    `subprocess.run(timeout=...)` only kills that one process, leaving anything it spawned
    (e.g. a recursively-invoked `pytest` tree) running and orphaned, exactly what happened
    before this existed."""
    proc = subprocess.Popen(["bash", VALIDATOR], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, start_new_session=True)
    try:
        out, err = proc.communicate(timeout=VALIDATOR_TIMEOUT)
        return proc.returncode, out, err
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
        out, err = proc.communicate()
        detail = (f"{VALIDATOR} exceeded {VALIDATOR_TIMEOUT:.0f}s and was killed (whole "
                 f"process group) — likely hung rather than failed cleanly (e.g. a generated "
                 f"test recursively invoking the validator or test runner itself)")
        return -1, out, f"{detail}\n{err}"


def run_validator(label: str, expect_zero: bool, runs: int = 1) -> Tuple[bool, str]:
    if not os.path.isfile(VALIDATOR):
        return True, f"skipped: no {VALIDATOR} yet (empty validator — see HARNESS.md)"
    for _ in range(runs):
        code, out, err = _run_validator_once()
        ok = (code == 0) == expect_zero
        if not ok:
            return False, f"{label}: exit {code}, expected {'0' if expect_zero else 'non-zero'}\n{out[-2000:]}\n{err[-2000:]}"
    return True, f"{label}: {VALIDATOR} exit matched expectation across {runs} run(s)"


class PlanBuildContext:
    """What `run_agent`/`run_check` need beyond the generic `context` dict: the issue,
    a run-scoped scratch dir for the plan file, and where new test files were discovered."""

    def __init__(self, issue_id: str, issue_text: str, prompts_dir: str, agent: str,
                reviewer: str, run_dir: str):
        self.issue_id = issue_id
        self.issue_text = issue_text
        self.prompts_dir = prompts_dir
        self.agent = agent
        self.reviewer = reviewer
        self.run_dir = run_dir
        self.new_test_files: List[str] = []


def make_run_agent(pbc: PlanBuildContext) -> loop_driver.AgentRunner:
    def run_agent(step: dict, context: dict) -> str:
        name = step["name"]
        prompt = step["prompt"]
        agent = pbc.reviewer if name == "review" else pbc.agent

        if name == "classify":
            rendered = prompts.render(pbc.prompts_dir, prompt, ARGUMENTS=pbc.issue_text)
            reply = invoke_kiro(rendered.text, agent=agent, step="classify", template=prompt,
                                params=rendered.params)
            block = prompts.extract(reply, "CLASSIFICATION")
            if block is None:
                raise RuntimeError("classify_issue reply had no <<<CLASSIFICATION>>> envelope")
            return json.loads(block)["type"]

        if name == "plan":
            rendered = prompts.render(pbc.prompts_dir, prompt, ARGUMENTS=pbc.issue_text)
            reply = invoke_kiro(rendered.text, agent=agent, step="plan", template=prompt,
                                params=rendered.params)
            spec_text = prompts.extract(reply, "SPEC")
            if spec_text is None:
                raise RuntimeError(f"{prompt} reply had no <<<SPEC>>> envelope")
            path = os.path.join(pbc.run_dir, "plan.md")
            os.makedirs(pbc.run_dir, exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(spec_text)
            context["plan_file_path"] = path
            return spec_text

        if name in ("write_tests", "implement"):
            rendered = prompts.render(pbc.prompts_dir, prompt, ARGUMENTS=context["plan_file_path"])
            reply = invoke_kiro(rendered.text, agent=agent, step=name, template=prompt,
                                params=rendered.params)
            if name == "write_tests":
                pbc.new_test_files = _changed_files()
            return reply

        if name == "review":
            payload = json.dumps({"issue": pbc.issue_text, "plan_file_path": context["plan_file_path"]},
                                 indent=2)
            rendered = prompts.render(pbc.prompts_dir, prompt, ARGUMENTS=payload)
            reply = invoke_kiro(rendered.text, agent=agent, step="review", template=prompt,
                                params=rendered.params)
            block = prompts.extract(reply, "REVIEW")
            if block is None:
                raise RuntimeError("review reply had no <<<REVIEW>>> envelope")
            return block

        if name in ("commit_tests", "commit"):
            verdict = context.get("result:review")
            if name == "commit" and verdict is not None and verdict.strip().splitlines()[-1].strip() != "APPROVE":
                raise RuntimeError(f"review did not APPROVE (last line: "
                                   f"{verdict.strip().splitlines()[-1]!r}) — refusing to commit")
            files = pbc.new_test_files if name == "commit_tests" else _changed_files()
            payload = json.dumps({"mode": name, "files": files, "issue_id": pbc.issue_id,
                                  "work_type": context.get("classification")}, indent=2)
            rendered = prompts.render(pbc.prompts_dir, prompt, ARGUMENTS=payload)
            return invoke_kiro(rendered.text, agent=agent, step=name, template=prompt,
                               params=rendered.params)

        raise RuntimeError(f"run_plan_build.py has no wiring for agent step `{name}`")
    return run_agent


def run_check(step: dict, context: dict) -> Tuple[bool, str]:
    name = step["name"]
    if name == "red":
        return run_validator("red", expect_zero=False, runs=2)
    if name == "green":
        return run_validator("green", expect_zero=True, runs=2)
    if name == "validate":
        return run_validator("validate", expect_zero=True, runs=1)
    return True, f"no deterministic check wired for `{name}` — treating as a no-op"


def _run(issue_id: str, issue_text: str, workflow_path: str, prompts_dir: str, agent: str,
        reviewer: str) -> List:
    """Shared core: load the workflow, build the context, run the loop. Raises on any step
    failure (`main()` lets that reach the terminal as a traceback, same as always)."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = os.path.join(".harness-runs", f"{stamp}-{issue_id}")
    set_audit_sink(AuditSink(f"plan_build-{stamp}", base_dir="agents", trigger_type="plan_build"))
    with open(workflow_path, encoding="utf-8") as fh:
        workflow = json.load(fh)
    pbc = PlanBuildContext(issue_id, issue_text, prompts_dir, agent, reviewer, run_dir)
    return loop_driver.run_loop(workflow, {"issue": issue_text}, make_run_agent(pbc), run_check,
                                log=print)


def run_issue(issue_id: str, issue_text: str, *, workflow_path: str = WORKFLOW_PATH,
             prompts_dir: str = PROMPTS_DIR, agent: str = "builder",
             reviewer: str = "reviewer") -> Tuple[bool, List, str]:
    """Run one issue through the full loop without raising — `run_implement.py`'s backlog
    loop needs one bad PBI to come back as `(False, [], detail)`, never a crash that takes
    the rest of the reservoir down with it. `main()` (interactive, single-issue use) calls
    `_run` directly instead, so a human still sees the real traceback."""
    try:
        return True, _run(issue_id, issue_text, workflow_path, prompts_dir, agent, reviewer), ""
    except Exception as e:                          # noqa: BLE001 - isolate one PBI's failure
        return False, [], str(e)


def main(argv: Optional[List[str]] = None) -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--issue")
    p.add_argument("--issue-file")
    p.add_argument("--issue-id", default=None)
    p.add_argument("--workflow", default=WORKFLOW_PATH)
    p.add_argument("--prompts-dir", default=PROMPTS_DIR)
    p.add_argument("--agent", default="builder")
    p.add_argument("--reviewer", default="reviewer")
    args = p.parse_args(argv)

    if args.issue_file:
        with open(args.issue_file, encoding="utf-8") as fh:
            issue_text = fh.read()
    elif args.issue:
        issue_text = args.issue
    else:
        raise SystemExit("need --issue or --issue-file")

    issue_id = args.issue_id or f"issue-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    results = _run(issue_id, issue_text, args.workflow, args.prompts_dir, args.agent, args.reviewer)
    for r in results:
        print(f"{'ok' if r.ok else 'FAILED'}  {r.kind:12s} {r.name}")


if __name__ == "__main__":
    main()
