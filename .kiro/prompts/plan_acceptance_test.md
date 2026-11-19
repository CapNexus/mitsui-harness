---
name: plan_acceptance_test
description: "Plan a scripted acceptance test with positive and negative cases per user, role or environment."
mode: "on-demand"
---

# Plan a scripted acceptance test

You are the **builder** agent. Write a plan for a scripted acceptance test, based on the issue. Do not write the test or the script. A later step writes the failing tests, and another step implements them.

An acceptance test here is a script that exercises a deployed or synthesized system as specific users, roles or environments. For each subject it runs positive cases (access or behavior that must work) and negative cases (access or behavior that must be refused). It exits non-zero on any failure and writes a dated report.

## Variables

issue: $1
classification: $2

## Instructions

- Read the issue (`$1`). It is a requirement item, typically a story or feature, with an id such as `F06-S03`. The plan must cite that story id.
- `$2` is the classification chosen earlier. It should be `acceptance-test`. If it is not, still write the plan and record the mismatch under `Notes`.
- Research before planning:
  - Read `package.json` for the real scripts, the Node version and the Jest coverage threshold.
  - Look under `bin/`, `lib/` and `test/` for existing conventions. Some may not exist yet. If a directory is missing, say so in `Notes` and follow the layout `package.json` implies (`bin/app.ts`, `lib/`, `test/`).
  - Read the steering files that apply: `tests-1`, `tests-2`, `tests-3` for test rules; `commands_scripts-1` and `commands_scripts-2` for script and make-target conventions; `types-1` and `types-2` for typing; `standard_output-1` and `standard_output-2` for output and logging; `plans-1` and `plans-2` for plan structure and location; `architecture-1` to `architecture-3` for layout; `documentation-1` for docs.
  - Read any existing plans and the files the issue names.
- Write the plan to the location and naming that `plans-1` defines. If it states none, use `specs/acceptance-test/<story-id>-<short-slug>.md`.
- Fill in every angle-bracket field in the `Plan Format` with real content. Do not leave any field text behind in the plan.
- Build the test matrix from the issue. Each row names one subject (user, role, group, account or environment), one action, the expected result, and the evidence recorded. Include at least one positive and one negative case per subject. Include write-refusal and fault cases when the issue mentions them. Do not invent subjects the issue does not support. List unknowns under `Open Questions` in `Notes`.
- Separate what runs offline from what needs live AWS:
  - Offline: the matrix parser, the case runner, result classification, report rendering and exit-code logic. These get Jest unit tests on fixture inputs, including a passing matrix and a failing one.
  - Live: calls against deployed resources. Gate them behind an explicit flag or environment variable. They must default to a dry run that makes no AWS calls.
- Safety constraints the plan must respect:
  - The test and its script are read-only against data sources. A negative write-attempt case must assert the refusal, never perform a successful write.
  - Credentials, tokens and secrets come from the environment or Secrets Manager. They are never written to the report, logs or fixtures.
  - The plan never includes `cdk deploy`. `npm run synth` is the only AWS-facing validation command.
  - A person performs any console step. Record such steps in the plan as manual prerequisites.
- The report: define its path, format, required fields (date, environment, subject, case, expected, actual, pass or fail) and that it is written even when cases fail.
- Write every acceptance criterion in EARS (When / While / If-then / Where ... shall). Number them. Make each singular, testable and mapped to at least one validation command or named test. Cover the happy path, each negative case class, the non-zero exit on failure, and the report content.
- Follow the existing conventions. Keep the planned change minimal. Add no dependencies unless unavoidable, and report any in `Notes`.
- Validation commands come from this project's validator and must all appear: `npm run format:check`, `npm run lint`, `npm run build`, `npm test`, `npm run synth`. Add any extra command the plan needs, such as running the script in dry-run mode, only if it works without live AWS access.
- The plan must satisfy the `plan_exists` check: the file exists, cites the story id and contains numbered criteria using "shall".

## Plan Format

```md
# Acceptance Test: <short name>

## Story
<story id, e.g. F06-S03, and its title>

## Description
<what is being accepted, which system or environment it runs against, and why>

## User Story
As a <type of user>
I want <action or goal>
So that <benefit or value>

## Test Matrix
| # | Subject (user / role / environment) | Action | Kind (positive / negative) | Expected result | Evidence recorded |
|---|---|---|---|---|---|
<one row per case, at least one positive and one negative per subject>

## Prerequisites
<manual steps, accounts, roles, environment variables and deployed resources that must exist before a live run; mark which are human-gated>

## Relevant Files
<existing files to read or modify, each with a one-line reason>

### New Files
<files to create: the script, its fixtures, its Jest tests, any make target or npm script, the report location>

## Design
<how the script loads the matrix, runs each case, classifies results, renders the report and sets the exit code; what is offline versus live; how dry-run is selected>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

<h3 headers with bullets. Start with shared types and fixtures, then the runner, then the report writer, then the live adapters, then wiring (npm script or make target) and docs. Include creating tests throughout. The last step runs the Validation Commands.>

## Testing Strategy
### Unit Tests
<runner, classification, report and exit-code tests on fixtures>

### Integration Tests
<dry-run end to end; live run only where a person supplies access>

### Edge Cases
<missing role, expired credential, partial failure, empty matrix, a negative case that unexpectedly succeeds, report path not writable>

## Acceptance Criteria
<numbered EARS statements>
1. When <trigger>, the <system> shall <response>.
2. If <condition>, then the <system> shall <response>.

## Validation Commands
Execute every command to validate the plan was implemented with zero regressions.

- `npm run format:check`
- `npm run lint`
- `npm run build`
- `npm test`
- `npm run synth`
<additional commands, if any>

## Notes
<new dependencies, open questions, classification mismatch if any, deferred work>
```

## Report

Your entire reply is the strict block below. Do not summarize the work outside it.

## Output contract (STRICT)

Your entire reply MUST be exactly one `<<<SPEC>>> ... <<<END SPEC>>>` block and nothing else: no preamble, no narration, no closing remarks, no code fences. The `<<<SPEC>>>` line MUST be the first line of your reply and `<<<END SPEC>>>` MUST be the last. Inside the block, put the repo-relative path of the plan file you wrote on the first line, then one line giving the story id, then one line giving the number of acceptance criteria.

```
<<<SPEC>>>
<repo-relative path to the plan file>
<story id>
<number of acceptance criteria>
<<<END SPEC>>>
```
