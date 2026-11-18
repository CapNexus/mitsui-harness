---
id: F01-S04
feature: F1
title: Submit Deliverable 1 and record the review clock
tier: integrate
executor: mixed
owner: Mike
repo: planning
status: ready
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
   - verify: `scripts/check-d1-draft.sh` checks the section headings and the question counts. Script is created by this story.
2. Given the reviewed D1, when it is submitted, then it goes to the acceptance owner with an acceptance form.
   - gate: submission email and form saved as evidence.
3. Given the submission, when it is sent, then the review clock start date and the end date (8 business days later) are recorded in the RAID log.
   - verify: `scripts/check-raid-log.sh --require-clock D1` exits 0.
4. Given the acceptance owner is named, when D1 is submitted, then the owner has been told how the 8-business-day clock and the written rejection path work.
   - gate: confirmation in the Week 1 status call notes.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-23 | C | Noah Jackson confirmed as the signer (decided at kick-off) | Noah Jackson is used as the signer |

## Evidence

The submitted D1 file, the submission email, the form, and the RAID log row with both dates.

## Status log

- 2026-11-17: created
