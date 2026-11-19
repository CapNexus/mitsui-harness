---
id: F06-S01
feature: F6
title: Confirm Entra prerequisites and run federation planning session
tier: integrate
executor: mixed
owner: Soma
repo: planning
status: blocked
sow: D4
due: 2026-11-24
blocked_by: [DEP-14]
depends_on_stories: []
params: [entra_tenant_id, entra_groups]
human_gates: [Matt Schiefelbein confirms Entra P1 licence and UPN equals primary email, Entra administrator session 1 held]
---

## Story

As Soma (solution architect), I want the Entra prerequisites confirmed and the federation steps agreed with Matt Schiefelbein before Dec 1, so that the one-time identity-source switch does not fail on licensing or claim mismatches.

## Context

Task list Week 2, Tue Nov 24: Entra administrator session 1 (federation and SCIM planning, Entra ID P1 licence check, risk 12). Steps follow item 5.2 of the Dependencies doc. The agent prepares the session pack. A human runs the session.

Out of scope: creating groups and apps (F06-S02), the switch itself (F06-S03).

## Acceptance criteria

1. Given the session is booked, when the pack is prepared, then `user-stories/evidence/F06/session-1-pack.md` lists the steps from item 5.2, the seven group names from `entra_groups`, the three app registrations from item 5.4, and the questions below.
   - verify: `grep -c 'sg-wda-' user-stories/evidence/F06/session-1-pack.md` returns 7 or more, and the file names WDA-API, WDA-TeamsBot and WDA-Clients.
2. Given session 1, when Matt Schiefelbein answers, then Entra ID P1 (or higher) licensing is confirmed in writing.
   - gate: Matt Schiefelbein's written confirmation saved in `user-stories/evidence/F06/`. If P1 is missing, a RAID issue is raised the same day.
3. Given session 1, when the UPN question is asked, then the answer (UPN equals primary email, or which claim to map) is recorded.
   - gate: answer recorded in the RAID log as a decision.
4. Given the Entra tenant ID is received, when it is recorded, then `entra_tenant_id` is a real value.
   - verify: `grep entra_tenant_id user-stories/config/parameters.md` shows status `set`.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-14 | D+B+A | Entra administrator time, licence answer, tenant ID | `TBD` tenant ID |

## Evidence

`user-stories/evidence/F06/session-1-pack.md` and the written P1 confirmation.

## Status log

- 2026-11-19: created
