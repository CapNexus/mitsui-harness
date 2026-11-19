---
id: F07-S03
feature: F7
title: Pre-fill and sign the masking and access matrix (Appendix E3)
tier: integrate
executor: mixed
owner: Mike
repo: planning
status: blocked
sow: D4
due: 2026-12-04
blocked_by: [DEP-16]
depends_on_stories: []
params: [approved_table_list, entra_groups, masked_column, classification_rules, access_matrix_file]   # access_matrix_file is proposed
human_gates: [Noah Jackson names the masked column and signs the tables, Matt Schiefelbein signs the groups]
---

## Story

As Mike (project manager), I want a pre-filled masking and access matrix sent to Mitsui and signed by Fri Dec 4, so that Lake Formation enforces what Mitsui agreed, not our guess.

## Context

Task list Week 3: request the masked column and classification rules on Mon Nov 30, sign the matrix on Fri Dec 4 (DEP-16, item 6.2). The agent pre-fills Appendix E3 from the approved table list (F4, DEP-10) and the table inventory, and proposes a masked column from candidate fields (royalty owner, lessor, price assumption, reserves value). Descriptions (F5) are due Dec 10, so use names and data types only.

The signed matrix is stored twice: the signed document as evidence, and `config/access-matrix.yaml` as the machine form read by F07-S01 and F07-S02.

## Acceptance criteria

1. Given the approved table list, when the matrix is pre-filled, then every approved table has a row with the groups for full, masked and no access, and at least one proposed masked column.
   - verify: `scripts/check-access-matrix.sh` exits 0 (every approved table present, every group name in `entra_groups`). Script created by this story.
2. Given the request on Nov 30, when Noah Jackson replies, then the masked column and the royalty owner and lessor classification rules are recorded.
   - gate: Noah Jackson's reply saved in `user-stories/evidence/F07/`.
3. Given the final matrix, when it is signed, then Noah Jackson signs the tables and Matt Schiefelbein signs the groups by Fri Dec 4.
   - gate: signed matrix saved in `user-stories/evidence/F07/`. If not signed by Dec 4, log a slip (F01-S06).
4. Given the signed matrix, when the YAML is updated, then it matches the signed document and `masked_column` is `set`.
   - verify: `scripts/check-access-matrix.sh --signed` exits 0.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-16 | A+C | Masked column, rules, signatures | Proposed matrix |
| DEP-10 | A+C | Approved table list | Table inventory |

## Evidence

Pre-filled matrix, Mitsui reply, signed matrix.

## Status log

- 2026-11-19: created
