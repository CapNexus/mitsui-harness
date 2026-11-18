---
id: F00-S00                 # feature number (2 digits) and story number
feature: F0
title: Short imperative title
tier: build                 # build = sandbox, no Mitsui dependency | integrate = Mitsui environment
executor: agent             # agent | human | mixed
owner: Mike                 # Mike (PM) | Soma (SA) | Venkat (DevOps)
repo: planning              # planning | code/infra | code/data | code/gateway-tools | code/assistant | code/teams-bot
status: draft               # draft | ready | in-progress | blocked | done
sow: D0                     # SOW deliverable
due: YYYY-MM-DD             # from the task list
blocked_by: []              # DEP-nn IDs. Required for integrate stories.
depends_on_stories: []      # story IDs that must be done first
params: []                  # names from config/parameters.md
human_gates: []             # approvals or actions the agent must stop for
---

## Story

As a <role>, I want <capability>, so that <outcome>.

## Context

Why this story exists and what is out of scope. Link the feature file and any ADR.

## Acceptance criteria

Each criterion is pass or fail and names how it is checked. Use `verify:` for a command or test the harness can run, and `gate:` for a human sign-off or action.

1. Given <state>, when <action>, then <result>.
   - verify: `<command or test>`
2. Given <state>, when <action>, then <result>.
   - gate: <who signs or does what>

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|

## Evidence

Where proof is saved (path, export name, log) for the Week 5/6 acceptance matrix.

## Status log

- YYYY-MM-DD: created
