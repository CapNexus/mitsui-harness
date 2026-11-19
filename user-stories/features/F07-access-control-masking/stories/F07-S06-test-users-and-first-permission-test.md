---
id: F07-S06
feature: F7
title: Create test users A, B, C and run the first permission test
tier: integrate
executor: mixed
owner: Soma
repo: project-mep-AWS-Code
status: blocked
sow: D9
due: 2026-12-04
blocked_by: [DEP-14]
depends_on_stories: [F07-S04, F07-S05, F06-S03]
params: [test_users, entra_groups, access_matrix_file]   # test_users and access_matrix_file are proposed
human_gates: [Matt Schiefelbein creates the three test users, each test user signs in for the run]
---

## Story

As Soma (solution architect), I want the three Mitsui test users created in the right groups and the first permission test run through Athena and the Gateway, so that we find access-control gaps in Week 3, not in UAT.

## Context

Task list Week 3: create test users and verify membership on Wed Dec 2 (item 5.6), first permission test through the Gateway on Fri Dec 4. The Integration & Test Engineer runs it. The Gateway run needs F8 deployed in the POC account (F08-S06). If F8 slips, run the Athena entry point only and log the gap.

## Acceptance criteria

1. Given the Entra administrator, when the test users are created, then User A is in all permitted groups and `sg-wda-econ-sensitive`, User B is in permitted groups but not `sg-wda-econ-sensitive`, and User C is in none, and all three appear in Identity Center.
   - gate: Matt Schiefelbein creates the users.
   - verify: `scripts/check-identity-center-groups.sh --test-users` (from F06-S03) confirms the memberships.
2. Given the POC account, when `scripts/permission-test.sh --env poc --entry athena` runs, then A sees all approved tables and the masked column, B sees the tables without the masked column, and C sees no restricted tables.
   - verify: the script exits 0. Report saved in `user-stories/evidence/F07/`.
3. Given F8 is deployed, when the same test runs with `--entry gateway`, then the results match the Athena run.
   - verify: the script exits 0 and the report shows identical results per user.
4. Given a write attempt sent directly to Athena by User A, when it runs, then Lake Formation refuses it.
   - verify: the harness write check passes in the POC account.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-14 | D+B+A | Test users A, B, C | none |
| DEP-16 | A+C | Matrix | Proposed matrix if not yet signed |

## Evidence

Permission test reports (Athena and Gateway) in `user-stories/evidence/F07/`.

## Status log

- 2026-11-19: created
