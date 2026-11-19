---
id: F02-S10
feature: F2
title: Confirm the temporary cross-account role is deleted
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
human_gates: [Mitsui deletes the role, Mitsui sends CloudTrail review confirmation]
---

## Story

As Mike (project manager), I want written proof that Mitsui deleted the temporary AdministratorAccess role after use, so that InfoSec can see CapNexus's elevated access ended on time.

## Context

Task list Fri Nov 20 and DEP-02 step 5. The role is deleted only after Control Tower and Identity Center preparation are done (F02-S06, F02-S07). Before deletion, confirm CapNexus engineers can reach the accounts through Identity Center, or the team loses access.

## Acceptance criteria

1. Given F02-S06 and F02-S07 are done, when Mike asks Mitsui to delete the role, then Mitsui confirms deletion in writing.
   - gate: Noah Jackson or Matt Schiefelbein confirms. The reply is saved in `evidence/F02/cross-account-role/`.
2. Given the role is deleted, when a CapNexus engineer tries to assume it, then the call is refused.
   - verify: `aws sts assume-role` with the old role ARN returns `AccessDenied`. Output saved as evidence.
3. Given the deletion, when Mitsui reviews CloudTrail for the role's sessions, then Mitsui sends a confirmation that the review is done.
   - gate: Mitsui's CloudTrail review confirmation is saved in the evidence folder and noted in the RAID log.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-02 | D+B | Mitsui deletes the role and reviews CloudTrail | None. |

## Evidence

`evidence/F02/cross-account-role/`: written confirmation, refused assume-role output, CloudTrail review confirmation.

## Status log

- 2026-11-19: created
