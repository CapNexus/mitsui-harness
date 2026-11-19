"""Run the whole reservoir, one `queued` PBI at a time: the missing link between
`run_frame.py`'s reservoir and `run_plan_build.py`'s loop.

Shipped by harness-bootstrap into every generated harness that declares BOTH a `loop`- and
a `frame`-shaped workflow (`harness/drivers/run_implement.py`) — nothing else reads
`ready_for_loop` back out of `harness/reservoir.json` and turns it into an `--issue` call.

A PBI's `dependencies` (checked by `atomic_check.py`) are what make this safe for
unattended, multi-PBI runs: an item is never `queued` while any dependency isn't `done`
yet, so there is no topological sort here — picking any `queued` item is always safe, and
finishing one naturally promotes its dependents from `blocked` to `queued` on the next pass.

Usage (run from the repo root, same prerequisites as `run_plan_build.py`/`run_frame.py`)::

    uv run python harness/drivers/run_implement.py init --issue "scaffold the initial project..."
    uv run python harness/drivers/run_implement.py run                   # until empty or a failure
    uv run python harness/drivers/run_implement.py run --max 1            # one PBI, then stop
    uv run python harness/drivers/run_implement.py run --continue-on-failure
    uv run python harness/drivers/run_implement.py status

`init` is the one-time bridge out of the chicken-and-egg start: a requirements-only harness
has no codebase to ground `scope.files` against, so nothing can ever reach `refined` (see
`run_frame.py`'s own note on this). `init` checks whether a codebase already exists under
`--root`; if not, it takes a hand-written `--issue`/`--issue-file` and runs it through
`run_plan_build.py`'s loop directly — bypassing the reservoir entirely, on purpose, since
nothing in it can be promoted yet — then either way regrades the whole reservoir
(`run_frame.py regrade`) against whatever now exists. Safe to call again any time the
codebase has grown since the last regrade; it just skips seeding if one's already there.

What this does NOT do: decide whether a PBI is ready. That is `run_frame.py promote`'s
human gate — `run`/`init` only ever touch items a person already promoted (or, for `init`,
the one hand-picked seed issue).
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atomic_check  # noqa: E402
import run_frame  # noqa: E402
from run_plan_build import run_issue  # noqa: E402
from run_plan_build import PROMPTS_DIR as PLAN_PROMPTS_DIR  # noqa: E402
from run_plan_build import VALIDATOR as PLAN_VALIDATOR  # noqa: E402
from run_plan_build import WORKFLOW_PATH as PLAN_WORKFLOW_PATH  # noqa: E402


def _issue_text(item: dict) -> str:
    """Turn a promoted reservoir PBI into the free-text issue `run_plan_build.run_issue`'s
    classify/plan steps expect."""
    lines = [item.get("title") or item["id"], "", item.get("intent", "")]
    if item.get("user_story"):
        lines += ["", item["user_story"]]
    ac = item.get("acceptance_criteria") or []
    if ac:
        lines += ["", "Acceptance criteria:"] + [f"- {c}" for c in ac]
    return "\n".join(lines).strip() + "\n"


def _queued_ids(items: dict) -> List[str]:
    atomic_check.refresh_status(items)
    return sorted(iid for iid, it in items.items() if it.get("status") == "queued")


def run_one(args: argparse.Namespace) -> Optional[bool]:
    """Claim and implement exactly one `queued` PBI. Returns `None` when nothing was queued
    (not a failure — the backlog may be empty, or everything left is `blocked`), else
    whether the implementation succeeded."""
    res = run_frame.load_reservoir(args.reservoir)
    queued = _queued_ids(res["items"])
    if not queued:
        return None
    iid = queued[0]
    item = res["items"][iid]
    run_id = f"implement-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    item["claim"] = {"run_id": run_id, "claimed_at": datetime.now(timezone.utc).isoformat()}
    atomic_check.refresh_status(res["items"])
    run_frame.save_reservoir(args.reservoir, res)
    print(f"== implementing {iid}: {item.get('title', '')}")

    ok, _results, detail = run_issue(
        iid, _issue_text(item), workflow_path=args.plan_workflow, prompts_dir=args.prompts_dir,
        agent=args.agent, reviewer=args.reviewer)

    res = run_frame.load_reservoir(args.reservoir)        # reload: a run can take a long time
    item = res["items"][iid]
    item.pop("claim", None)
    item["outcome"] = "done" if ok else "failed"
    item.setdefault("run_history", []).append({
        "run_id": run_id, "outcome": item["outcome"], "detail": detail,
        "finished_at": datetime.now(timezone.utc).isoformat()})
    run_frame.save_reservoir(args.reservoir, res)

    # A successful (or even a failed-but-file-touching) implement can grow the codebase,
    # so every other PBI's grounding may have just changed — regrade the whole reservoir,
    # not just this item's status, so `run_frame.py list` is never stale between PBIs.
    res = run_frame.regrade(args.reservoir, args.plan_workflow, args.root)
    item = res["items"][iid]
    print(f"{iid}: {item['status']}" + (f" ({detail})" if detail else ""))
    return ok


def run_init(args: argparse.Namespace) -> None:
    if run_frame.known_files(args.root):
        print(f"a codebase already exists under {args.root!r} -- nothing to seed")
    else:
        if not args.issue and not args.issue_file:
            raise SystemExit(f"no codebase yet under {args.root!r}, and no --issue/--issue-file "
                             "given to seed one")
        issue_text = args.issue
        if args.issue_file:
            with open(args.issue_file, encoding="utf-8") as fh:
                issue_text = fh.read()
        ok, _results, detail = run_issue(
            args.issue_id or "seed", issue_text, workflow_path=args.plan_workflow,
            prompts_dir=args.prompts_dir, agent=args.agent, reviewer=args.reviewer)
        if not ok:
            raise SystemExit(f"seed issue failed: {detail}")
        print("seed issue landed")
        if os.path.isfile(PLAN_VALIDATOR):
            print(f"NOTE: {PLAN_VALIDATOR} now exists -- run it yourself once (`bash "
                  f"{PLAN_VALIDATOR}`) to confirm it's wired correctly before relying on "
                  "red/green/validate.")
        else:
            print(f"NOTE: {PLAN_VALIDATOR} is still a no-op until real lint/test/build "
                  "commands are wired into it -- do that now, before relying on red/green.")

    res = run_frame.regrade(args.reservoir, args.plan_workflow, args.root)
    leaves = [i for i in res["items"].values() if i.get("level") == "pbi"]
    by_status: dict = {}
    for i in leaves:
        s = i.get("status", "raw")
        by_status[s] = by_status.get(s, 0) + 1
    print(f"reservoir regraded: {len(leaves)} PBI(s), by status: {by_status}")


def run_run(args: argparse.Namespace) -> None:
    done = 0
    while args.max is None or done < args.max:
        ok = run_one(args)
        if ok is None:
            print("nothing queued -- stopping")
            break
        done += 1
        if not ok and not args.continue_on_failure:
            print("stopping after the first failure (pass --continue-on-failure to keep going)")
            raise SystemExit(1)
    print(f"implemented {done} PBI(s) this run")


def main(argv: Optional[List[str]] = None) -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--reservoir", default=run_frame.DEFAULT_RESERVOIR)
    p.add_argument("--plan-workflow", default=PLAN_WORKFLOW_PATH)
    p.add_argument("--prompts-dir", default=PLAN_PROMPTS_DIR)
    p.add_argument("--root", default=".", help="where to scan for grounding (default: cwd)")
    p.add_argument("--agent", default="builder")
    p.add_argument("--reviewer", default="reviewer")
    sub = p.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="seed a codebase if none exists yet, then regrade the reservoir")
    init.add_argument("--issue")
    init.add_argument("--issue-file")
    init.add_argument("--issue-id", default=None)
    init.set_defaults(func=run_init)

    run = sub.add_parser("run", help="implement queued PBIs until empty or a failure")
    run.add_argument("--max", type=int, default=None)
    run.add_argument("--continue-on-failure", action="store_true")
    run.set_defaults(func=run_run)

    status = sub.add_parser("status", help="counts by status (same as `run_frame.py status`)")
    status.set_defaults(func=run_frame.run_status)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
