---
name: plan_config_generator
description: "Plan a generator script with fixture inputs and expected outputs."
category: "planning"
mode: "on-demand"
---

# Plan a config generator

Write an implementation plan for a script that turns a config, inventory, permission matrix or spreadsheet into pipeline or permission artifacts. You are the **builder** agent. You write the plan file only. You do not implement the generator, and you do not write its tests or fixtures.

## Variables

issue: $1
classification: $2

## Instructions

- `$1` is the issue text: the story or feature to plan. It cites a story id such as `F04-S03`. `$2` is the classification already assigned to it, expected to be `config-generator`. If it is a different value, plan the work as the issue describes it and say so in `Notes`.
- Write the plan to `specs/config-generator/<story-id>-<short-slug>.md`, creating the directory if needed. Use the story id from the issue. Do not invent one. If the issue cites no story id, stop and put the question under `Notes` instead of guessing.
- Research before planning. Read `README.md` and `ENGINEERING-STANDARDS.md` if they exist. Read `package.json`, and use `glob` and `grep` to find existing files under `lib/`, `bin/`, `test/` and any scripts directory. Follow existing layout and naming. The codebase may still be nearly empty. In that case, plan the files from the layout in `package.json` (entry `bin/app.ts`, source under `lib/`, tests under `test/`) and mark them as new files.
- Identify the generator's contract and write it into the plan:
  - **Input**: file format and location (YAML, JSON, CSV or spreadsheet export), required fields, and how malformed or missing fields are rejected.
  - **Output**: the artifact produced (for example pipeline definitions, IAM or Lake Formation permission grants, Entra group mappings, or a table name map), its format and its destination path.
  - **Mode switch**: if the issue calls for one (for example dry-run versus apply, or sandbox versus production), name each mode and its default. The default shall be the non-mutating mode.
  - **Determinism**: the same input shall produce byte-identical output. Plan sorted keys and stable ordering, and no timestamps in generated content.
- Plan fixture-driven unit tests. The plan shall list the fixture files under `test/fixtures/`, each with a named input and its expected output. Cover at least:
  - a valid minimal input;
  - a valid realistic input with several rows, roles or tables;
  - each mode of the mode switch, where one exists;
  - an invalid input for each rejection rule (missing field, duplicate key, unknown value);
  - an empty input.
- Respect the project's constraints where the issue touches them:
  - Lowercase schema, table and column names for S3 Tables, Glue and Lake Formation, with a 100% source-to-target name map. Plan a check that no name is dropped or collides after lowercasing.
  - The generator shall never write or print secret values. Plan for references to Secrets Manager entries only.
  - The generator shall grant read-only access. No generated permission may allow a write path to the sources.
  - The generator shall not deploy or call AWS. It only reads input and writes files. Any step that needs a person (approval, console change) goes in `Notes` as a handoff, not as a task for the agent.
- Plan tests so they meet the 80% global Jest coverage threshold, and plan code that passes `npm run lint` with zero warnings and `npm run format:check`.
- Follow `standard_output-1`, `standard_output-2`, `types-1`, `types-2`, `architecture-1`, `architecture-2`, `documentation-1`, `commands_scripts-1`, `plans-1`, `aews-1`, `tests-1`, `tests-2` and `tests-3` where they apply. Use typed inputs and outputs, with no untyped `any` on the config boundary. Add a Make target or npm script for the generator if the issue asks for one, and list it in the plan.
- Do not add libraries unless the issue requires one. If you do, name it and the reason in `Notes`.
- Replace every angle-bracket field in the Plan Format with real content. Do not leave unfilled fields, TODO markers or secrets in the plan.
- IMPORTANT: Write every acceptance criterion in EARS notation (When/While/If-then/Where ... shall). Number them. Each shall be singular, testable and traceable to a validation command or a named fixture.

## Plan Format

```md
# Config Generator: <title>

## Story
<story id and one-line title from the issue>

## Description
<what the generator produces, from what input, and why>

## User Story
As a <role>
I want <goal>
So that <benefit>

## Generator Contract
- Input: <format, location, required fields, rejection rules>
- Output: <artifact, format, destination>
- Modes: <each mode and its default, or "single mode">
- Determinism: <how stable output is ensured>

## Relevant Files
<existing files to read or change, each with a reason>

### New Files
<generator source, entry point or script, fixtures, tests>

## Fixtures
| Fixture | Input path | Expected output path | Purpose |
|---|---|---|---|
| <name> | <path> | <path or "error: <message>"> | <case covered> |

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### <task title>
- <step>

<Order: types and schema for the input, fixtures with expected outputs, generator logic, mode switch, script or Make target wiring, documentation of usage. The last task runs the Validation Commands.>

## Testing Strategy
### Unit Tests
<tests per fixture; assertions on exact expected output>

### Edge Cases
<empty input, duplicate keys, name collisions after lowercasing, unknown values, re-running over existing output>

## Acceptance Criteria
1. <EARS statement>
2. <EARS statement>

<Cover the happy path, each mode, determinism, and each rejection rule. Each criterion maps to a fixture or a validation command.>

## Validation Commands
- `npm run format:check`
- `npm run lint`
- `npm run build`
- `npm test`
- `npm run synth`
- <the command that runs the generator against a fixture, if applicable>

## Notes
<assumptions, human handoffs, new dependencies, open questions>
```

## Report

- State the path of the plan file you wrote.
- List any assumptions or open questions in one short bullet list.

## Output contract (STRICT)

Your entire reply MUST be one `<<<SPEC>>> ... <<<END SPEC>>>` block and nothing else. No preamble, no narration, no closing remarks, no code fences around it. The `<<<SPEC>>>` line is the first line of your reply and the `<<<END SPEC>>>` line is the last. Inside the block, put the path of the plan file you wrote on the first line, followed by the assumptions and open questions from the Report section.

<<<SPEC>>>
specs/config-generator/<story-id>-<short-slug>.md
- <assumption or open question>
<<<END SPEC>>>
