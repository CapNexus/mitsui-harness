"""Run the `loop` shape for real: classify -> plan -> TDD -> validate -> review -> commit.

Shipped by harness-bootstrap into every generated harness that declares a `loop`-shaped
workflow (`harness/drivers/run_plan_build.py`), and corrected for this harness
(mitsui-harness, 2026-11-19) so it matches the deployed `.kiro/prompts` contracts:

  * every prompt is rendered with the **named variables** its `## Variables` block declares
    (`issue`, `classification`, `plan_file_path`, `base_ref`, `scope`), never a bare
    ARGUMENTS, which those templates reject;
  * the plan step's <<<SPEC>>> envelope is the **path** of the plan file the agent wrote;
  * `plan_exists`, `red` (skipped for TDD-free work types) and `tests_unchanged` are real
    deterministic checks;
  * `commit_tests` records the commit it made, and `commit` refuses unless the review
    ended in APPROVE.

This module is the single source of truth for what each step does. `harness/run_story.py`
(CLI) and Harness Studio (`harness/studio/`) both drive it through `PlanBuildContext`,
`make_run_agent` and `make_run_check`; Studio runs the steps one at a time so it can
checkpoint and resume, but never changes what a step does.

Usage (run from the repo root, with `uv pip install -r harness/drivers/requirements.txt`
and `kiro-cli` on PATH)::

    uv run python harness/drivers/run_plan_build.py --issue "<issue text>" [--issue-id ST-42]
    uv run python harness/drivers/run_plan_build.py --issue-file path/to/issue.md

`red`/`green`/`validate` run this harness's own `scripts/validate.sh` and check its exit
code. If that script does not exist yet they report "skipped: no validator yet".

Every validator run is bounded by `VALIDATOR_TIMEOUT` (default 300s); on timeout the whole
process tree is killed (process group on POSIX, `taskkill /T` on Windows).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import threading
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loop_driver  # noqa: E402
from agents import invoke_kiro, set_audit_sink  # noqa: E402
from audit import AuditSink  # noqa: E402

import prompts  # noqa: E402

PROMPTS_DIR = ".kiro/prompts"
WORKFLOW_PATH = "harness/workflows/plan_build.json"
VALIDATOR = "scripts/validate.sh"
VALIDATOR_TIMEOUT = float(os.getenv("VALIDATOR_TIMEOUT", "300"))

# HARNESS.md "Classifications": the work types with TDD = no. `red` and `tests_unchanged`
# are skipped for them (the plan_build workflow's own check text says so).
NO_TDD = frozenset({
    "human-gated-step", "customer-approval", "documentation", "docs", "harness-feature",
    "harness-prompt", "harness-agent", "harness-classification", "harness-tune",
})

Invoker = Callable[..., str]


# --- process helpers ------------------------------------------------------------------------

def find_bash() -> str:
    """Git Bash on Windows (never WSL's bash.exe), `bash` elsewhere; HARNESS_BASH overrides."""
    explicit = os.getenv("HARNESS_BASH")
    if explicit:
        return explicit
    if os.name == "nt":
        for p in (r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files\Git\usr\bin\bash.exe"):
            if os.path.isfile(p):
                return p
    return "bash"


def kill_tree(proc: subprocess.Popen) -> None:
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, OSError):
        pass


def _git(*args: str, cwd: Optional[str] = None) -> Tuple[int, str]:
    cmd = ["git", "-C", cwd, *args] if cwd else ["git", *args]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout + r.stderr).strip()


def _changed_files(cwd: Optional[str] = None) -> List[str]:
    """Every path with uncommitted changes, from `git status` (never an agent's self-report).
    `-uall` lists files inside new directories instead of the directory."""
    code, out = _git("status", "--porcelain", "-uall", cwd=cwd)
    if code != 0:
        return []
    files = []
    for line in out.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip().strip('"')
        files.append(path.split(" -> ", 1)[1] if " -> " in path else path)
    return files


# --- the run context ------------------------------------------------------------------------

