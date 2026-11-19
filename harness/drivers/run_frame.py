"""Run the `frame` shape for real: triage/decompose new items into the reservoir.

Shipped by harness-bootstrap into every generated harness that declares a `frame`-shaped
workflow (`harness/drivers/run_frame.py`) — this is the piece that was missing before: a
real, runnable entrypoint wiring `frame_driver.run_frame` to actual Kiro turns (via
`agents.invoke_kiro`), this harness's own `atomic_check` predicate, and a persisted
reservoir file, using the fixed `TRIAGE`/`DECOMPOSITION` envelope contract every
`frame_triage`/`frame_decompose` prompt is now required to follow (`plan_harness.md`).

This is for ONGOING intake — one new epic/story (or a small batch) at a time, after the
baseline. The one-time intake of a whole requirements set is `bootstrap frame` in
harness-bootstrap itself; its output (`proposal/reservoir/`) is this harness's *starting*
reservoir, not something this script regenerates.

Usage (run from the repo root, with `uv pip install -r harness/drivers/requirements.txt`
and `kiro-cli` on PATH)::

    uv run python harness/drivers/run_frame.py add --title "..." --text "..." [--parent ID]
    uv run python harness/drivers/run_frame.py add --file new_items.json   # one item or a list
    uv run python harness/drivers/run_frame.py status
    uv run python harness/drivers/run_frame.py list [--ready-only]
    uv run python harness/drivers/run_frame.py promote <id> [<id> ...]
    uv run python harness/drivers/run_frame.py regrade   # re-ground every PBI once the codebase has grown
    uv run python harness/drivers/run_frame.py elaborate <id> [<id> ...]   # fix a drafted item's fields/scope
    uv run python harness/drivers/run_frame.py decompose <id> [<id> ...]   # split a too-big item into children

Where the taxonomy and workflow come from: `harness/workflows/plan_build.json`'s `plan`
step `prompt_map` keys ARE this harness's full classification taxonomy (every declared
classification has an entry there — `validate_spec` guarantees it), so this script reads
them from there rather than needing its own copy of the plan.

Budgets (`max_ac`, `max_children`, `max_depth`, `max_files`, `triage_batch`) are not
recorded anywhere in a deployed harness today — only `bootstrap`'s own run used them. The
defaults here match `bootstrap/config.py`'s own defaults; override with the `--max-*` /
`--triage-batch` flags if this harness's plan used different ones.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import deque
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atomic_check  # noqa: E402
import frame_driver  # noqa: E402
from agents import invoke_kiro, set_audit_sink  # noqa: E402
from audit import AuditSink  # noqa: E402

import prompts  # noqa: E402

DEFAULT_RESERVOIR = "harness/reservoir.json"
PROMPTS_DIR = ".kiro/prompts"
WORKFLOW_PATH = "harness/workflows/plan_build.json"
# Never the grounding set: harness scaffolding itself, not the application code a PBI's
# `scope` describes, plus driver-generated runtime state (`agents/` is AuditSink's own
# output dir — same name every run_plan_build.py/run_frame.py invocation uses) and the
# usual VCS/build noise.
_SKIP_DIRS = {".git", ".kiro", "harness", "scripts", ".harness-runs", "agents",
             ".venv", "venv", "node_modules", "__pycache__"}
# The one top-level file `apply()`/`render_kiro` itself writes outside those directories —
# excluded by name since it sits at the repo root, where no directory-skip rule reaches it.
_SKIP_FILES = {"HARNESS.md"}


def known_files(root: str) -> Set[str]:
    """Every file under `root`, relative to it, excluding harness scaffolding and VCS/build
    noise — the grounding set `atomic_check.refined_problems` checks a PBI's `scope.files`
    against, and what `run_implement.py init` checks to decide whether a codebase already
    exists. Always a set, never `None`: this driver runs *in* the target repo, so by the
    time anyone calls `add`, grounding is either real (a codebase landed) or correctly empty
    (nothing has, so every `scope.files` reference stays "unknown" until it does). Hidden
    files (`.gitignore`, ...) are excluded too — never something a PBI's scope references,
    and `.gitignore` alone would otherwise make `init` think a codebase already exists."""
    out: Set[str] = set()
    for dirpath, dirnames, files in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        for f in files:
            if f.startswith(".") or f in _SKIP_FILES:
                continue
            out.add(os.path.relpath(os.path.join(dirpath, f), root))
    return out


# --- reservoir persistence ---------------------------------------------------------------


def load_reservoir(path: str) -> dict:
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {"items": {}, "out_of_scope": [], "not_decomposed": []}


def save_reservoir(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False, sort_keys=True)


def taxonomy_from_workflow(path: str = WORKFLOW_PATH) -> Set[str]:
    with open(path, encoding="utf-8") as fh:
        wf = json.load(fh)
    plan_step = next(s for s in wf["steps"] if s["name"] == "plan")
    pm = plan_step.get("prompt_map")
    return set(pm.keys()) if pm else set()


def _safe_id(raw: str, taken: Set[str]) -> str:
    base = "".join(c if c.isalnum() or c in "-_" else "-" for c in raw.strip().lower())[:60] or "item"
    sid, n = base, 1
    while sid in taken:
        n += 1
        sid = f"{base}-{n}"
    return sid


# --- agent-backed triage / decompose -----------------------------------------------------


def make_triage(prompts_dir: str, agent: str) -> frame_driver.TriageRunner:
    def triage(batch: List[dict]) -> List[dict]:
        payload = [{"id": it["id"], "title": it.get("title", ""), "text": it.get("text", ""),
                   "parent": it.get("parent"), "grounding": []} for it in batch]
        rendered = prompts.render(prompts_dir, "frame_triage", ARGUMENTS=json.dumps(payload, indent=2))
        reply = invoke_kiro(rendered.text, agent=agent, step="frame_triage", template="frame_triage",
                            params=rendered.params)
        block = prompts.extract(reply, "TRIAGE")
        if block is None:
            raise RuntimeError("frame_triage reply had no <<<TRIAGE>>> envelope")
        data = json.loads(block)
        return data["decisions"]
    return triage


def make_elaborate(prompts_dir: str, agent: str):
    """One `frame_triage` round-trip asking the agent to fix `problems` on an EXISTING,
    already-decomposed item — reuses `frame_triage`'s own `"refine"` decision contract
    (`{"id", "decision": "refine", "item": <complete item>}`), the one every frame-shaped
    harness already has, instead of inventing a second mandatory prompt type. The payload
    carries the item's full current content (not just title/text, the shape `make_triage`
    sends for brand-new backlog entries) plus concrete `problems`, real `grounding`, and a
    deliberately tiny `dependency_context` (direct dependencies' id/title/intent/scope
    only — never transitive, never the whole reservoir) so the agent stays consistent with
    what a prerequisite already settled on, without the token cost of whole items."""
    def elaborate(item: dict, problems: List[str], grounding: List[str],
                 dependency_context: List[dict]) -> dict:
        payload = [{**item, "problems": problems, "grounding": grounding,
                   "dependency_context": dependency_context}]
        rendered = prompts.render(prompts_dir, "frame_triage", ARGUMENTS=json.dumps(payload, indent=2))
        reply = invoke_kiro(rendered.text, agent=agent, step="frame_elaborate", template="frame_triage",
                            params=rendered.params)
        block = prompts.extract(reply, "TRIAGE")
        if block is None:
            raise RuntimeError("frame_triage reply had no <<<TRIAGE>>> envelope")
        data = json.loads(block)
        dec = next((d for d in data.get("decisions", []) if d.get("id") == item["id"]), None)
        if dec is None:
            raise RuntimeError(f"frame_triage reply had no decision for `{item['id']}`")
        return dec
    return elaborate


def _dep_context(item: dict, items: Dict[str, dict]) -> List[dict]:
    """Direct dependencies only — never transitive, never the whole reservoir — so an
    elaborate payload's size stays proportional to this one item's own (necessarily small,
    PBIs are Bolt-sized) dependency count, not the backlog's."""
    out = []
    for d in item.get("dependencies") or []:
        dep = items.get(d)
        if dep:
            out.append({"id": d, "title": dep.get("title", ""), "intent": dep.get("intent", ""),
                       "scope": dep.get("scope", {})})
    return out


