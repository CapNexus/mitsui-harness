---
id: F02-S07
feature: F2
title: Verify the POC workload account and IAM Identity Center
tier: integrate
executor: mixed
owner: Venkat
repo: planning
status: blocked
sow: D2
due: 2026-11-19
blocked_by: [DEP-02]
depends_on_stories: [F02-S06]
params: [aws_home_region]
human_gates: [Soma confirms the Identity Center identity source is left unchanged, Mitsui confirms Blank Canvas is the POC account]
---

## Story

As Venkat (DevOps), I want evidence that the POC workload account exists in the Workloads OU and IAM Identity Center is enabled, so that all POC resources have a governed home and CapNexus can work through Identity Center.

## Context

Mitsui created the accounts (RAID I-11, decided 2026-11-22). The POC account is `Blank Canvas`, `108953016877`. Identity Center is administered from the delegated admin account `166390307071`. The identity source stays the default directory until the one-time switch to Entra (F6). This story is verify-only.

Out of scope: creating accounts and a CapNexus deployment role in the POC account. Ask Mitsui for that role as a new dependency if F02-S08 or F02-S09 need it.

## Acceptance criteria

1. Given the POC account `108953016877`, when Mitsui shows its enrollment, then it is in the Workloads OU with no drift.
   - gate: Noah Jackson or Matt Schiefelbein sends the enrollment status and confirms `Blank Canvas` is the POC account. Evidence saved in `evidence/F02/accounts/`.
2. Given Identity Center, when instances are listed from `166390307071`, then one organization instance exists in us-east-1 and the identity source is still the Identity Center directory.
   - verify: `aws sso-admin list-instances` returns one instance in us-east-1. Output (instance ARN only) saved in `evidence/F02/accounts/`.
   - gate: Soma confirms the identity source was not switched.
3. Given Identity Center, when each CapNexus engineer signs in to the AWS access portal, then they can reach the POC account with their assigned permission set.
   - gate: each engineer confirms sign-in.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-02 | D+B | Mitsui confirms the POC account and sends enrollment status | None. |

## Evidence

Account enrollment output and the Identity Center instance ARN, in `evidence/F02/accounts/`.

## Status log

- 2026-11-19: created
- 2026-11-22: rewritten as verify-only after RAID I-11. `account_email_poc` and DEP-03 dropped. POC account is `Blank Canvas` `108953016877`, pending Mitsui confirmation.
