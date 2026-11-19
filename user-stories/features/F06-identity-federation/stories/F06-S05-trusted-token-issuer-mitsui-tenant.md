---
id: F06-S05
feature: F6
title: Deploy the trusted token issuer for the Mitsui Entra tenant
tier: integrate
executor: mixed
owner: Soma
repo: project-mep-AWS-Infrastructure
status: blocked
sow: D4
due: 2026-12-01
blocked_by: [DEP-14]
depends_on_stories: [F06-S02, F06-S03, F06-S04]
params: [entra_tenant_id, entra_issuer_url, wda_api_audience]
human_gates: [A Mitsui test user signs in to obtain a WDA-API token]
---

## Story

As Soma (solution architect), I want the trusted token issuer pointed at Mitsui's Entra tenant, so that tokens issued for WDA-API are accepted and the signed-in user can be carried to Athena.

## Context

Task list Week 3, Tue Dec 1 (item 5.4). Deploys the stack from F06-S04 through the pipeline with real values. Only config changes, no code changes.

Out of scope: the propagation test and decision (F06-S07).

## Acceptance criteria

1. Given the real values in `config/parameters.md`, when the pipeline deploys, then the trusted token issuer uses the Mitsui tenant issuer URL and maps the `email` claim.
   - verify: `aws sso-admin describe-trusted-token-issuer` output matches `entra_issuer_url` and the claim mapping. Saved by `scripts/test-token-exchange.sh --env poc`.
2. Given a Mitsui test user, when they obtain a token for the WDA-API audience, then the token exchange with the trusted token issuer succeeds.
   - verify: `scripts/test-token-exchange.sh --env poc` exits 0.
   - gate: the test user signs in interactively. Their token is never stored.
3. Given a token for a different audience, when it is exchanged, then the exchange is refused.
   - verify: the same script runs a negative case.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-14 | D+B+A | Tenant ID, issuer URL, WDA-API audience, a test user | none, blocked |

## Evidence

Script output (no tokens) in `user-stories/evidence/F06/`.

## Status log

- 2026-11-19: created
