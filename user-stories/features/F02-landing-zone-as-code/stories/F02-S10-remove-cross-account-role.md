---
id: F02-S10
feature: F2
title: Confirm the elevated cross-account access is removed or scoped
tier: integrate
executor: human
owner: Mike
repo: planning
status: blocked
sow: D2
due: 2026-11-20
blocked_by: [DEP-02]
depends_on_stories: [F02-S06, F02-S07]
params: []
human_gates: [Mitsui confirms the state of the CapNexus roles, Mitsui sends CloudTrail review confirmation]
---

## Story

As Mike (project manager), I want written proof of what CapNexus access exists in Mitsui's accounts and that no elevated temporary role remains, so that InfoSec can see CapNexus's access is limited and ended on time.

## Context

Task list Fri Nov 20 and DEP-02 step 5. CapNexus was never given an AdministratorAccess role in the management account `463768556578` (RAID I-11, decided 2026-11-22). It uses `CapNexusDeploymentRole` in `166390307071`, which can be assumed without an external ID or MFA (RAID I-10, accepted by Soma 2026-11-22). Before any role is deleted, confirm CapNexus engineers can reach the accounts through Identity Center, or the team loses access.

## Acceptance criteria

1. Given F02-S06 and F02-S07 are done, when Mike asks Mitsui, then Mitsui confirms in writing that no temporary AdministratorAccess role for CapNexus exists in the management account, and states the permissions and expiry of `CapNexusDeploymentRole`.
   - gate: Noah Jackson or Matt Schiefelbein confirms. The reply is saved in `evidence/F02/cross-account-role/`.
2. Given any temporary role Mitsui has issued is deleted, when a CapNexus engineer tries to assume it, then the call is refused.
   - verify: `aws sts assume-role` with that role ARN returns `AccessDenied`. Output saved as evidence. Skip if Mitsui confirms in AC1 that no such role exists.
3. Given the confirmation, when Mitsui reviews CloudTrail for CapNexus role sessions, then Mitsui sends a confirmation that the review is done.
   - gate: Mitsui's CloudTrail review confirmation is saved in the evidence folder and noted in the RAID log.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-02 | D+B | Mitsui confirms the roles and reviews CloudTrail | None. |

## Evidence

`evidence/F02/cross-account-role/`: written confirmation, refused assume-role output if applicable, CloudTrail review confirmation.

## Status log

- 2026-11-19: created
- 2026-11-22: rescoped after RAID I-10 and I-11. No management-account temporary role was issued. Title and AC1 changed, AC2 made conditional.
