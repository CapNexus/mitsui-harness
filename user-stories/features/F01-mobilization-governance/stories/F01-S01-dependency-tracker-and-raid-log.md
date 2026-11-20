---
id: F01-S01
feature: F1
title: Set up the dependency tracker and RAID log
tier: build
executor: agent
owner: Mike
repo: planning
status: done
sow: D1
due: 2026-11-18
blocked_by: []
depends_on_stories: []
params: []
human_gates: []
---

## Story

As Mike (CapNexus project manager), I want one tracker that holds every client dependency and every risk, assumption, issue and decision, so that nobody has to ask who owns an item or when it is due.

## Context

The dependency tracker is `user-stories/dependencies/README.md`. The RAID log (risks, assumptions, issues, decisions) is a new file, `user-stories/raid-log.md`. All 29 dependencies from Feature List Section 3 are already in the register with a type, owner and needed-by date. This story adds the RAID log, adds the checking script, and seeds both.

Out of scope: getting Mitsui to confirm names (F01-S02).

## Acceptance criteria

1. Given the dependency register, when the checker runs, then all 29 DEP IDs (DEP-01 to DEP-29) exist and each has a non-empty owner, needed-by date, type and status.
   - verify: `scripts/check-dependency-register.sh` exits 0. Script is created by this story.
2. Given the RAID log, when it is opened, then it has sections for Risks, Assumptions, Issues and Decisions, and is seeded with Feature List Section 5 (gaps 1 to 9) as issues and Section 7 (questions 1 to 7) as open decisions, each with an owner and date.
   - verify: `scripts/check-raid-log.sh` exits 0. Script is created by this story.
3. Given a dependency row with status `slipped`, when the checker runs, then it fails unless the row has a slip date and a cause.
   - verify: the same script has a test with one valid and one invalid slipped row.

## Dependencies

None. Owner names that are `to be named` stay as such until F01-S02 resolves them.

## Evidence

Commit that adds the files and the passing script output.

## Status log

- 2026-11-17: created
- 2026-11-19: done
