---
id: F03-S08
feature: F3
title: Prove Bedrock, Athena and logs work over PrivateLink with no internet
tier: integrate
executor: mixed
owner: Venkat
repo: project-mep-AWS-Infrastructure
status: blocked
sow: D2
due: 2026-11-24
blocked_by: [DEP-06]
depends_on_stories: [F03-S05, F02-S08]
params: [aws_home_region, vpc_cidr]
human_gates: []
---

## Story

As Venkat (DevOps), I want a test that calls Bedrock, Athena and CloudWatch Logs from inside the VPC with no internet route, so that we know the assistant and tools will work over private endpoints only.

## Context

F3 criterion 5. The test runs as a Lambda function in the tool subnet, which has no internet gateway or NAT. It reuses the Bedrock smoke test from F02-S08, so it waits for model access (DEP-06). The due date follows DEP-06 ("Week 1 or Week 2").

## Acceptance criteria

1. Given the tool subnet, when the test resolves the Bedrock runtime, Athena and Logs hostnames, then each resolves to a private IP inside `vpc_cidr`.
   - verify: `scripts/privatelink-check.sh --dns` exits 0. Script is created by this story.
2. Given the same subnet, when the test calls Claude on Bedrock, runs `SELECT 1` on Athena and writes a log event, then all three succeed.
   - verify: `scripts/privatelink-check.sh --calls` exits 0.
3. Given the VPC, when the test tries to reach a public internet address, then it fails.
   - verify: `scripts/privatelink-check.sh --expect-no-internet` exits 0.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-06 | A+D | Claude model access in the POC account | Proposed new parameter `bedrock_model_id` |

## Evidence

Test output in `evidence/F03/privatelink/`.

## Status log

- 2026-11-19: created
