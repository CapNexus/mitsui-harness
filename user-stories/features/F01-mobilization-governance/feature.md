---
id: F1
title: Mobilization, plan and governance
sow: D1
due: 2026-11-20
status: in-progress
depends_on_features: []
blocked_by: [DEP-01, DEP-04, DEP-23, DEP-26, DEP-29]
---

## Description

Kick off the engagement, name owners for every client dependency, keep a RAID log and dependency tracker, and submit Deliverable 1 (confirmed project plan and question set outline). This feature also covers the weekly status call and the 8-business-day review clock.

Source: `WDA-POC-Feature-List.md`, F1.

## Feature-level acceptance criteria

| # | Criterion | Covered by |
|---|---|---|
| 1 | Written confirmation of the kick-off date (Mon Nov 16) and named owners and backups for each Week 1 dependency exist in the RAID log. | F01-S02 |
| 2 | The RAID log and dependency tracker contain every item from the Dependencies doc, each with an owner, due date and status. | F01-S01 |
| 3 | A shared Teams channel exists and the CapNexus engineers can sign in to it. | F01-S03 |
| 4 | Deliverable 1 is submitted with an acceptance form, and the date the 8-business-day review clock started is recorded. | F01-S04 |
| 5 | A weekly status report is sent every Monday at 3:00 PM Eastern to the kick-off attendees. | F01-S05 |
| 6 | Any slipped Week 1 dependency is logged with date and cause, and plan dates are shifted day for day (SOW Assumption 8). | F01-S06 |

## Stories

| ID | Title | Tier | Executor | Blocked by | Status |
|---|---|---|---|---|---|
| [F01-S01](stories/F01-S01-dependency-tracker-and-raid-log.md) | Set up the dependency tracker and RAID log | build | agent | none | ready |
| [F01-S02](stories/F01-S02-named-owners-and-kickoff-confirmation.md) | Confirm kick-off date and named owners with backups | integrate | human | DEP-01 | ready |
| [F01-S03](stories/F01-S03-shared-teams-channel-and-access.md) | Create the shared Teams channel and confirm CapNexus access | integrate | human | DEP-29 | ready |
| [F01-S04](stories/F01-S04-deliverable-1-submission.md) | Submit Deliverable 1 and record the review clock | integrate | mixed | DEP-23 | ready |
| [F01-S05](stories/F01-S05-weekly-status-report.md) | Send the weekly status report | build | mixed | none | ready |
| [F01-S06](stories/F01-S06-slipped-dependency-handling.md) | Log slipped dependencies and shift plan dates | build | mixed | none | ready |

## Open points

- DEP-04 (change-freeze calendar) and DEP-26 (budget approval) are Week 1 items under this feature's governance, but no story here resolves them. They are tracked as register rows in F01-S01 and are resolved by Mitsui. Their consumers are F2 and F3.
- Feature List Section 5, gap 5 (executive sponsor) and gap 6 (empty kick-off action items 5 and 6) are governance items. They are covered as checks in F01-S02.
- The kick-off date was Nov 16 and today is Nov 17, so F01-S02 is already behind its own date. Record it as a slip under F01-S06 if the confirmation is not in writing yet.
