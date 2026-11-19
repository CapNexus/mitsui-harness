---
name: plan_deployed_state_verification
description: "Plan a live-state check script with failure exit and dated evidence."
mode: "on-demand"
---

# Plan a deployed-state verification

Write the implementation plan for one story whose work is a script that checks the live state of a deployed AWS environment (VPN tunnel status, route exports, firewall configuration, AWS API answers, Lambda reachability or isolation probes, clean-run streaks). The script exits non-zero on failure and saves dated evidence. You write the plan only. Do not write the script, the tests, or any other source file.

## Variables

issue: $1
classification: $2

## Instructions

- `$1` is the story or issue text, including its id (for example `F03-S03`). `$2` is the classification the classifier chose. If `$2` is not `deployed-state-verification`, say so in the plan's Notes and plan the work as the issue describes it.
- Read the issue and identify: the story id, what live state must be true, which AWS API calls or probes observe it, and what counts as pass and fail. If the story names thresholds (for example "four clean loads", a row count, an expected CIDR list, a tunnel count), copy them into the criteria exactly.
- Research before planning. Read `package.json`, `tsconfig.json` and `jest.config.*` if present, and list `bin/`, `lib/`, `test/`, `scripts/` and any `Makefile` to see what exists. Reuse existing conventions for script location, naming and test layout. If a directory or file you need does not exist yet, list it under New Files rather than assuming it.
- Read the steering files that apply: `plans-1` and `plans-2` (plan shape and location), `commands_scripts-1` and `commands_scripts-2` (script and Make target conventions), `standard_output-1` and `standard_output-2` (what a script prints and how it reports), `types-1` and `types-2` (typed results, no untyped `any`), `architecture-1` to `architecture-3` (where code lives), `tests-1` to `tests-3` (test style and coverage), and `documentation-1`. Cite the rules you rely on by file name in the plan.
- Write the plan to `specs/<story-id>-<short-slug>.md`. If `plans-1` or `plans-2` name a different location, use that. Create the directory if needed.
- Replace every angle-bracket placeholder in the Plan Format with real content. The plan must cite the story id in its title or first section so the `plan_exists` check can find it.
- Design rules the plan must follow:
  - Read-only. The script makes only read or describe calls (for example `Describe*`, `Get*`, `List*`, or a read-only probe Lambda invocation). It never creates, modifies or deletes resources, and the plan never includes a deploy.
  - Three outcomes with distinct exit codes: all checks pass (0), at least one check fails (1), the check could not run such as missing credentials, wrong Region or API error (2). A failed check must never be reported as pass because of an error.
  - Each check returns a typed result: name, expected, observed, pass or fail, and the timestamp of observation.
  - AWS access goes through an injected client or runner so unit tests run with fakes and never call AWS. Region, account and resource identifiers come from arguments, environment variables or CDK stack outputs. Never hardcode account ids or secrets.
  - Dated evidence: write one file per run to an evidence folder named for the story, with the UTC date and time in the file name (for example `evidence/<story-id>/<YYYY-MM-DDTHHMMSSZ>-<check>.json`). The file records inputs (non-secret), every check's expected and observed values, the overall result and the exit code. Evidence is written on failure as well as on success. Evidence must not contain credentials, tokens, secret values or full connection strings.
  - Where the story requires a streak (for example consecutive clean loads), the script reads prior evidence files to count the streak and resets it on a failed run. Plan how the streak is computed and tested.
  - Where the story requires an isolation or negative check (for example a probe that must be unreachable), a successful connection is the failure case. Plan a test for both directions.
  - Where the story is subject to Region-deny or the schedule constraints in the profile, make the script refuse to run against a Region it was not configured for.
- Plan tests that the `write_tests` step can write before the script exists. Each acceptance criterion must map to a Jest test that uses fakes, or, if it can only be shown against the live environment, to a clearly labelled "Live run" step. Live runs are performed by a person with credentials after deployment. They are not part of the Validation Commands.
- Plan for the repo gates: Prettier formatting, ESLint with zero warnings, `tsc --noEmit`, Jest with the global 80% coverage threshold, and `npm run synth`. If the repo has a Makefile or an established `npm run` convention for verification scripts, plan the target or script entry that runs the check, following `commands_scripts-1`.
- Write every acceptance criterion in EARS notation (When/While/If-then/Where ... shall). Each criterion is singular, testable and numbered. Cover: the pass case, each failing condition, the could-not-run case and its exit code, evidence file creation and naming, evidence content on failure, no secrets in evidence, and read-only behavior.
- Use only validation commands from the profile: `npm run format:check`, `npm run lint`, `npm run build`, `npm test`, `npm run synth`. Add a command to run the new test file alone only if it uses the existing Jest setup.
- If the issue is ambiguous in a way that changes the checks (unknown threshold, unknown resource, unclear pass condition), do not guess silently. Record the question in Notes under "Open questions" and plan the most conservative reading.

## Plan Format

```md
# Deployed-State Verification: <story id> <short title>

## Description
<what live state is verified, why it matters, and which stack, account or environment it applies to>

## User Story
As a <role>
I want <to verify that deployed state matches what was agreed>
So that <benefit, and what evidence the customer or reviewer receives>

## Checks
| Check | Expected | How observed (API call or probe) | Failure meaning |
|---|---|---|---|
| <name> | <value> | <read-only call> | <what a failure indicates> |

## Relevant Files
<existing files that matter, each with a reason>

### New Files
<script path, test path, evidence folder, any Make target or npm script entry>

## Design
- Exit codes: 0 pass, 1 check failed, 2 could not run.
- Inputs: <arguments, environment variables, stack outputs>
- Evidence: <folder, file name pattern with UTC date, fields recorded, fields excluded>
- Streak logic: <if the story needs one, otherwise "not applicable">

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

<h3 headers with bullets. Start with types and the injectable client, then each check, then evidence writing, then the exit-code wrapper and command entry, then tests alongside each part. Last step: run the Validation Commands.>

## Testing Strategy
### Unit Tests
<pass, fail and could-not-run for each check, using fakes>

### Evidence Tests
<file name uses the UTC date, written on pass and on fail, no secret fields>

### Edge Cases
<empty responses, partial results, wrong Region, expired credentials, malformed prior evidence, clock at date boundary>

## Live Run (performed by a person after deployment, not part of validation)
<exact command, required credentials and Region, where evidence lands, who reviews it>

## Acceptance Criteria
<numbered EARS statements, each using "shall", each mapped to a test or the Live Run step>

## Validation Commands
Execute every command to validate the plan's work with zero regressions.

<list from: npm run format:check, npm run lint, npm run build, npm test, npm run synth>

## Notes
<new dependencies, open questions, steering rules relied on by file name, constraints from the story>
```

## Output contract (STRICT)

After writing the plan file, your entire reply MUST be exactly one block delimited by the markers below, and nothing else. No preamble, no narration, no closing remarks, no code fences around it. The `<<<SPEC>>>` line MUST be the first line of your reply and `<<<END SPEC>>>` MUST be the last.

Inside the block, put the plan file path on the first line as `plan_file: <path>`, followed by a short bullet list of what the plan covers (the story id, the checks planned, the evidence location, and any open questions).

```
<<<SPEC>>>
plan_file: specs/<story-id>-<short-slug>.md
- <story id and what is verified>
- <checks planned>
- <evidence location and naming>
- <open questions, or "none">
<<<END SPEC>>>
```
