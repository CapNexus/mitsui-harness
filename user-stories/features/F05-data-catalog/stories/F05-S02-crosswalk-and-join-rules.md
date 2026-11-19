---
id: F05-S02
feature: F5
title: Capture the crosswalk and join rules from the SMEs
tier: integrate
executor: mixed
owner: Mike
repo: planning
status: ready
sow: D3
due: 2026-11-27
blocked_by: [DEP-13]
depends_on_stories: [F01-S01]
params: [crosswalk_rules]
human_gates: [SMEs run the data-model session, an SME reviews the written join paths]
---

## Story

As the assistant, I want written rules for how wells are identified across MEPWELL, SDEDBPROD and MEPS_ARIES, so that cross-database questions join on the right keys.

## Context

Dependencies doc item 4.6. The SME data-model session is Mon Nov 23. It collects ER diagrams, data dictionaries, ARIES table guides and the crosswalk logic (API number format, UWI, ARIES property IDs, MEPWELL crosswalk tables). The result goes into `config/crosswalk.yaml` (parameter `crosswalk_rules`): for each database pair, the tables, the key columns, any format conversion (for example API-10 to API-14), and caveats.

F05-S03 turns these rules into join hints in the catalog. F9 uses them in the prompt.

## Acceptance criteria

1. Given the session notes, when `config/crosswalk.yaml` is written, then it has a join path for each of the three database pairs, each naming the crosswalk table, the key columns and any format conversion.
   - verify: `scripts/check-crosswalk.sh` exits 0. It fails if any pair is missing or a path has no crosswalk table. Script is created by this story.
2. Given the written rules, when an SME reviews them, then the reviewer's name and date are recorded in the file.
   - gate: SME review, by email or in the session follow-up.
3. Given the session, when it ends, then the SME names and the documents received are recorded in the RAID log, and DEP-13 is updated.
   - verify: `scripts/check-dependency-register.sh` exits 0.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-13 | A | Data dictionary, join keys, SME session | Sandbox crosswalk from F04-S04 |

## Evidence

`evidence/F05/crosswalk/`: session notes, received documents list, SME review.

## Status log

- 2026-11-19: created
