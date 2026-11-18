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
human_gates: [Mike (PM) approves the shifted dates before they are sent to Mitsui]
---

## Story

As Mike (CapNexus project manager), I want every slipped Week 1 dependency logged with its date and cause and the plan shifted day for day, so that the SOW schedule protection (Assumption 8) is documented when a Mitsui dependency is late.

## Context

SOW Assumption 8 shifts plan dates by the number of days a Mitsui dependency is late. This story adds the procedure and a helper. It applies to all dependencies, not only Week 1, but Week 1 is where the first slips are likely (the Nov 16 items are already due).

## Acceptance criteria

1. Given a dependency whose needed-by date has passed without status `resolved`, when the checker runs, then it lists the dependency as overdue.
   - verify: `scripts/check-overdue.sh --today 2026-11-17` exits non-zero and lists DEP-01 and any other item due on or before that date that is not resolved.
2. Given an overdue dependency is marked `slipped`, when the row is saved, then it has a slip start date, the cause, and the number of days late.
   - verify: `scripts/check-dependency-register.sh` fails if any of these is empty.
3. Given a slipped dependency, when the shift helper runs, then it proposes new dates for the tasks that depend on it, shifted by the number of days late.
   - verify: `scripts/shift-plan.sh DEP-<nn> <days> --dry-run` prints the changed dates and writes nothing. Script is created by this story.
4. Given the proposed dates, when they are approved, then the task list files are updated and the change is described in the next weekly status report.
   - gate: Mike (PM) approves. The report from F01-S05 mentions the shift.

## Dependencies

None.

## Evidence

The register row, the `shift-plan.sh` dry-run output and the updated task list commit.

## Status log

- 2026-11-17: created
