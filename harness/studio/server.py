"""Harness Studio: a local web app to pick, analyze, build and review user stories with Kiro.

Run from anywhere (it changes into the repo root, because Kiro sessions use the process cwd):

    set AEW_AUTO_APPROVE=1            (PowerShell: $env:AEW_AUTO_APPROVE = "1")
    uv run --with-requirements harness/studio/requirements.txt python harness/studio/server.py

Then open http://127.0.0.1:8765. Binds to localhost only.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import catalog  # noqa: E402
from catalog import ROOT  # noqa: E402

os.chdir(ROOT)

from fastapi import FastAPI, HTTPException, Request  # noqa: E402
from fastapi.responses import FileResponse, StreamingResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

import runner as runner_mod  # noqa: E402
from db import DB  # noqa: E402

db = DB()
interrupted = db.mark_interrupted()
runner = runner_mod.Runner(db)
app = FastAPI(title="Harness Studio")
app.mount("/static", StaticFiles(directory=os.path.join(HERE, "static")), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(os.path.join(HERE, "static", "index.html"))


# --- overview and stories -------------------------------------------------------------------

@app.get("/api/overview")
def overview() -> dict:
    features, stories, next_id = catalog.overview()
    for s in stories:
        a = db.latest(s["id"], "analysis")
        i = db.latest(s["id"], "implementation")
        s["confidence"] = a["confidence"] if a and a["status"] == "completed" else None
        s["analysis_status"] = a["status"] if a else None
        s["impl_status"] = i["status"] if i else None
        s["impl_run"] = i["id"] if i else None
    return {"features": features, "stories": stories, "next": next_id,
            "next_reason": catalog.next_reason(next_id, stories),
            "tokens": db.token_totals(), "active_run": runner.active,
            "threshold": runner_mod.CONFIDENCE_THRESHOLD}


@app.get("/api/environment")
def environment() -> dict:
    return {
        "kiro_cli": shutil.which(os.getenv("KIRO_CLI_PATH", "kiro-cli")),
        "auto_approve": os.getenv("AEW_AUTO_APPROVE", "").lower() in ("1", "true", "yes"),
        "npm": shutil.which("npm"),
        "bash": runner_mod.rpb.find_bash(),
        "parent_dirty": catalog.dirty_files(ROOT)[:20],
        "interrupted_at_start": interrupted,
        "db": db.path,
        "os": "windows" if os.name == "nt" else ("mac" if sys.platform == "darwin" else "linux"),
        "submodules": {m: os.path.exists(os.path.join(ROOT, m, ".git")) for m in catalog.SUBMODULES},
    }


def _compare_url(target: str, branch: str) -> str:
    """Web link to open a pull request for `branch` (GitHub and GitHub Enterprise)."""
    _, url = catalog.git(target, "remote", "get-url", "origin")
    url = url.strip()
    if url.startswith("git@"):
        url = "https://" + url[4:].replace(":", "/", 1)
    url = url[:-4] if url.endswith(".git") else url
    return f"{url}/compare/{branch}?expand=1" if url.startswith("http") else ""


@app.get("/api/stories/{sid}")
def story(sid: str) -> dict:
    stories = catalog.load_stories()
    if sid not in stories:
        raise HTTPException(404, "unknown story")
    s = stories[sid]
    _, summaries, next_id = catalog.overview()
    summary = next(x for x in summaries if x["id"] == sid)
    deps = catalog.load_dependencies()
    return {
        "summary": summary,
        "text": s["text"],
        "dependencies": [deps.get(d, {"id": d, "status": "unknown"}) for d in summary["blocked_by"]],
        "readiness": catalog.readiness(sid),
        "branch_suggestion": catalog.suggest_branch(sid, s["meta"].get("title", "")),
        "is_next": sid == next_id,
        "runs": db.runs(sid),
        "tokens": db.token_totals(sid),
    }


# --- runs ------------------------------------------------------------------------------------

class ImplementBody(BaseModel):
    branch: str
    scaffold: bool = False
    override_reason: str = ""


class ReviewBody(BaseModel):
    action: str          # approve | reject
    note: str = ""


class ResumeBody(BaseModel):
    from_step: str = ""


def _guard(fn, *args, **kw):
    try:
        return fn(*args, **kw)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(409, str(e))


@app.post("/api/stories/{sid}/analyze")
def analyze(sid: str) -> dict:
    return {"run_id": _guard(runner.start_analysis, sid)}


class AnswerItem(BaseModel):
    question: str
    answer: str


class AnswersBody(BaseModel):
    answers: list[AnswerItem]


@app.get("/api/stories/{sid}/answers")
def get_answers(sid: str) -> dict:
    return {"answers": db.answers(sid)}


@app.put("/api/stories/{sid}/answers")
def put_answers(sid: str, body: AnswersBody) -> dict:
    db.save_answers(sid, [a.model_dump() for a in body.answers])
    return {"answers": db.answers(sid)}


@app.post("/api/stories/{sid}/preflight")
def preflight(sid: str, body: ImplementBody) -> dict:
    errors, _ = runner.preflight(sid, body.branch, body.override_reason)
    return {"ok": not errors, "errors": errors}


@app.post("/api/stories/{sid}/implement")
def implement(sid: str, body: ImplementBody) -> dict:
    return {"run_id": _guard(runner.start_implementation, sid, body.branch, body.scaffold,
                             body.override_reason)}


@app.get("/api/runs")
def runs() -> list:
    return db.runs(limit=100)


@app.get("/api/runs/{rid}")
def run(rid: str) -> dict:
    r = db.run(rid)
    if not r:
        raise HTTPException(404, "unknown run")
    r["steps"] = db.steps(rid)
    r["active"] = runner.active == rid
    return r


@app.post("/api/runs/{rid}/stop")
def stop(rid: str) -> dict:
    _guard(runner.stop, rid)
    return {"ok": True}


@app.post("/api/runs/{rid}/resume")
def resume(rid: str, body: ResumeBody = ResumeBody()) -> dict:
    _guard(runner.resume, rid, body.from_step or None)
    return {"ok": True}


@app.post("/api/runs/{rid}/reset")
def reset(rid: str) -> dict:
    return _guard(runner.reset, rid)


@app.post("/api/stories/{sid}/restart")
def restart(sid: str) -> dict:
    return _guard(runner.restart_story, sid)


@app.get("/api/runs/{rid}/diff")
def diff(rid: str) -> dict:
    r = db.run(rid)
    if not r or r["kind"] != "implementation":
        raise HTTPException(404, "unknown implementation run")
    target = ROOT if r["target_repo"] in (".", "") else os.path.join(ROOT, r["target_repo"])
    _, stat = catalog.git(target, "diff", "--stat", r["base_ref"])
    _, log = catalog.git(target, "log", "--format=%h %s", f"{r['base_ref']}..{r['branch']}")
    loop = r["context"].get("loop") or {}
    return {"target": r["target_repo"], "branch": r["branch"], "base": r["base_ref"],
            "stat": stat, "commits": [c for c in log.splitlines() if c.strip()],
            "uncommitted": catalog.dirty_files(target),
            "diff": runner_mod.run_story.review_diff(target, r["base_ref"]),
            "review": loop.get("result:review", ""), "plan": loop.get("plan_file_path", ""),
            "push_cmd": ("git push -u origin " if target == ROOT else f"git -C {r['target_repo']} push -u origin ")
                        + r["branch"],
            "compare_url": _compare_url(target, r["branch"]),
            "record_cmd": ("uv run --with-requirements harness/drivers/requirements.txt python "
                           f"harness/run_story.py record {r['story_id']}") if target != ROOT else ""}


@app.post("/api/runs/{rid}/review")
def review(rid: str, body: ReviewBody) -> dict:
    return _guard(runner.complete_review, rid, body.action, body.note)


@app.get("/api/runs/{rid}/events")
async def events(rid: str, request: Request, after: int = 0) -> StreamingResponse:
    """Server-sent events: every console line after `after`, then a status line whenever
    the run or its steps change. Reconnecting browsers resume from Last-Event-ID."""
    last = int(request.headers.get("last-event-id") or after or 0)

    async def stream():
        nonlocal last
        prev_state = None
        while not await request.is_disconnected():
            batch = db.events(rid, last)
            for e in batch:
                last = e["id"]
                yield f"id: {e['id']}\nevent: line\ndata: {json.dumps(e)}\n\n"
            r = db.run(rid)
            if r:
                state = (r["status"], tuple((s["status"], s["input_tokens"], s["output_tokens"])
                                            for s in db.steps(rid)))
                if state != prev_state:
                    prev_state = state
                    yield f"event: status\ndata: {json.dumps({'status': r['status']})}\n\n"
            if not batch and (not r or (runner.active != rid and r["status"] not in ("queued", "running"))):
                # Finished run and every line sent: tell the browser to stop listening.
                yield "event: end\ndata: {}\n\n"
                return
            if not batch:
                await asyncio.sleep(0.4)

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("STUDIO_PORT", "8765"))
    print(f"Harness Studio on http://127.0.0.1:{port}  (repo {ROOT})")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
