---
id: F02-S06
feature: F2
title: Launch the Control Tower landing zone with Region-deny exceptions
tier: integrate
executor: mixed
owner: Venkat
repo: project-mep-AWS-Infrastructure
status: blocked
sow: D2
due: 2026-11-18
blocked_by: [DEP-02, DEP-03]
depends_on_stories: [F02-S01]
params: [aws_home_region, aws_allowed_regions, account_email_log_archive, account_email_audit]
human_gates: [Venkat and Soma approve the landing zone manifest before launch]
---

## Story

As Venkat (DevOps), I want the Control Tower landing zone launched from a manifest kept in the repository, so that the account structure is repeatable and the Region-deny control already allows the Regions Claude cross-region inference needs.

## Context

Task list Tue Nov 17 (prepare) and Wed Nov 18 (launch). Home Region us-east-1. Region-deny allows us-east-1, us-east-2 and us-west-2 (risk 5). Control Tower creates the Log Archive and Audit accounts from the DEP-03 emails, and the Security OU. This story also creates the Workloads OU. The launch uses the Control Tower landing zone API with a manifest file, so the settings are stored in the repository.

Out of scope: the POC workload account (F02-S07).

## Acceptance criteria

1. Given the manifest in the repository, when it is validated, then it sets home Region `aws_home_region`, governed Regions `aws_allowed_regions`, Region deny on, organization trail and Config on, and uses the two account emails.
   - verify: `scripts/validate-landing-zone-manifest.sh` exits 0. Script is created by this story.
2. Given the activated management account, when the landing zone is launched, then its status is ACTIVE and the Log Archive and Audit accounts are enrolled.
   - verify: `aws controltower get-landing-zone` shows status `ACTIVE` and drift status `IN_SYNC`.
   - gate: Venkat and Soma approve the manifest before launch.
3. Given the landing zone, when the OUs are listed, then Security and Workloads OUs exist and Workloads is registered with Control Tower.
   - verify: `aws organizations list-organizational-units-for-parent` shows both OUs, and `aws controltower list-enabled-baselines` includes Workloads.
4. Given the Region-deny control, when a call is made in us-east-2 or us-west-2 from a governed account, then it is not denied, and a call in another Region is denied.
   - verify: `scripts/check-region-deny.sh` exits 0. Script is created by this story.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-02 | D+B | Activated management account with root MFA and the cross-account role | None. The story waits. |
| DEP-03 | D+A | Log Archive and Audit account emails | `account_email_log_archive`, `account_email_audit` |

## Evidence

Landing zone status output and the validated manifest, in `evidence/F02/landing-zone/`.

## Status log

- 2026-11-19: created