def _topo_order(items: Dict[str, dict]) -> List[str]:
    """PBI leaf ids, prerequisites first (Kahn's algorithm) — ties broken by id for a
    deterministic, reviewable order. Ids on a dependency cycle (already flagged elsewhere:
    `atomic_check.refresh_status` demotes their maturity) cannot be topologically placed;
    they're appended at the end in id order rather than dropped, so `elaborate --all` still
    reaches them."""
    pbis = {iid: it for iid, it in items.items() if it.get("level") == "pbi"}
    deps = {iid: [d for d in (it.get("dependencies") or []) if d in pbis] for iid, it in pbis.items()}
    indegree = {iid: 0 for iid in deps}
    children: Dict[str, List[str]] = {iid: [] for iid in deps}
    for iid, ds in deps.items():
        for d in ds:
            children[d].append(iid)
            indegree[iid] += 1
    ready = sorted(iid for iid, n in indegree.items() if n == 0)
    order: List[str] = []
    while ready:
        iid = ready.pop(0)
        order.append(iid)
        newly_ready = []
        for c in children[iid]:
            indegree[c] -= 1
            if indegree[c] == 0:
                newly_ready.append(c)
        ready = sorted(ready + newly_ready)
    order += sorted(set(deps) - set(order))      # cycle members: stable fallback, not dropped
    return order


