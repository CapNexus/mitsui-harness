---
id: F06-S07
feature: F6
title: Test identity propagation in the POC account and decide the identity mode
tier: integrate
executor: mixed
owner: Soma
repo: project-mep-AWS-Code
status: blocked
sow: D4
due: 2026-12-02
blocked_by: [DEP-27, DEP-14]
depends_on_stories: [F06-S05, F06-S06]
params: [entra_issuer_url, wda_api_audience, identity_mode]   # identity_mode is proposed, not yet in config/parameters.md
human_gates: [Soma decides the identity mode, Noah Jackson accepts the fallback in writing by Fri Dec 4 if it is used]
---

## Story

As Soma (solution architect), I want to run the identity propagation test in the POC account and set the identity mode, so that F7 and F8 enforce permissions the agreed way and every question still traces to a named user.

## Context

Task list Week 3, Wed Dec 2 (DEP-27, SOW Assumption 8, risk 1). Runs the script from F06-S06 against the POC account with a Mitsui test user (User A from F07-S06 if ready, otherwise any test user in a permitted group).

The result sets the proposed parameter `identity_mode`:
- `propagated`: tools query Athena as the signed-in user through the trusted token issuer.
- `group_fallback`: tools query with a role per Entra group, and the user's identity is logged at the application layer (F12).

Out of scope: the full A/B/C permission tests (F07-S06).

## Acceptance criteria

1. Given a Mitsui test user's token, when the test runs, then the query is attributed to that user in Athena query history or CloudTrail, or the failure is captured with the error.
   - verify: `scripts/test-identity-propagation.sh --env poc` output saved in `user-stories/evidence/F06/`.
2. Given the result, when the decision is made, then `identity_mode` is set to `propagated` or `group_fallback` and the decision is in the RAID log with the date.
   - gate: Soma decides.
3. Given `group_fallback` is chosen, when the fallback is documented, then Noah Jackson accepts it in writing by Fri Dec 4.
   - gate: Noah Jackson's written acceptance saved in `user-stories/evidence/F06/`.
4. Given the decision, when F7 and F8 stories are checked, then each has `identity_mode` in its params.
   - verify: `grep -l identity_mode user-stories/features/F07-*/stories/*.md user-stories/features/F08-*/stories/*.md` lists the stories that build the switch.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-27 | E | Identity mode decision | Both modes built behind `identity_mode` |
| DEP-14 | D+B+A | Mitsui test user | none |

## Evidence

Test output, RAID decision, Noah's acceptance if the fallback is used.

## Status log

- 2026-11-19: created
