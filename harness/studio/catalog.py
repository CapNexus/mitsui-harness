"""Read-only views of the planning repo for the UI: features, story summaries, next story.

All story rules come from the harness: discovery and the "runnable" rule from
`harness/run_story.py`, readiness and dependencies from `harness/story_analysis.py`.
"""

from __future__ import annotations

import glob
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FEATURES = os.path.join(ROOT, "user-stories", "features")

sys.path.insert(0, os.path.join(ROOT, "harness"))
sys.path.insert(0, os.path.join(ROOT, "harness", "drivers"))
import run_story  # noqa: E402
import story_analysis  # noqa: E402

SUBMODULES = run_story.SUBMODULES
load_stories = run_story.load_stories
load_dependencies = story_analysis.load_dependencies
readiness = story_analysis.readiness


def rel(path: str) -> str:
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def list_field(v: str) -> List[str]:
    return run_story._list_field(v or "")


def load_features() -> List[dict]:
    out = []
    for path in sorted(glob.glob(os.path.join(FEATURES, "F*", "feature.md"))):
        with open(path, encoding="utf-8") as fh:
            meta = run_story._front_matter(fh.read())
        folder = os.path.basename(os.path.dirname(path))
        out.append({"id": meta.get("id", folder[:3]), "folder": folder, "title": meta.get("title", folder),
                    "sow": meta.get("sow", ""), "due": meta.get("due", ""), "status": meta.get("status", ""),
                    "path": rel(path)})
    return out


def story_summary(sid: str, s: dict, stories: Dict[str, dict], runnable_ids: List[str]) -> dict:
    m = s["meta"]
    deps = list_field(m.get("depends_on_stories", ""))
    waiting = [d for d in deps if stories.get(d, {}).get("meta", {}).get("status") != "done"]
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
        "id": sid, "feature_folder": os.path.basename(os.path.dirname(os.path.dirname(s["path"]))),
        "feature": m.get("feature", ""), "title": m.get("title", ""), "tier": m.get("tier", ""),
        "executor": m.get("executor", ""), "owner": m.get("owner", ""), "repo": m.get("repo", "planning"),
        "status": m.get("status", ""), "due": m.get("due", ""),
        "blocked_by": list_field(m.get("blocked_by", "")), "depends_on": deps, "waiting_on": waiting,
        "human_gates": list_field(m.get("human_gates", "")), "state": state, "path": rel(s["path"]),
    }


def overview() -> Tuple[List[dict], List[dict], Optional[str]]:
    stories = load_stories()
    runnable_ids = run_story.runnable(stories)
    summaries = sorted((story_summary(sid, s, stories, runnable_ids) for sid, s in stories.items()),
                       key=lambda x: x["id"])
    return load_features(), summaries, (runnable_ids[0] if runnable_ids else None)


def next_reason(sid: Optional[str], summaries: List[dict]) -> str:
    if not sid:
        return "No story is ready, agent-executable and free of unfinished story dependencies."
    s = next(x for x in summaries if x["id"] == sid)
    return (f"Earliest due ({s['due']}) story that is `ready`, executor `{s['executor']}`, "
            "with every depends_on story done (same rule as `run_story.py list`).")


def git(target: str, *args: str) -> Tuple[int, str]:
    return run_story.git(target, *args)


def dirty_files(target: str) -> List[str]:
    try:
        return run_story.dirty(target)
    except SystemExit as e:
        return [str(e)]


def slug(text: str, limit: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if len(s) <= limit:
        return s
    cut = s[:limit + 1]
    return (cut.rsplit("-", 1)[0] if "-" in cut else s[:limit]).rstrip("-")


def suggest_branch(sid: str, title: str) -> str:
    """`story/<id>-<title-slug>`; the harness default without a title is `story/<id>`."""
    return f"{run_story.default_branch(sid)}-{slug(title)}" if title else run_story.default_branch(sid)