def make_decompose(prompts_dir: str, agent: str, max_children: int,
                   max_attempts: int = 3) -> frame_driver.DecomposeRunner:
    def decompose(item: dict) -> List[dict]:
        wanted = atomic_check.must_cover(item)
        payload = {**item, "must_cover": [f"{n}. {c}" for n, c in enumerate(wanted, 1)]}
        feedback = None
        for attempt in range(max_attempts):
            args = dict(payload)
            if feedback:
                args["previous_attempt_feedback"] = feedback
            rendered = prompts.render(prompts_dir, "frame_decompose",
                                      ARGUMENTS=json.dumps(args, indent=2))
            reply = invoke_kiro(rendered.text, agent=agent, step=f"frame_decompose.{attempt}",
                                template="frame_decompose", params=rendered.params)
            block = prompts.extract(reply, "DECOMPOSITION")
            if block is None:
                feedback = "Your reply had no <<<DECOMPOSITION>>> envelope. Reply again with one."
                continue
            try:
                data = json.loads(block)
            except ValueError as e:
                feedback = f"Your DECOMPOSITION envelope was not valid JSON: {e}"
                continue
            children = data.get("children") or []
            coverage = data.get("coverage") or []
            problems = atomic_check.coverage_problems(item, children, coverage, max_children)
            if not problems:
                return children
            feedback = "Fix these problems and reply again:\n" + "\n".join(f"- {p}" for p in problems)
        return []
    return decompose


def _apply_decompose(decompose, iid: str, item: dict, res: dict, taken: Set[str],
                     max_children: int) -> Optional[List[str]]:
    """Split `item` (id `iid`) into new children via `decompose`, renumber them under `iid`
    (`frame_driver._renumber` — the same Python-owns-identity renumbering `add`'s own
    decompose path already uses, never trusting agent-proposed ids), add them to
    `res["items"]`, and reclassify the parent to `level: "feature"` so compute_statuses /
    `elaborate` / `promote` / `list` never treat it as a leaf PBI again — only its children
    are. Returns the new child ids, or `None` if the agent couldn't produce a covering split
    (`res`/`item` are left completely unchanged in that case)."""
    try:
        children = decompose(item)
    except Exception as e:                            # noqa: BLE001 - one bad id must not stop a batch
        print(f"`{iid}`: decompose failed: {e}")
        return None
    if not children:
        print(f"`{iid}`: agent could not produce a covering split -- left unchanged")
        return None
    kids = frame_driver._renumber(iid, children[:max_children], taken)
    for c in kids:
        res["items"][c["id"]] = c
        taken.add(c["id"])
    item["level"] = "feature"
    return [c["id"] for c in kids]


