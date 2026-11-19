"""Run story analysis and the plan_build loop in the background, checkpointed in harness-db.

Kiro is the only agent (harness/drivers/agents.invoke_kiro, `kiro-cli acp`). The shipped
drivers and run_story.py are imported, never edited: they are in the answer key.

Differences from `run_story.py run`, all deliberate:
  * Prompts are rendered with the named variables each .kiro/prompts template declares
    (the shipped run_plan_build.py passes a bare ARGUMENTS, which these templates reject).
  * The plan step's <<<SPEC>>> envelope is the path of the plan file the agent wrote, as the
    plan templates specify.
  * No agent commits. `commit_tests` is replaced by a hash snapshot of the test files, which
    `tests_unchanged` compares after `implement`; the final `commit` is a human review gate.
  * Every step is checkpointed, so a stopped, failed or interrupted run resumes from the
    first step that did not finish.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import traceback
from typing import Any, Dict, List, Optional, Tuple

import catalog
from catalog import ROOT
from db import DB

sys.path.insert(0, os.path.join(ROOT, "harness", "drivers"))
import agents  # noqa: E402  (shipped, unchanged)
import prompts  # noqa: E402
from audit import AuditSink, StepAudit  # noqa: E402

import run_story  # noqa: E402  (imported via catalog's sys.path)

KIRO_PROMPTS = os.path.join(ROOT, ".kiro", "prompts")
STUDIO_PROMPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")
WORKFLOW = os.path.join(ROOT, "harness", "workflows", "plan_build.json")
VALIDATOR = os.path.join(ROOT, "scripts", "validate.sh")
VALIDATOR_TIMEOUT = float(os.getenv("VALIDATOR_TIMEOUT", "600"))
AUDIT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "audit")
CONFIDENCE_THRESHOLD = 80
CHARS_PER_TOKEN = 4

# HARNESS.md "Classifications": TDD = no.
NO_TDD = {"human-gated-step", "customer-approval", "documentation", "docs", "harness-feature",
          "harness-prompt", "harness-agent", "harness-classification", "harness-tune"}


def find_bash() -> str:
    explicit = os.getenv("HARNESS_BASH")
    if explicit:
        return explicit
    if os.name == "nt":
        for p in (r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files\Git\usr\bin\bash.exe"):
            if os.path.isfile(p):
                return p
    return shutil.which("bash") or "bash"


class Stopped(Exception):
    pass


class StepFailed(Exception):
    pass


# --- live console + token capture from Kiro's ACP stream ----------------------------------

class StudioSink(AuditSink):
    """The shipped audit sink (raw JSONL + summaries under data/audit), plus a live copy of
    each agent turn into harness-db for the console and the token meter."""

    def __init__(self, db: DB, run_id: str) -> None:
        super().__init__(run_id, base_dir=AUDIT_DIR, trigger_type="studio")
        self.db = db
        self.run_id = run_id
        self.step_idx = 0
        self.step_name = ""

    def start_step(self, step: str) -> StepAudit:
        with self._lock:
            self._step_index += 1
            idx = self._step_index
        return StudioStepAudit(self, idx, step)


class StudioStepAudit(StepAudit):
    def __init__(self, sink: StudioSink, index: int, step: str) -> None:
        super().__init__(sink, index, step)
        self._studio = sink
        self._buf = {"agent": "", "thought": ""}
        self._in_chars = 0
        self._out_chars = 0
        self._tool_state: Dict[str, str] = {}

    def _emit(self, kind: str, text: str) -> None:
        if text.strip():
            self._studio.db.event(self._studio.run_id, kind, text.rstrip(), self._studio.step_name)

    def _feed(self, kind: str, text: str) -> None:
        self._out_chars += len(text)
        buf = self._buf[kind] + text
        if "\n" in buf:
            head, buf = buf.rsplit("\n", 1)
            self._emit(kind, head)
        elif len(buf) > 600:
            self._emit(kind, buf)
            buf = ""
        self._buf[kind] = buf

    def record(self, event_type: str, payload: Any) -> None:
        super().record(event_type, payload)
        if event_type == "prompt" and isinstance(payload, dict):
            n = len(str(payload.get("text", "")))
            self._in_chars += n
            self._emit("info", f"prompt sent ({n:,} chars, template {payload.get('template')})")

    def add_assistant_text(self, text: str) -> None:
        super().add_assistant_text(text)
        self._feed("agent", text)

    def add_thinking_text(self, text: str) -> None:
        super().add_thinking_text(text)
        self._feed("thought", text)

    def upsert_tool_call(self, data: Dict[str, Any]) -> None:
        super().upsert_tool_call(data)
        tid = str(data.get("tool_call_id") or data.get("toolCallId") or "")
        status = str(data.get("status") or "")
        title = data.get("title") or self._tool_state.get(tid + ":title") or "tool"
        if data.get("title"):
            self._tool_state[tid + ":title"] = data["title"]
        for key, into in (("raw_input", "out"), ("raw_output", "in"), ("content", "in")):
            if data.get(key) is not None:
                n = len(json.dumps(data[key], default=str))
                if into == "in":
                    self._in_chars += n
                else:
                    self._out_chars += n
        if self._tool_state.get(tid) != status:
            self._tool_state[tid] = status
            self._emit("tool", f"{title} [{status or 'started'}]")

    def add_permission(self, tool: str, decision: str, option: Optional[str]) -> None:
        super().add_permission(tool, decision, option)
        if decision != "allowed":
            self._emit("warn", f"permission {decision}: {tool}")

    def finalize(self, stop_reason: Optional[str], usage: Optional[Dict[str, Any]]) -> None:
        super().finalize(stop_reason, usage)
        for kind in ("agent", "thought"):
            if self._buf[kind]:
                self._emit(kind, self._buf[kind])
                self._buf[kind] = ""
        u = usage or self.usage or {}
        if isinstance(u.get("input_tokens"), int) and isinstance(u.get("output_tokens"), int):
            inp, out, reported = u["input_tokens"], u["output_tokens"], True
        else:
            inp = -(-self._in_chars // CHARS_PER_TOKEN)
            out = -(-self._out_chars // CHARS_PER_TOKEN)
            reported = False
        self._studio.db.add_tokens(self._studio.run_id, self._studio.step_idx, inp, out, reported)
        self._emit("info", f"turn ended: {stop_reason}; tokens in {inp:,} / out {out:,}"
                           + ("" if reported else " (estimated)"))


# --- the runner ---------------------------------------------------------------------------

def implementation_steps() -> List[dict]:
    with open(WORKFLOW, encoding="utf-8") as fh:
        wf = json.load(fh)
    steps = [dict(s) for s in wf["steps"] if s["name"] not in ("commit_tests", "commit")]
    steps.append({"name": "human_review", "kind": "human", "prompt": None, "prompt_map": None,
                  "agent": None, "check": "a human reviews the diff and commits"})
    return steps


ANALYSIS_STEPS = [
    {"name": "readiness", "kind": "deterministic", "check": "story, dependency and parameter facts"},
    {"name": "analyze", "kind": "agent", "agent": "reviewer", "prompt": "analyze_story"},
    {"name": "score", "kind": "deterministic", "check": "combine agent and readiness scores"},
]


class Runner:
    def __init__(self, db: DB) -> None:
        self.db = db
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._active: Optional[str] = None
        self._stop = threading.Event()
        self._proc: Optional[subprocess.Popen] = None

    # --- public API -----------------------------------------------------------------------

    @property
    def active(self) -> Optional[str]:
        return self._active if self._thread and self._thread.is_alive() else None

    def start_analysis(self, sid: str) -> str:
        stories = catalog.load_stories()
        if sid not in stories:
            raise ValueError(f"unknown story {sid}")
        rid = self.db.create_run(sid, "analysis")
        self.db.init_steps(rid, ANALYSIS_STEPS)
        self._launch(rid)
        return rid

    def preflight(self, sid: str, branch: str, confidence_override: Optional[str]) -> Tuple[List[str], dict]:
        """Everything run_story.py checks, plus the confidence gate. Returns (errors, info)."""
        errors: List[str] = []
        stories = catalog.load_stories()
        if sid not in stories:
            return [f"unknown story {sid}"], {}
        meta = stories[sid]["meta"]
        if meta.get("executor") == "human":
            errors.append(f"{sid} is executor: human; the harness does not run it")
        if os.getenv("AEW_AUTO_APPROVE", "").lower() not in ("1", "true", "yes"):
            errors.append("start the server with AEW_AUTO_APPROVE=1; without it Kiro denies every "
                          "write and shell call")
        if not shutil.which(os.getenv("KIRO_CLI_PATH", "kiro-cli")):
            errors.append("kiro-cli is not on PATH")
        try:
            target = catalog.target_dir(meta)
        except ValueError as e:
            return errors + [str(e)], {}
        if not os.path.exists(os.path.join(target, ".git")):
            errors.append(f"{catalog.rel(target)} is not checked out (git submodule update --init)")
            return errors, {}
        dirty = catalog.dirty_files(target)
        if dirty:
            errors.append(f"{catalog.rel(target)} has uncommitted changes; commit or stash them so "
                          "the story's change holds only its own work: " + "; ".join(dirty[:8]))
        if not catalog.valid_branch(branch):
            errors.append(f"`{branch}` is not a valid branch name starting with story/")
        elif catalog.git(target, "rev-parse", "--verify", "--quiet", branch)[0] == 0:
            errors.append(f"branch {branch} already exists in {catalog.rel(target)}")
        analysis = self.db.latest(sid, "analysis")
        conf = analysis.get("confidence") if analysis and analysis["status"] == "completed" else None
        if conf is None:
            errors.append("run the analysis first; the confidence score gates the start")
        elif conf < CONFIDENCE_THRESHOLD and not (confidence_override or "").strip():
            errors.append(f"confidence {conf}% is below {CONFIDENCE_THRESHOLD}%; give a reason to "
                          "override, or resolve the risks and re-analyze")
        if meta.get("repo", "planning") != "planning" and not shutil.which("npm"):
            errors.append("npm is not on PATH; the code-repo validator runs `npm ci` and will fail")
        return errors, {"target": target, "confidence": conf}

    def start_implementation(self, sid: str, branch: str, scaffold: bool,
                             confidence_override: Optional[str]) -> str:
        errors, info = self.preflight(sid, branch, confidence_override)
        if errors:
            raise ValueError("\n".join(errors))
        target = info["target"]
        code, base_name = catalog.git(target, "rev-parse", "--abbrev-ref", "HEAD")
        _, base_sha = catalog.git(target, "rev-parse", "HEAD")
        code, out = catalog.git(target, "checkout", "-b", branch)
        if code != 0:
            raise ValueError(f"could not create {branch}: {out}")
        rid = self.db.create_run(sid, "implementation", branch=branch, base_ref=base_sha,
                                 target_repo=catalog.rel(target), scaffold=1 if scaffold else 0,
                                 confidence=info["confidence"],
                                 override_reason=(confidence_override or None))
        self.db.set_context(rid, {"base_name": base_name})
        self.db.init_steps(rid, implementation_steps())
        self.db.event(rid, "phase", f"created branch {branch} in {catalog.rel(target)} from "
                                    f"{base_name} @ {base_sha[:10]}")
        self._launch(rid)
        return rid

    def resume(self, rid: str) -> None:
        run = self.db.run(rid)
        if not run:
            raise ValueError("unknown run")
        if run["status"] not in ("failed", "stopped", "interrupted"):
            raise ValueError(f"run is {run['status']}; only failed, stopped or interrupted runs resume")
        if run["kind"] == "implementation":
            target = os.path.join(ROOT, run["target_repo"]) if run["target_repo"] != "." else ROOT
            _, cur = catalog.git(target, "rev-parse", "--abbrev-ref", "HEAD")
            if cur != run["branch"]:
                code, out = catalog.git(target, "checkout", run["branch"])
                if code != 0:
                    raise ValueError(f"cannot check out {run['branch']}: {out}")
        self.db.update_run(rid, status="queued", error=None)
        self.db.event(rid, "phase", "resuming from the first unfinished step")
        self._launch(rid)

    def stop(self, rid: str) -> None:
        if self._active != rid:
            raise ValueError("this run is not active")
        self._stop.set()
        self.db.event(rid, "warn", "stop requested")
        proc = self._proc
        if proc and proc.poll() is None:
            _kill_tree(proc)
        # Ends the Kiro subprocesses so an in-flight agent turn returns.
        threading.Thread(target=agents.shutdown_shared_client, daemon=True).start()

    def complete_review(self, rid: str, action: str, message: str = "") -> dict:
        run = self.db.run(rid)
        if not run or run["kind"] != "implementation":
            raise ValueError("unknown implementation run")
        if run["status"] != "awaiting_review":
            raise ValueError(f"run is {run['status']}, not awaiting review")
        target = os.path.join(ROOT, run["target_repo"]) if run["target_repo"] != "." else ROOT
        steps = self.db.steps(rid)
        idx = next(s["idx"] for s in steps if s["name"] == "human_review")
        if action == "reject":
            self.db.update_step(rid, idx, status="failed", detail="rejected by reviewer",
                                ended_at=_now())
            self.db.update_run(rid, status="rejected")
            self.db.event(rid, "warn", f"rejected by reviewer; the work stays on {run['branch']}")
            return {"status": "rejected"}
        if action == "commit":
            if not message.strip():
                raise ValueError("a commit message is required")
            _, cur = catalog.git(target, "rev-parse", "--abbrev-ref", "HEAD")
            if cur != run["branch"]:
                raise ValueError(f"{catalog.rel(target)} is on {cur}, not {run['branch']}")
            code, out = catalog.git(target, "add", "-A")
            if code != 0:
                raise ValueError(out)
            code, out = catalog.git(target, "commit", "-m", message)
            if code != 0:
                raise ValueError(out)
            self.db.event(rid, "info", out.splitlines()[0] if out else "committed")
        elif action != "committed":
            raise ValueError("action must be commit, committed or reject")
        _, head = catalog.git(target, "rev-parse", "HEAD")
        if head == run["base_ref"]:
            raise ValueError("no commit on the story branch yet")
        left = catalog.dirty_files(target)
        self.db.update_step(rid, idx, status="ok", ended_at=_now(),
                            detail=f"committed {head[:10]}" + (f"; still uncommitted: {len(left)} file(s)" if left else ""))
        self.db.update_run(rid, status="completed", commit_sha=head)
        self.db.event(rid, "phase", f"human committed {head[:10]} on {run['branch']}")
        return {"status": "completed", "commit": head}

    # --- thread ---------------------------------------------------------------------------

    def _launch(self, rid: str) -> None:
        with self._lock:
            if self.active:
                raise RuntimeError(f"run {self._active} is still active; stop it or wait")
            self._stop.clear()
            self._active = rid
            self._thread = threading.Thread(target=self._main, args=(rid,), daemon=True,
                                            name=f"run-{rid}")
            self._thread.start()

    def _main(self, rid: str) -> None:
        run = self.db.run(rid)
        sink = StudioSink(self.db, rid)
        agents.set_audit_sink(sink)
        self.db.update_run(rid, status="running")
        self.db.event(rid, "phase", f"{run['kind']} of {run['story_id']} started")
        try:
            if run["kind"] == "analysis":
                self._run_steps(rid, sink, self._analysis_step)
            else:
                self._prepare_env(run)
                self._run_steps(rid, sink, self._impl_step)
        except Stopped:
            self.db.update_run(rid, status="stopped", error="stopped by user")
            self.db.event(rid, "warn", "run stopped; resume continues from the stopped step")
        except StepFailed as e:
            self.db.update_run(rid, status="failed", error=str(e))
            self.db.event(rid, "error", f"run failed: {e}")
        except Exception as e:  # noqa: BLE001
            self.db.update_run(rid, status="failed", error=f"{type(e).__name__}: {e}")
            self.db.event(rid, "error", traceback.format_exc()[-3000:])
        finally:
            agents.set_audit_sink(None)
            # Fresh Kiro processes per run: they inherit this run's environment at launch.
            agents.shutdown_shared_client()
            self._active = None

    def _run_steps(self, rid: str, sink: StudioSink, execute) -> None:
        for step in self.db.steps(rid):
            if step["status"] in ("ok", "skipped"):
                continue
            if self._stop.is_set():
                raise Stopped()
            run = self.db.run(rid)
            ctx = run["context"]
            sink.step_idx, sink.step_name = step["idx"], step["name"]
            self.db.update_step(rid, step["idx"], status="running", started_at=_now(), detail=None)
            self.db.event(rid, "step", f"▶ {step['name']} ({step['kind']})", step["name"])
            try:
                status, detail = execute(run, step, ctx)
            except Exception as e:  # noqa: BLE001
                if self._stop.is_set():
                    self.db.update_step(rid, step["idx"], status="pending", detail="stopped")
                    raise Stopped() from e
                self.db.update_step(rid, step["idx"], status="failed", ended_at=_now(),
                                    detail=f"{type(e).__name__}: {e}")
                self.db.set_context(rid, ctx)
                raise StepFailed(f"{step['name']}: {e}") from e
            self.db.set_context(rid, ctx)
            if status == "awaiting_review":
                self.db.update_step(rid, step["idx"], status="running", detail=detail)
                self.db.update_run(rid, status="awaiting_review")
                self.db.event(rid, "phase", detail, step["name"])
                return
            self.db.update_step(rid, step["idx"], status=status, ended_at=_now(), detail=detail)
            self.db.event(rid, "check" if status == "ok" else "info",
                          f"✓ {step['name']}: {detail}" if status == "ok" else f"– {step['name']} {status}: {detail}",
                          step["name"])
        self.db.update_run(rid, status="completed")
        self.db.event(rid, "phase", "run completed")

    # --- analysis -------------------------------------------------------------------------

    def _analysis_step(self, run: dict, step: dict, ctx: dict) -> Tuple[str, str]:
        sid = run["story_id"]
        name = step["name"]
        if name == "readiness":
            r = catalog.readiness(sid)
            ctx["readiness"] = r
            for f in r["factors"]:
                self.db.event(run["id"], "check" if f["ok"] else "warn",
                              f"{'✓' if f['ok'] else '✗'} {f['name']}: {f['detail']}", name)
            return "ok", f"score {r['score']}%, cap {r['cap']}%"
        if name == "analyze":
            story = catalog.load_stories()[sid]
            docs = catalog.relevant_docs(sid)
            rendered = prompts.render(STUDIO_PROMPTS, "analyze_story",
                                      story=f"Source: {catalog.rel(story['path'])}\n\n{story['text']}",
                                      docs="\n".join(f"- {d}" for d in docs),
                                      readiness=ctx["readiness"])
            reply = agents.invoke_kiro(rendered.text, agent="reviewer", step="analyze",
                                       template="analyze_story", params={"story": sid})
            block = prompts.extract(reply, "ANALYSIS")
            if block is None:
                raise RuntimeError("analysis reply had no <<<ANALYSIS>>> envelope")
            ctx["analysis"] = json.loads(block)
            return "ok", f"agent confidence {ctx['analysis'].get('confidence')}%"
        if name == "score":
            r, a = ctx["readiness"], ctx["analysis"]
            agent_score = int(a.get("confidence", 0))
            blended = round(0.6 * agent_score + 0.4 * r["score"])
            final = min(blended, r["cap"])
            result = {"confidence": final, "agent": agent_score, "readiness": r["score"],
                      "cap": r["cap"], "threshold": CONFIDENCE_THRESHOLD,
                      "ready_to_start": final >= CONFIDENCE_THRESHOLD, **a,
                      "factors": r["factors"], "confidence_agent": agent_score}
            result["confidence"] = final
            self.db.update_run(run["id"], confidence=final, result_json=json.dumps(result))
            capped = f", capped at {r['cap']}%" if blended > r["cap"] else ""
            return "ok", (f"confidence {final}% = 60% agent ({agent_score}) + 40% readiness "
                          f"({r['score']}){capped}")
        raise RuntimeError(f"no analysis step {name}")

    # --- implementation -------------------------------------------------------------------

    def _target(self, run: dict) -> str:
        return ROOT if run["target_repo"] in (".", "", None) else os.path.join(ROOT, run["target_repo"])

    def _prepare_env(self, run: dict) -> None:
        target = self._target(run)
        os.environ["HARNESS_TARGET_REPO"] = target
        os.environ["VALIDATE_BASE_REF"] = run["base_ref"]
        if run["scaffold"]:
            os.environ["VALIDATE_SCAFFOLD"] = "1"
            self.db.event(run["id"], "warn", "scaffold unlock: protected configs may be ADDED in this run")
        else:
            os.environ.pop("VALIDATE_SCAFFOLD", None)

    def _issue(self, run: dict) -> Tuple[str, str, dict]:
        story = catalog.load_stories()[run["story_id"]]
        meta = story["meta"]
        pre = run_story.preamble(run["story_id"], meta, self._target(run))
        issue = (f"{pre}# {run['story_id']}: {meta.get('title', '')}\n\nSource: "
                 f"{catalog.rel(story['path'])}\n\n{story['text']}")
        return pre, issue, meta

    def _invoke(self, pre: str, text: str, agent: str, step: str, template: str, params: dict) -> str:
        return agents.invoke_kiro(pre + text, agent=agent, step=step, template=template,
                                  params=params)

    def _impl_step(self, run: dict, step: dict, ctx: dict) -> Tuple[str, str]:
        name = step["name"]
        rid = run["id"]
        target = self._target(run)
        pre, issue, meta = self._issue(run)
        sid = run["story_id"]

        if name == "classify":
            r = prompts.render(KIRO_PROMPTS, step["prompt"], issue=issue)
            reply = self._invoke(pre, r.text, step["agent"], name, step["prompt"], {"issue": sid})
            block = prompts.extract(reply, "CLASSIFICATION")
            if block is None:
                raise RuntimeError("classify_issue reply had no <<<CLASSIFICATION>>> envelope")
            info = json.loads(block)
            if info.get("type") not in step_prompt_map():
                raise RuntimeError(f"unknown classification {info.get('type')!r}")
            ctx["classification"] = info["type"]
            ctx["classification_info"] = info
            return "ok", f"{info['type']} ({info.get('confidence')}): {info.get('rationale', '')}"

        if name == "plan":
            cls = ctx["classification"]
            template = step["prompt_map"][cls]
            r = prompts.render(KIRO_PROMPTS, template, issue=issue, classification=cls)
            reply = self._invoke(pre, r.text, step["agent"], name, template, {"issue": sid})
            spec = prompts.extract(reply, "SPEC")
            if spec is None:
                raise RuntimeError(f"{template} reply had no <<<SPEC>>> envelope")
            path_line = spec.strip().splitlines()[0].strip().strip("`")
            plan = _resolve(path_line, target)
            if not plan:
                raise RuntimeError(f"plan file `{path_line}` was not found in the repo root or "
                                   f"{catalog.rel(target)}")
            ctx["plan_file_path"] = catalog.rel(plan)
            return "ok", f"plan written to {ctx['plan_file_path']} using {template}"

        if name == "plan_exists":
            path = os.path.join(ROOT, ctx["plan_file_path"])
            text = open(path, encoding="utf-8").read() if os.path.isfile(path) else ""
            problems = []
            if not text:
                problems.append("plan file missing")
            if sid not in text:
                problems.append(f"plan does not cite {sid}")
            if not re.search(r"^\s*\d+[.)].*\bshall\b", text, re.M | re.I):
                problems.append("no numbered criterion containing 'shall'")
            if problems:
                raise RuntimeError("; ".join(problems))
            return "ok", "plan cites the story and has numbered 'shall' criteria"

        if name == "write_tests":
            r = prompts.render(KIRO_PROMPTS, "write_tests", plan_file_path=ctx["plan_file_path"])
            reply = self._invoke(pre, r.text, step["agent"], name, "write_tests",
                                 {"plan_file_path": ctx["plan_file_path"]})
            block = prompts.extract(reply, "TESTS")
            tests = json.loads(block) if block else {"status": "unknown"}
            ctx["tests"] = tests
            snap = _snapshot(target, exclude={os.path.join(ROOT, ctx["plan_file_path"])})
            ctx["test_snapshot"] = snap
            return "ok", (f"tests {tests.get('status')}: {len(tests.get('files') or [])} file(s); "
                          f"snapshot of {len(snap)} changed file(s) for tests_unchanged")

        if name == "red":
            if ctx.get("classification") in NO_TDD or (ctx.get("tests") or {}).get("status") == "skipped":
                return "skipped", "no TDD for this classification or tests were skipped"
            self._validator(rid, name, expect_zero=False, runs=2)
            return "ok", "validator failed twice before implementation, as expected"

        if name == "implement":
            r = prompts.render(KIRO_PROMPTS, "implement", plan_file_path=ctx["plan_file_path"])
            self._invoke(pre, r.text, step["agent"], name, "implement",
                         {"plan_file_path": ctx["plan_file_path"]})
            changed = _changed(target)
            return "ok", f"{len(changed)} file(s) changed on the branch"

        if name == "tests_unchanged":
            snap = ctx.get("test_snapshot") or {}
            if ctx.get("classification") in NO_TDD and not snap:
                return "skipped", "no test snapshot for this classification"
            moved = [p for p, h in snap.items() if _sha(os.path.join(target, p)) != h]
            if moved:
                raise RuntimeError("implement changed files written by write_tests: " + ", ".join(moved))
            return "ok", f"{len(snap)} test-step file(s) byte-identical"

        if name == "green":
            self._validator(rid, name, expect_zero=True, runs=2)
            return "ok", "validator passed twice"

        if name == "validate":
            self._validator(rid, name, expect_zero=True, runs=1)
            return "ok", "all validator stages passed"

        if name == "review":
            r = prompts.render(KIRO_PROMPTS, "review", plan_file_path=ctx["plan_file_path"],
                               base_ref=run["base_ref"])
            text = (r.text + "\n\n## The actual change under review (from git, not from the builder)\n\n"
                    + run_story.review_diff(target, run["base_ref"]))
            reply = self._invoke(pre, text, "reviewer", name, "review",
                                 {"plan_file_path": ctx["plan_file_path"], "base_ref": run["base_ref"]})
            block = prompts.extract(reply, "REVIEW")
            if block is None:
                raise RuntimeError("review reply had no <<<REVIEW>>> envelope")
            verdict = block.strip().splitlines()[-1].strip()
            ctx["review"] = {"text": block, "verdict": verdict}
            return "ok", f"reviewer verdict: {verdict}"

        if name == "human_review":
            ctx["suggested_commit_message"] = _commit_message(sid, meta, ctx)
            return "awaiting_review", (f"waiting for a human to review and commit on {run['branch']} "
                                       f"(reviewer verdict: {(ctx.get('review') or {}).get('verdict', 'n/a')})")

        raise RuntimeError(f"no wiring for step {name}")

    def _validator(self, rid: str, step: str, expect_zero: bool, runs: int) -> None:
        bash = find_bash()
        for i in range(runs):
            if self._stop.is_set():
                raise Stopped()
            self.db.event(rid, "info", f"validator run {i + 1}/{runs} ({'expect pass' if expect_zero else 'expect fail'})", step)
            flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
            self._proc = subprocess.Popen([bash, VALIDATOR.replace(os.sep, "/")], cwd=ROOT,
                                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                          encoding="utf-8", errors="replace", creationflags=flags,
                                          start_new_session=(os.name != "nt"))
            timer = threading.Timer(VALIDATOR_TIMEOUT, lambda p=self._proc: _kill_tree(p))
            timer.start()
            tail: List[str] = []
            try:
                for line in self._proc.stdout:  # type: ignore[union-attr]
                    line = line.rstrip()
                    tail = (tail + [line])[-40:]
                    self.db.event(rid, "output", line, step)
                code = self._proc.wait()
            finally:
                timer.cancel()
                self._proc = None
            if self._stop.is_set():
                raise Stopped()
            if (code == 0) != expect_zero:
                raise RuntimeError(f"validator exit {code}, expected {'0' if expect_zero else 'non-zero'}. "
                                   + " | ".join(tail[-6:]))


def step_prompt_map() -> Dict[str, str]:
    for s in implementation_steps():
        if s["name"] == "plan":
            return s["prompt_map"]
    return {}


# --- helpers ----------------------------------------------------------------------------

def _now() -> str:
    from db import now
    return now()


def _kill_tree(proc: subprocess.Popen) -> None:
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        else:
            import signal
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except Exception:  # noqa: BLE001
        pass


def _resolve(path_line: str, target: str) -> Optional[str]:
    p = path_line.replace("\\", "/")
    for base in (ROOT, target):
        cand = os.path.normpath(os.path.join(base, p))
        if os.path.isfile(cand):
            return cand
    return None


def _changed(target: str) -> List[str]:
    _, out = catalog.git(target, "status", "--porcelain", "-uall")
    files = []
    for ln in out.splitlines():
        if not ln.strip():
            continue
        path = ln[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if target == ROOT and path in catalog.SUBMODULES:
            continue
        files.append(path)
    return files


def _sha(path: str) -> Optional[str]:
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return None


def _snapshot(target: str, exclude: set) -> Dict[str, Optional[str]]:
    snap = {}
    for p in _changed(target):
        full = os.path.normpath(os.path.join(target, p))
        if full in {os.path.normpath(e) for e in exclude}:
            continue
        snap[p] = _sha(full)
    return snap


def _commit_message(sid: str, meta: dict, ctx: dict) -> str:
    title = meta.get("title", "").strip()
    lines = [f"{sid}: {title}" if title else sid, ""]
    if ctx.get("classification"):
        lines.append(f"Work type: {ctx['classification']}")
    if ctx.get("plan_file_path"):
        lines.append(f"Plan: {ctx['plan_file_path']}")
    verdict = (ctx.get("review") or {}).get("verdict")
    if verdict:
        lines.append(f"Harness review: {verdict}")
    return "\n".join(lines).strip() + "\n"
