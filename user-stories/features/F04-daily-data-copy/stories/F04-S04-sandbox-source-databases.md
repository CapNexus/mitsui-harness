---
id: F04-S04
feature: F4
title: Build sandbox source databases with synthetic data
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Code
status: ready
sow: D3
due: 2026-11-23
blocked_by: []
depends_on_stories: [F02-S12]
params: [approved_table_list]
human_gates: []
---

## Story

As Venkat (DevOps), I want a sandbox SQL Server with synthetic MEPWELL, SDEDBPROD and MEPS_ARIES databases, so that the whole load pipeline can be built and tested before Mitsui's network and logins are ready.

## Context

No Mitsui data is used. The synthetic schemas imitate what the pipeline must handle: mixed-case names, a well hub and crosswalk in MEPWELL, a versioned feature class with `_evw` view and a `geometry` column in SDEDBPROD, economics tables in MEPS_ARIES, one table with a `sql_variant` column (unsupported by DMS), and one large shape value above the LOB cap.

The sandbox runs as SQL Server 2017 in a container (local and in the CapNexus sandbox account), with the read-only login from Appendix A2. It also produces inventory CSVs in the same format as scripts A3 and A4, so F04-S01 can be tested.

## Acceptance criteria

1. Given the sandbox scripts, when they run, then a SQL Server 2017 instance holds the three databases with mixed-case table and column names and seeded rows that join across databases through the crosswalk.
   - verify: `make sandbox-up && make sandbox-test` runs a cross-database join on the crosswalk and returns at least one row.
2. Given the sandbox, when the edge-case check runs, then it finds one `sql_variant` table, one `geometry` column with a value larger than the default LOB cap, and one `_evw` view.
   - verify: `make sandbox-test` includes these three checks.
3. Given the Appendix A2 script, when it runs on the sandbox, then `dms_wda_ro` exists with only `db_datareader`, `VIEW DATABASE STATE` and `VIEW DEFINITION`, and `IS_SRVROLEMEMBER('sysadmin', 'dms_wda_ro')` returns 0.
   - verify: `make sandbox-test` runs the permission query.
4. Given the sandbox, when the inventory scripts A3 and A4 run, then CSVs are written in the format F04-S01 expects, and a sandbox approved list is written to `fixtures/approved-tables.sandbox.yaml`.
   - verify: `make sandbox-inventory` writes both CSVs and the YAML, and the test checks their headers.

## Dependencies

None.

## Evidence

PR with the sandbox scripts and passing `make sandbox-test` output.

## Status log

- 2026-11-19: created
- 2026-11-19: depends on F02-S12 (project CDK app and baseline lookup in Code)
