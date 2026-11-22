---
id: F01-S06
feature: F1
title: Log slipped dependencies and shift plan dates
tier: build
executor: mixed
owner: Mike
repo: planning
status: ready
sow: D1
due: 2026-11-20
blocked_by: []
depends_on_stories: [F01-S01]
params: []
human_gates: [Mike (PM) approves shifted dates in the project plan (RAID D-13)]
---

## Story

As Mike (CapNexus project manager), I want every late dependency listed with its due date and days late, and every slipped one logged with its date and cause, so that the SOW schedule protection (Assumption 8) is documented when a Mitsui dependency is late.

## Context

SOW Assumption 8 shifts plan dates by the number of days a Mitsui dependency is late. This story adds `check-overdue.sh`; plan shifts are made by Mike Charow in the project plan (RAID D-08, D-13). It applies to all dependencies, not only Week 1, but Week 1 is where the first slips are likely (the Nov 16 items are already due).

## Acceptance criteria

1. Given a dependency whose needed-by date has passed without status `resolved`, when the checker runs, then it lists the dependency as overdue.
   - verify: `scripts/check-overdue.sh --today 2026-11-17` exits non-zero and lists every item due on or before that date that is not resolved: DEP-01 in the test fixture, DEP-02 in the register snapshot of 2026-11-20 (DEP-01 was resolved that day).
2. Given an overdue dependency is marked `slipped`, when the row is saved, then it has a slip start date, the cause, and the number of days late.
   - verify: `scripts/check-dependency-register.sh` fails if the slip date or cause is empty. Days late are computed by `scripts/check-overdue.sh` from the needed-by date, not stored in the row (RAID D-13).
3. Given a slipped dependency, when the shift helper runs, then it proposes new dates for the tasks that depend on it, shifted by the number of days late.
   - gate: dropped (RAID D-13). Plan dates live in the project plan (RAID D-08); Mike Charow shifts them there.
4. Given the proposed dates, when they are approved, then the task list files are updated and the change is described in the next weekly status report.
   - gate: Mike Charow approves shifts in the project plan and reports them in the weekly report (RAID D-10, D-13). No slip on 2026-11-20.

## Dependencies

None.

## Evidence

The register row and the `check-overdue.sh` output.

## Status log

- 2026-11-17: created
- 2026-11-20: scope cut to `check-overdue.sh` (RAID D-13); `shift-plan.sh` dropped.
