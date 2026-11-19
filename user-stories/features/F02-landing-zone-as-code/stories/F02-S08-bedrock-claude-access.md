---
id: F02-S08
feature: F2
title: Prove a Bedrock Claude call works from the POC account
tier: integrate
executor: mixed
owner: Soma
repo: project-mep-AWS-Infrastructure
status: blocked
sow: D2
due: 2026-11-24
blocked_by: [DEP-06]
depends_on_stories: [F02-S06, F02-S07]
params: [aws_home_region, aws_allowed_regions]
human_gates: [Mitsui submits the Anthropic first-use form and the quota request]
---

## Story

As Soma (solution architect), I want a repeatable smoke test that calls Claude on Bedrock from the POC account, so that model access, quotas and the Region-deny exceptions are proven before the assistant is built.

## Context

DEP-06 steps 2 to 5 and risk 4. The Anthropic first-use text and quota request were sent to Mitsui on Tue Nov 17 (item 2.6). Mitsui submits them. A new account starts with default quotas. The test uses a cross-region inference profile, so it also proves the Region-deny exceptions from F02-S06. The due date follows DEP-06 ("Week 1 or Week 2").

## Acceptance criteria

1. Given the POC account, when the smoke test calls Claude through the US cross-region inference profile, then it gets a response with no access or Region error.
   - verify: `scripts/smoke/bedrock-invoke.sh --profile poc` exits 0. Script is created by this story.
2. Given the first-use form and quota request, when Mitsui submits them, then the case or request IDs are recorded.
   - gate: Mitsui sends the IDs. Mike records them in the RAID log.
3. Given the current quotas, when they are read, then tokens-per-minute and requests-per-minute for the chosen model are recorded and compared with the pilot need (about 15 users).
   - verify: `aws service-quotas list-service-quotas --service-code bedrock` output for the model is saved in `evidence/F02/bedrock/`.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-06 | A+D | Claude model access and quotas | Proposed new parameter `bedrock_model_id` (model not chosen yet) |

## Evidence

Smoke test output and quota values in `evidence/F02/bedrock/`.

## Status log

- 2026-11-19: created
