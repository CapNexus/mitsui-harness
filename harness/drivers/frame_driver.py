"""Generic Frame-shaped AEW driver.

Shipped verbatim by harness-bootstrap into every generated harness that declares a
workflow with `"shape": "frame"` (`harness/drivers/frame_driver.py`) — not written per
harness. It runs the triage -> decompose -> atomic_check -> human promote pattern:
batched triage over a backlog of raw items, then recursive, budgeted decomposition of
anything not yet atomic, mirroring `bootstrap/frame.py`'s own `run_frame` — but
standalone, with no dependency on `bootstrap`'s pydantic models, so it runs inside the
target repo this harness was generated for, whatever that repo's own stack is.

Pure control flow, same split as `loop_driver.py`: `triage`, `decompose`, and
`atomic_check` are injected by the caller. `atomic_check` in particular carries this
harness's own domain-specific notion of "atomic" (EARS criteria, effort, grounded scope,
...) — the same content a plan's `atomic_check` step `check` field already describes in
prose; here it is the one small, reviewable predicate function a person (or a narrowly
scoped build step) writes to make that prose executable. The recursion and batching
around it are never reinvented.
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

TriageRunner = Callable[[List[dict]], List[dict]]
DecomposeRunner = Callable[[dict], List[dict]]
AtomicCheck = Callable[[dict], List[str]]
PromoteGate = Callable[[dict], bool]


class FrameFailed(RuntimeError):
    pass


@dataclass
class FrameBudgets:
    triage_batch: int = 20
    max_decompose: int = 300
    max_depth: int = 3
    max_children: int = 12


@dataclass
class Reservoir:
    items: Dict[str, dict] = field(default_factory=dict)
    ready: List[str] = field(default_factory=list)          # atomic and promoted
    drafted: List[str] = field(default_factory=list)        # atomic but not (yet) promoted, or still has problems
    out_of_scope: List[dict] = field(default_factory=list)  # {"id", "reason"}
    not_decomposed: List[str] = field(default_factory=list) # left as-is: budget or depth ran out


def load_workflow(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        wf = json.load(fh)
    if wf.get("shape") != "frame":
        raise ValueError(f"{path}: shape is {wf.get('shape')!r}, not 'frame'")
    return wf


def _renumber(parent_id: str, children: List[dict], taken: set) -> List[dict]:
    """Python, not the agent, owns child identity: ids are `<parent>.<n>`, skipping ids
    already in use, and the parent is forced — the same invariant `bootstrap/frame.py`
    enforces, so a decompose step can't overwrite or re-parent another item."""
    out = []
    n = 0
    for c in children:
        n += 1
        while f"{parent_id}.{n}" in taken:
            n += 1
        cid = f"{parent_id}.{n}"
        taken.add(cid)
        out.append({**c, "id": cid, "parent": parent_id})
    return out


def run_frame(backlog: List[dict], triage: TriageRunner, decompose: DecomposeRunner,
              atomic_check: AtomicCheck, promote: Optional[PromoteGate] = None,
              budgets: Optional[FrameBudgets] = None,
              log: Callable[[str], None] = lambda m: None) -> Reservoir:
    """Triage every item in batches, decompose anything `atomic_check` still flags,
    breadth-first, bounded by `max_depth` / `max_decompose` / `max_children`.

    Each item is a plain dict with at least `id` and `parent`. `triage` is given one
    batch (a list of items) and returns one decision per item:
    `{"id", "decision": "refine"|"decompose"|"refuse", "reason", "item"?}` — `item` is
    the refined replacement when `decision == "refine"`. `decompose` is given one item
    and returns its children (un-renumbered; this module renumbers them). A failed
    triage or decompose step (the caller's `triage`/`decompose` raising) leaves the
    batch's remaining items untouched rather than stopping the whole run, mirroring
    `bootstrap/frame.py`'s "a failed agent step leaves its items as they were; it never
    stops the run".
    """
    b = budgets or FrameBudgets()
    items: Dict[str, dict] = {it["id"]: it for it in backlog}
    taken = set(items)
    out_of_scope: List[dict] = []
    not_decomposed: List[str] = []
    queue: deque = deque()
    depth_of: Dict[str, int] = {}

    ids = list(items)
    for start in range(0, len(ids), b.triage_batch):
        batch = [items[i] for i in ids[start:start + b.triage_batch]]
        log(f"triage {start}..{start + len(batch)}")
        try:
            decisions = triage(batch)
        except Exception as e:                      # noqa: BLE001 - a bad batch must not stop the run
            log(f"triage {start}..{start + len(batch)} failed: {e}")
            continue
        for d in decisions:
            iid = d.get("id")
            if iid not in items:
                continue
            if d.get("decision") == "refuse":
                out_of_scope.append({"id": iid, "reason": d.get("reason", "")})
                items.pop(iid, None)
                continue
            if d.get("decision") == "refine" and d.get("item"):
                items[iid] = {**d["item"], "id": iid, "parent": items[iid].get("parent")}
            if not atomic_check(items[iid]):
                continue
            queue.append(iid)
            depth_of[iid] = 0

    done = 0
    while queue:
        iid = queue.popleft()
        if iid not in items:
            continue
        depth = depth_of.get(iid, 0)
        problems = atomic_check(items[iid])
        if not problems:
            continue
        if done >= b.max_decompose:
            not_decomposed.append(iid)
            continue
        done += 1
        log(f"decompose {iid} (depth {depth})")
        try:
            children = decompose(items[iid])
        except Exception as e:                       # noqa: BLE001 - as above: isolate the failure
            log(f"decompose {iid} failed: {e}")
            not_decomposed.append(iid)
            continue
        if not children:
            not_decomposed.append(iid)
            continue
        kids = _renumber(iid, children[: b.max_children], taken)
        for c in kids:
            items[c["id"]] = c
            if depth + 1 < b.max_depth:
                queue.append(c["id"])
                depth_of[c["id"]] = depth + 1
            else:
                not_decomposed.append(c["id"])

    ready, drafted = [], []
    for iid, it in items.items():
        if atomic_check(it):
            drafted.append(iid)
        elif promote is None or promote(it):
            ready.append(iid)
        else:
            drafted.append(iid)
    return Reservoir(items=items, ready=ready, drafted=drafted,
                     out_of_scope=out_of_scope, not_decomposed=not_decomposed)
