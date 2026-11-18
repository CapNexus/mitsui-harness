---
id: F01-S05
feature: F1
title: Send the weekly status report
tier: build
executor: mixed
owner: Mike
repo: planning
status: ready
sow: D1
due: 2026-11-23
blocked_by: []
depends_on_stories: [F01-S01]
params: []
human_gates: [Mike (PM) reviews and sends each report]
---

## Story

As the Mitsui sponsor, I want a weekly status report every Monday at 3:00 PM Eastern, so that I know what is done, what is late and what I need to do.

## Context

The agent generates the report from the dependency register, the RAID log and the weekly task list. A human reviews and sends it. Recipients are the kick-off attendees. The schedule starts Mon Nov 23, then every Monday through the end of the Period of Performance.

## Acceptance criteria

1. Given the register, the RAID log and the current week's plan, when the generator runs, then it produces a report with: work done, work planned, dependencies due this week with their status, slipped items with cause, and open decisions.
   - verify: `scripts/generate-status-report.sh --week <n>` produces a file with those five sections. Script is created by this story.
2. Given a report is ready, when it is sent on Monday by 3:00 PM Eastern, then it reaches every kick-off attendee.
   - gate: sent email saved as evidence. Recipient list matches the kick-off attendee list.
3. Given a week with no report, when the next check runs, then the miss is logged in the RAID log.
   - verify: `scripts/check-status-reports.sh` lists each Monday since kick-off and flags any without a saved copy.

## Dependencies

None.

## Evidence

`user-stories/evidence/F01/status-reports/` with one file per week.

## Status log

- 2026-11-17: created