def run_decompose(args: argparse.Namespace) -> None:
    """Split one or more existing PBIs flagged as too big for one Bolt (`size_problems`:
    too many acceptance criteria, effort L/XL, too many files, spans >2 top-level areas)
    into properly-covered children — the counterpart to `elaborate` for items that need
    splitting rather than field completion, via the exact same `frame_decompose` contract
    and coverage-gap retry loop `add` already uses for brand-new items. Same dependency
    ordering, incremental saving, one-id-failing-doesn't-stop-the-batch rules, and (for
    `--all`) immediate re-queueing of a child that's STILL too big — bounded by
    `--max-depth` — as `elaborate` — see its docstring."""
    if not args.ids and not args.all:
        raise SystemExit("`decompose` needs one or more ids, or --all")
    res = load_reservoir(args.reservoir)
    taxonomy = taxonomy_from_workflow(args.workflow)
    known = known_files(args.root)
    ac_budgets = atomic_check.Budgets(max_ac=args.max_ac, max_files=args.max_files)
    decompose = make_decompose(args.prompts_dir, args.agent, args.max_children)
    taken = set(res["items"])

    def needs_split(iid: str) -> bool:
        it = res["items"][iid]
        return it.get("level") == "pbi" and bool(atomic_check.size_problems(it, True, ac_budgets))

    order = _topo_order(res["items"])
    position = {iid: i for i, iid in enumerate(order)}
    depth_of: Dict[str, int] = {}
    if args.all:
        queue = deque(iid for iid in order if needs_split(iid))
    else:
        queue = deque(sorted(args.ids, key=lambda iid: position.get(iid, len(order))))
    for iid in queue:
        depth_of[iid] = 0

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    set_audit_sink(AuditSink(f"decompose-{stamp}", base_dir="agents", trigger_type="frame_elaborate"))

    attempted = 0
    done = 0
    while queue:
        if args.all and args.max is not None and attempted >= args.max:
            break
        iid = queue.popleft()
        item = res["items"].get(iid)
        if item is None:
            print(f"`{iid}`: no such item in {args.reservoir}")
            continue
        if item.get("level") != "pbi":
            print(f"`{iid}`: not a PBI leaf (level={item.get('level')!r}) -- nothing to decompose")
            continue
        attempted += 1
        new_ids = _apply_decompose(decompose, iid, item, res, taken, args.max_children)
        if new_ids:
            print(f"`{iid}`: split into {len(new_ids)} new PBI(s): {', '.join(new_ids)}")
            done += 1
            if args.all and depth_of.get(iid, 0) + 1 < args.max_depth:
                for cid in new_ids:
                    if needs_split(cid):
                        depth_of[cid] = depth_of.get(iid, 0) + 1
                        queue.append(cid)
        atomic_check.compute_statuses(res["items"], taxonomy, known, ac_budgets)
        save_reservoir(args.reservoir, res)

    print(f"decomposed {done} of {attempted} attempted item(s)")


# --- the `add` command ---------------------------------------------------------------------


