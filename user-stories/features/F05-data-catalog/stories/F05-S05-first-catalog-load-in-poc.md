---
id: F05-S05
feature: F5
title: Register the real tables and load the first descriptions
tier: integrate
executor: mixed
owner: Venkat
repo: project-mep-AWS-Code
status: blocked
sow: D3
due: 2026-11-30
blocked_by: [DEP-10, DEP-17]
depends_on_stories: [F04-S09, F05-S02, F05-S03]
params: [approved_table_list, sme_descriptions_file, crosswalk_rules]
human_gates: [Noah Jackson has signed the approved table list]
---

## Story

As the F7 to F9 builders, we want the real approved tables registered with whatever SME descriptions have arrived by Nov 30, so that permissions, tools and prompts are built against the real catalog and not the sandbox.

## Context

Week 3 Mon Nov 30: register tables and columns in the Glue Data Catalog and load the descriptions already received. This is the catalog F7 (Lake Formation), F8 (tools) and F9 (prompts) build on in Week 3. The rest of the descriptions arrive by Dec 10 (F05-S06).

## Acceptance criteria

1. Given the signed approved list and the first loads, when the loader runs in the POC account, then every approved table and column is in the Glue Data Catalog.
   - verify: `make check-catalog ENV=poc` exits 0.
2. Given the descriptions received by Nov 30, when they are imported and loaded, then those tables and columns carry the SME text, and the rest carry `DRAFT:` text.
   - verify: `scripts/description-coverage.sh --env poc` prints the count of SME, draft and missing descriptions. Script is created by this story.
3. Given the crosswalk rules, when the loader runs, then the join hints for all three database pairs are in the catalog.
   - verify: the coverage script also lists the join hints found per pair and fails if a pair has none.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-10 | A+C | Signed approved table list | None. Hard stop. |
| DEP-17 | A | SME descriptions received so far | Draft text |

## Evidence

`evidence/F05/first-load/`: catalog check and coverage output for Nov 30.

## Status log

- 2026-11-19: created
