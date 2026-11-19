"""Run one user story through the plan_build loop, in the repository its `repo:` names.

The drivers (harness/drivers/) run the loop; the code lives in git submodules (ADR
user-stories/docs/0002). This wrapper points the loop at the story's repository:

  * git (changed-file discovery, commits) and scripts/validate.sh run inside that repo
    (`PlanBuildContext.repo_dir`, HARNESS_TARGET_REPO) against the base commit;
  * every agent prompt starts with which repo to work in, and the review step gets the
    real diff (the reviewer agent has no shell);
  * work happens on a `story/<id>` branch (or `--branch`) inside that repo.

Kiro agents, hooks, steering and prompts stay in this parent repo (the process cwd), so
the tool boundaries and guards apply unchanged. Harness Studio calls `prepare()`,
`resume()` and `make_context()` from here, so the CLI and the web app run stories the
same way.

    uv run python harness/run_story.py list                  # runnable stories, first one first
    uv run python harness/run_story.py analyze F02-S02       # readiness + Kiro analysis -> confidence
    uv run python harness/run_story.py run --next            # run the first runnable story
    uv run python harness/run_story.py run F02-S02 --scaffold   # human unlock: first code in a repo
    uv run python harness/run_story.py record F02-S02        # after the submodule PR is merged

Prerequisites: `uv pip install -r harness/drivers/requirements.txt`, `kiro-cli` on PATH,
and AEW_AUTO_APPROVE=1 (the agents cannot write or run commands without it).
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Callable, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORIES = os.path.join(ROOT, "user-stories", "features")
SUBMODULES = ("project-mep-AWS-Infrastructure", "project-mep-AWS-Code")
VALIDATOR = os.path.join(ROOT, "scripts", "validate.sh").replace(os.sep, "/")
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


def default_branch(sid: str) -> str:
    return f"story/{sid}"


# --- git in the target repo -----------------------------------------------------------------

def git(target: str, *args: str) -> Tuple[int, str]:
    r = subprocess.run(["git", "-C", target, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout + r.stderr).strip()


def must(target: str, *args: str) -> str:
    code, out = git(target, *args)
    if code != 0:
        raise SystemExit(f"git -C {target} {' '.join(args)} failed:\n{out}")
    return out


def dirty(target: str) -> List[str]:
    return [line for line in must(target, "status", "--porcelain").splitlines()
            if line.strip() and not (target == ROOT and line[3:].strip() in SUBMODULES)]


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


# --- preparing a run ------------------------------------------------------------------------

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


@dataclass
class StoryRun:
    """What a story run needs to (re)start: persisted by callers that resume."""
    sid: str
    target: str          # absolute path of the repo the story changes
    branch: str
    base_ref: str        # commit the branch was created from
    base_name: str       # branch name it was created from, for messages
    scaffold: bool = False

    @property
    def target_rel(self) -> str:
        return os.path.relpath(self.target, ROOT).replace(os.sep, "/")

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "StoryRun":
        return StoryRun(**{k: d[k] for k in ("sid", "target", "branch", "base_ref", "base_name", "scaffold")})


def preflight(sid: str, branch: Optional[str] = None) -> Tuple[List[str], Optional[str]]:
    """Problems that stop a run, and the target repo. Never changes anything."""
    if os.getenv("AEW_AUTO_APPROVE", "").lower() not in ("1", "true", "yes"):
        problems = ["set AEW_AUTO_APPROVE=1 first: without it every agent tool call is denied"]
    else:
        problems = []
    stories = load_stories()
    if sid not in stories:
        return problems + [f"no story file for {sid} under user-stories/features/*/stories/"], None
    meta = stories[sid]["meta"]
    if meta.get("executor") == "human":
        problems.append(f"{sid} is executor: human; the harness does not run it")
    try:
        target = target_dir(meta)
    except SystemExit as e:
        return problems + [str(e)], None
    left = dirty(target)
    if left:
        problems.append(f"{os.path.relpath(target, ROOT)} has uncommitted changes; commit or stash them "
                        "first so the story's commits hold only its own work: " + "; ".join(left[:10]))
    branch = branch or default_branch(sid)
    if subprocess.run(["git", "check-ref-format", "--branch", branch], capture_output=True).returncode != 0:
        problems.append(f"`{branch}` is not a valid branch name")
    else:
        if git(target, "rev-parse", "--abbrev-ref", "HEAD")[1] == branch:
            problems.append(f"already on {branch}; check out the base branch first")
        elif git(target, "rev-parse", "--verify", "--quiet", branch)[0] == 0:
            problems.append(f"branch {branch} already exists in {target}; delete it or finish that run")
    return problems, target


def _set_env(sr: StoryRun) -> None:
    os.environ["HARNESS_TARGET_REPO"] = sr.target
    os.environ["VALIDATE_BASE_REF"] = sr.base_ref
    if sr.scaffold:
        os.environ["VALIDATE_SCAFFOLD"] = "1"
    else:
        os.environ.pop("VALIDATE_SCAFFOLD", None)


def prepare(sid: str, scaffold: bool = False, branch: Optional[str] = None) -> StoryRun:
    """Check, create the story branch in the target repo, and set the validator environment."""
    problems, target = preflight(sid, branch)
    if problems:
        raise SystemExit("\n".join(problems))
    branch = branch or default_branch(sid)
    base_name = must(target, "rev-parse", "--abbrev-ref", "HEAD")
    base_ref = must(target, "rev-parse", "HEAD")
    must(target, "checkout", "-b", branch)
    sr = StoryRun(sid, target, branch, base_ref, base_name, scaffold)
    _set_env(sr)
    return sr


def resume(sr: StoryRun) -> None:
    """Back on the story branch with the run's environment (after a stop or a restart)."""
    if git(sr.target, "rev-parse", "--abbrev-ref", "HEAD")[1] != sr.branch:
        must(sr.target, "checkout", sr.branch)
    _set_env(sr)


