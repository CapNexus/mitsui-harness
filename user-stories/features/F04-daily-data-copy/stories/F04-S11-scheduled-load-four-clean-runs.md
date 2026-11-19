---
id: F04-S11
feature: F4
title: Schedule the load in the agreed window and reach four clean runs
tier: integrate
executor: mixed
owner: Venkat
repo: project-mep-AWS-Code
status: ready
sow: D3
due: 2026-12-04
blocked_by: [DEP-12]
depends_on_stories: [F04-S08, F04-S09]
params: [load_window, load_blackout_dates]
human_gates: [DBAs confirm the load window and blackout dates]
---

## Story

As Noah Jackson (Mitsui), I want the daily load to run on its own inside the window our DBAs agreed, so that it does not compete with our batch jobs and needs no one to start it.

## Context

Week 2 Mon Nov 23: confirm the window with the DBAs. Week 3 Tue Dec 1: set the schedule and check the first scheduled run. Week 3 Fri Dec 4: four consecutive clean daily loads. The window must also fit after the SDEDBPROD compress job if that option is chosen (F04-S10).

## Acceptance criteria

1. Given the DBAs' answer, when it is recorded, then `load_window` and `load_blackout_dates` in `config/parameters.md` are `set`, with the source of the values in the RAID log.
   - gate: DBA confirmation, in writing.
   - verify: `scripts/check-raid-log.sh` exits 0.
2. Given the agreed window, when the schedule is deployed to the POC account on Dec 1, then the EventBridge schedule fires at the window start in `America/Chicago`, and the first scheduled run starts with no manual action.
   - verify: `aws scheduler get-schedule` output matches `load_window`. The Step Functions execution for Dec 1 or Dec 2 has no manual start.
3. Given four days of scheduled runs, when `scripts/clean-load-streak` runs on Fri Dec 4, then it reports at least 4.
   - verify: `scripts/clean-load-streak --as-of 2026-12-04` prints a value of 4 or more.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-12 | A | Load window and blackouts | `01:00-04:00 America/Chicago` example |

## Evidence

`evidence/F04/schedule/`: schedule output, `load_runs` export for Dec 1 to Dec 4.

## Status log

- 2026-11-19: created
