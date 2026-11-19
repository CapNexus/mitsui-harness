---
id: F07-S04
feature: F7
title: Apply the access matrix in the POC account
tier: integrate
executor: mixed
owner: Venkat
repo: project-mep-AWS-Code
status: blocked
sow: D4
due: 2026-12-04
blocked_by: [DEP-14, DEP-16]
depends_on_stories: [F07-S01, F07-S02, F06-S03]
params: [access_matrix_file, masked_column, entra_groups, identity_mode]   # access_matrix_file and identity_mode are proposed
human_gates: [Venkat approves the pipeline deployment to the POC account]
---

## Story

As Venkat (DevOps), I want the Lake Formation grants and masking filter deployed to the POC account, first from the proposed matrix and then from the signed one, so that the Week 3 permission tests run against real tables and real Entra groups.

## Context

Task list Week 3, Wed Dec 2: configure Lake Formation by Entra group and the masked column. The matrix is signed on Fri Dec 4 (F07-S03), so deploy the proposed matrix on Dec 2 and re-deploy the signed one on Dec 4. Needs the approved tables loaded in S3 Tables (F4) and the Entra groups in Identity Center (F06-S03).

If `identity_mode` is still undecided on Dec 2 (F06-S07 runs the same day), deploy `propagated` and switch with a config change if needed.

## Acceptance criteria

1. Given the proposed matrix, when the pipeline deploys on Dec 2, then the grants and the data filter exist for every table in the matrix.
   - verify: `scripts/check-lf-deployed.sh --env poc` compares `aws lakeformation list-permissions` with the matrix and exits 0. Script created by this story.
2. Given the signed matrix (F07-S03), when the pipeline re-deploys, then the deployed grants match the signed matrix and no extra grants exist.
   - verify: the same script exits 0 after the re-deploy.
3. Given the deployment, when the permission export is saved, then it is in the evidence folder for InfoSec.
   - verify: `user-stories/evidence/F07/lf-permissions-<date>.json` exists.
   - gate: Venkat approves the pipeline run.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-14 | D+B+A | Entra groups synced to Identity Center | none |
| DEP-16 | A+C | Signed matrix | Proposed matrix on Dec 2 |
| DEP-27 | E | Identity mode | `propagated` until decided |

## Evidence

Lake Formation permission exports for Dec 2 and Dec 4.

## Status log

- 2026-11-19: created
