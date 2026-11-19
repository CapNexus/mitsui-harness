---
id: F08-S03
feature: F8
title: Publish the tools through AgentCore Gateway with a JWT authorizer
tier: build
executor: agent
owner: Soma
repo: project-mep-AWS-Code
status: ready
sow: D5
due: 2026-12-03
blocked_by: []
depends_on_stories: [F08-S02]
params: [entra_issuer_url, wda_api_audience, aws_home_region]
human_gates: []
---

## Story

As Soma (solution architect), I want the four tool Lambdas registered as targets of an AgentCore Gateway that only accepts tokens for the WDA-API audience, so that every MCP client must present a valid signed-in user token.

## Context

Task list Week 3, Thu Dec 3. Workflow steps Q6 and C1. The authorizer takes the OIDC discovery URL from `entra_issuer_url` and the audience from `wda_api_audience`. In the sandbox, use the sandbox OIDC provider. Pointing at Mitsui's Entra is F08-S06.

## Acceptance criteria

1. Given the Gateway as code, when synthesized, then it has four Lambda targets with the names from the tool contract and a JWT authorizer using `entra_issuer_url` and `wda_api_audience`.
   - verify: `make test-gateway` passes (synth assertions). Target created by this story.
2. Given the sandbox Gateway, when an MCP client lists tools with a valid token, then exactly the four tools are listed.
   - verify: `scripts/test-gateway.sh --env sandbox --case list-tools` exits 0. Script created by this story.
3. Given requests with no token, an expired token, a wrong audience and a bad signature, when they reach the Gateway, then each is refused before any tool runs.
   - verify: `scripts/test-gateway.sh --env sandbox --case auth-negative` exits 0, and no Lambda invocation is logged for these requests.
4. Given a valid token, when each tool is called through the Gateway, then the result matches a direct Lambda call.
   - verify: `scripts/test-gateway.sh --env sandbox --case tools` exits 0.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-14 | A | Issuer URL and audience | Sandbox OIDC provider |
| DEP-06 | A+D | Gateway available in the Region | Sandbox in us-east-1 |

## Evidence

Test output.

## Status log

- 2026-11-19: created