class PlanBuildContext:
    """Everything a step needs beyond the loop's `context` dict.

    `repo_dir` is where git and the validator run (a submodule or the repo root);
    `base_ref` is what the work is compared against. `invoke` sends one agent turn and
    defaults to `agents.invoke_kiro`; `harness/run_story.py` wraps it to add the story's
    repository preamble and the real diff for the review step. `on_output(line)` and
    `on_process(proc_or_None)` let a UI stream validator output and stop it.

    `state()` / `restore()` carry the fields later steps depend on, so a caller that
    checkpoints after each step can resume a run in a new process.
    """

    STATE_FIELDS = ("issue_id", "run_dir", "base_ref", "repo_dir", "new_test_files",
                    "tests_commit", "tests_status")

    def __init__(self, issue_id: str, issue_text: str, prompts_dir: str, agent: str,
                 reviewer: str, run_dir: str, *, base_ref: Optional[str] = None,
                 repo_dir: Optional[str] = None, invoke: Optional[Invoker] = None,
                 validator: Optional[str] = None,
                 on_output: Optional[Callable[[str], None]] = None,
                 on_process: Optional[Callable[[Optional[subprocess.Popen]], None]] = None):
        self.issue_id = issue_id
        self.issue_text = issue_text
        self.prompts_dir = prompts_dir
        self.agent = agent
        self.reviewer = reviewer
        self.run_dir = run_dir
        self.base_ref = base_ref or os.getenv("VALIDATE_BASE_REF") or "HEAD"
        self.repo_dir = repo_dir or os.getenv("HARNESS_TARGET_REPO") or os.getcwd()
        self.invoke: Invoker = invoke or invoke_kiro
        self.validator = validator or VALIDATOR
        self.on_output = on_output
        self.on_process = on_process
        self.new_test_files: List[str] = []
        self.tests_commit: Optional[str] = None
        self.tests_status: Optional[str] = None

    def state(self) -> Dict[str, object]:
        return {k: getattr(self, k) for k in self.STATE_FIELDS}

    def restore(self, state: Dict[str, object]) -> "PlanBuildContext":
        for k in self.STATE_FIELDS:
            if k in state:
                setattr(self, k, state[k])
        return self

    def git(self, *args: str) -> Tuple[int, str]:
        return _git(*args, cwd=self.repo_dir)

    def head(self) -> str:
        return self.git("rev-parse", "HEAD")[1]


# --- validator ------------------------------------------------------------------------------

def _run_validator_once(pbc: Optional[PlanBuildContext]) -> Tuple[int, str]:
    validator = pbc.validator if pbc else VALIDATOR
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0  # type: ignore[attr-defined]
    proc = subprocess.Popen([find_bash(), validator], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                            errors="replace", creationflags=flags,
                            start_new_session=(os.name != "nt"))
    if pbc and pbc.on_process:
        pbc.on_process(proc)
    timed_out = threading.Event()

    def _timeout() -> None:
        timed_out.set()
        kill_tree(proc)

    timer = threading.Timer(VALIDATOR_TIMEOUT, _timeout)
    timer.start()
    lines: List[str] = []
    try:
        for line in proc.stdout:  # type: ignore[union-attr]
            line = line.rstrip("\n")
            lines.append(line)
            if pbc and pbc.on_output:
                pbc.on_output(line)
        code = proc.wait()
    finally:
        timer.cancel()
        if proc.stdout:
            proc.stdout.close()
        if pbc and pbc.on_process:
            pbc.on_process(None)
    out = "\n".join(lines)
    if timed_out.is_set():
        return -1, (f"{validator} exceeded {VALIDATOR_TIMEOUT:.0f}s and was killed (whole process "
                    f"tree) — likely hung rather than failed cleanly\n{out}")
    return code, out


def run_validator(label: str, expect_zero: bool, runs: int = 1,
                  pbc: Optional[PlanBuildContext] = None) -> Tuple[bool, str]:
    validator = pbc.validator if pbc else VALIDATOR
    if not os.path.isfile(validator):
        return True, f"skipped: no {validator} yet (empty validator — see HARNESS.md)"
    for _ in range(runs):
        code, out = _run_validator_once(pbc)
        if (code == 0) != expect_zero:
            return False, f"{label}: exit {code}, expected {'0' if expect_zero else 'non-zero'}\n{out[-4000:]}"
    return True, f"{label}: {validator} exit matched expectation across {runs} run(s)"


