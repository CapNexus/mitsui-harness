"""The Frame "atomic" predicate: is this PBI one well-formed Bolt?

Shipped by harness-bootstrap into every generated harness that uses the `frame` shape
(`harness/drivers/atomic_check.py`) — the same deterministic checks `bootstrap/frame.py`
uses on itself, ported to work on plain dicts (the canonical PBI shape pinned in
`plan_harness.md`/`build_prompt.md` for the `TRIAGE`/`DECOMPOSITION` envelopes) and
parameterized by this harness's own budgets and work-type taxonomy instead of a
hardcoded one. "Atomic" means the same thing in every domain — 1-6 EARS acceptance
criteria, effort XS/S/M, a known work type, scope within the known files, no more than two
code areas — so this is never a per-harness guess.

Two tiers, matching `bootstrap/frame.py`'s own split:
- `leaf_problems` (size + form) decides whether `frame_driver.run_frame` should keep
  decomposing an item — this IS its `atomic_check` callable.
- `refined_problems` decides whether an already-atomic item is fully fleshed out (no open
  questions, grounded in the codebase) — decomposing further would not fix these, so they
  never feed back into the recursion; `maturity()` uses them to label an item for a person.

On top of that, `compute_statuses`/`refresh_status` layer a `status` onto every PBI leaf —
raw/drafted/refined mirror `maturity` until a person promotes an item (`ready_for_loop`),
then blocked/queued/in_progress/done/failed take over. `queued` (promoted AND every
`dependencies` entry already `done`) is the only status `run_implement.py` is allowed to
pull work from — this is what makes an unattended, multi-PBI `implement` run safe: an item
can never jump the queue ahead of something it depends on. `dependency_problems`/`cycles`
are the same existence/cycle checks `bootstrap/frame.py`'s `finalize()` already runs on its
one-time intake, ported here so the *deployed* harness enforces them on every `run_frame.py
add` too, not just the initial bootstrap.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

EARS = re.compile(r"^\s*(when|while|if|where|the|once|after|during)\b.*\bshall\b", re.I | re.S)
LEAF_EFFORT = ("XS", "S", "M")


@dataclass
class Budgets:
    max_ac: int = 6
    max_files: int = 12


def size_problems(item: dict, grounded: bool, b: Optional[Budgets] = None) -> List[str]:
    """Why an item is bigger than one Bolt. Non-empty -> decompose it further."""
    b = b or Budgets()
    p = []
    if item.get("level") != "pbi":
        p.append("not a PBI")
    ac = item.get("acceptance_criteria") or []
    if len(ac) > b.max_ac:
        p.append(f"{len(ac)} acceptance criteria (> {b.max_ac}) — too big for one Bolt")
    if item.get("effort") in ("L", "XL"):
        p.append(f"effort {item.get('effort')} — a leaf is XS/S/M")
    scope = item.get("scope") or {}
    files = scope.get("files") or []
    if grounded and len(files) > b.max_files:
        p.append(f"touches {len(files)} files (> {b.max_files})")
    areas = scope.get("areas") or []
    if len({a.strip("/").split("/")[0] for a in areas if a}) > 2:
        p.append("spans more than two top-level areas")
    return p


def form_problems(item: dict, taxonomy: Set[str]) -> List[str]:
    """Why a Bolt-sized PBI is not well-formed yet. Decomposing won't fix these."""
    p = []
    ac = item.get("acceptance_criteria") or []
    if not ac:
        p.append("no acceptance criteria")
    bad = [c for c in ac if not EARS.match(c)]
    if bad:
        p.append(f"{len(bad)} acceptance criteria are not EARS ('... shall ...')")
    if not item.get("effort"):
        p.append("effort missing")
    wt = item.get("work_type")
    if not wt or wt not in taxonomy:
        p.append(f"work type `{wt}` is not a harness classification")
    return p


def leaf_problems(item: dict, taxonomy: Set[str], grounded: bool,
                  b: Optional[Budgets] = None) -> List[str]:
    """Why a PBI is not (yet) one well-formed Bolt. Empty = atomic. This is
    `frame_driver.run_frame`'s `atomic_check` callable (bind `taxonomy`/`grounded`/`b`)."""
    return size_problems(item, grounded, b) + form_problems(item, taxonomy)


