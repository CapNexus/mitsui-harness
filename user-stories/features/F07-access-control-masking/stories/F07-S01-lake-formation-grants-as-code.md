---
id: F07-S01
feature: F7
title: Build Lake Formation table grants by Entra group as code
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Code
status: ready
sow: D4
due: 2026-12-01
blocked_by: []
depends_on_stories: []
params: [entra_groups, approved_table_list, identity_mode, access_matrix_file]   # identity_mode and access_matrix_file are proposed
human_gates: []
---

## Story

As Venkat (DevOps), I want Lake Formation table grants generated from one access matrix file, so that changing who sees which table is a config change and the same code works in the sandbox and the POC account.

## Context

Workflow step D8. The grants read `access_matrix_file` (proposed: `config/access-matrix.yaml`, the machine form of Appendix E3). Until the matrix is signed (F07-S03), use a sandbox matrix with dummy tables in the three databases and the group names from `entra_groups`.

Two modes behind `identity_mode` (DEP-27):
- `propagated`: grant to the Identity Center groups.
- `group_fallback`: grant to one IAM role per Entra group (`wda-grp-<group>`).

Depends on F4 (tables in S3 Tables) and F6 (groups) for the POC deployment, not for this build story.

Out of scope: column masking (F07-S02), applying in the POC account (F07-S04).

## Acceptance criteria

1. Given a matrix file, when the code is synthesized, then each group gets SELECT and DESCRIBE only on its listed tables, and no group gets ALTER, DROP, INSERT or any data-location permission.
   - verify: `make test-lf-grants` passes (unit test over the synthesized grants). Target created by this story.
2. Given a table not in the matrix, when grants are generated, then no group gets access to it.
   - verify: the same test includes a table missing from the matrix.
3. Given `identity_mode: group_fallback`, when synthesized, then grants target one IAM role per group, and with `propagated` they target Identity Center groups.
   - verify: the test runs both modes.
4. Given the sandbox, when deployed, then a member of `sg-wda-users-well` can list MEPWELL tables and cannot list MEPS_ARIES tables.
   - verify: `scripts/test-lf-grants.sh --env sandbox` exits 0. Script created by this story.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-10 | A+C | Approved table list | Dummy tables |
| DEP-16 | A+C | Signed matrix | Sandbox matrix |
| DEP-27 | E | Identity mode | Both modes built |

## Evidence

Test output.

## Status log

- 2026-11-19: created