# --- agent steps ----------------------------------------------------------------------------

def _resolve_plan(path_line: str, pbc: PlanBuildContext) -> Optional[str]:
    """The plan templates reply with the repo-relative path of the plan file they wrote.
    Accept it relative to the process cwd (the parent repo) or to the target repo."""
    p = path_line.strip().strip("`").replace("\\", "/")
    for base in (os.getcwd(), pbc.repo_dir):
        cand = os.path.normpath(os.path.join(base, p))
        if os.path.isfile(cand):
            return os.path.relpath(cand, os.getcwd()).replace(os.sep, "/")
    return None


def make_run_agent(pbc: PlanBuildContext) -> loop_driver.AgentRunner:
    def run_agent(step: dict, context: dict) -> str:
        name = step["name"]
        template = step["prompt"]
        # The workflow names the tool boundary per step; the read-only reviewer for
        # `classify` and `review`, the builder for the rest.
        agent = pbc.reviewer if step.get("agent") == "reviewer" else pbc.agent

        def ask(**values: object) -> str:
            rendered = prompts.render(pbc.prompts_dir, template, **values)
            return pbc.invoke(rendered.text, agent=agent, step=name, template=template,
                              params=rendered.params)

        if name == "classify":
            block = prompts.extract(ask(issue=pbc.issue_text), "CLASSIFICATION")
            if block is None:
                raise RuntimeError("classify_issue reply had no <<<CLASSIFICATION>>> envelope")
            info = json.loads(block)
            context["classification_info"] = info
            return info["type"]

        if name == "plan":
            spec = prompts.extract(ask(issue=pbc.issue_text, classification=context["classification"]),
                                   "SPEC")
            if spec is None:
                raise RuntimeError(f"{template} reply had no <<<SPEC>>> envelope")
            line = next((ln for ln in spec.splitlines() if ln.strip()), "")
            path = _resolve_plan(line, pbc)
            if path is None:
                raise RuntimeError(f"plan file `{line.strip()}` from <<<SPEC>>> does not exist")
            context["plan_file_path"] = path
            return path

        if name == "write_tests":
            reply = ask(plan_file_path=context["plan_file_path"])
            block = prompts.extract(reply, "TESTS")
            tests = json.loads(block) if block else {}
            context["tests"] = tests
            pbc.tests_status = tests.get("status")
            pbc.new_test_files = _changed_files(pbc.repo_dir)
            return reply

        if name == "implement":
            return ask(plan_file_path=context["plan_file_path"])

        if name == "review":
            block = prompts.extract(ask(plan_file_path=context["plan_file_path"], base_ref=pbc.base_ref),
                                    "REVIEW")
            if block is None:
                raise RuntimeError("review reply had no <<<REVIEW>>> envelope")
            return block

        if name in ("commit_tests", "commit"):
            if name == "commit":
                verdict = (context.get("result:review") or "").strip().splitlines()
                last = verdict[-1].strip() if verdict else ""
                if last != "APPROVE":
                    raise RuntimeError(f"review did not APPROVE (last line: {last!r}) — refusing to commit")
            if name == "commit_tests" and (context.get("classification") in NO_TDD
                                           or pbc.tests_status == "skipped" or not pbc.new_test_files):
                return "skipped: no tests to commit for this work type"
            if not _changed_files(pbc.repo_dir):
                # e.g. a re-run after a human already committed the change themselves
                return "skipped: nothing left to commit"
            before = pbc.head()
            reply = ask(plan_file_path=context["plan_file_path"],
                        scope="tests" if name == "commit_tests" else "full")
            after = pbc.head()
            if after == before:
                raise RuntimeError(f"{name}: the agent made no commit")
            if name == "commit_tests":
                pbc.tests_commit = after
            context[f"{name}_sha"] = after
            return reply

        raise RuntimeError(f"run_plan_build.py has no wiring for agent step `{name}`")
    return run_agent


# --- deterministic checks -------------------------------------------------------------------

