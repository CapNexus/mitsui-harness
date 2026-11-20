"""Run story analysis and the plan_build loop in the background, checkpointed in harness-db.

The harness is the brain. Every step here is executed by harness code, unchanged:

  * analysis: `harness/story_analysis.py` (readiness, the Kiro `analyze_story` turn, score);
  * implementation: `harness/run_story.py` (preflight, branch, environment, repository
    preamble, review diff) and `harness/drivers/run_plan_build.py` (what every step of
    `harness/workflows/plan_build.json` does, including the agent's `commit_tests` and
    `commit`).

Studio only adds what a UI needs: it runs the workflow one step at a time so each step is
checkpointed (loop context + `PlanBuildContext.state()`), streams Kiro's events and the
validator output into the console, can stop a run, and ends with a human review gate
before anything is pushed.
"""

from __future__ import annotations

import datetime as dt
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
from db import DB, now

sys.path.insert(0, os.path.join(ROOT, "harness", "drivers"))
import agents  # noqa: E402
import loop_driver  # noqa: E402
import run_plan_build as rpb  # noqa: E402
from audit import AuditSink, StepAudit  # noqa: E402

import run_story  # noqa: E402
import story_analysis  # noqa: E402

AUDIT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "audit")
RUNS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "runs")
CONFIDENCE_THRESHOLD = story_analysis.THRESHOLD
CHARS_PER_TOKEN = 4

ANALYSIS_STEPS = [
    {"name": "readiness", "kind": "deterministic"},
    {"name": "analyze", "kind": "agent", "agent": "reviewer", "prompt": "analyze_story"},
    {"name": "score", "kind": "deterministic"},
]
HUMAN_GATE = {"name": "human_review", "kind": "human"}
RESETTABLE = ("failed", "stopped", "interrupted", "awaiting_review", "rejected", "queued")


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
        if data.get("title"):
            self._tool_state[tid + ":title"] = data["title"]
        title = self._tool_state.get(tid + ":title", "tool")
        for key, into in (("raw_input", "out"), ("raw_output", "in"), ("content", "in")):
            if data.get(key) is not None:
                n = len(json.dumps(data[key], default=str))
                if into == "in":
                    self._in_chars += n
                else:
                    self._out_chars += n
        seen = tid in self._tool_state
        if not seen or (status == "failed" and self._tool_state.get(tid) != "failed"):
            self._emit("tool" if status != "failed" else "warn",
                       f"{'✗ failed: ' if status == 'failed' else '→ '}{title}")
        self._tool_state[tid] = status

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
    """The harness workflow, unchanged, followed by the human review gate."""
    return [*rpb.load_workflow(os.path.join(ROOT, rpb.WORKFLOW_PATH))["steps"], HUMAN_GATE]


