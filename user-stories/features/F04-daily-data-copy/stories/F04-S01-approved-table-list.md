---
id: F04-S01
feature: F4
title: Pre-fill and sign off the approved table list
tier: integrate
executor: mixed
owner: Mike
repo: planning
status: blocked
sow: D3
due: 2026-11-27
blocked_by: [DEP-08, DEP-10]
depends_on_stories: [F01-S01]
params: [approved_table_list]
human_gates: [DBAs return inventory scripts A1, A3 and A4, Noah Jackson signs the approved table list]
---

## Story

As Venkat (DevOps), I want a signed list of the tables and views we may copy, in a file the pipeline can read, so that DMS, the catalog and the permissions all use the same list.

## Context

The list is Appendix E1 of the Dependencies doc. It lives as `config/approved-tables.yaml` (parameter `approved_table_list`). The DBAs return the inventory scripts (Appendix A, A3 and A4) as CSV. This story turns the CSV into a pre-filled list, flags unsupported columns, and gets it signed by the end of Week 2 (Fri Nov 27). The MEPWELL well hub and crosswalk tables must be on it, because every cross-database question joins through them.

Out of scope: masking decisions (F7, DEP-16). The `Allowed groups` column stays empty until then.

## Acceptance criteria

1. Given the returned inventory CSVs for the three databases, when the generator runs, then `config/approved-tables.yaml` lists every table with database, schema, table, row count, size and an empty decision field.
   - verify: `scripts/prefill-approved-tables.sh --inventory evidence/F04/inventory/ --dry-run` prints one row per inventory table. Script is created by this story and has a test with a sample CSV.
2. Given the inventory column report (A4), when the generator runs, then any table with a `sql_variant` or sparse column, or reported as temporal or memory-optimized, is marked `unsupported` with the reason.
   - verify: the same script's test includes one `sql_variant` table and checks it is marked `unsupported`.
3. Given the list sent to the data owners, when it is returned, then each row has a decision (Approved, Approved with masking, Not approved) and the MEPWELL well hub and crosswalk tables are Approved.
   - verify: `scripts/check-approved-tables.sh` exits 0. It fails on an empty decision or a missing crosswalk table. Script is created by this story.
4. Given the completed list, when Noah Jackson signs it, then the signed copy is saved and DEP-10 is set to `resolved` in the register.
   - gate: Noah Jackson's signed list, saved in `evidence/F04/approved-table-list/`.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-08 | D+A | Inventory output from scripts A1, A3, A4 | Sample CSVs from the sandbox databases (F04-S04) |
| DEP-10 | A+C | The signed list | Empty `config/approved-tables.yaml`. Build stories use the sandbox table list. |

## Evidence

`evidence/F04/inventory/` (returned CSVs, metadata only) and `evidence/F04/approved-table-list/` (signed list).

## Status log

- 2026-11-19: created
