---
id: F07-S07
feature: F7
title: Prove Lake Formation refuses writes sent directly to Athena
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Code
status: ready
sow: D4
due: 2026-12-02
blocked_by: []
depends_on_stories: [F07-S01]
params: [entra_groups, identity_mode]   # identity_mode is proposed
human_gates: []
---

## Story

As Venkat (DevOps), I want an automated test that sends write statements straight to Athena and shows Lake Formation refuses them, so that the second layer of write protection is proven even if AgentCore Policy (F8) were bypassed.

## Context

Write attempts must be refused twice: by AgentCore Policy (F8) and by Lake Formation. This story covers the Lake Formation layer only. It runs in the sandbox now and is reused in the POC account by F07-S06 and in Week 5 and Week 6 testing (F13).

## Acceptance criteria

1. Given a user in every permitted group, when INSERT, UPDATE, DELETE, MERGE, CREATE TABLE AS, DROP TABLE and ALTER TABLE are sent to Athena through the identity-aware workgroup, then each is refused with an access error.
   - verify: `scripts/test-lf-write-refusal.sh --env sandbox` exits 0 and lists each statement as refused. Script created by this story.
2. Given the refusals, when the table row counts are checked after the test, then they are unchanged.
   - verify: the same script compares counts before and after.
3. Given `identity_mode: group_fallback`, when the test runs with a group role, then the same refusals hold.
   - verify: `scripts/test-lf-write-refusal.sh --env sandbox --mode group_fallback` exits 0.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-27 | E | Identity mode | Both modes tested |

## Evidence

Script output, later re-run in the POC account.

## Status log

- 2026-11-19: created