def run_add(args: argparse.Namespace) -> None:
    res = load_reservoir(args.reservoir)
    taken = set(res["items"])
    taxonomy = taxonomy_from_workflow(args.workflow)
    ac_budgets = atomic_check.Budgets(max_ac=args.max_ac, max_files=args.max_files)
    fd_budgets = frame_driver.FrameBudgets(triage_batch=args.triage_batch,
                                           max_decompose=args.max_decompose,
                                           max_depth=args.max_depth, max_children=args.max_children)

    raw_items = _load_raw_items(args)
    backlog = []
    for it in raw_items:
        iid = _safe_id(it["title"], taken)
        taken.add(iid)
        backlog.append({"id": iid, "parent": it.get("parent"), "title": it["title"],
                        "text": it.get("text", "")})

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    set_audit_sink(AuditSink(f"frame-{stamp}", base_dir="agents", trigger_type="frame_elaborate"))

    def atomic(item: dict) -> List[str]:
        return atomic_check.leaf_problems(item, taxonomy, grounded=False, b=ac_budgets)

    reservoir = frame_driver.run_frame(
        backlog,
        triage=make_triage(args.prompts_dir, args.agent),
        decompose=make_decompose(args.prompts_dir, args.agent, args.max_children),
        atomic_check=atomic,
        budgets=fd_budgets,
        log=print,
    )

    for iid, item in reservoir.items.items():
        res["items"][iid] = item
    res["out_of_scope"] = res.get("out_of_scope", []) + reservoir.out_of_scope
    res["not_decomposed"] = sorted(set(res.get("not_decomposed", [])) | set(reservoir.not_decomposed))
    atomic_check.compute_statuses(res["items"], taxonomy, known_files(args.root), ac_budgets)
    save_reservoir(args.reservoir, res)

    print(f"\nadded {len(backlog)} item(s): {[b['id'] for b in backlog]}")
    print(f"ready (atomic): {sorted(reservoir.ready)}")
    print(f"drafted (atomic, needs completing): {sorted(reservoir.drafted)}")
    if reservoir.not_decomposed:
        print(f"not decomposed (budget/depth): {sorted(reservoir.not_decomposed)}")
    print(f"reservoir saved to {args.reservoir}")


def regrade(reservoir_path: str, workflow_path: str, root: str,
           budgets: Optional["atomic_check.Budgets"] = None) -> dict:
    """Recompute maturity/validation_tier/review/status for every PBI already in the
    reservoir against the codebase at `root` right now — no new items, no agent calls. What
    `run_frame.py regrade` runs directly, and what `run_implement.py init` runs right after
    a seed issue lands, so an imported backlog never sits stale against a codebase that has
    since grown. Takes plain paths (not an `argparse.Namespace`) so both CLIs can share it
    without coupling to each other's flag names."""
    res = load_reservoir(reservoir_path)
    taxonomy = taxonomy_from_workflow(workflow_path)
    atomic_check.compute_statuses(res["items"], taxonomy, known_files(root), budgets or atomic_check.Budgets())
    save_reservoir(reservoir_path, res)
    return res


def run_regrade(args: argparse.Namespace) -> None:
    ac_budgets = atomic_check.Budgets(max_ac=args.max_ac, max_files=args.max_files)
    res = regrade(args.reservoir, args.workflow, args.root, ac_budgets)
    leaves = [i for i in res["items"].values() if i.get("level") == "pbi"]
    by_status: Dict[str, int] = {}
    for i in leaves:
        s = i.get("status", "raw")
        by_status[s] = by_status.get(s, 0) + 1
    print(f"regraded {len(leaves)} PBI(s) against {args.root}")
    print(f"by status: {by_status}")


def _load_raw_items(args: argparse.Namespace) -> List[dict]:
    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, list) else [data]
    if not args.title:
        raise SystemExit("`add` needs --title/--text or --file")
    return [{"title": args.title, "text": args.text or "", "parent": args.parent}]


# --- status / list / promote ---------------------------------------------------------------


def run_status(args: argparse.Namespace) -> None:
    res = load_reservoir(args.reservoir)
    atomic_check.refresh_status(res["items"])
    leaves = [i for i in res["items"].values() if i.get("level") == "pbi"]
    by_status: Dict[str, int] = {}
    for i in leaves:
        s = i.get("status", "raw")
        by_status[s] = by_status.get(s, 0) + 1
    print(f"{len(res['items'])} items, {len(leaves)} leaves")
    print(f"by status: {by_status}")
    print(f"out of scope: {len(res.get('out_of_scope', []))}")
    print(f"not decomposed: {len(res.get('not_decomposed', []))}")


def run_list(args: argparse.Namespace) -> None:
    res = load_reservoir(args.reservoir)
    atomic_check.refresh_status(res["items"])
    for iid, item in sorted(res["items"].items()):
        if item.get("level") != "pbi":
            continue
        if args.ready_only and item.get("status") != "queued":
            continue
        print(f"{iid}\t{item.get('status', 'raw')}\t{item.get('title', '')}")


