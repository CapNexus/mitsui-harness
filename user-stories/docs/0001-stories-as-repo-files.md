# 0001. Track features and user stories as files in the repo

Status: accepted (Nov 17, 2026)

## Decision

Features, user stories and dependencies are markdown files in this repository. We do not use Jira or git issues as the source of truth. Status is kept in each file's front-matter and changed in the same pull request as the work.

## Why

| Concern | Repo files | Git issues |
|---|---|---|
| Agent access | The harness reads and edits files directly, offline, and updates status in the same commit as the code. | Needs API or CLI access and tokens, and depends on the git host. |
| Versioning | Story history sits next to the code and the pull request (PR) that changed it. | Weak edit history. Stories can change silently. |
| Validation | A CI check can enforce required fields, valid DEP IDs and a verify command on every acceptance criterion. | Hard to enforce. |
| Context loading | The harness loads one story plus `config/parameters.md`. | Needs API calls to assemble. |
| Handover | Moves with the repo. | Stays on the host and may not transfer. |
| Discussion and visibility | Weak. Comments go in PRs. | Strong: assignees, comments, boards. |
| Single source of truth | One copy. | Drift risk if both are kept. |

## Rules

1. The story file is the source of truth. Status lives only in its front-matter.
2. One branch and one PR per story. The PR sets `status: done` only after the verify commands pass.
3. Do not duplicate build stories into issues.
4. If Mitsui needs to track or discuss an item, open an issue for the human-gate stories (dependency types C and D) only, and link it to the story file. The issue holds discussion, the file holds status.
5. If the git host supports project boards, generate the board view from the front-matter later.

## When to revisit

If Mitsui staff (not CapNexus engineers) need to update status themselves, or if the repo moves to a host without PR checks.
