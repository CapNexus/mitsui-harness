---
id: F02-S06
feature: F2
title: Verify the Control Tower landing zone and Region-deny exceptions
tier: integrate
executor: mixed
owner: Venkat
repo: planning
status: blocked
sow: D2
due: 2026-11-18
blocked_by: [DEP-02]
depends_on_stories: [F02-S01]
params: [aws_home_region, aws_allowed_regions]
human_gates: [Mitsui sends the landing zone export, Soma reviews it against the design]
---

## Story

As Venkat (DevOps), I want written evidence that the Control Tower landing zone Mitsui launched matches the design, so that the account structure is known and the Region-deny control allows the Regions Claude cross-region inference needs.

## Context

Mitsui launched Control Tower in the management account `463768556578` (RAID I-11, decided 2026-11-22). CapNexus does not launch it and has no management-account access. This story is verify-only. Region-deny must allow us-east-1, us-east-2 and us-west-2 (risk 5). `aws organizations list-accounts` from `166390307071` shows five accounts: Management, Identity Delegated Admin, Log Archive, Audit and Blank Canvas (`108953016877`, the POC account).

Out of scope: launching or changing the landing zone, and the POC account itself (F02-S07).

## Acceptance criteria

1. Given Mitsui's export of `aws controltower get-landing-zone`, when it is checked, then status is `ACTIVE`, drift status is `IN_SYNC`, the home Region is `aws_home_region` and the governed Regions include `aws_allowed_regions`.
   - verify: `scripts/check-landing-zone-export.sh evidence/F02/landing-zone/landing-zone.json` exits 0. Script is created by this story.
   - gate: Noah Jackson or Matt Schiefelbein sends the export. Soma reviews it.
2. Given the organization, when accounts and OUs are listed, then Log Archive, Audit and the POC account exist and the Security and Workloads OUs exist.
   - verify: `aws organizations list-accounts` (run from `166390307071`) output is saved in `evidence/F02/landing-zone/`.
   - gate: Mitsui sends the OU listing, which needs the management account.
3. Given the Region-deny control, when Mitsui shows its configuration, then us-east-2 and us-west-2 are allowed and other Regions are denied.
   - gate: Mitsui sends the control configuration. Soma records the result in the RAID log.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-02 | D+B | Mitsui sends the landing zone export and the OU listing | None. The story waits for the exports. |

## Evidence

Landing zone export and the checker output, in `evidence/F02/landing-zone/`.

## Status log

- 2026-11-19: created
- 2026-11-22: rewritten as verify-only after RAID I-11. Repo changed from `project-mep-AWS-Infrastructure` to `planning`. The manifest and `validate-landing-zone-manifest.sh` are dropped, `check-region-deny.sh` is replaced by a gate.
