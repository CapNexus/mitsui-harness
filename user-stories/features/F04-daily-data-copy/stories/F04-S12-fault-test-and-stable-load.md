---
id: F04-S12
feature: F4
title: Run the partial-load fault test and reach a stable load
tier: integrate
executor: mixed
owner: Venkat
repo: project-mep-AWS-Code
status: ready
sow: D3
due: 2026-12-11
blocked_by: [DEP-24]
depends_on_stories: [F04-S07, F04-S11]
params: [alarm_distribution_list]
human_gates: [a Mitsui recipient confirms the alarm email arrived]
---

## Story

As a Mitsui DBA, I want proof that a broken load raises an alarm to our list, and that the load is stable before the unattended window, so that we can trust it to run alone over the holidays.

## Context

Week 4 (Dec 7 to Dec 11) is for stabilizing the load. Fixes are allowed. Fri Dec 11 is the hard target: five clean daily loads, Dec 7 to Dec 11. The fault test is also end-to-end scenario E2E-6. Run it outside the load window, on a manual run, before Dec 11.

## Acceptance criteria

1. Given a manual load run in the POC account, when the DMS task is stopped mid-load, then the partial-load alarm goes to ALARM and an email reaches `alarm_distribution_list`.
   - gate: a Mitsui recipient confirms receipt. Email saved as evidence.
   - verify: `aws cloudwatch describe-alarm-history` shows the transition. Output saved.
2. Given the stopped run, when the next scheduled load completes, then counts match again and the assistant data shows no half-loaded tables (`wda_meta.load_runs` shows `ok` for every table).
   - verify: `load_runs` query for the next run.
3. Given the scheduled runs from Dec 7 to Dec 11, when `scripts/clean-load-streak --as-of 2026-12-11` runs, then it reports at least 5.
   - verify: the script output, saved as evidence.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-24 | A | Mitsui distribution list | CapNexus on-call address. The gate needs the real list. |

## Evidence

`evidence/F04/fault-test/` and `evidence/F04/stable-load/`.

## Status log

- 2026-11-19: created