def refined_problems(item: dict, known_files: Optional[Set[str]]) -> List[str]:
    """What stands between an atomic leaf and Refined (structurally complete AND grounded).
    Never feeds back into decomposition — only into `maturity()`."""
    p = []
    for field in ("intent", "user_story"):
        if not (item.get(field) or "").strip():
            p.append(f"missing {field}")
    if not item.get("data_class") or not item.get("consequence"):
        p.append("missing data class or consequence level")
    if item.get("open_questions"):
        p.append(f"{len(item['open_questions'])} open question(s)")
    scope = item.get("scope") or {}
    if known_files is None:
        p.append("not grounded: no codebase supplied")
    elif not (scope.get("areas") or scope.get("files")):
        p.append("not grounded in the codebase")
    else:
        unknown = [f for f in (scope.get("files") or []) if f not in known_files]
        if unknown:
            p.append(f"scope names {len(unknown)} file(s) not in the codebase: {', '.join(unknown[:3])}")
    return p


def maturity(item: dict, taxonomy: Set[str], known_files: Optional[Set[str]],
            b: Optional[Budgets] = None) -> str:
    """"raw" (not atomic yet), "drafted" (atomic but incomplete), or "refined"
    (atomic and complete) — Ready-for-Loop stays a person's call beyond this."""
    grounded = known_files is not None
    if leaf_problems(item, taxonomy, grounded, b):
        return "raw"
    return "refined" if not refined_problems(item, known_files) else "drafted"


def must_cover(item: dict) -> List[str]:
    """What a split has to cover: the item's criteria, or its intent/title as one line."""
    return list(item.get("acceptance_criteria") or []) or [item.get("intent") or item.get("title") or ""]


def coverage_problems(parent: dict, children: List[dict], coverage: List[dict],
                      max_children: int = 12) -> List[str]:
    """Every numbered criterion of `parent` is covered by a real child; every child covers
    one. Checked against the raw (un-renumbered) child entries a `frame_decompose` reply
    carries its own `id`/role for — this runs before `frame_driver` renumbers them."""
    p = []
    child_ids = {c.get("id") for c in children if c.get("id")}
    if not children:
        p.append("no children")
    if len(children) > max_children:
        p.append(f"{len(children)} children (> {max_children}) — split into features first")
    wanted = must_cover(parent)
    hit: Dict[int, Set[str]] = {}
    for link in coverage or []:
        n = link.get("criterion")
        if not isinstance(n, int) or not 1 <= n <= len(wanted):
            p.append(f"coverage names criterion {n!r}; the item has {len(wanted)}")
            continue
        hit.setdefault(n, set()).update(set(link.get("covered_by") or []) & child_ids)
    for n, crit in enumerate(wanted, 1):
        if not hit.get(n):
            p.append(f"criterion {n} not covered by any child: {crit[:120]}")
    used = set().union(*hit.values()) if hit else set()
    for c in children:
        if c.get("id") and c["id"] not in used:
            p.append(f"child `{c['id']}` covers no criterion of the parent")
    return p


def validation_tier(item: dict) -> str:
    """Light / Standard / Full. Fails closed: an unknown data class or consequence is Full."""
    dc, cq = item.get("data_class"), item.get("consequence")
    if dc in (None, "regulated") or cq in (None, "autonomous_action"):
        return "full"
    if dc == "confidential" or cq == "authorized_action":
        return "standard"
    return "light"


def review_level(item: dict) -> str:
    """A light dev-lead check only for low-consequence, non-sensitive items; otherwise full."""
    light = item.get("data_class") in ("public", "internal") and item.get("consequence") == "recommendation"
    return "light" if light else "full"


def dependency_problems(item: dict, by_id: Dict[str, dict]) -> List[str]:
    """Missing dependency ids — existence only; cycles are reservoir-wide (see `cycles()`)."""
    return [f"dependency `{d}` does not exist" for d in (item.get("dependencies") or []) if d not in by_id]


