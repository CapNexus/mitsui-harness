---
name: plan_checker_script
description: "Plan a checker script or Make target with valid and invalid fixtures."
mode: "on-demand"
---

# Plan a checker script

Write an implementation plan for a checker script or Make target. A checker validates a repo artifact (a Markdown register, deliverable coverage, a crosswalk, a lint rule) or is a guarded dry-run operational script. It exits non-zero on failure and is proven by valid and invalid fixtures. You are writing the plan only. Do not write the checker, its tests, or its fixtures. Later workflow steps do that.

## Variables

issue: $1
classification: $2

## Instructions

- `$1` is the issue text: the story or feature, including its story id (for example `F01-S01`) and its acceptance criteria. `$2` is the classification token chosen for it. Record `$2` in the plan's description.
- Read the issue fully. Extract the story id and every stated requirement. Every requirement must end up in at least one acceptance criterion.
- Research before planning, using read, grep and glob:
  - Read `package.json` for the real scripts, and look for an existing `Makefile` and any existing scripts, `lib/`, `bin/` and `test/` content.
  - Read the steering files that apply, and follow them: `commands_scripts-1` and `commands_scripts-2` (script and Make target conventions), `standard_output-1` and `standard_output-2` (what the checker prints and its exit codes), `types-1` and `types-2` (typed data, no untyped escape hatches), `architecture-1` to `architecture-3` (where code lives), `documentation-1` (docs the checker needs), `plans-1` and `plans-2` (plan location and shape), `tests-1` to `tests-3` (fixtures and test layout).
  - Locate the artifact the checker validates. If it does not exist yet, say so in the plan and state which story creates it or what minimal shape the fixtures assume.
- Design the checker:
  - Name the single behavior it verifies and the exact input it reads (path, file format, flags).
  - Define every failure condition, the message printed for each (file and line or identifier where possible), and the exit codes: zero only when all checks pass, non-zero otherwise.
  - Make it deterministic: no network, no AWS calls, no clock or randomness in its verdict. A checker of deployed state belongs to a different classification.
  - If the issue describes an operational script that changes something, plan it as dry-run by default. It acts only with an explicit flag, prints what it would do, and refuses to run without its guard conditions. It must never deploy.
  - Plan the entry point as a TypeScript script under the location `architecture-1` dictates, plus a Make target (or an `npm run` script when no Makefile exists, following `commands_scripts-1`). Put the verdict logic in a pure function so Jest can test it without spawning a process, and keep a thin CLI wrapper for argument parsing and exit codes.
  - Do not add new dependencies unless the issue cannot be met without them. If one is needed, name it and justify it in `Notes`.
- Plan the fixtures. Every checker needs both kinds:
  - At least one valid fixture that passes.
  - One invalid fixture per failure condition, each failing for exactly one reason, so a test can assert on that reason.
  - Fixtures live under `test/` as `tests-1` to `tests-3` direct, and contain no secrets, real account ids, or real customer data.
- Plan the tests the `write_tests` step will write: one test per acceptance criterion, covering each fixture, the exit codes, and the CLI wrapper. The global Jest coverage threshold is 80% for lines, branches, functions and statements, so the plan must keep the checker above it.
- Write every acceptance criterion in EARS notation (When/While/If-then/Where ... shall). Each must be singular, testable, and mapped to a test or a validation command. Number them. The plan must cite the story id so the `plan_exists` check can find it.
- Respect the constraints that apply: Node >= 20, lint with zero warnings, Prettier formatting, source under `lib/` and `bin/`, tests under `test/`. Do not plan any step that deploys or touches a live AWS account.
- Replace every angle-bracket slot in the Plan Format with real content. Use only files, scripts and steering files that exist in the repo or that the plan explicitly lists as new files.
- Write the plan to a new Markdown file under `specs/`, in the subdirectory and with the naming that `plans-1` and `plans-2` prescribe. If they are silent, use `specs/checker-scripts/<story-id>-<short-slug>.md`. Do not modify any other file.

## Plan Format

```md
# Checker: <short name>

## Description
<what the checker validates or guards, the issue's story id, the classification token, and why it matters>

## User Story
As a <role>
I want <goal>
So that <benefit>

## Relevant Files
<existing files that matter and why, as bullets>

### New Files
<each new file: the checker module, its CLI wrapper, the Make target or npm script, the valid fixtures, the invalid fixtures (one per failure condition), and the test file>

## Checker Design
- Input: <what it reads and how it is invoked>
- Checks: <each check and its failure message>
- Exit codes: <zero on pass, non-zero on any failure, and any distinct codes>
- Guards: <dry-run default and guard flags, or "none: read-only check">

## Fixtures
- Valid: <fixture and what makes it pass>
- Invalid: <one fixture per failure condition and the single reason it fails>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

<h3 headers with bullets. Start with fixtures and types, then the pure verdict function, then the CLI wrapper and Make target, then docs. Include tests throughout. The last step runs the Validation Commands.>

## Testing Strategy
### Unit Tests
<tests for the verdict function, one per check>

### CLI Tests
<exit code and output tests against valid and invalid fixtures>

### Edge Cases
<missing input, empty file, malformed content, unexpected encoding, and similar>

## Acceptance Criteria
1. <EARS statement citing the story id where relevant, using "shall">
2. <...>

## Validation Commands
Execute every command; each must exit zero.

- `npm run format:check`
- `npm run lint`
- `npm run build`
- `npm test`
- `npm run synth`
- <the Make target or npm script for the checker, run against a valid fixture (expect exit 0) and against an invalid fixture (expect non-zero)>

## Notes
<new dependencies and why, dependencies on other stories, open questions>
```

## Report

Write the plan file, then reply with the output contract below.

## Output contract (STRICT)

Your entire reply MUST be exactly one block and nothing else: no preamble, no narration, no closing remarks, no code fences. The `<<<SPEC>>>` line MUST be the first line and the `<<<END SPEC>>>` line MUST be the last line. Between them, put only the repo-relative path of the plan file you wrote, on one line.

<<<SPEC>>>
specs/checker-scripts/<story-id>-<short-slug>.md
<<<END SPEC>>>
