---
id: F02-S04
feature: F2
title: Build the AWS Budgets alert
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Infrastructure
status: ready
sow: D2
due: 2026-11-19
blocked_by: []
depends_on_stories: [F02-S02]
params: [billing_contact_email, budget_monthly_usd]
human_gates: []
---

## Story

As Mike (project manager), I want a monthly AWS budget with email alerts to Mitsui's billing contact, so that AWS spend, which Mitsui pays directly, never surprises anyone.

## Context

Task list Thu Nov 19. The base estimate is about $350 a month (`adr/WDA-POC-AWS-Run-Cost-Estimate.md`). The values come from DEP-26 and stay placeholders here. Deploying and the test alert are in F02-S09.

## Acceptance criteria

1. Given the budget stack, when it is synthesized, then it creates a monthly cost budget for the amount in `budget_monthly_usd`.
   - verify: CDK assertion test passes.
2. Given the budget, when its notifications are checked, then it emails `billing_contact_email` at 80% of actual spend and 100% of forecast spend.
   - verify: assertion test on thresholds and subscriber passes.
3. Given `budget_monthly_usd` or `billing_contact_email` is still `TBD`, when synth runs for the POC stage, then synth fails with a message naming the parameter.
   - verify: unit test for the missing-value case passes.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-26 | C+A | Budget amount and billing contact | `budget_monthly_usd`, `billing_contact_email` (sandbox values in the sandbox stage) |

## Evidence

PR and test output.

## Status log

- 2026-11-19: created
