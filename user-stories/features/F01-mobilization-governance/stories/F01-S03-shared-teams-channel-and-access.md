---
id: F01-S03
feature: F1
title: Create the shared Teams channel and confirm CapNexus access
tier: integrate
executor: human
owner: Mike
repo: planning
status: done
sow: D1
due: 2026-11-20
blocked_by: [DEP-29]
depends_on_stories: [F01-S02]
params: []
human_gates: [Mitsui sends guest invitations, each engineer confirms sign-in]
---

## Story

As a CapNexus engineer, I want to sign in to the shared Teams channel, the AWS access portal and Entra as a guest, so that I can work with Mitsui staff and reach the POC environment.

## Context

Five CapNexus roles need access: Jeff Miller, Mike Charow, Soma Muniyappa, Venkat Paidipalli and Uday Gulbi (RAID D-08). AWS portal access depends on F2 (Identity Center) and Entra access on F6, so this story covers Teams and the guest invitation only. Portal sign-in is verified in F6.

## Acceptance criteria

1. Given the five CapNexus engineers, when access is checked, then each can sign in to the POC AWS environment and the Git repository.
   - gate: confirmed for all five by Soma Muniyappa, 2026-11-20 (RAID D-10, D-12).
2. Given the project meetings, when they are held, then they run in the CapNexus team channel. No shared Mitsui Teams channel is used for continuous discussion (RAID D-12).
   - gate: attested by Soma Muniyappa, 2026-11-20. The Entra guest invitation moves to F6.
3. Given a CapNexus engineer without access on the due date, when the date passes, then the gap is logged as a slipped DEP-29 with date and cause.
   - verify: `scripts/check-dependency-register.sh` passes with the slip fields filled.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-29 | D | Guest invitations from Mitsui | None. Engineers work in the CapNexus sandbox. |

## Evidence

`user-stories/evidence/F01/` with screenshots of each engineer's test post.

## Status log

- 2026-11-17: created
- 2026-11-20: named the five CapNexus engineers, adding Uday Gulbi from the project plan (RAID D-08).
- 2026-11-20: scope narrowed to AWS and Git access (RAID D-12); no shared Mitsui Teams channel. Done, attested by Soma Muniyappa.
