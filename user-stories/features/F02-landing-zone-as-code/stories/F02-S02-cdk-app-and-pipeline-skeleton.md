---
id: F02-S02
feature: F2
title: Create the CDK app and pipeline skeleton
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Infrastructure
status: ready
sow: D2
due: 2026-11-19
blocked_by: []
depends_on_stories: []
params: [aws_home_region, aws_allowed_regions, repo_home_url]
human_gates: [Venkat confirms the CDK language (TypeScript or Python) before the agent starts]
---

## Story

As Venkat (DevOps), I want a CDK app with a pipeline skeleton and a config file that mirrors `config/parameters.md`, so that every later infrastructure story adds a stack in one place and Mitsui values are swapped by config, not code.

## Context

Task list Thu Nov 19. The repository is `project-mep-AWS-Infrastructure` (docs/0002). The pipeline uses CDK Pipelines with an AWS CodeConnections source. In the sandbox the connection ARN is a placeholder. Wiring it to Mitsui's repository is F02-S09.

Out of scope: the KMS, budget and network stacks (their own stories) and deploying to Mitsui's account.

## Acceptance criteria

1. Given a clean checkout, when the build runs, then dependencies install, lint passes and `cdk synth` succeeds with placeholder values.
   - verify: the CI build (install, lint, `cdk synth`) exits 0.
2. Given the config file, when a stack reads a value, then it reads it by the parameter name used in `config/parameters.md`, and a missing value fails synth with a message naming the parameter.
   - verify: config unit tests pass, including one missing-parameter case.
3. Given the pipeline stack, when it is synthesized, then it has a source stage on a CodeConnections connection (ARN from config), a synth step, and a deploy stage for the POC account in us-east-1.
   - verify: CDK assertion test on the pipeline template passes.
4. Given the repository, when a new engineer opens it, then the README explains how to install, synth, test and deploy, and where each parameter comes from.
   - gate: Venkat reviews the README in the PR.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-25 | A+D | Repository and pipeline home | `repo_home_url`. Proposed new parameter `codeconnections_connection_arn`. |

## Evidence

The PR in `project-mep-AWS-Infrastructure` and its passing CI run.

## Status log

- 2026-11-19: created
