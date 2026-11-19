---
id: F04-S10
feature: F4
title: Decide the SDEDBPROD approach and prove current edits load
tier: integrate
executor: mixed
owner: Soma
repo: planning
status: blocked
sow: D3
due: 2026-11-25
blocked_by: [DEP-11]
depends_on_stories: [F04-S03]
params: [sdedbprod_mode]
human_gates: [Noah Jackson decides the approach and names the GIS admin, GIS admin makes a test edit and reports geometry storage and largest shape size]
---

## Story

As Soma (Solution Architect), I want the SDEDBPROD approach decided and proven with a real edit, so that GIS answers are based on current data and not on stale base tables.

## Context

DEP-11 (type E). In a versioned ArcGIS geodatabase, recent edits sit in delta tables until the geodatabase is compressed. Two options (Dependencies doc item 4.4):
- Compress to state 0 before each load window (`compress_state0`). The GIS admin's job must finish before the window opens.
- Read the `_evw` versioned views (`evw_views`). The GIS admin grants the DMS login read access to the views.

The decision is on the Mon Nov 23 agenda with Noah Jackson (interim owner). If there is no decision by then, SDEDBPROD stays out of the load (`undecided`) and the skipped alarm fires (F04-S08). The proof is planned for Wed Nov 25.

## Acceptance criteria

1. Given the Nov 23 meeting, when Noah Jackson decides, then the decision, the named GIS admin and the compress job timing (if option 1) are recorded in the RAID log, and `sdedbprod_mode` is set in `config/parameters.md`.
   - gate: Noah Jackson's decision, in writing.
   - verify: `scripts/check-raid-log.sh` exits 0 and `grep "sdedbprod_mode" config/parameters.md` shows `set`.
2. Given the chosen mode, when the GIS admin makes a known test edit and the next load runs, then the edited value appears in the S3 Tables copy.
   - gate: GIS admin sends the feature class, object ID and new value of the test edit.
   - verify: Athena query for that object ID returns the new value. Query and result saved as evidence.
3. Given the GIS admin's answers, when they are recorded, then the geometry storage type per feature class and the largest shape size are documented, and the LOB size cap is set to cover it or the truncation is documented.
   - gate: GIS admin's answers (Appendix A5).
   - verify: `evidence/F04/sdedbprod/geometry.md` exists and states the cap.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-11 | E | Approach and owner | `sdedbprod_mode: undecided`, SDEDBPROD skipped with an alarm |

## Evidence

`evidence/F04/sdedbprod/`: decision record, test edit proof, geometry notes.

## Status log

- 2026-11-19: created
