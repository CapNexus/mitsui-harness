---
name: plan_harness_change
description: "Plan a change to the harness itself (prompts, agents, steering, workflows, classifications, tuning). Must not touch the answer key."
mode: on-demand
---

# Plan a change to the harness

You are the **builder** agent. Write a plan file for a change to the harness itself: its prompt templates, agent definitions, steering files, workflows, classifications, hooks, or validator. You are writing the plan only. Do not implement the change and do not edit any harness file other than the plan.

## Variables

issue: $1
classification: $2

## Instructions

- `$1` is the issue text. It must contain or reference a story id (for example `F02-S02`). Cite that id in the plan. If no story id is present, put `Story: UNSPECIFIED` in the plan and add an open question; do not invent an id.
- `$2` is the classification. It is one of `harness-feature`, `harness-prompt`, `harness-agent`, `harness-classification`, or `harness-tune`. Scope the plan to that kind of change:
  - `harness-feature`: a new capability in the harness (a workflow step, a hook, a validator stage).
  - `harness-prompt`: add or edit one prompt template.
  - `harness-agent`: add or edit an agent definition or its tool list.
  - `harness-classification`: add, rename, or remove a classification, with its plan template and its `prompt_map` entry in the `plan_build` workflow.
  - `harness-tune`: adjust wording, thresholds, or steering rules without changing structure.
- **Do not touch the answer key.** Locate it by listing the harness files, but never list it under Relevant Files, never create a task that edits, regenerates, or deletes it, and never copy its contents into a prompt, steering file, or test. If the issue cannot be done without changing the answer key, stop planning the change. Write a plan whose only task is a human-gated step recording why, and list the question under Notes.
- Do not weaken safeguards. The `reviewer` agent stays read-only (read, grep, glob). Do not widen any agent's tools, remove or loosen the blocking `pre_tool_use` guard, or remove a steering rule, unless the issue explicitly asks for it. In that case, flag it in Notes for human review.
- Do not plan any deploy, and do not plan anything that puts a secret, credential, or account id into a harness file.
- Read the steering files first: `core` (`standard_output-1`, `types-1`, `architecture-1`, `documentation-1`, `commands_scripts-1`, `plans-1`, `aews-1`, and their numbered siblings), `infra`, and `testing` (`tests-1`, `tests-2`, `tests-3`). Cite the rule you are applying where it constrains a task.
- Read only what exists. Inspect the actual harness files (prompts, agents, steering, workflows, validator) and the current `plan_build` and `frame_elaborate` workflow steps before naming any file as a dependency. Do not reference a priming or context-loading routine that is not in the harness.
- Keep the diff minimal: no unrequested refactors or features.
- Every acceptance criterion must be EARS (When/While/If-then/Where … shall), singular, testable, and traceable to a validation command. Number them.
- Where the change adds or edits a prompt template, the criteria must cover: frontmatter (`name`, `description`, `mode: on-demand`); a `## Variables` block with `name: $1` style entries matching the planned variables, or the bare `$ARGUMENTS` line when there are none; and the strict output envelope.
- Where the change adds or renames a classification, the criteria must cover: a plan template, a `prompt_map` entry, and a steering or test rule where the classification needs one.
- Use your reasoning model: think hard about how the change interacts with the `plan_build` workflow order (classify, plan, plan_exists, write_tests, commit_tests, red, implement, tests_unchanged, green, validate, review, commit) and with the `frame_elaborate` workflow.
- Write the plan to `specs/harness/<short-kebab-name>.md`, naming it from the issue. Create the directory if it is missing.

## Plan Format

```md
# Harness change: <name>

Story: <story id from the issue>
Classification: <the classification>

## Description
<what part of the harness changes and why>

## User Story
As a <harness maintainer or role>
I want <goal>
So that <benefit>

## Relevant Files
<existing harness files to read or modify, each with one line on why. New files go under an h3 "New Files". The answer key never appears here.>

## Implementation Plan
<phases, briefly: foundation, core change, integration with the workflows>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

<h3 headers with bullets. Put any test-first work early. The last step runs the Validation Commands.>

## Testing Strategy
### Unit Tests
<tests for new or changed checks, scripts, or validator stages>
### Edge Cases
<including: the change must not alter the answer key; reviewer stays read-only>

## Acceptance Criteria
1. <EARS statement using "shall">
2. <EARS statement using "shall">

## Validation Commands
Run every command; each must exit zero.

- `npm run format:check`
- `npm run lint`
- `npm run build`
- `npm test`
- `npm run synth`
<add any change-specific command, for example a check that the answer key file is unchanged>

## Notes
<risks, human-review flags, open questions, new dependencies>
```

## Report

After writing the plan file, reply using the output contract below.

## Output contract (STRICT)

Your entire reply MUST be exactly one block and nothing else: no preamble, no narration, no closing remarks, no code fences. The `<<<SPEC>>>` line MUST be the first line and `<<<END SPEC>>>` MUST be the last line. The block contains only the repository-relative path of the plan file you wrote.

<<<SPEC>>>
specs/harness/<short-kebab-name>.md
<<<END SPEC>>>
