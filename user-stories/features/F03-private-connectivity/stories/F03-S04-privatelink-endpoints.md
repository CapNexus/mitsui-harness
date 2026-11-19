---
id: F03-S04
feature: F3
title: Build the PrivateLink endpoints
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Infrastructure
status: ready
sow: D2
due: 2026-11-23
blocked_by: []
depends_on_stories: [F03-S02]
params: [aws_home_region]
human_gates: [Soma approves the endpoint list]
---

## Story

As Venkat (DevOps), I want interface endpoints for Bedrock, Athena and logging, and an S3 gateway endpoint, so that the tools, assistant and DMS reach AWS services without any internet path.

## Context

SOW and diagram: endpoints for Bedrock, Athena and logging. DMS also needs Secrets Manager and S3 (staging bucket). The cost estimate assumes one AZ for interface endpoints. Gap 8: an AgentCore endpoint may be needed later, so the list is configurable.

## Acceptance criteria

1. Given the endpoint stack, when it is synthesized, then it has interface endpoints for Bedrock runtime, Athena, CloudWatch Logs and Secrets Manager with private DNS on, and an S3 gateway endpoint on the DMS route table.
   - verify: CDK assertion test passes.
2. Given the endpoint security group, when it is checked, then it allows inbound 443 only from the VPC's own subnets.
   - verify: assertion test passes.
3. Given the endpoint list in config, when a service is added (for example AgentCore), then a new endpoint is created with no code change.
   - verify: unit test adds a service to the config and checks the extra endpoint.
4. Given the cost assumption, when the stack is synthesized, then interface endpoints are placed in one AZ by default, and the AZ count is a config value.
   - verify: assertion test passes for the default and for a two-AZ setting.

## Dependencies

None open. Proposed new parameter `endpoint_az_count` (default 1).

## Evidence

PR and test output.

## Status log

- 2026-11-19: created
