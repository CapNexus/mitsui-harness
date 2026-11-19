"""Run one user story through the plan_build loop, in the repository its `repo:` names.

The shipped drivers (harness/drivers/, copied verbatim from harness-bootstrap) assume the
code lives in the repo they run from. Here it lives in git submodules (ADR
user-stories/docs/0002), so this wrapper keeps the drivers unchanged and redirects only
what must follow the story's repository:

  * git (changed-file discovery, the commit steps' file list) runs inside that repo;
  * scripts/validate.sh validates that repo (HARNESS_TARGET_REPO) against its base branch;
  * every agent prompt starts with which repo to work in, and the review step gets the
    real diff (the reviewer agent has no shell);
  * work happens on a `story/<id>` branch inside that repo.

Kiro agents, hooks, steering and prompts stay in this parent repo (the process cwd), so
the tool boundaries and guards apply unchanged.

    uv run python harness/run_story.py list                 # runnable stories, first one first
    uv run python harness/run_story.py run --next           # run the first runnable story
    uv run python harness/run_story.py run F02-S02 --scaffold   # human unlock: first code in a repo
    uv run python harness/run_story.py record F02-S02       # after the submodule PR is merged

Prerequisites: `uv pip install -r harness/drivers/requirements.txt`, `kiro-cli` on PATH,
and AEW_AUTO_APPROVE=1 (the agents cannot write or run commands without it).
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORIES = os.path.join(ROOT, "user-stories", "features")
SUBMODULES = ("project-mep-AWS-Infrastructure", "project-mep-AWS-Code")
DIFF_CAP = 60_000

sys.path.insert(0, os.path.join(ROOT, "harness", "drivers"))


# --- stories --------------------------------------------------------------------------------

def _front_matter(text: str) -> Dict[str, str]:
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.S)
    meta: Dict[str, str] = {}
    for line in (m.group(1).splitlines() if m else []):
        line = line.split(" #", 1)[0].rstrip()
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta


def _list_field(v: str) -> List[str]:
    return [x.strip() for x in v.strip().strip("[]").split(",") if x.strip()]


def load_stories() -> Dict[str, dict]:
    out = {}
    for p in glob.glob(os.path.join(STORIES, "*", "stories", "F*-S*.md")):
        with open(p, encoding="utf-8") as fh:
            text = fh.read()
        meta = _front_matter(text)
        if meta.get("id"):
            out[meta["id"]] = {"meta": meta, "path": p, "text": text}
    return out


def runnable(stories: Dict[str, dict]) -> List[str]:
    """`ready`, agent-executable (agent or mixed), every depends_on story `done`;
    earliest due date first, then id."""
    ids = []
    for sid, s in stories.items():
        m = s["meta"]
        if m.get("status") != "ready" or m.get("executor") not in ("agent", "mixed"):
            continue
        deps = _list_field(m.get("depends_on_stories", ""))
        if all(stories.get(d, {}).get("meta", {}).get("status") == "done" for d in deps):
            ids.append(sid)
    return sorted(ids, key=lambda i: (stories[i]["meta"].get("due", "9999"), i))


def target_dir(meta: Dict[str, str]) -> str:
    repo = meta.get("repo", "planning")
    if repo == "planning":
        return ROOT
    if repo not in SUBMODULES:
        raise SystemExit(f"story repo `{repo}` is not planning or a known submodule {SUBMODULES}")
    path = os.path.join(ROOT, repo)
    if not os.path.exists(os.path.join(path, ".git")):
        raise SystemExit(f"submodule {repo} is not checked out (git submodule update --init)")
    return path


# --- git in the target repo -----------------------------------------------------------------

def git(target: str, *args: str) -> Tuple[int, str]:
    r = subprocess.run(["git", "-C", target, *args], capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def must(target: str, *args: str) -> str:
    code, out = git(target, *args)
    if code != 0:
        raise SystemExit(f"git -C {target} {' '.join(args)} failed:\n{out}")
    return out


def review_diff(target: str, base: str) -> str:
    """Committed + uncommitted changes against the base, plus new untracked files."""
    _, diff = git(target, "diff", base)
    _, untracked = git(target, "ls-files", "--others", "--exclude-standard")
    parts = [f"## git diff {base} (in {os.path.relpath(target, ROOT) or '.'})\n\n{diff}"]
    for rel in [u for u in untracked.splitlines() if u.strip()]:
        try:
            with open(os.path.join(target, rel), encoding="utf-8", errors="replace") as fh:
                parts.append(f"## new file: {rel}\n\n{fh.read()}")
        except OSError:
            parts.append(f"## new file: {rel} (unreadable)")
    text = "\n\n".join(parts)
    return text if len(text) <= DIFF_CAP else text[:DIFF_CAP] + "\n\n[diff truncated]"


# --- the run -------------------------------------------------------------------------------

def preamble(sid: str, meta: Dict[str, str], target: str) -> str:
    rel = os.path.relpath(target, ROOT).replace(os.sep, "/")
    repo = meta.get("repo", "planning")
    if rel == ".":
        where = ("This story changes the PARENT planning repository (repo: planning). Work at "
                 "the repository root. Never edit files inside the submodules "
                 f"{', '.join(SUBMODULES)}.")
        cmds = "Run git and scripts from the repository root."
    else:
        where = (f"This story changes ONLY the submodule `{rel}/` (repo: {repo}). Every file you "
                 f"create or edit MUST be under `{rel}/`; paths in plans, steering rules and checks "
                 f"(lib/, bin/, test/, package.json ...) are relative to `{rel}/`. Never edit "
                 "planning files or the other submodule.")
        cmds = (f"Run git as `git -C {rel} ...` and npm as `npm --prefix {rel} run <script>` "
                f"(or `cd {rel} && ...`). File lists you are given for commits are relative to `{rel}/`.")
    return (f"<<<HARNESS CONTEXT>>>\nStory: {sid}\nTarget repository: {rel}\n{where}\n{cmds}\n"
            "Follow .kiro/steering/project-context.md and .kiro/steering/engineering-standards.md.\n"
            "<<<END HARNESS CONTEXT>>>\n\n")


def run(sid: str, scaffold: bool) -> int:
    if os.getenv("AEW_AUTO_APPROVE", "").lower() not in ("1", "true", "yes"):
        raise SystemExit("set AEW_AUTO_APPROVE=1 first: without it every agent tool call is denied")
    stories = load_stories()
    if sid not in stories:
        raise SystemExit(f"no story file for {sid} under user-stories/features/*/stories/")
    story = stories[sid]
    meta = story["meta"]
    if meta.get("executor") == "human":
        raise SystemExit(f"{sid} is executor: human; the harness does not run it")
    target = target_dir(meta)

    dirty = [line for line in must(target, "status", "--porcelain").splitlines()
             if not (target == ROOT and line[3:].strip() in SUBMODULES)]
    if dirty:
        raise SystemExit(f"{os.path.relpath(target, ROOT)} has uncommitted changes; commit or stash "
                         "them first so the story's commit holds only its own work:\n  "
                         + "\n  ".join(dirty[:20]))
    base = must(target, "rev-parse", "--abbrev-ref", "HEAD")
    branch = f"story/{sid}"
    if base == branch:
        raise SystemExit(f"already on {branch}; check out the base branch first")
    if git(target, "rev-parse", "--verify", branch)[0] == 0:
        raise SystemExit(f"branch {branch} already exists in {target}; delete it or finish that run")
    must(target, "checkout", "-b", branch)

    os.environ["HARNESS_TARGET_REPO"] = target
    os.environ["VALIDATE_BASE_REF"] = base
    if scaffold:
        os.environ["VALIDATE_SCAFFOLD"] = "1"
        print(f"scaffold unlock: protected configs may be ADDED in {target} for this run only")

    import run_plan_build as rpb  # noqa: E402  (shipped driver, unchanged)

    rpb._git = lambda *args: git(target, *args)
    rpb.VALIDATOR = os.path.join(ROOT, "scripts", "validate.sh").replace(os.sep, "/")
    pre = preamble(sid, meta, target)
    real_invoke = rpb.invoke_kiro

    def invoke(text: str, **kw):
        if kw.get("step") == "review":
            text += "\n\n## The actual change under review (from git, not from the builder)\n\n" \
                    + review_diff(target, base)
        return real_invoke(pre + text, **kw)

    rpb.invoke_kiro = invoke
    if not hasattr(os, "killpg"):   # Windows: the validator-timeout path kills a process tree
        os.getpgid = lambda pid: pid                                    # type: ignore[attr-defined]
        os.killpg = lambda pid, _sig: subprocess.run(                   # type: ignore[attr-defined]
            ["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)

    issue = (f"{pre}# {sid}: {meta.get('title', '')}\n\nSource: "
             f"{os.path.relpath(story['path'], ROOT).replace(os.sep, '/')}\n\n{story['text']}")
    ok, results, detail = rpb.run_issue(sid, issue)
    for r in results:
        print(f"{'ok' if r.ok else 'FAILED'}  {r.kind:12s} {r.name}")
    rel = os.path.relpath(target, ROOT)
    if not ok:
        print(f"\n{sid} FAILED: {detail}\nThe work so far is on branch {branch} in {rel}.")
        return 1
    print(f"\n{sid} passed the loop on branch {branch} in {rel}.\nNext (human):"
          + ("" if target == ROOT else
             f"\n  git -C {rel} push -u origin {branch}   # open a PR in {meta.get('repo')}")
          + f"\n  after the PR is merged: uv run python harness/run_story.py record {sid}")
    return 0


def record(sid: str) -> int:
    """ADR 0002 rule 2: record the merged submodule commit and the story status in one
    parent commit. Only the submodule pointer and the story file are committed."""
    stories = load_stories()
    story = stories.get(sid) or sys.exit(f"no story {sid}")
    meta = story["meta"]
    target = target_dir(meta)
    paths = [os.path.relpath(story["path"], ROOT).replace(os.sep, "/")]
    sha = ""
    if target != ROOT:
        rel = os.path.relpath(target, ROOT).replace(os.sep, "/")
        must(target, "fetch", "origin")
        must(target, "checkout", "--detach", "origin/main")
        sha = must(target, "rev-parse", "--short", "HEAD")
        paths.insert(0, rel)
    with open(story["path"], encoding="utf-8") as fh:
        text = fh.read()
    text = re.sub(r"^status:.*$", "status: done", text, count=1, flags=re.M)
    note = f"- {dt.date.today().isoformat()}: done" + (f" (submodule {sha})" if sha else "")
    text = text.rstrip("\n") + "\n" + note + "\n"
    with open(story["path"], "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    must(ROOT, "add", "--", *paths)
    must(ROOT, "commit", "-m", f"Record {sid} done" + (f" ({paths[0]} @ {sha})" if sha else ""),
         "--", *paths)
    print(f"recorded {sid}: " + ", ".join(paths))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    r = sub.add_parser("run")
    r.add_argument("story", nargs="?")
    r.add_argument("--next", action="store_true", help="the first runnable story")
    r.add_argument("--scaffold", action="store_true",
                   help="human unlock: allow ADDING protected configs (first code in a repo)")
    rec = sub.add_parser("record")
    rec.add_argument("story")
    a = ap.parse_args(argv)

    if a.cmd == "list":
        stories = load_stories()
        for sid in runnable(stories):
            m = stories[sid]["meta"]
            print(f"{m.get('due', '?'):10} {sid}  {m.get('executor'):6} {m.get('repo'):32} {m.get('title')}")
        return 0
    if a.cmd == "run":
        sid = a.story
        if a.next:
            ids = runnable(load_stories())
            if not ids:
                raise SystemExit("no runnable story (ready, agent/mixed, dependencies done)")
            sid = ids[0]
        if not sid:
            raise SystemExit("name a story id or pass --next")
        return run(sid, a.scaffold)
    return record(a.story)


if __name__ == "__main__":
    sys.exit(main())
