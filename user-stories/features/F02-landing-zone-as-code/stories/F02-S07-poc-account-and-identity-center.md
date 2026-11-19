---
id: F02-S07
feature: F2
title: Create the POC workload account and enable IAM Identity Center
tier: integrate
executor: mixed
owner: Venkat
repo: planning
status: blocked
sow: D2
due: 2026-11-19
blocked_by: [DEP-02, DEP-03]
depends_on_stories: [F02-S06]
params: [account_email_poc, aws_home_region]
human_gates: [Soma confirms the Identity Center identity source is left unchanged]
---

## Story

As Venkat (DevOps), I want the POC workload account created through Account Factory and IAM Identity Center enabled, so that all POC resources have a governed home and CapNexus can work without the temporary cross-account role.

## Context

Task list Thu Nov 19 (items 2.3, 2.7). The account goes in the Workloads OU. Identity Center is enabled as the organization instance in us-east-1. The identity source stays the default directory until the one-time switch to Entra on Tue Dec 1 (F6). CapNexus engineers get temporary Identity Center users so they can keep working after the role is deleted on Fri Nov 20.

## Acceptance criteria

1. Given Account Factory, when the POC account is created from `account_email_poc`, then it is enrolled in the Workloads OU with no drift.
   - verify: `aws controltower list-enabled-baselines` shows the account enrolled and `aws organizations list-accounts-for-parent` lists it under Workloads.
2. Given the management account, when Identity Center is enabled, then an organization instance exists in us-east-1 and the identity source is still the Identity Center directory.
   - verify: `aws sso-admin list-instances` returns one instance in us-east-1.
   - gate: Soma confirms the identity source was not switched.
3. Given Identity Center, when each CapNexus engineer signs in to the AWS access portal, then they can reach the POC account with their assigned permission set.
   - gate: each engineer confirms sign-in. Matches task list Thu Nov 19 (item 1.6).

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-02 | D+B | Management account access | None. |
| DEP-03 | D+A | POC account email | `account_email_poc` |

## Evidence

Account enrollment output and the Identity Center instance ARN, in `evidence/F02/accounts/`.

## Status log

- 2026-11-19: created
