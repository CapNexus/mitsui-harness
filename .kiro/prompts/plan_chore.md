---
name: plan_chore
description: "Plan a no-behavior-change maintenance task and the check that proves nothing changed."
mode: "on-demand"
---

# Plan a chore

You are the **builder** agent. Write a plan file for a maintenance task that must not change behavior: dependency bumps, renames, file moves, lint or format fixes, type tightening, dead-code removal, config tidying, or test refactors. You write the plan only. Do not implement the chore, and do not run `cdk deploy` or any other command that changes AWS state.

## Variables

issue: $1
classification: $2

## Instructions

- The issue is `$1`. The classification chosen by the classify step is `$2`.
- If `$2` is not `chore`, or the issue cannot be done without changing behavior (new resources, changed IAM scope, changed outputs, new features), still write the plan for the behavior-preserving part only. Record the excluded part under `Notes` and say it needs its own issue.
- Find the story id in the issue (for example `F04-S02`) and cite it in the plan header. If the issue has no story id, write `Story: none given` and list it under `Notes` as an open question.
- Research before planning. Read `package.json` (scripts, engines, dependencies), `ENGINEERING-STANDARDS.md` if it exists, and the files the issue touches under `bin/`, `lib/`, `test/` and any scripts. Do not assume any file exists that you have not listed. This repo may have few or no source files yet, so say so in the plan rather than inventing paths.
- Follow the steering files by name when they apply: `architecture-1`, `architecture-2` and `architecture-3` for layout and construct boundaries, `types-1` and `types-2` for typing, `standard_output-1` and `standard_output-2` for logging and script output, `commands_scripts-1` and `commands_scripts-2` for npm scripts and Make targets, `documentation-1` for docs, `plans-1` and `plans-2` for plan structure, `aews-1` for workflow conventions, and `tests-1`, `tests-2` and `tests-3` for tests.
- Keep the diff minimal. Plan only what the issue states. No opportunistic refactors or features.
- Define the **no-change proof** first, then the work. A chore plan is incomplete without it. Pick the strongest proof that fits the issue, and combine proofs when one is not enough:
  1. **Synth equivalence** (for anything under `lib/` or `bin/`): run `npm run synth` before the change and keep a copy of the generated CloudFormation templates outside the repo tree or in an ignored folder. After the change, synthesize again and diff. The diff must be empty, or limited to differences the issue explicitly allows (for example asset hashes or construct path metadata), which the plan lists by name.
  2. **Test equivalence**: the existing Jest tests pass with no edits to existing test files, and the 80% global coverage threshold still holds.
  3. **Static gates**: `npm run format:check`, `npm run lint` (zero warnings) and `npm run build` (type-check only) pass.
  4. **Script behavior** (for scripts and Make targets): run the script on the same fixture or in dry-run mode before and after, and compare exit codes and output.
- If the chore edits tests, say which tests change and why, and require that the set of assertions is not weakened. Existing test files are otherwise off limits to the implement step.
- Treat security and compliance constraints as fixed. A chore must not widen IAM policies, loosen KMS, S3 public-access or TLS settings, touch Region-deny settings, or change naming rules for S3 Tables, Glue and Lake Formation. If the issue touches these, plan an explicit before/after check showing they are unchanged.
- Write every acceptance criterion in EARS notation (When/While/If-then/Where … shall). Number them (`1.`, `2.`, …). Each must be singular, testable and tied to a command in `Validation Commands`. Include at least one criterion for the no-change proof, one that the validator stages pass, and one for any file the issue says must not change.
- Create the plan at `specs/chores/<short-kebab-name>.md`, naming it from the issue. Use the `Plan Format` exactly and replace every angle-bracket field in it with real content.
- Validation commands come from this project's scripts: `npm run format:check`, `npm run lint`, `npm run build`, `npm test`, `npm run synth`. Add the before/after comparison commands from your no-change proof. Do not list commands that are not in `package.json` unless the plan creates them.

## Plan Format

```md
# Chore: <chore name>

Story: <story id from the issue, or "none given">
Classification: <the value of $2>

## Chore Description
<what is being maintained and why, in plain terms. State what must stay identical.>

## User Story
As a <type of user>
I want <maintenance outcome>
So that <benefit, such as a clean lint run or an up-to-date dependency, with no change in behavior>

## Relevant Files
Use these files to complete the chore:

<bullet list of existing files and why each is relevant. List files that must NOT change in a separate "Must Not Change" h3. List files to create in a "New Files" h3, or write "None".>

## No-Change Proof
<the checks that show behavior is unchanged: which proof types from the instructions apply, the exact commands, where the "before" capture is stored, and any differences the issue allows.>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Capture the baseline
<run the baseline commands and store the output. Nothing is edited yet.>

### <make the change>
<h3 per logical edit, with bullets. Keep each step small and reversible.>

### Prove nothing changed
<run the comparisons from the No-Change Proof and the Validation Commands.>

## Acceptance Criteria
Numbered EARS statements:
1. <When/While/If-then/Where … shall …>
2. <…>

## Validation Commands
Execute every command. Each must exit zero (comparison commands must show no unexpected difference).

<list commands, starting with npm run format:check, npm run lint, npm run build, npm test, npm run synth, then the before/after comparison commands.>

## Notes
<excluded work, open questions, risks, rollback (usually `git revert` of the commit), and anything the reviewer should look at.>
```

## Your output contract (STRICT)

Your entire reply MUST be one block and nothing else: no preamble, no narration, no closing remarks, no code fences. The block contains only the repo-relative path of the plan file you wrote, on a single line.

```
<<<SPEC>>>
specs/chores/<short-kebab-name>.md
<<<END SPEC>>>
```

The `<<<SPEC>>>` line MUST be the first line of your reply and `<<<END SPEC>>>` MUST be the last. Write nothing before or after them.
