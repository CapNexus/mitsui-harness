---
id: F06-S06
feature: F6
title: Spike identity propagation to Athena in the sandbox
tier: build
executor: agent
owner: Soma
repo: project-mep-AWS-Code
status: ready
sow: D4
due: 2026-11-25
blocked_by: []
depends_on_stories: [F06-S04]
params: [entra_issuer_url, wda_api_audience, masked_column]
human_gates: [Soma reviews the spike findings]
---

## Story

As Soma (solution architect), I want to prove in the CapNexus sandbox that a user's OIDC token can be carried through the trusted token issuer to Athena and Lake Formation, so that we know before Dec 2 whether `identity_mode: propagated` is realistic or we should plan on the group fallback.

## Context

DEP-27 (type E) is the biggest design risk in F6 to F8 (risk 1). The real test runs on Wed Dec 2 (F06-S07). This spike de-risks it a week earlier with a sandbox OIDC provider, a sandbox Identity Center, one dummy S3 Table and a dummy masked column.

The spike produces a reusable test script that F06-S07 runs against the POC account.

Out of scope: Mitsui's tenant and data.

## Acceptance criteria

1. Given two sandbox users in different groups, when each runs the same SELECT through the identity-aware workgroup with their own token, then each query appears under that user's identity in Athena query history or CloudTrail.
   - verify: `scripts/test-identity-propagation.sh --env sandbox` exits 0 and prints the user identity per query. Script created by this story.
2. Given a Lake Formation grant on the dummy table to one group only, when the other user queries it, then the query is refused.
   - verify: the same script includes this negative case.
3. Given the spike results, when they are written up, then `docs/identity-propagation-spike.md` in this repo lists what worked, what failed, the services involved and the limits found, and recommends `propagated` or `group_fallback`.
   - gate: Soma reviews the write-up and records the recommendation in the RAID log.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-27 | E | Decision on identity mode | Spike informs it, does not decide it |

## Evidence

Script output and the write-up.

## Status log

- 2026-11-19: created