def run_promote(args: argparse.Namespace) -> None:
    """Promote one or more ids in a single call — order never matters: `queued` requires
    every `dependencies` entry to already be `done`, not just promoted, so a dependent
    promoted before its prerequisite simply sits `blocked` until the prerequisite finishes.
    One id failing its gate (not refined, doesn't exist) does not stop the others in the
    same call from being promoted."""
    res = load_reservoir(args.reservoir)
    failures = []
    promoted = []
    for iid in args.ids:
        item = res["items"].get(iid)
        if item is None:
            failures.append(f"`{iid}`: no such item in {args.reservoir}")
            continue
        if item.get("maturity") != "refined":
            failures.append(f"`{iid}` is {item.get('maturity', 'raw')}, not refined — "
                            "nothing to promote yet")
            continue
        if item.get("review") == "full":
            print(f"NOTE: `{iid}` is validation_tier={item.get('validation_tier')} and needs "
                  "full review before promotion — make sure that happened before continuing.")
        item["ready_for_loop"] = True
        promoted.append(iid)
    atomic_check.refresh_status(res["items"])
    save_reservoir(args.reservoir, res)
    for iid in promoted:
        print(f"`{iid}` promoted: Refined -> {res['items'][iid]['status']}")
    if failures:
        raise SystemExit("\n".join(failures))


def run_elaborate(args: argparse.Namespace) -> None:
    """Send one or more existing `drafted`/`raw` items back through `frame_triage`'s own
    `"refine"` decision to fill in missing fields, resolve open questions, or correct
    `scope` against the real codebase — the only way to make an *existing* item progress
    before this was hand-editing `harness/reservoir.json`, which does not scale.

    Both explicit ids and `--all` are processed in dependency order (`_topo_order`): a
    prerequisite is elaborated before its dependent whenever possible, and the reservoir is
    saved after every single item — not batched at the end — so each later item's
    `dependency_context` reflects whatever a prerequisite earlier in this SAME run just
    decided, and so a long `--all` run's progress survives an interruption.

    For `--all`, a "decompose" decision's new children are enqueued immediately (not left
    for a separate re-run) if they still need work — bounded by `--max-depth` (default 3,
    same convention as `add`'s own decomposition budget) so an agent that keeps saying
    "decompose" without ever reaching atomic can't recurse forever. Explicit ids never
    auto-expand into children — an explicit list means exactly that list.

    One id's call failing (bad envelope, exception) does not stop the rest — unlike
    `run_implement.py run`'s stop-on-first-failure, an incomplete item has no destructive
    consequence, so there's no reason to let one stuck id block hundreds of others."""
    if not args.ids and not args.all:
        raise SystemExit("`elaborate` needs one or more ids, or --all")
    res = load_reservoir(args.reservoir)
    taxonomy = taxonomy_from_workflow(args.workflow)
    known = known_files(args.root)
    ac_budgets = atomic_check.Budgets(max_ac=args.max_ac, max_files=args.max_files)
    elaborate = make_elaborate(args.prompts_dir, args.agent)
    decompose = make_decompose(args.prompts_dir, args.agent, args.max_children)
    taken = set(res["items"])

    def needs_work(iid: str) -> bool:
        it = res["items"][iid]
        return bool(atomic_check.leaf_problems(it, taxonomy, True, ac_budgets)
                   or atomic_check.refined_problems(it, known))

    order = _topo_order(res["items"])
    position = {iid: i for i, iid in enumerate(order)}
    depth_of: Dict[str, int] = {}
    if args.all:
        queue = deque(iid for iid in order if needs_work(iid))
    else:
        queue = deque(sorted(args.ids, key=lambda iid: position.get(iid, len(order))))
    for iid in queue:
        depth_of[iid] = 0

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    set_audit_sink(AuditSink(f"elaborate-{stamp}", base_dir="agents", trigger_type="frame_elaborate"))

    attempted = 0
    done = 0
    now_refined = 0
    while queue:
        if args.all and args.max is not None and attempted >= args.max:
            break
        iid = queue.popleft()
        item = res["items"].get(iid)
        if item is None:
            print(f"`{iid}`: no such item in {args.reservoir}")
            continue
        if not needs_work(iid):
            print(f"`{iid}`: already refined, nothing to do")
            continue
        attempted += 1
        problems = (atomic_check.leaf_problems(item, taxonomy, True, ac_budgets)
                   + atomic_check.refined_problems(item, known))
        dep_context = _dep_context(item, res["items"])
        try:
            dec = elaborate(item, problems, sorted(known), dep_context)
        except Exception as e:                        # noqa: BLE001 - one bad id must not stop the batch
            print(f"`{iid}`: elaborate failed: {e}")
            continue
        decision = dec.get("decision")
        if decision == "refine" and dec.get("item"):
            res["items"][iid] = {**dec["item"], "id": iid, "parent": item.get("parent")}
            done += 1
            # "elaborated" alone is misleading: the agent call succeeding is not the same
            # as the item actually reaching refined (a genuinely unanswerable open question
            # — e.g. "which codebase area owns X" when X doesn't exist yet — is a legitimate
            # outcome, not a failure). Say which one happened, and why, so a human
            # immediately sees "this needs YOUR input" instead of assuming success.
            remaining = (atomic_check.leaf_problems(res["items"][iid], taxonomy, True, ac_budgets)
                        + atomic_check.refined_problems(res["items"][iid], known))
            if remaining:
                print(f"`{iid}`: elaborated, still not refined -- {'; '.join(remaining)}")
            else:
                print(f"`{iid}`: elaborated -> refined")
                now_refined += 1
        elif decision == "refuse":
            res.setdefault("out_of_scope", []).append({"id": iid, "reason": dec.get("reason", "")})
            res["items"].pop(iid, None)
            print(f"`{iid}`: refused by the agent ({dec.get('reason', '')}) -- moved to out_of_scope")
        elif decision == "decompose":
            new_ids = _apply_decompose(decompose, iid, item, res, taken, args.max_children)
            if new_ids:
                print(f"`{iid}`: agent says this needs splitting, not elaborating -- "
                      f"split into {len(new_ids)} new PBI(s): {', '.join(new_ids)}")
                done += 1
                if args.all and depth_of.get(iid, 0) + 1 < args.max_depth:
                    for cid in new_ids:
                        if needs_work(cid):
                            depth_of[cid] = depth_of.get(iid, 0) + 1
                            queue.append(cid)
        else:
            print(f"`{iid}`: unrecognized decision {decision!r} -- left unchanged")
        atomic_check.compute_statuses(res["items"], taxonomy, known, ac_budgets)
        save_reservoir(args.reservoir, res)

    print(f"elaborated {done} of {attempted} attempted item(s); {now_refined} now refined")


