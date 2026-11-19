---
id: F04-S13
feature: F4
title: Run the unattended window and export the evidence
tier: integrate
executor: mixed
owner: Venkat
repo: planning
status: blocked
sow: D3
due: 2026-12-24
blocked_by: [DEP-04, DEP-12]
depends_on_stories: [F04-S12]
params: [load_window, load_blackout_dates]
human_gates: [Mitsui DBAs and network team confirm no changes Dec 14 to Dec 25, Mitsui accepts the next-business-day check of the Dec 25 load, Mitsui DBAs confirm the Dec 25 load]
---

## Story

As Noah Jackson (Mitsui), I want evidence that the daily load ran without intervention for the final two weeks, so that I can sign the acceptance criterion for the load.

## Context

Decided Nov 17: the unattended window is Mon Dec 14 to Fri Dec 25. The load pipeline is frozen from Dec 14. Only fixes for a failed load are allowed. Dec 25 is a holiday and the readout is Thu Dec 24, so the DMS task history and alarm history for Dec 14 to Dec 24 are exported on Dec 24. The Dec 25 run is checked on the next business day and added (Feature List Section 5, gap 1).

## Acceptance criteria

1. Given Mon Dec 7, when the notice is sent, then Mitsui DBAs and the network team have confirmed in writing that the servers and VPN do not change from Dec 14 to Dec 25, and the window is in the change-freeze calendar.
   - gate: written confirmations, saved as evidence.
2. Given Dec 14, when the freeze starts, then a freeze tag exists in the code repository and no deploy of the load pipeline happens after it unless it is linked to a failed-load issue in the RAID log.
   - verify: `scripts/check-load-freeze.sh --since 2026-12-14` lists deploys after the tag and fails on any without a RAID issue ID. Script is created by this story.
3. Given Thu Dec 24, when the export runs, then the DMS task history, Step Functions executions, `load_runs` and alarm history for Dec 14 to Dec 24 are saved, with no manual starts.
   - verify: `scripts/export-load-evidence.sh --from 2026-12-14 --to 2026-12-24` writes the files and fails if any execution was started manually. Script is created by this story.
4. Given the Dec 25 holiday load, when Mitsui DBAs check it on the next business day, then the result is added to the evidence.
   - gate: Mitsui accepts this plan in writing before Dec 14, and the DBAs confirm the Dec 25 result.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-04 | C | Change-freeze calendar covering Dec 14 to Dec 25 | None |
| DEP-12 | A | Load window and blackouts | Values from F04-S11 |

## Evidence

`evidence/F04/unattended-window/`: confirmations, freeze check output, Dec 14 to Dec 24 export, Dec 25 confirmation.

## Status log

- 2026-11-19: created
