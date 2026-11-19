"""Read the planning repo: features, stories, dependencies, parameters and readiness.

Story files under user-stories/features/*/stories/ are the source of truth (ADR 0001).
Story discovery and the "runnable" rule reuse harness/run_story.py so the web app and
the CLI never disagree about which story is next.
"""

from __future__ import annotations

import glob
import os
import re
import subprocess
from typing import Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FEATURES = os.path.join(ROOT, "user-stories", "features")
DEP_REGISTER = os.path.join(ROOT, "user-stories", "dependencies", "README.md")
PARAMETERS = os.path.join(ROOT, "user-stories", "config", "parameters.md")

import sys  # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "harness"))
import run_story  # noqa: E402  (shipped wrapper, read-only use)

SUBMODULES = run_story.SUBMODULES

# Dependency types that a placeholder cannot stand in for (README "Types").
HUMAN_DEP_TYPES = {"C", "D", "E"}
RESOLVED = {"resolved"}


def rel(path: str) -> str:
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def _read(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


# --- features and stories --------------------------------------------------------------------

def load_features() -> List[dict]:
    out = []
    for path in sorted(glob.glob(os.path.join(FEATURES, "F*", "feature.md"))):
        meta = run_story._front_matter(_read(path))
        folder = os.path.basename(os.path.dirname(path))
        out.append({
            "id": meta.get("id", folder[:3]),
            "folder": folder,
            "title": meta.get("title", folder),
            "sow": meta.get("sow", ""),
            "due": meta.get("due", ""),
            "status": meta.get("status", ""),
            "path": rel(path),
        })
    return out


def load_stories() -> Dict[str, dict]:
    return run_story.load_stories()


def list_field(v: str) -> List[str]:
    return run_story._list_field(v or "")


def story_summary(sid: str, s: dict, stories: Dict[str, dict], runnable_ids: List[str]) -> dict:
    m = s["meta"]
    deps = list_field(m.get("depends_on_stories", ""))
    waiting = [d for d in deps if stories.get(d, {}).get("meta", {}).get("status") != "done"]
    folder = os.path.basename(os.path.dirname(os.path.dirname(s["path"])))
    if m.get("status") == "done":
        state = "done"
    elif sid in runnable_ids:
        state = "runnable"
    elif m.get("executor") == "human":
        state = "human"
    elif m.get("status") == "ready":
        state = "waiting"
    else:
        state = m.get("status", "draft")
    return {
        "id": sid,
        "feature_folder": folder,
        "feature": m.get("feature", ""),
        "title": m.get("title", ""),
        "tier": m.get("tier", ""),
        "executor": m.get("executor", ""),
        "owner": m.get("owner", ""),
        "repo": m.get("repo", "planning"),
        "status": m.get("status", ""),
        "due": m.get("due", ""),
        "blocked_by": list_field(m.get("blocked_by", "")),
        "depends_on": deps,
        "waiting_on": waiting,
        "params": [p.replace("(proposed)", "").strip() for p in list_field(m.get("params", ""))],
        "human_gates": list_field(m.get("human_gates", "")),
        "state": state,
        "path": rel(s["path"]),
    }


def overview() -> Tuple[List[dict], List[dict], Optional[str]]:
    stories = load_stories()
    runnable_ids = run_story.runnable(stories)
    summaries = [story_summary(sid, s, stories, runnable_ids) for sid, s in stories.items()]
    summaries.sort(key=lambda x: x["id"])
    return load_features(), summaries, (runnable_ids[0] if runnable_ids else None)


def next_reason(sid: Optional[str], summaries: List[dict]) -> str:
    if not sid:
        return "No story is ready, agent-executable and free of unfinished story dependencies."
    s = next(x for x in summaries if x["id"] == sid)
    return (f"Earliest due ({s['due']}) story that is `ready`, executor `{s['executor']}`, "
            f"with every depends_on story done.")


# --- dependency register and parameters ---------------------------------------------------

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
        if not m:
            continue
        cells = [c.strip() for c in m.group(2).strip().strip("|").split("|")]
        status = cells[-1] if cells else ""
        out[m.group(1)] = {"name": m.group(1), "status": status if status in ("set", "placeholder") else "n/a",
                           "value": cells[1] if len(cells) > 1 else ""}
    return out


# --- deterministic readiness (half of the confidence score) --------------------------------

def readiness(sid: str) -> dict:
    """Facts the harness can check without an agent. Returns a 0-100 score, a cap that the
    final confidence can never exceed, and each factor with its reason."""
    stories = load_stories()
    if sid not in stories:
        raise KeyError(sid)
    s = stories[sid]
    m = s["meta"]
    deps = load_dependencies()
    params = load_parameters()
    factors: List[dict] = []
    cap = 100

    def add(name: str, ok: bool, weight: int, detail: str, level: str = "") -> None:
        factors.append({"name": name, "ok": ok, "weight": weight, "detail": detail,
                        "level": level or ("ok" if ok else "warn")})

    status = m.get("status", "")
    add("Story status", status == "ready", 15, f"status is `{status}`"
        + ("" if status == "ready" else " (only `ready` stories should be built)"))
    if status not in ("ready", "in-progress"):
        cap = min(cap, 50)

    executor = m.get("executor", "")
    add("Executor", executor in ("agent", "mixed"), 10, f"executor is `{executor}`")
    if executor == "human":
        cap = 0

    waiting = [d for d in list_field(m.get("depends_on_stories", ""))
               if stories.get(d, {}).get("meta", {}).get("status") != "done"]
    add("Story dependencies", not waiting, 25,
        "all done" if not waiting else "not done: " + ", ".join(waiting), "ok" if not waiting else "block")
    if waiting:
        cap = min(cap, 40)

    human_open, placeholder_open, unknown = [], [], []
    for d in list_field(m.get("blocked_by", "")):
        row = deps.get(d)
        if not row:
            unknown.append(d)
            continue
        if row["status"] in RESOLVED:
            continue
        types = set(re.findall(r"[A-E]", row["type"]))
        (human_open if types & HUMAN_DEP_TYPES else placeholder_open).append(f"{d} ({row['type']}, {row['status']})")
    add("Approvals/access/decisions (DEP type C, D, E)", not human_open, 20,
        "none open" if not human_open else "open: " + ", ".join(human_open),
        "ok" if not human_open else "block")
    if human_open:
        cap = min(cap, 60)
    add("Values (DEP type A, B)", True, 0,
        "none open" if not placeholder_open else "open, built against placeholders: " + ", ".join(placeholder_open),
        "ok" if not placeholder_open else "info")
    if unknown:
        add("Unknown DEP IDs", False, 0, ", ".join(unknown), "warn")

    used = [p.replace("(proposed)", "").strip() for p in list_field(m.get("params", ""))]
    missing = [p for p in used if p not in params]
    placeholders = [p for p in used if params.get(p, {}).get("status") == "placeholder"]
    add("Parameters exist in config", not missing, 10,
        "all present" if not missing else "missing from parameters.md: " + ", ".join(missing))
    add("Parameter values", True, 0,
        "all set" if not placeholders else "placeholders: " + ", ".join(placeholders),
        "ok" if not placeholders else "info")

    text = s["text"]
    ac = text.split("## Acceptance criteria", 1)[1].split("\n## ", 1)[0] if "## Acceptance criteria" in text else ""
    n = len(re.findall(r"^\d+\.\s", ac, re.M))
    vg = len(re.findall(r"^\s+- (verify|gate):", ac, re.M))
    add("Acceptance criteria are checkable", n > 0 and vg >= n, 20,
        f"{n} criteria, {vg} with verify/gate")

    repo = m.get("repo", "planning")
    target_ok, target_detail = True, "planning repo"
    if repo != "planning":
        path = os.path.join(ROOT, repo)
        target_ok = os.path.exists(os.path.join(path, ".git"))
        target_detail = f"{repo} " + ("checked out" if target_ok else "not checked out (git submodule update --init)")
    add("Target repository", target_ok, 0, target_detail, "ok" if target_ok else "block")

    total = sum(f["weight"] for f in factors) or 1
    score = round(100 * sum(f["weight"] for f in factors if f["ok"]) / total)
    return {"score": score, "cap": cap, "factors": factors}


# --- context the analysis agent should read -------------------------------------------------

def relevant_docs(sid: str) -> List[str]:
    stories = load_stories()
    s = stories[sid]
    feature_dir = os.path.dirname(os.path.dirname(s["path"]))
    paths = [s["path"], os.path.join(feature_dir, "feature.md"), DEP_REGISTER, PARAMETERS,
             os.path.join(ROOT, "user-stories", "WDA-POC-Feature-List.md"),
             os.path.join(ROOT, "user-stories", "docs", "0002-repo-structure-and-roles.md")]
    for d in list_field(s["meta"].get("depends_on_stories", "")):
        if d in stories:
            paths.append(stories[d]["path"])
    paths += sorted(glob.glob(os.path.join(ROOT, "adr", "*.md")))
    paths += sorted(glob.glob(os.path.join(ROOT, "knowledge", "*.md")))
    paths += sorted(glob.glob(os.path.join(ROOT, "harness", "context", "**", "*.md"), recursive=True))
    paths += sorted(glob.glob(os.path.join(ROOT, ".kiro", "steering", "*.md")))
    seen, out = set(), []
    for p in paths:
        if os.path.isfile(p) and p not in seen:
            seen.add(p)
            out.append(rel(p))
    return out


# --- git helpers ------------------------------------------------------------------------------

def git(target: str, *args: str) -> Tuple[int, str]:
    r = subprocess.run(["git", "-C", target, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout + r.stderr).strip()


def target_dir(meta: Dict[str, str]) -> str:
    repo = meta.get("repo", "planning")
    if repo == "planning":
        return ROOT
    if repo not in SUBMODULES:
        raise ValueError(f"story repo `{repo}` is not planning or one of {SUBMODULES}")
    return os.path.join(ROOT, repo)


def dirty_files(target: str) -> List[str]:
    code, out = git(target, "status", "--porcelain")
    if code != 0:
        return [out]
    # Same exemption as run_story.py: the parent may show moved submodule pointers.
    return [ln for ln in out.splitlines()
            if ln.strip() and not (target == ROOT and ln[3:].strip() in SUBMODULES)]


def slug(text: str, limit: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if len(s) <= limit:
        return s
    cut = s[:limit + 1]
    return (cut.rsplit("-", 1)[0] if "-" in cut else s[:limit]).rstrip("-")


def suggest_branch(sid: str, title: str) -> str:
    return f"story/{sid}-{slug(title)}" if title else f"story/{sid}"


def valid_branch(name: str) -> bool:
    r = subprocess.run(["git", "check-ref-format", "--branch", name], capture_output=True)
    return r.returncode == 0 and name.startswith("story/")
