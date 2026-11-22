---
id: F01-S05
feature: F1
title: Send the weekly status report
tier: build
executor: mixed
owner: Mike
repo: planning
status: done
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
   - gate: the report is produced in the CapNexus project management workspace (RAID D-10). The generator script was dropped (RAID D-13).
2. Given a report is ready, when it is sent on Monday by 3:00 PM Eastern, then it reaches every kick-off attendee.
   - gate: covered in the CapNexus project management workspace, attested by Soma Muniyappa (RAID D-10). A copy is saved when the meeting recording is available.
3. Given a week with no report, when the next check runs, then the miss is logged in the RAID log.
   - gate: missed reports are tracked in the CapNexus project management workspace. The checker script was dropped (RAID D-13).

## Dependencies

None.

## Evidence

`user-stories/evidence/F01/status-reports/` with one file per week.

## Status log

- 2026-11-17: created
- 2026-11-20: kick-off moved to 2026-11-11 (RAID D-08). The first report stays Mon Nov 23, so the checker starts there and does not flag Mon Nov 16.
- 2026-11-20: done. Reporting runs in the CapNexus project management workspace (RAID D-10); scripts dropped (RAID D-13). Attested by Soma Muniyappa.
