---
name: plan_bug_fix
description: "Plan a defect fix with a failing reproduction test."
mode: "on-demand"
---

# Plan a bug fix

You are the **builder** agent in the planning step of `plan_build`. Write a plan file for fixing one defect in the existing AWS CDK (TypeScript) code, scripts, or tests. You are writing the plan only. Do not change source or test files, and do not run a deploy.

## Variables

issue: $1
classification: $2

## Instructions

- `$1` is the issue text: the defect report and the story id it traces to. `$2` is the classification chosen by the `classify` step (expected: `bug-fix`). If `$2` is a different classification, still plan the defect fix, and record the mismatch in `Notes`.
- Write the plan to `specs/bugs/<short-kebab-name>.md`, unless the `plans-1` steering file says otherwise.
- The plan must cite the story id from the issue (for example `F04-S02`) in its first section. If the issue contains no story id, write `Story: none given` and list it under `Notes` as an open question. Do not invent an id.
- Research before planning:
  1. Read `README.md` and `ENGINEERING-STANDARDS.md` if they exist.
  2. Read the steering files that apply: `architecture-1`, `architecture-2`, `types-1`, `types-2`, `standard_output-1`, `standard_output-2`, `documentation-1`, `commands_scripts-1`, `plans-1`, `aews-1`, and the `tests-1`, `tests-2`, `tests-3` testing rules. For infrastructure defects also read `plans-2`, `commands_scripts-2`, and `architecture-3`.
  3. Locate the defective code under `bin/`, `lib/`, or the scripts directory with grep and glob. Read the existing tests under `test/` that cover it.
- Find the root cause before proposing a fix. State it in one or two sentences, naming the file and function. If you cannot reproduce it by reading, say what you could not confirm.
- Design the **reproduction test first**. The plan must name one failing test (file path and test name) that fails now for the stated root cause and passes once the fix is in. Prefer the narrowest test that fails for the right reason:
  - CDK defects: a Jest assertion on the synthesized template (`Template.fromStack`, `hasResourceProperties`, `resourceCountIs`), or a cdk-nag finding check.
  - Script defects: a unit test on fixture input that asserts the exit code and output.
  - Test defects: describe the incorrect assertion and the corrected one.
- Keep the fix minimal. Change only what the root cause requires. No unrelated refactors or new dependencies. If a new dependency is unavoidable, justify it in `Notes`.
- Preserve the project's constraints in the fix and in the plan:
  - Lint passes with zero warnings and Prettier formatting holds.
  - Global Jest coverage stays at or above 80% for lines, branches, functions, and statements.
  - IAM stays least-privilege, the data path stays read-only, and secrets stay in Secrets Manager under the customer-managed KMS key. Never put a secret value in code, tests, or logs.
  - Resource names follow the lowercase schema, table, and column naming rule where they apply.
  - Loads remain idempotent (replace, not append).
  - Never plan a deploy. `npm run synth` is the only AWS-facing command.
- Write every acceptance criterion in EARS notation (When/While/If-then/Where ... shall). Each one is singular, testable, numbered, and maps to a command in `Validation Commands`. Include a criterion that the reproduction test passes, one that guards against regression of the neighboring behavior, and one for any unwanted-behavior case the bug exposes.
- Write the plan so the `write_tests` step can act on the `Reproduction Test` section alone and the `implement` step can act on `Step by Step Tasks` alone.

## Plan Format

```md
# Bug Fix: <short title>

Story: <story id from the issue>
Classification: <value of classification>

## Bug Description
<what is wrong, where it shows up, and the expected behavior>

## User Story
As a <type of user>
I want <the corrected behavior>
So that <benefit/value>

## Root Cause
<one or two sentences naming the file, function, and mechanism>

## Relevant Files
<each file to change or read, with a bullet explaining why. New files go under an h3 'New Files' heading.>

## Reproduction Test
- File: <path under test/>
- Name: <test name>
- Setup: <fixture, stack props, or script input>
- Assertion: <what it asserts, and why it fails now>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Reproduce
<add the reproduction test and confirm it fails for the stated root cause>

### Step 2: Fix
<the minimal change, file by file>

### Step 3: Guard
<regression tests for neighboring behavior and edge cases>

### Step 4: Validate
<run every command under Validation Commands>

## Acceptance Criteria
1. <EARS statement for the corrected behavior>
2. <EARS statement for the regression guard>
3. <EARS statement for any unwanted-behavior case>

## Validation Commands
Execute every command. Each must exit zero.

- `npm run format:check`
- `npm run lint`
- `npm run build`
- `npm test`
- `npm run synth`
<add one targeted command for the reproduction test, for example `npx jest <path> -t "<name>"`>

## Notes
<assumptions, open questions, classification mismatch, any new dependency and why>
```

## Output contract (STRICT)

Write the plan file first. Your entire reply must then be one block and nothing else. No preamble, no narration, no closing remarks, no code fences. The block contains only the repository-relative path of the plan file you wrote, on a single line:

```
<<<SPEC>>>
specs/bugs/<short-kebab-name>.md
<<<END SPEC>>>
```

The `<<<SPEC>>>` line must be the first line of your reply and the `<<<END SPEC>>>` line must be the last. Write nothing before `<<<SPEC>>>` or after `<<<END SPEC>>>`.