class Runner:
    def __init__(self, db: DB) -> None:
        self.db = db
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._active: Optional[str] = None
        self._stop = threading.Event()
        self._proc: Optional[subprocess.Popen] = None

    @property
    def active(self) -> Optional[str]:
        return self._active if self._thread and self._thread.is_alive() else None

    # --- starting runs --------------------------------------------------------------------

    def start_analysis(self, sid: str) -> str:
        if sid not in run_story.load_stories():
            raise ValueError(f"unknown story {sid}")
        rid = self.db.create_run(sid, "analysis")
        self.db.init_steps(rid, ANALYSIS_STEPS)
        self._launch(rid)
        return rid

    def preflight(self, sid: str, branch: str, override: Optional[str]) -> Tuple[List[str], dict]:
        """The harness preflight (run_story.preflight) plus Studio's start gate: a completed
        analysis at the harness threshold, or a recorded reason to override it."""
        errors, target = run_story.preflight(sid, branch)
        if not shutil.which(os.getenv("KIRO_CLI_PATH", "kiro-cli")):
            errors.append("kiro-cli is not on PATH")
        stories = run_story.load_stories()
        if sid in stories and stories[sid]["meta"].get("repo", "planning") != "planning" and not shutil.which("npm"):
            errors.append("npm is not on PATH; the code-repo validator runs `npm ci` and will fail")
        analysis = self.db.latest(sid, "analysis")
        conf = analysis.get("confidence") if analysis and analysis["status"] == "completed" else None
        if conf is None:
            errors.append("run the analysis first; the confidence score gates the start")
        elif conf < CONFIDENCE_THRESHOLD and not (override or "").strip():
            errors.append(f"confidence {conf}% is below {CONFIDENCE_THRESHOLD}%; give a reason to "
                          "override, or resolve the risks and re-analyze")
        return errors, {"target": target, "confidence": conf}

    def start_implementation(self, sid: str, branch: str, scaffold: bool, override: Optional[str]) -> str:
        errors, info = self.preflight(sid, branch, override)
        if errors:
            raise ValueError("\n".join(errors))
        try:
            sr = run_story.prepare(sid, scaffold, branch)
        except SystemExit as e:
            raise ValueError(str(e))
        rid = self.db.create_run(sid, "implementation", branch=sr.branch, base_ref=sr.base_ref,
                                 target_repo=sr.target_rel, scaffold=1 if scaffold else 0,
                                 confidence=info["confidence"], override_reason=(override or None))
        self.db.set_context(rid, {"story_run": sr.to_dict(), "loop": {"issue": None}, "pbc": None})
        self.db.init_steps(rid, implementation_steps())
        self.db.event(rid, "phase", f"created branch {sr.branch} in {sr.target_rel} from "
                                    f"{sr.base_name} @ {sr.base_ref[:10]}")
        self._launch(rid)
        return rid

    def resume(self, rid: str, from_step: Optional[str] = None) -> None:
        run = self.db.run(rid)
        if not run:
            raise ValueError("unknown run")
        if run["status"] not in ("failed", "stopped", "interrupted", "awaiting_review", "rejected"):
            raise ValueError(f"run is {run['status']}; it cannot be resumed")
        if from_step:
            steps = self.db.steps(rid)
            idx = next((s["idx"] for s in steps if s["name"] == from_step), None)
            if idx is None:
                raise ValueError(f"no step {from_step}")
            for s in steps:
                if s["idx"] >= idx:
                    self.db.update_step(rid, s["idx"], status="pending", detail=None)
        if run["kind"] == "implementation":
            sr = run_story.StoryRun.from_dict(run["context"]["story_run"])
            if run_story.git(sr.target, "rev-parse", "--verify", "--quiet", f"refs/heads/{sr.branch}")[0] != 0:
                raise ValueError(f"branch {sr.branch} no longer exists in {sr.target_rel}, so this run cannot "
                                 "continue. Use Reset to discard this run and start the story again.")
            try:
                run_story.resume(run_story.StoryRun.from_dict(run["context"]["story_run"]))
            except SystemExit as e:
                raise ValueError(str(e))
        self.db.update_run(rid, status="queued", error=None)
        self.db.event(rid, "phase", f"resuming from {from_step or 'the first unfinished step'}")
        self._launch(rid)

    def stop(self, rid: str) -> None:
        if self._active != rid:
            raise ValueError("this run is not active")
        self._stop.set()
        self.db.event(rid, "warn", "stop requested")
        proc = self._proc
        if proc and proc.poll() is None:
            rpb.kill_tree(proc)
        threading.Thread(target=agents.shutdown_shared_client, daemon=True).start()

    def reset(self, rid: str) -> dict:
        """Discard an unfinished build so the story can start again from the beginning.

        Leaves the story's work branch (checking out the branch it was created from, and
        stashing any uncommitted work so nothing is lost), deletes the branch if it still
        exists, and marks the run `discarded`. Works when the branch is already gone. The
        old run stays in the history; a new build creates a fresh run and branch."""
        run = self.db.run(rid)
        if not run or run["kind"] != "implementation":
            raise ValueError("unknown implementation run")
        if self.active:
            raise ValueError(f"run {self._active} is still active; stop it before resetting")
        if run["status"] not in RESETTABLE:
            raise ValueError(f"run is {run['status']}; only an unfinished, failed, stopped or rejected "
                             "build can be reset")
        sr = run_story.StoryRun.from_dict(run["context"]["story_run"])
        notes: List[str] = []
        g = run_story.git
        on_branch = g(sr.target, "rev-parse", "--abbrev-ref", "HEAD")[1].strip() == sr.branch
        if on_branch:
            if run_story.dirty(sr.target):
                code, out = g(sr.target, "stash", "push", "--include-untracked", "-m", f"studio reset {rid}")
                if code != 0:
                    raise ValueError(f"could not stash the uncommitted work on {sr.branch}: {out.strip()}")
                notes.append(f"uncommitted work saved in git stash 'studio reset {rid}'")
            if g(sr.target, "rev-parse", "--verify", "--quiet", f"refs/heads/{sr.base_name}")[0] != 0:
                raise ValueError(f"cannot leave {sr.branch}: its base branch {sr.base_name} no longer exists. "
                                 "Check out a branch yourself, then reset again.")
            code, out = g(sr.target, "checkout", sr.base_name)
            if code != 0:
                raise ValueError(f"could not check out {sr.base_name}: {out.strip()}")
            notes.append(f"checked out {sr.base_name}")
        code, tip = g(sr.target, "rev-parse", "--verify", "--quiet", f"refs/heads/{sr.branch}")
        if code == 0:
            code, out = g(sr.target, "branch", "-D", sr.branch)
            if code != 0:
                raise ValueError(f"could not delete {sr.branch}: {out.strip()}")
            notes.append(f"deleted branch {sr.branch} (was at {tip.strip()[:10]}; recoverable from the reflog)")
        else:
            notes.append(f"branch {sr.branch} was already gone")
        for s in self.db.steps(rid):
            if s["status"] in ("running",):
                self.db.update_step(rid, s["idx"], status="pending")
        self.db.update_run(rid, status="discarded", error="reset by user; start the story again")
        self.db.event(rid, "warn", "run reset: " + "; ".join(notes))
        return {"status": "discarded", "notes": notes}

    def complete_review(self, rid: str, action: str, note: str = "") -> dict:
        """The human gate after the harness `commit` step: approve (ready to push and open a
        PR) or reject. Nothing is pushed from here."""
        run = self.db.run(rid)
        if not run or run["kind"] != "implementation" or run["status"] != "awaiting_review":
            raise ValueError("this run is not awaiting review")
        idx = next(s["idx"] for s in self.db.steps(rid) if s["name"] == HUMAN_GATE["name"])
        if action == "reject":
            self.db.update_step(rid, idx, status="failed", ended_at=now(), detail=f"rejected: {note}".strip())
            self.db.update_run(rid, status="rejected")
            self.db.event(rid, "warn", f"rejected by reviewer; the commits stay on {run['branch']}. {note}")
            return {"status": "rejected"}
        if action != "approve":
            raise ValueError("action must be approve or reject")
        marked = self._mark_story_done(rid, run)      # raises (and leaves the run in review) on a git error
        self.db.update_step(rid, idx, status="ok", ended_at=now(), detail=f"approved: {note}".strip())
        self.db.update_run(rid, status="completed")
        self.db.event(rid, "phase", f"approved by a human; push {run['branch']} and open a PR")
        return {"status": "completed", "story_marked_done": marked}

    def _mark_story_done(self, rid: str, run: dict) -> str:
        """On approval, set `status: done` in the story file and commit just that file, so the
        pull request that is merged already carries it (docs/0001: the PR sets done).

        Planning story: committed on the story branch, in the same repository as the work.
        Code story: the story file lives in this (parent) repository while the work is in a
        submodule, so the file is committed on the parent's current branch; it is skipped when
        that is `main`/`master`, which only accepts pull requests. Returns a short description."""
        sr = run_story.StoryRun.from_dict(run["context"]["story_run"])
        story = run_story.load_stories()[sr.sid]
        path = story["path"]
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        if (story["meta"].get("status") or "").strip() == "done":
            return "already done"
        if sr.target == ROOT:
            run_story.resume(sr)                      # be on the story branch
        else:
            parent = run_story.git(ROOT, "rev-parse", "--abbrev-ref", "HEAD")[1].strip()
            if parent in ("main", "master", "HEAD"):
                note = (f"story file not updated: the parent repository is on {parent}. Check out a working "
                        f"branch and set status: done in {rel}, or run record after the merge")
                self.db.event(rid, "warn", note)
                return note
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        text = re.sub(r"^status:.*$", "status: done", text, count=1, flags=re.M)
        text = text.rstrip("\n") + f"\n- {dt.date.today().isoformat()}: done (approved in Studio)\n"
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        for args in (("add", "--", rel), ("commit", "-m", f"Record {sr.sid} done", "--", rel)):
            code, out = run_story.git(ROOT, *args)
            if code != 0:
                run_story.git(ROOT, "checkout", "--", rel)      # leave the story file as it was
                raise ValueError(f"could not record {sr.sid} as done: {out.strip()[:400]}")
        sha = run_story.git(ROOT, "rev-parse", "--short", "HEAD")[1].strip()
        self.db.event(rid, "phase", f"story {sr.sid} marked done in {rel} (commit {sha})")
        return f"committed {sha}"

    # --- thread ---------------------------------------------------------------------------

    def _launch(self, rid: str) -> None:
        with self._lock:
            if self.active:
                raise RuntimeError(f"run {self._active} is still active; stop it or wait")
            self._stop.clear()
            self._active = rid
            self._thread = threading.Thread(target=self._main, args=(rid,), daemon=True, name=f"run-{rid}")
            self._thread.start()

    def _main(self, rid: str) -> None:
        run = self.db.run(rid)
        sink = StudioSink(self.db, rid)
        agents.set_audit_sink(sink)
        self.db.update_run(rid, status="running")
        self.db.event(rid, "phase", f"{run['kind']} of {run['story_id']} started")
        try:
            if run["kind"] == "analysis":
                self._run_analysis(rid, sink)
            else:
                self._run_implementation(rid, sink)
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
            agents.shutdown_shared_client()     # fresh Kiro processes per run (environment)
            self._active = None

    def _each_pending(self, rid: str, sink: StudioSink):
        for step in self.db.steps(rid):
            if step["status"] in ("ok", "skipped"):
                continue
            if self._stop.is_set():
                raise Stopped()
            sink.step_idx, sink.step_name = step["idx"], step["name"]
            self.db.update_step(rid, step["idx"], status="running", started_at=now(), detail=None)
            self.db.event(rid, "step", f"▶ {step['name']} ({step['kind']})", step["name"])
            yield step

    def _fail(self, rid: str, step: dict, e: Exception) -> None:
        if self._stop.is_set():
            self.db.update_step(rid, step["idx"], status="pending", detail="stopped")
            raise Stopped() from e
        detail = e.detail if isinstance(e, loop_driver.LoopFailed) else f"{type(e).__name__}: {e}"
        self.db.update_step(rid, step["idx"], status="failed", ended_at=now(), detail=detail[-4000:])
        raise StepFailed(f"{step['name']}: {detail[:600]}") from e

    def _ok(self, rid: str, step: dict, detail: str) -> None:
        status = "skipped" if detail.startswith("skipped") else "ok"
        self.db.update_step(rid, step["idx"], status=status, ended_at=now(), detail=detail[-4000:])
        self.db.event(rid, "check", f"✓ {step['name']}: {detail.splitlines()[0][:300]}", step["name"])

    # --- analysis (harness/story_analysis.py) ---------------------------------------------

    def _run_analysis(self, rid: str, sink: StudioSink) -> None:
        sid = self.db.run(rid)["story_id"]
        for step in self._each_pending(rid, sink):
            ctx = self.db.run(rid)["context"]
            try:
                if step["name"] == "readiness":
                    ctx["readiness"] = story_analysis.readiness(sid)
                    for f in ctx["readiness"]["factors"]:
                        self.db.event(rid, "check" if f["ok"] else "warn",
                                      f"{'✓' if f['ok'] else '✗'} {f['name']}: {f['detail']}", step["name"])
                    detail = f"score {ctx['readiness']['score']}%, cap {ctx['readiness']['cap']}%"
                elif step["name"] == "analyze":
                    ctx["analysis"] = story_analysis.analyze(sid, ctx["readiness"])
                    detail = f"agent confidence {ctx['analysis'].get('confidence')}%"
                else:
                    result = story_analysis.score(ctx["readiness"], ctx["analysis"])
                    self.db.update_run(rid, confidence=result["confidence"], result_json=json.dumps(result))
                    detail = (f"confidence {result['confidence']}% = 60% agent ({result['agent']}) + 40% "
                              f"readiness ({result['readiness']})" + (f", capped at {result['cap']}%" if result["capped"] else ""))
            except Exception as e:  # noqa: BLE001
                self._fail(rid, step, e)
            self.db.set_context(rid, ctx)
            self._ok(rid, step, detail)
        self.db.update_run(rid, status="completed")
        self.db.event(rid, "phase", "analysis completed")

    # --- implementation (harness/run_story.py + drivers/run_plan_build.py) -----------------

    def _run_implementation(self, rid: str, sink: StudioSink) -> None:
        run = self.db.run(rid)
        sr = run_story.StoryRun.from_dict(run["context"]["story_run"])
        run_story.resume(sr)        # on the branch, environment set (no-op on a fresh run)

        def on_output(line: str) -> None:
            self.db.event(rid, "output", line, sink.step_name)

        def on_process(proc: Optional[subprocess.Popen]) -> None:
            self._proc = proc

        pbc = run_story.make_context(sr, os.path.join(RUNS_DIR, rid), on_output=on_output,
                                     on_process=on_process)
        if run["context"].get("pbc"):
            pbc.restore(run["context"]["pbc"])
        loop_ctx = run["context"].get("loop") or {}
        loop_ctx["issue"] = pbc.issue_text
        workflow = rpb.load_workflow(os.path.join(ROOT, rpb.WORKFLOW_PATH))

        for step in self._each_pending(rid, sink):
            if step["name"] == HUMAN_GATE["name"]:
                _, log = run_story.git(sr.target, "log", "--oneline", f"{sr.base_ref}..HEAD")
                verdict = (loop_ctx.get("result:review") or "").strip().splitlines()
                self.db.update_step(rid, step["idx"], detail="waiting for a human to review the commits")
                self.db.update_run(rid, status="awaiting_review")
                self.db.event(rid, "phase", f"committed on {sr.branch} ({len(log.splitlines())} commit(s)); "
                                            f"reviewer verdict {verdict[-1] if verdict else 'n/a'}. "
                                            "Waiting for human review.", step["name"])
                return
            wf_step = next(s for s in workflow["steps"] if s["name"] == step["name"])
            try:
                result = rpb.run_step(workflow, wf_step, loop_ctx, pbc)
            except Exception as e:  # noqa: BLE001
                self._save(rid, loop_ctx, pbc)
                self._fail(rid, step, e)
            self._save(rid, loop_ctx, pbc)
            self._ok(rid, step, self._describe(step["name"], result, loop_ctx))
        self.db.update_run(rid, status="completed")

    def _save(self, rid: str, loop_ctx: dict, pbc: rpb.PlanBuildContext) -> None:
        ctx = self.db.run(rid)["context"]
        ctx["loop"] = {k: v for k, v in loop_ctx.items() if k != "issue"}
        ctx["pbc"] = pbc.state()
        self.db.set_context(rid, ctx)

    @staticmethod
    def _describe(name: str, result: loop_driver.StepResult, ctx: dict) -> str:
        if result.kind != "agent":
            return result.detail
        if name == "classify":
            info = ctx.get("classification_info") or {}
            return f"{ctx.get('classification')} ({info.get('confidence')}): {info.get('rationale', '')}"
        if name == "plan":
            return f"plan written to {ctx.get('plan_file_path')} ({result.detail})"
        if name == "write_tests":
            t = ctx.get("tests") or {}
            return f"tests {t.get('status', '?')}: {len(t.get('files') or [])} file(s)"
        if name == "review":
            lines = (ctx.get("result:review") or "").strip().splitlines()
            return f"reviewer verdict: {lines[-1] if lines else '?'}"
        if name in ("commit_tests", "commit"):
            reply = ctx.get(f"result:{name}") or ""
            sha = ctx.get(f"{name}_sha")
            return reply if reply.startswith("skipped") else f"committed {sha[:10] if sha else '?'}"
        return f"{name} done ({result.detail})"
