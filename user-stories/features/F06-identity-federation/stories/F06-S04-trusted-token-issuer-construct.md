---
id: F06-S04
feature: F6
title: Build the trusted token issuer and identity-aware Athena workgroup as code
tier: build
executor: agent
owner: Soma
repo: project-mep-AWS-Infrastructure
status: ready
sow: D4
due: 2026-11-25
blocked_by: []
depends_on_stories: []
params: [entra_issuer_url, wda_api_audience, aws_home_region, athena_scan_cutoff_gb]
human_gates: []
---

## Story

As Soma (solution architect), I want the trusted token issuer and the identity-aware Athena workgroup defined as CDK code that takes the issuer URL and audience as parameters, so that we can test it in the sandbox now and point it at Mitsui's Entra tenant on Dec 1 with a config change only.

## Context

Workflow step I3. Entra values (DEP-14) are not available until Nov 30. In the sandbox, use any OIDC provider (for example an Amazon Cognito user pool) as `entra_issuer_url`. The workgroup has a per-query scan cutoff of `athena_scan_cutoff_gb`.

Uses the CDK app and pipeline skeleton from F2. If that is not merged yet, build the stack so it can be added to the F2 app without changes.

Out of scope: deploying to Mitsui's account (F06-S05), the end-to-end propagation test (F06-S06).

## Acceptance criteria

1. Given the CDK stack, when synthesized with sandbox values, then it creates a trusted token issuer with the issuer URL from `entra_issuer_url` and the claim mapping `email` to the Identity Center user email.
   - verify: `make test-tti` passes (CDK assertions test). Target created by this story.
2. Given the stack, when synthesized, then it creates an Athena workgroup with IAM Identity Center authentication enabled and a per-query scan cutoff equal to `athena_scan_cutoff_gb`.
   - verify: the same test checks the workgroup properties.
3. Given the sandbox, when deployed, then a token from the sandbox OIDC provider is accepted by the trusted token issuer (token exchange succeeds).
   - verify: `scripts/test-token-exchange.sh --env sandbox` exits 0. Script created by this story.
4. Given no hard-coded tenant values, when the code is scanned, then no tenant ID, issuer URL or audience appears outside the config file.
   - verify: `make lint-config` passes.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-14 | A | Real issuer URL and audience (only for F06-S05) | Sandbox OIDC provider |

## Evidence

Test output and the sandbox token exchange log.

## Status log

- 2026-11-19: created