def make_run_check(pbc: Optional[PlanBuildContext]) -> loop_driver.CheckRunner:
    def run_check(step: dict, context: dict) -> Tuple[bool, str]:
        name = step["name"]
        tdd_off = context.get("classification") in NO_TDD or (pbc and pbc.tests_status == "skipped")

        if name == "plan_exists":
            path = context.get("plan_file_path") or ""
            text = ""
            if path and os.path.isfile(path):
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
            problems = []
            if not text:
                problems.append(f"plan file `{path}` missing")
            elif pbc and not pbc.issue_id.startswith("issue-") and pbc.issue_id not in text:
                problems.append(f"plan does not cite {pbc.issue_id}")
            if text and not re.search(r"^\s*\d+[.)].*\bshall\b", text, re.M | re.I):
                problems.append("no numbered criterion containing 'shall'")
            return (not problems), ("; ".join(problems) or "plan cites the story and has numbered 'shall' criteria")

        if name == "red":
            if tdd_off:
                return True, "skipped: no TDD for this work type or tests were skipped"
            return run_validator("red", expect_zero=False, runs=2, pbc=pbc)

        if name == "tests_unchanged":
            if not pbc or not pbc.tests_commit:
                return True, "skipped: commit_tests made no commit"
            _, files = pbc.git("show", "--name-only", "--format=", pbc.tests_commit)
            paths = [f for f in files.splitlines() if f.strip()]
            if not paths:
                return True, "skipped: the tests commit has no files"
            code, out = pbc.git("diff", "--name-only", pbc.tests_commit, "--", *paths)
            changed = [f for f in out.splitlines() if f.strip()]
            if code != 0 or changed:
                return False, "implement changed files committed by commit_tests: " + ", ".join(changed or [out])
            return True, f"{len(paths)} file(s) from commit_tests byte-identical"

        if name == "green":
            return run_validator("green", expect_zero=True, runs=2, pbc=pbc)
        if name == "validate":
            return run_validator("validate", expect_zero=True, runs=1, pbc=pbc)
        return True, f"no deterministic check wired for `{name}` — treating as a no-op"
    return run_check


# Backward-compatible module-level check (no context): validator checks only.
run_check = make_run_check(None)


# --- entrypoints ----------------------------------------------------------------------------

def load_workflow(workflow_path: str = WORKFLOW_PATH) -> dict:
    with open(workflow_path, encoding="utf-8") as fh:
        return json.load(fh)


def run_step(workflow: dict, step: dict, context: dict, pbc: PlanBuildContext,
             log: Callable[[str], None] = lambda m: None) -> loop_driver.StepResult:
    """Run ONE workflow step with the same semantics as the full loop (classify sets
    `classification`, agent replies land in `result:<step>`, failed checks raise
    `LoopFailed`). Used by callers that checkpoint between steps."""
    single = {**workflow, "steps": [step]}
    return loop_driver.run_loop(single, context, make_run_agent(pbc), make_run_check(pbc), log=log)[0]


def run_pbc(pbc: PlanBuildContext, workflow_path: str = WORKFLOW_PATH,
            log: Callable[[str], None] = print) -> List[loop_driver.StepResult]:
    return loop_driver.run_loop(load_workflow(workflow_path), {"issue": pbc.issue_text},
                                make_run_agent(pbc), make_run_check(pbc), log=log)


def _run(issue_id: str, issue_text: str, workflow_path: str, prompts_dir: str, agent: str,
         reviewer: str) -> List:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = os.path.join(".harness-runs", f"{stamp}-{issue_id}")
    set_audit_sink(AuditSink(f"plan_build-{stamp}", base_dir="agents", trigger_type="plan_build"))
    pbc = PlanBuildContext(issue_id, issue_text, prompts_dir, agent, reviewer, run_dir)
    return run_pbc(pbc, workflow_path)


def run_issue(issue_id: str, issue_text: str, *, workflow_path: str = WORKFLOW_PATH,
              prompts_dir: str = PROMPTS_DIR, agent: str = "builder",
              reviewer: str = "reviewer") -> Tuple[bool, List, str]:
    """Run one issue through the full loop without raising — `run_implement.py`'s backlog
    loop needs one bad PBI to come back as `(False, [], detail)`."""
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
