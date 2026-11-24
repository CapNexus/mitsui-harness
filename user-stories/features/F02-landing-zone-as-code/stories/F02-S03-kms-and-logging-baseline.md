---
id: F02-S03
feature: F2
title: Build the KMS key and log encryption baseline
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Infrastructure
status: done
sow: D2
due: 2026-11-19
blocked_by: []
depends_on_stories: [F02-S02]
params: [aws_home_region]
human_gates: []
---

## Story

As Venkat (DevOps), I want one customer-managed KMS key that encrypts secrets and logs, so that DMS credentials, audit logs and Bedrock logs are all under a key Mitsui controls.

## Context

Used later by Secrets Manager (DEP-09 SQL credentials, F4), CloudWatch Logs and the audit trail (F12). See data workflow step D1 and Section 7.

Out of scope: who may read the logs (DEP-24, F12).

## Acceptance criteria

1. Given the baseline stack, when it is synthesized, then it has a customer-managed KMS key with rotation on and an alias, and the key is retained if the stack is deleted.
   - verify: CDK assertion test for rotation, alias and retain policy passes.
2. Given the key policy, when it is checked, then Secrets Manager and CloudWatch Logs in the POC account may use the key, and no principal outside the POC account is allowed.
   - verify: assertion test on the key policy statements passes.
3. Given a stack that creates a secret or a log group through the shared baseline helpers, when it is synthesized, then the secret and the log group use this key.
   - verify: unit test with a sample secret and log group checks the key reference.

## Dependencies

None.

## Evidence

PR and test output in `project-mep-AWS-Infrastructure`.

## Status log

- 2026-11-19: created
- 2026-11-24: done (approved in Studio)
