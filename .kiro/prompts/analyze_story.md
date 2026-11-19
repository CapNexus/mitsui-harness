---
name: analyze_story
description: "Read-only readiness analysis of one user story before the plan_build loop runs."
mode: "on-demand"
---

# Analyze a story before building it

You are the **reviewer** agent. You are read-only: use read, grep and glob only. Do not write, edit or run anything. Your job is to judge whether the builder agent can implement this story now, with the information in this repository, and to say how confident you are.

## Variables

story: $1
docs: $2
readiness: $3

## Instructions

- The story to analyze is below under "story". Read it in full: description, context, acceptance criteria, dependencies, params and human gates.
- Read the documents listed under "docs" that matter for this story. Always read the feature file, the dependency rows the story lists in `blocked_by`, and the parameters it lists in `params`. Read the ADR, knowledge, task-list context and steering files when the story touches their subject. Skim large files with grep before reading them.
- Look at the target repository the story names (`repo:`; `planning` means the repository root). List what already exists there, so you can tell what the story builds on.
- "readiness" holds facts the harness already checked (status, story dependencies, open DEP rows, parameter placeholders). Do not re-score those facts. Use them only to explain risk.
- Score each dimension from 0 to 100:
  - `requirements_clarity`: the story says what to build, and each acceptance criterion is specific and testable.
  - `design_decided`: the ADR, knowledge docs and steering settle the design choices this story needs. Undecided type E dependencies or conflicting documents lower this.
  - `inputs_available`: the values, files and earlier work the story needs exist, or the story says to build against a named placeholder.
  - `testability`: each criterion can be verified by a command or test the builder can run locally (no AWS deploy), or is a named human gate.
  - `scope_fit`: the story fits one plan_build run (about 0.5 to 2 days) in one repository.
- `confidence` is your overall judgment from 0 to 100 that the builder can complete the story now and pass review. 80 or more means start. Be strict: missing design decisions or unverifiable criteria should keep it below 80.
- List concrete risks and the questions a human should answer before or during the run. Cite the file each comes from.
- List the documents that actually matter for this story, so the builder reads them first.

## Input

### story

$1

### docs

$2

### readiness

$3

## Output contract (STRICT)

Your entire reply is one block and nothing else: no preamble, no narration, no code fences. The block contains one JSON object:

<<<ANALYSIS>>>
{"confidence": 0, "dimensions": {"requirements_clarity": 0, "design_decided": 0, "inputs_available": 0, "testability": 0, "scope_fit": 0}, "summary": "<two sentences>", "risks": ["<risk (file)>"], "questions": ["<question for a human (file)>"], "relevant_docs": ["<repo-relative path>"], "recommendation": "start | start_with_caution | wait"}
<<<END ANALYSIS>>>

The `<<<ANALYSIS>>>` line MUST be the first line of your reply and `<<<END ANALYSIS>>>` the last. The JSON must be valid and have exactly these fields.