def cycles(items: Dict[str, dict]) -> List[List[str]]:
    """Dependency cycles across the reservoir, found iteratively (ported from
    `bootstrap/frame.py`'s `_cycles` — dependency chains can be thousands long, so no
    recursion)."""
    graph = {iid: [d for d in (it.get("dependencies") or []) if d in items] for iid, it in items.items()}
    state: Dict[str, int] = {}                  # 1 = on the current path, 2 = done
    out: List[List[str]] = []
    for root in sorted(graph):
        if root in state:
            continue
        path, stack = [root], [(root, iter(graph.get(root, [])))]
        state[root] = 1
        while stack:
            node, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                stack.pop(); path.pop(); state[node] = 2
            elif state.get(nxt) == 1:
                out.append(path[path.index(nxt):] + [nxt])
            elif nxt not in state:
                state[nxt] = 1; path.append(nxt)
                stack.append((nxt, iter(graph.get(nxt, []))))
    return out


def status_of(item: dict, dep_problems: List[str], done_ids: Set[str]) -> str:
    """raw/drafted/refined mirror `maturity` until an item is promoted (`ready_for_loop`);
    after that, blocked/queued/in_progress/done/failed take over. `queued` is the only
    status `run_implement.py` may claim work from."""
    if item.get("claim"):
        return "in_progress"
    outcome = item.get("outcome")
    if outcome in ("done", "failed"):
        return outcome
    if not item.get("ready_for_loop"):
        return item.get("maturity", "raw")
    deps = item.get("dependencies") or []
    if dep_problems or any(d not in done_ids for d in deps):
        return "blocked"
    return "queued"


def refresh_status(items: Dict[str, dict]) -> None:
    """Recompute just `status` for every PBI leaf from its already-stored maturity /
    ready_for_loop / dependencies / claim / outcome — no taxonomy or grounding needed, so
    `run_frame.py`'s `promote`/`retry`/`unclaim` and `run_implement.py` can call this alone,
    as often as they like, without re-deriving `maturity` (that is `compute_statuses`'s job,
    and only `run_frame.py add` has the taxonomy/grounding to do it)."""
    pbis = {iid: it for iid, it in items.items() if it.get("level") == "pbi"}
    cycle_ids = {iid for cyc in cycles(pbis) for iid in cyc}
    done = {iid for iid, it in pbis.items() if it.get("outcome") == "done"}
    for iid, it in pbis.items():
        problems = dependency_problems(it, pbis)
        if iid in cycle_ids:
            problems = problems + ["dependency cycle"]
        if problems and it.get("maturity") == "refined":
            it["maturity"] = "drafted"
        it["status"] = status_of(it, problems, done)


def compute_statuses(items: Dict[str, dict], taxonomy: Set[str],
                     known_files: Optional[Set[str]], b: Optional[Budgets] = None) -> None:
    """Recompute `maturity`, `atomic`, `problems`, `validation_tier`, and `review` for every
    PBI leaf (mirrors `bootstrap/frame.py`'s `finalize()`), then `refresh_status`. The only
    place `maturity` itself gets recomputed — `run_frame.py add`/`regrade`/`elaborate` are
    the only callers with grounding to offer.

    `problems` in particular must be written here, not left as whatever an `elaborate`/
    `decompose` agent reply happened to echo back (or the stale value from the one-time
    bootstrap intake that originally produced the item): a human — or a future `elaborate`
    payload — reading `harness/reservoir.json` needs it to reflect *why the item is drafted
    right now*, not a snapshot from whenever it was last agent-touched."""
    grounded = known_files is not None
    for it in items.values():
        if it.get("level") == "pbi":
            lp = leaf_problems(it, taxonomy, grounded, b)
            rp = refined_problems(it, known_files)
            it["atomic"] = not lp
            it["problems"] = lp + rp
            it["maturity"] = "raw" if lp else ("refined" if not rp else "drafted")
            it["validation_tier"] = validation_tier(it)
            it["review"] = review_level(it)
    refresh_status(items)
