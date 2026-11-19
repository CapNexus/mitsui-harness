---
id: F08-S06
feature: F8
title: Deploy the Gateway and tools to the POC account with Entra
tier: integrate
executor: mixed
owner: Soma
repo: project-mep-AWS-Code
status: blocked
sow: D5
due: 2026-12-03
blocked_by: [DEP-06, DEP-14]
depends_on_stories: [F08-S03, F08-S04, F08-S05, F06-S05, F07-S04]
params: [entra_issuer_url, wda_api_audience, test_users, identity_mode]   # test_users and identity_mode are proposed
human_gates: [User A signs in for the test, Soma approves the deployment]
---

## Story

As Soma (solution architect), I want the Gateway, Policy and tools deployed to the POC account against Mitsui's Entra tenant and real tables, so that the Week 3 permission test (F07-S06) and the Week 4 assistant (F9) can use them.

## Context

Task list Week 3, Thu Dec 3. Only config changes from the sandbox build: issuer URL, audience, identity mode. Needs the approved tables (F4), placeholder or SME descriptions (F5), Lake Formation grants (F07-S04) and the trusted token issuer (F06-S05).

## Acceptance criteria

1. Given the POC config, when the pipeline deploys, then the Gateway authorizer uses the Mitsui Entra issuer and the WDA-API audience.
   - verify: `scripts/test-gateway.sh --env poc --case config` exits 0.
2. Given requests with no token, a wrong audience and a bad signature, when they reach the POC Gateway, then each is refused.
   - verify: `scripts/test-gateway.sh --env poc --case auth-negative` exits 0.
3. Given User A's token, when each of the four tools is called, then each returns correct results against the approved tables.
   - verify: `scripts/test-gateway.sh --env poc --case tools` exits 0.
   - gate: User A signs in interactively. The token is never stored.
4. Given a write attempt through the POC Gateway, when sent, then the Policy refuses it and logs it.
   - verify: `scripts/test-gateway.sh --env poc --case write-refusal` exits 0.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-06 | A+D | AgentCore Gateway and Policy confirmed in us-east-1 | none |
| DEP-14 | D+B+A | Entra issuer, audience, User A | none |
| DEP-27 | E | Identity mode | `propagated` until F06-S07 decides |

## Evidence

Test output in `user-stories/evidence/F08/`.

## Status log

- 2026-11-19: created
