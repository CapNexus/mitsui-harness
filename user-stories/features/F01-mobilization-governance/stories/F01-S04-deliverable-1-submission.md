---
id: F01-S04
feature: F1
title: Submit Deliverable 1 and record the review clock
tier: integrate
executor: mixed
owner: Mike
repo: planning
status: done
sow: D1
due: 2026-11-20
blocked_by: [DEP-23]
depends_on_stories: [F01-S01, F01-S02]
params: []
human_gates: [Mike (PM) submits D1, Noah Jackson receives the acceptance form]
---

## Story

As Mike (CapNexus project manager), I want to submit Deliverable 1 and record when the review clock starts, so that Mitsui accepts or rejects it within the 8 business days and we can plan around it.

## Context

D1 is the confirmed project plan and question set outline (about 7 questions per database and 9 joins). The agent drafts D1 from `task-list/` and the Feature List. A human reviews, submits and records the date. Under the SOW, silence for 8 business days is acceptance, so the written rejection path must be explained to the acceptance owner.

## Acceptance criteria

1. Given the task list and the feature list, when the agent drafts D1, then the draft contains the project plan with dates, the dependency owners, and a question set outline with about 7 questions per database and 9 joins.
   - gate: dropped 2026-11-20 (RAID D-10). D1 was submitted 2026-11-16 and is kept in the CapNexus project management workspace, so no repo copy exists to check. Attested by Soma Muniyappa.
2. Given the reviewed D1, when it is submitted, then it goes to the acceptance owner with an acceptance form.
   - gate: D1 submitted to Noah Jackson 2026-11-16. Attested by Soma Muniyappa; the email and form are kept in the CapNexus project management workspace (RAID D-10).
3. Given the submission, when it is sent, then the review clock start date and the end date (8 business days later) are recorded in the RAID log.
   - gate: recorded as RAID D-11 (start 2026-11-16, end 2026-11-30, excluding the 2026-11-26 and 2026-11-27 holidays). The `--require-clock` flag was dropped (RAID D-13).
4. Given the acceptance owner is named, when D1 is submitted, then the owner has been told how the 8-business-day clock and the written rejection path work.
   - gate: explained to Noah Jackson at the meeting. Attested by Soma Muniyappa (RAID D-10, D-11).

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-23 | C | Noah Jackson confirmed as the signer (decided at kick-off) | Noah Jackson is used as the signer |

## Evidence

The submitted D1 file, the submission email, the form, and the RAID log row with both dates.

## Status log

- 2026-11-17: created
- 2026-11-20: criterion 1 script dropped (D1 already submitted, held outside the repo under RAID D-10). Clock recorded as RAID D-11.
- 2026-11-20: done. Gates attested by Soma Muniyappa (RAID D-10); review clock in RAID D-11; scripts dropped (RAID D-13).
