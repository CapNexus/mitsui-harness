---
id: F01-S02
feature: F1
title: Confirm kick-off date and named owners with backups
tier: integrate
executor: human
owner: Mike
repo: planning
status: ready
sow: D1
due: 2026-11-18
blocked_by: [DEP-01]
depends_on_stories: [F01-S01]
params: []
human_gates: [Noah Jackson names owners and backups in writing]
---

## Story

As Mike (CapNexus project manager), I want Mitsui to confirm the kick-off date and name an owner and a backup for every Week 1 dependency, so that the Period of Performance is fixed and every dependency has someone to chase.

## Context

The decisions log sets kick-off (start of the Period of Performance) at Mon Nov 16. The owner table is item 1.1 of the Dependencies doc. Unnamed roles today: DBA, GIS admin, Azure admin, InfoSec reviewer, SMEs, IT/PMO lead, executive sponsor.

## Acceptance criteria

1. Given the owner table sent to Noah Jackson, when Mitsui replies, then the reply confirms the kick-off date of Mon Nov 16 in writing.
   - gate: Noah Jackson's written reply, saved in the evidence folder.
2. Given each Week 1 dependency in the register, when owners are confirmed, then each has a named owner and a named backup recorded in the register and the RAID log.
   - verify: `scripts/check-dependency-register.sh --require-backup` exits 0 for DEP-01 to DEP-06 and DEP-25, DEP-26, DEP-29.
3. Given roles still blank on the next business day, when the check runs, then each is escalated to Noah Jackson and logged as an issue.
   - gate: escalation message sent, and RAID entry present.
4. Given the open governance gaps, when the owner table is answered, then it also records who the executive sponsor is above Noah Jackson, or records that none was named (Feature List Section 5, gap 5).
   - gate: Noah Jackson's answer.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-01 | D | Names and backups from Mitsui | Owner column keeps "to be named" |

## Evidence

`user-stories/evidence/F01/` for the written confirmations.

## Status log

- 2026-11-17: created. The Nov 16 target has passed, so record a slip under F01-S06 if no written confirmation exists.