def run_retry(args: argparse.Namespace) -> None:
    res = load_reservoir(args.reservoir)
    item = res["items"].get(args.id)
    if item is None:
        raise SystemExit(f"no item `{args.id}` in {args.reservoir}")
    if item.get("outcome") != "failed":
        raise SystemExit(f"`{args.id}` has no failed outcome — nothing to retry")
    item.pop("outcome", None)
    item.pop("claim", None)
    atomic_check.refresh_status(res["items"])
    save_reservoir(args.reservoir, res)
    print(f"`{args.id}` reset: failed -> {item['status']}")


def run_unclaim(args: argparse.Namespace) -> None:
    res = load_reservoir(args.reservoir)
    item = res["items"].get(args.id)
    if item is None:
        raise SystemExit(f"no item `{args.id}` in {args.reservoir}")
    if not item.get("claim"):
        raise SystemExit(f"`{args.id}` has no claim to release")
    item.pop("claim", None)
    atomic_check.refresh_status(res["items"])
    save_reservoir(args.reservoir, res)
    print(f"`{args.id}` unclaimed -> {item['status']}")


# --- CLI -------------------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--reservoir", default=DEFAULT_RESERVOIR)
    sub = p.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="triage and (if needed) decompose a new item")
    add.add_argument("--title")
    add.add_argument("--text", default="")
    add.add_argument("--parent", default=None)
    add.add_argument("--file", default=None, help="JSON file: one {title,text,parent?} or a list")
    add.add_argument("--workflow", default=WORKFLOW_PATH)
    add.add_argument("--root", default=".", help="where to scan for grounding (default: cwd)")
    add.add_argument("--prompts-dir", default=PROMPTS_DIR)
    add.add_argument("--agent", default="builder")
    add.add_argument("--max-ac", type=int, default=6)
    add.add_argument("--max-files", type=int, default=12)
    add.add_argument("--max-children", type=int, default=12)
    add.add_argument("--max-depth", type=int, default=3)
    add.add_argument("--max-decompose", type=int, default=300)
    add.add_argument("--triage-batch", type=int, default=20)
    add.set_defaults(func=run_add)

    status = sub.add_parser("status", help="counts by status")
    status.set_defaults(func=run_status)

    lst = sub.add_parser("list", help="list PBIs")
    lst.add_argument("--ready-only", action="store_true")
    lst.set_defaults(func=run_list)

    promote = sub.add_parser("promote", help="mark one or more refined PBIs Ready-for-Loop")
    promote.add_argument("ids", nargs="+", metavar="id")
    promote.set_defaults(func=run_promote)

    retry = sub.add_parser("retry", help="send a failed PBI back to the queue")
    retry.add_argument("id")
    retry.set_defaults(func=run_retry)

    unclaim = sub.add_parser("unclaim", help="release a stale in_progress claim (e.g. after a crash)")
    unclaim.add_argument("id")
    unclaim.set_defaults(func=run_unclaim)

    regrade = sub.add_parser("regrade", help="recompute maturity/status for every PBI — no new items")
    regrade.add_argument("--workflow", default=WORKFLOW_PATH)
    regrade.add_argument("--root", default=".", help="where to scan for grounding (default: cwd)")
    regrade.add_argument("--max-ac", type=int, default=6)
    regrade.add_argument("--max-files", type=int, default=12)
    regrade.set_defaults(func=run_regrade)

    elaborate = sub.add_parser(
        "elaborate", help="send one or more existing drafted/raw items back through triage")
    elaborate.add_argument("ids", nargs="*", metavar="id")
    elaborate.add_argument("--all", action="store_true",
                           help="every non-refined PBI, in dependency order, instead of explicit ids")
    elaborate.add_argument("--max", type=int, default=None,
                           help="cap how many items --all processes in one call")
    elaborate.add_argument("--workflow", default=WORKFLOW_PATH)
    elaborate.add_argument("--root", default=".", help="where to scan for grounding (default: cwd)")
    elaborate.add_argument("--prompts-dir", default=PROMPTS_DIR)
    elaborate.add_argument("--agent", default="builder")
    elaborate.add_argument("--max-ac", type=int, default=6)
    elaborate.add_argument("--max-files", type=int, default=12)
    elaborate.add_argument("--max-children", type=int, default=12)
    elaborate.add_argument("--max-depth", type=int, default=3,
                           help="--all only: how deep a chain of agent-triggered splits may recurse")
    elaborate.set_defaults(func=run_elaborate)

    decompose = sub.add_parser(
        "decompose", help="split one or more existing too-big PBIs into covered children")
    decompose.add_argument("ids", nargs="*", metavar="id")
    decompose.add_argument("--all", action="store_true",
                           help="every PBI flagged too-big, in dependency order, instead of explicit ids")
    decompose.add_argument("--max", type=int, default=None,
                           help="cap how many items --all processes in one call")
    decompose.add_argument("--workflow", default=WORKFLOW_PATH)
    decompose.add_argument("--root", default=".", help="where to scan for grounding (default: cwd)")
    decompose.add_argument("--prompts-dir", default=PROMPTS_DIR)
    decompose.add_argument("--agent", default="builder")
    decompose.add_argument("--max-ac", type=int, default=6)
    decompose.add_argument("--max-files", type=int, default=12)
    decompose.add_argument("--max-children", type=int, default=12)
    decompose.add_argument("--max-depth", type=int, default=3,
                           help="--all only: how deep a chain of still-too-big splits may recurse")
    decompose.set_defaults(func=run_decompose)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
