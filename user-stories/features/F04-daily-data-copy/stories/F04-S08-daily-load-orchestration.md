---
id: F04-S08
feature: F4
title: Orchestrate and schedule the daily load
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Code
status: ready
sow: D3
due: 2026-12-01
blocked_by: []
depends_on_stories: [F04-S05, F04-S06]
params: [load_window, load_blackout_dates, sdedbprod_mode]
human_gates: []
---

## Story

As Venkat (DevOps), I want one scheduled workflow that runs the whole daily load in order, so that the load runs every day inside the agreed window with no manual action.

## Context

Load decision flow in `adr/WDA-POC-Data-Workflow.md`. A Step Functions state machine, started by an EventBridge schedule at the start of `load_window`:

1. Check SDEDBPROD is current (per `sdedbprod_mode`). If not, or if the mode is `undecided`, skip SDEDBPROD and publish the SDEDBPROD-skipped metric.
2. Start the DMS full-load tasks and wait for them to finish.
3. Run the load job (F04-S05).
4. Run the row-count check (F04-S06).
5. If the schema changed, call the catalog update hook (F5, F05-S04). Until F5 delivers it, the hook is a no-op.

The schedule skips dates in `load_blackout_dates`. The state machine has a timeout equal to the window length, so a load never runs past the window.

## Acceptance criteria

1. Given the state machine in the sandbox, when it runs, then it runs the steps in order and ends with the row-count check result.
   - verify: integration test `make test-orchestration` runs it end to end on the sandbox data.
2. Given `sdedbprod_mode: undecided`, when it runs, then MEPWELL and MEPS_ARIES load and the SDEDBPROD-skipped metric is published.
   - verify: integration test with the mode set to `undecided`.
3. Given `load_window` of `01:00-04:00 America/Chicago`, when the schedule is synthesized, then it starts at 01:00 Chicago time and the state machine timeout is 3 hours.
   - verify: CDK assertion test on the schedule expression, time zone and timeout.
4. Given a date in `load_blackout_dates`, when the schedule fires that day, then no DMS task starts and a `LoadSkippedBlackout` log entry is written.
   - verify: unit test of the blackout check.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-11 | E | SDEDBPROD approach | `sdedbprod_mode: undecided` |
| DEP-12 | A | Load window and blackout dates | `01:00-04:00 America/Chicago` example, no blackout dates |

## Evidence

PR with passing tests and a state machine run graph from the sandbox.

## Status log

- 2026-11-19: created
