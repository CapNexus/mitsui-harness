---
id: F04-S03
feature: F4
title: Generate DMS table mappings from the approved list
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Infrastructure
status: ready
sow: D3
due: 2026-11-24
blocked_by: []
depends_on_stories: [F04-S02]
params: [approved_table_list, sdedbprod_mode]
human_gates: []
---

## Story

As Venkat (DevOps), I want the DMS table mappings generated from the approved table list, so that DMS copies only approved tables, names them in lowercase, and reads SDEDBPROD the way Mitsui decides.

## Context

Feature criteria 2, 4 and 10. The generator reads `config/approved-tables.yaml` and writes the DMS table-mapping JSON for each database's task. Only rows with decision `Approved` or `Approved with masking` are included. Selection rules use explicit table names, never wildcards.

S3 Tables, Glue and Lake Formation need lowercase names, so the mappings add DMS transformation rules that lowercase schema, table and column names.

SDEDBPROD is undecided (DEP-11, type E). The switch `sdedbprod_mode` selects the source:
- `compress_state0`: base tables.
- `evw_views`: the `_evw` versioned views (DMS reads views in full-load-only tasks).
- `undecided`: SDEDBPROD is left out of the task, and the orchestration raises the SDEDBPROD-skipped alarm (F04-S08).

Geometry and geography columns are copied as text only where DMS supports them. The task uses limited-LOB mode with a size cap. The cap is a constant in this story (proposed parameter `geometry_lob_max_kb`, default 64) until the GIS admin gives the largest shape size (F04-S10).

## Acceptance criteria

1. Given an approved list with approved and not-approved rows, when the generator runs, then the mapping contains selection rules for exactly the approved rows and no wildcard rules.
   - verify: unit test with a fixture list of 5 rows (3 approved, 1 not approved, 1 unsupported).
2. Given any mapping, when it is generated, then it includes lowercase transformation rules for schema, table and column names.
   - verify: unit test checks the `convert-lowercase` rules for each rule target.
3. Given `sdedbprod_mode` set to each of `compress_state0`, `evw_views` and `undecided`, when the generator runs, then SDEDBPROD selects base tables, selects `_evw` views, or is left out.
   - verify: parameterized unit test covers all three values.
4. Given the task settings, when they are generated, then LOB mode is limited, the LOB size equals the configured cap, and the cap is written in the repo README with the note that larger shapes are truncated.
   - verify: unit test on task settings, and `grep -q "LOB size cap" README.md`.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-10 | A+C | Approved table list | Sandbox list from F04-S04 |
| DEP-11 | E | SDEDBPROD approach | `sdedbprod_mode: undecided`. Both options built behind the switch. |

## Evidence

PR with passing unit tests and a generated mapping for the sandbox list.

## Status log

- 2026-11-19: created