def issue_text(sr: StoryRun) -> str:
    story = load_stories()[sr.sid]
    pre = preamble(sr.sid, story["meta"], sr.target)
    return (f"{pre}# {sr.sid}: {story['meta'].get('title', '')}\n\nSource: "
            f"{os.path.relpath(story['path'], ROOT).replace(os.sep, '/')}\n\n{story['text']}")


def make_context(sr: StoryRun, run_dir: str, invoke: Optional[Callable[..., str]] = None, **hooks):
    """The PlanBuildContext for this story: target repo, base, validator, and an invoke that
    prefixes the repository preamble and gives the reviewer the real diff."""
    import run_plan_build as rpb  # noqa: E402
    from agents import invoke_kiro  # noqa: E402

    base_invoke = invoke or invoke_kiro
    pre = preamble(sr.sid, load_stories()[sr.sid]["meta"], sr.target)

    def story_invoke(text: str, **kw) -> str:
        if kw.get("step") == "review":
            text += ("\n\n## The actual change under review (from git, not from the builder)\n\n"
                     + review_diff(sr.target, sr.base_ref))
        return base_invoke(pre + text, **kw)

    return rpb.PlanBuildContext(sr.sid, issue_text(sr), rpb.PROMPTS_DIR, "builder", "reviewer",
                                run_dir, base_ref=sr.base_ref, repo_dir=sr.target,
                                invoke=story_invoke, validator=VALIDATOR, **hooks)


# --- CLI commands ---------------------------------------------------------------------------

def run(sid: str, scaffold: bool, branch: Optional[str] = None) -> int:
    import run_plan_build as rpb  # noqa: E402
    from agents import set_audit_sink  # noqa: E402
    from audit import AuditSink  # noqa: E402

    sr = prepare(sid, scaffold, branch)
    if scaffold:
        print(f"scaffold unlock: protected configs may be ADDED in {sr.target} for this run only")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    set_audit_sink(AuditSink(f"plan_build-{stamp}", base_dir="agents", trigger_type="plan_build"))
    pbc = make_context(sr, os.path.join(".harness-runs", f"{stamp}-{sid}"))
    try:
        results = rpb.run_pbc(pbc)
        ok, detail = True, ""
    except Exception as e:  # noqa: BLE001
        results, ok, detail = [], False, str(e)
    for r in results:
        print(f"{'ok' if r.ok else 'FAILED'}  {r.kind:12s} {r.name}")
    if not ok:
        print(f"\n{sid} FAILED: {detail}\nThe work so far is on branch {sr.branch} in {sr.target_rel}.")
        return 1
    meta = load_stories()[sid]["meta"]
    print(f"\n{sid} passed the loop and is committed on {sr.branch} in {sr.target_rel}.\nNext (human): "
          "review the commits"
          + ("" if sr.target == ROOT else
             f", then  git -C {sr.target_rel} push -u origin {sr.branch}   # open a PR in {meta.get('repo')}")
          + f"\n  after the PR is merged: uv run python harness/run_story.py record {sid}")
    return 0


def analyze(sid: str) -> int:
    import story_analysis  # noqa: E402

    result = story_analysis.run(sid)
    print(json.dumps({k: result[k] for k in ("confidence", "agent", "readiness", "cap", "ready_to_start",
                                              "recommendation", "dimensions", "risks", "questions")
                      if k in result}, indent=2))
    return 0 if result["ready_to_start"] else 2


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
    an = sub.add_parser("analyze", help="readiness + Kiro analysis -> confidence (exit 2 if below 80)")
    an.add_argument("story")
    r = sub.add_parser("run")
    r.add_argument("story", nargs="?")
    r.add_argument("--next", action="store_true", help="the first runnable story")
    r.add_argument("--branch", help="branch to create (default story/<id>)")
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
    if a.cmd == "analyze":
        return analyze(a.story)
    if a.cmd == "run":
        sid = a.story
        if a.next:
            ids = runnable(load_stories())
            if not ids:
                raise SystemExit("no runnable story (ready, agent/mixed, dependencies done)")
            sid = ids[0]
        if not sid:
            raise SystemExit("name a story id or pass --next")
        return run(sid, a.scaffold, a.branch)
    return record(a.story)


if __name__ == "__main__":
    sys.exit(main())
