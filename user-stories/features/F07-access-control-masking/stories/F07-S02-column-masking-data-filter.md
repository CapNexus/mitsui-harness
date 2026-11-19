---
id: F07-S02
feature: F7
title: Build the column-masking data filter as code
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Code
status: ready
sow: D4
due: 2026-12-01
blocked_by: []
depends_on_stories: [F07-S01]
params: [masked_column, classification_rules, entra_groups, identity_mode, access_matrix_file]   # identity_mode and access_matrix_file are proposed
human_gates: []
---

## Story

As Venkat (DevOps), I want the masked column enforced by a Lake Formation data filter driven by the matrix file, so that only `sg-wda-econ-sensitive` sees the real value and swapping in Mitsui's chosen column is a config change.

## Context

SOW: "column masking demonstrated on at least one column". The column is not named yet (DEP-16). In the sandbox, use a dummy column on a dummy MEPS_ARIES table, for example `dummy_royalty_owner`.

Lake Formation data filters exclude columns. "Masked" in the POC means the column is not returned to users outside `sg-wda-econ-sensitive`. If Mitsui wants a partial value (for example the last 4 characters), that is a design change and needs a decision.

Out of scope: choosing the column (F07-S03).

## Acceptance criteria

1. Given `masked_column` in the matrix, when synthesized, then a data filter on that table includes all columns except the masked one, and is granted to every permitted group except `sg-wda-econ-sensitive`, which gets the full table.
   - verify: `make test-lf-masking` passes. Target created by this story.
2. Given a member of `sg-wda-econ-sensitive` in the sandbox, when they select the table, then the masked column is returned.
   - verify: `scripts/test-lf-grants.sh --env sandbox --case masked-full` exits 0.
3. Given a member of `sg-wda-users-econ` only, when they select the table (including `SELECT *`), then the masked column is not returned.
   - verify: `scripts/test-lf-grants.sh --env sandbox --case masked-hidden` exits 0.
4. Given the column name changes in the matrix, when redeployed, then only config changes.
   - verify: `make lint-config` passes and no column name is hard-coded.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-16 | A+C | Masked column and rules | `dummy_royalty_owner` in the sandbox |

## Evidence

Test output.

## Status log

- 2026-11-19: created
