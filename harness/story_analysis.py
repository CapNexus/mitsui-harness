"""Story readiness and confidence: the harness's judgment of whether a story can be built now.

Two parts, combined into one confidence score (0-100):

  * readiness (40%): deterministic facts from the story front-matter, the dependency
    register (`user-stories/dependencies/README.md`) and `user-stories/config/parameters.md`;
  * analysis (60%): the read-only Kiro `reviewer` reads the story and the documents that
    decide it (`.kiro/prompts/analyze_story.md`) and scores clarity, decided design,
    available inputs, testability and scope.

Caps: an unfinished story dependency caps the score at 40, an open type C/D/E dependency
(approval, Mitsui action, design decision) at 60, executor `human` at 0. 80 or more is the
threshold to start the plan_build loop.

Used by `harness/run_story.py analyze <id>` and by Harness Studio; both get the same result.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from typing import Callable, Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "harness", "drivers"))
sys.path.insert(0, os.path.join(ROOT, "harness"))

import prompts  # noqa: E402
import run_story  # noqa: E402

PROMPTS_DIR = os.path.join(ROOT, ".kiro", "prompts")
DEP_REGISTER = os.path.join(ROOT, "user-stories", "dependencies", "README.md")
PARAMETERS = os.path.join(ROOT, "user-stories", "config", "parameters.md")

THRESHOLD = 80
AGENT_WEIGHT = 0.6
HUMAN_DEP_TYPES = {"C", "D", "E"}


def _rel(path: str) -> str:
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def _read(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def load_dependencies() -> Dict[str, dict]:
    out = {}
    for line in _read(DEP_REGISTER).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 6 and re.fullmatch(r"DEP-\d\d", cells[0]):
            out[cells[0]] = {"id": cells[0], "what": cells[1], "owner": cells[2],
                             "needed_by": cells[3], "type": cells[4], "status": cells[5]}
    return out


def load_parameters() -> Dict[str, dict]:
    out = {}
    for line in _read(PARAMETERS).splitlines():
        m = re.match(r"^\|\s*`([a-z0-9_]+)`\s*\|(.*)$", line)
        if m:
            cells = [c.strip() for c in m.group(2).strip().strip("|").split("|")]
            status = cells[-1] if cells else ""
            out[m.group(1)] = {"name": m.group(1),
                               "status": status if status in ("set", "placeholder") else "n/a"}
    return out


def _params(meta: Dict[str, str]) -> List[str]:
    return [p.replace("(proposed)", "").strip() for p in run_story._list_field(meta.get("params", ""))]


# --- readiness ------------------------------------------------------------------------------

def readiness(sid: str) -> dict:
    stories = run_story.load_stories()
    if sid not in stories:
        raise KeyError(f"no story {sid}")
    s = stories[sid]
    m = s["meta"]
    deps, params = load_dependencies(), load_parameters()
    factors: List[dict] = []
    cap = 100

    def add(name: str, ok: bool, weight: int, detail: str, level: str = "") -> None:
        factors.append({"name": name, "ok": ok, "weight": weight, "detail": detail,
                        "level": level or ("ok" if ok else "warn")})

    status = m.get("status", "")
    add("Story status", status == "ready", 15, f"status is `{status}`")
    if status not in ("ready", "in-progress"):
        cap = min(cap, 50)

    executor = m.get("executor", "")
    add("Executor", executor in ("agent", "mixed"), 10, f"executor is `{executor}`")
    if executor == "human":
        cap = 0

    waiting = [d for d in run_story._list_field(m.get("depends_on_stories", ""))
               if stories.get(d, {}).get("meta", {}).get("status") != "done"]
    add("Story dependencies", not waiting, 25,
        "all done" if not waiting else "not done: " + ", ".join(waiting), "ok" if not waiting else "block")
    if waiting:
        cap = min(cap, 40)

    human_open, value_open, unknown = [], [], []
    for d in run_story._list_field(m.get("blocked_by", "")):
        row = deps.get(d)
        if not row:
            unknown.append(d)
        elif row["status"] != "resolved":
            types = set(re.findall(r"[A-E]", row["type"]))
            (human_open if types & HUMAN_DEP_TYPES else value_open).append(
                f"{d} ({row['type']}, {row['status']})")
    add("Approvals, access, decisions (DEP type C, D, E)", not human_open, 20,
        "none open" if not human_open else "open: " + ", ".join(human_open),
        "ok" if not human_open else "block")
    if human_open:
        cap = min(cap, 60)
    add("Values (DEP type A, B)", True, 0,
        "none open" if not value_open else "open, built against placeholders: " + ", ".join(value_open),
        "ok" if not value_open else "info")
    if unknown:
        add("Unknown DEP IDs", False, 0, ", ".join(unknown))

    used = _params(m)
    missing = [p for p in used if p not in params]
    placeholders = [p for p in used if params.get(p, {}).get("status") == "placeholder"]
    add("Parameters exist in config", not missing, 10,
        "all present" if not missing else "missing from parameters.md: " + ", ".join(missing))
    add("Parameter values", True, 0, "all set" if not placeholders else "placeholders: " + ", ".join(placeholders),
        "ok" if not placeholders else "info")

    text = s["text"]
    ac = text.split("## Acceptance criteria", 1)[1].split("\n## ", 1)[0] if "## Acceptance criteria" in text else ""
    n = len(re.findall(r"^\d+\.\s", ac, re.M))
    vg = len(re.findall(r"^\s+- (verify|gate):", ac, re.M))
    add("Acceptance criteria are checkable", n > 0 and vg >= n, 20, f"{n} criteria, {vg} with verify/gate")

    repo = m.get("repo", "planning")
    ok = repo == "planning" or os.path.exists(os.path.join(ROOT, repo, ".git"))
    add("Target repository", ok, 0,
        f"{repo} " + ("ready" if ok else "not checked out (git submodule update --init)"),
        "ok" if ok else "block")

    total = sum(f["weight"] for f in factors) or 1
    score = round(100 * sum(f["weight"] for f in factors if f["ok"]) / total)
    return {"score": score, "cap": cap, "factors": factors}


def relevant_docs(sid: str) -> List[str]:
    stories = run_story.load_stories()
    s = stories[sid]
    feature_dir = os.path.dirname(os.path.dirname(s["path"]))
    paths = [s["path"], os.path.join(feature_dir, "feature.md"), DEP_REGISTER, PARAMETERS,
             os.path.join(ROOT, "user-stories", "WDA-POC-Feature-List.md"),
             os.path.join(ROOT, "user-stories", "docs", "0002-repo-structure-and-roles.md")]
    paths += [stories[d]["path"] for d in run_story._list_field(s["meta"].get("depends_on_stories", ""))
              if d in stories]
    for pattern in ("adr/*.md", "knowledge/*.md", "harness/context/**/*.md", ".kiro/steering/*.md"):
        paths += sorted(glob.glob(os.path.join(ROOT, pattern), recursive=True))
    seen, out = set(), []
    for p in paths:
        if os.path.isfile(p) and p not in seen:
            seen.add(p)
            out.append(_rel(p))
    return out


# --- agent analysis and score ---------------------------------------------------------------

def format_decisions(decisions: Optional[List[dict]]) -> str:
    """Human answers as settled decisions for the prompt; blank answers are ignored."""
    given = [d for d in (decisions or []) if d.get("answer", "").strip()]
    lines = [f"{i}. Q: {d['question'].strip()}\n   A: {d['answer'].strip()}" for i, d in enumerate(given, 1)]
    return "\n".join(lines) if lines else "(none)"


def analyze(sid: str, ready: dict, invoke: Optional[Callable[..., str]] = None,
            decisions: Optional[List[dict]] = None) -> dict:
    """One read-only Kiro `reviewer` turn. Returns the parsed <<<ANALYSIS>>> object.

    `decisions` are `{"question", "answer"}` pairs a human settled after an earlier analysis."""
    if invoke is None:
        from agents import invoke_kiro as invoke  # noqa: E402
    story = run_story.load_stories()[sid]
    rendered = prompts.render(PROMPTS_DIR, "analyze_story",
                              story=f"Source: {_rel(story['path'])}\n\n{story['text']}",
                              docs="\n".join(f"- {d}" for d in relevant_docs(sid)),
                              readiness=ready, decisions=format_decisions(decisions))
    reply = invoke(rendered.text, agent="reviewer", step="analyze", template="analyze_story",
                   params={"story": sid})
    block = prompts.extract(reply, "ANALYSIS")
    if block is None:
        raise RuntimeError("analyze_story reply had no <<<ANALYSIS>>> envelope")
    return json.loads(block)


def score(ready: dict, analysis: dict) -> dict:
    agent_score = int(analysis.get("confidence", 0))
    blended = round(AGENT_WEIGHT * agent_score + (1 - AGENT_WEIGHT) * ready["score"])
    final = min(blended, ready["cap"])
    return {**analysis, "confidence": final, "agent": agent_score, "readiness": ready["score"],
            "cap": ready["cap"], "capped": blended > ready["cap"], "threshold": THRESHOLD,
            "ready_to_start": final >= THRESHOLD, "factors": ready["factors"]}


def run(sid: str, invoke: Optional[Callable[..., str]] = None,
        decisions: Optional[List[dict]] = None) -> dict:
    ready = readiness(sid)
    return score(ready, analyze(sid, ready, invoke, decisions))
