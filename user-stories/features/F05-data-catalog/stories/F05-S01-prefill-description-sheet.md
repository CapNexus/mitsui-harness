---
id: F05-S01
feature: F5
title: Pre-fill the description sheet and send it to the SMEs
tier: build
executor: mixed
owner: Mike
repo: planning
status: ready
sow: D3
due: 2026-11-25
blocked_by: []
depends_on_stories: [F01-S01]
params: [approved_table_list, sme_descriptions_file]
human_gates: [Mike (PM) sends the sheet to the SMEs]
---

## Story

As a Mitsui SME, I want a description sheet that is already filled in with table names, column names, types and draft text, so that I only correct and complete it instead of starting from a blank page.

## Context

Appendix E2 of the Dependencies doc defines the sheet: database, table, table description, column, column description, unit, code values or format, caveats, SME reviewer. The working copy is `config/descriptions.yaml` (parameter `sme_descriptions_file`). The sheet is sent as a spreadsheet (SMEs edit it there) and read back into the YAML.

Draft text comes from names, data types and any documents from the SME session (DEP-13). Each drafted description is marked `source: draft` so it is never mistaken for SME text. Pre-fill uses the approved list (or the inventory, if the list is not signed by Nov 25).

## Acceptance criteria

1. Given the approved list or inventory, when `scripts/prefill-descriptions.sh` runs, then `config/descriptions.yaml` has one entry per table and per column with every E2 field, and every drafted description has `source: draft`.
   - verify: the script's test with the sandbox list from F04-S04. Script is created by this story.
2. Given `config/descriptions.yaml`, when it is exported, then a spreadsheet with the E2 columns is written, and reading it back gives the same YAML (round trip).
   - verify: `scripts/descriptions-sheet.sh export` then `import`, and `diff` shows no change.
3. Given the sheet, when it is sent on Wed Nov 25, then the send date and the SME names are recorded in the RAID log.
   - gate: Mike (PM) sends it. Email saved as evidence.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-10 | A+C | Approved table list | Inventory or sandbox list |
| DEP-17 | A | SME descriptions | Draft text marked `source: draft` |

## Evidence

`evidence/F05/description-sheet/`: the sent sheet and the email.

## Status log

- 2026-11-19: created
