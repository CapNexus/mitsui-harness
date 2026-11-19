# Harness Studio

A local web app for working one user story at a time with the Kiro harness: pick the
suggested story, score readiness, run the `plan_build` loop with a live console, and review
and commit the result yourself.

## Start

From the repository root:

| Windows (PowerShell or cmd) | macOS / Linux (Terminal) |
|---|---|
| `.\studio` (or double-click `studio.cmd`) | `./studio.sh` |
| `.\studio 8780` for another port | `./studio.sh 8780` for another port |

The launcher sets `AEW_AUTO_APPROVE=1`, starts the server and opens http://127.0.0.1:8765 in
your browser. Stop it with Ctrl+C. The server binds to localhost only. Set
`STUDIO_NO_BROWSER=1` to skip opening the browser. Both launchers run:

```
AEW_AUTO_APPROVE=1  uv run --with-requirements harness/studio/requirements.txt python harness/studio/server.py
```

## One-time setup

| | Windows | macOS |
|---|---|---|
| Git | Git for Windows (provides Git Bash) | Xcode Command Line Tools or `brew install git` |
| uv | `winget install astral-sh.uv` | `brew install uv` |
| Node.js LTS with npm | `winget install OpenJS.NodeJS.LTS` | `brew install node` |
| Kiro CLI | install, then sign in | install, then sign in |
| Submodules | `git submodule update --init` | `git submodule update --init` |

Open a new terminal after installing so the tools are on PATH; the top bar of the page shows
a green badge for `kiro-cli`, `AEW_AUTO_APPROVE` and `npm` when each is found.

The validator (`scripts/validate.sh`) runs in bash on both platforms: Git Bash on Windows
(never WSL's bash), `/bin/bash` on macOS. It is written for bash 3.2, which macOS ships, and
for both GNU and BSD tools. Set `HARNESS_BASH` to use a different bash. Line endings are
pinned by `.gitattributes` (`*.sh`, `*.py` LF; `*.cmd` CRLF), so a Windows checkout with
`core.autocrlf=true` does not break the scripts.

## The harness is the brain

Studio is a UI over the harness. It does not decide what a step does:

| Concern | Harness code (also used by the CLI) |
|---|---|
| Which story is next | `harness/run_story.py` `runnable()` (same as `run_story.py list`) |
| Readiness, analysis, confidence | `harness/story_analysis.py` with `.kiro/prompts/analyze_story.md` (same as `run_story.py analyze`) |
| Preflight, branch, environment, repository preamble, review diff | `harness/run_story.py` `preflight()`, `prepare()`, `resume()`, `make_context()` |
| Every implementation step, including the agent's commits | `harness/drivers/run_plan_build.py` `run_step()` over `harness/workflows/plan_build.json` |

Studio adds only what a UI needs: it runs the workflow one step at a time to checkpoint the
loop context and `PlanBuildContext.state()` in harness-db, streams Kiro's events and the
validator output, can stop a run, can re-run from a chosen step, and ends with a human
approve/reject gate before anything is pushed. A run started in Studio and
`run_story.py run` produce the same steps, checks and commits.

## What it does

| Feature | How |
|---|---|
| Features, stories and next story | From `user-stories/features/*` through `run_story.py`. |
| Confidence score | **Readiness** (40%) and the Kiro **analysis** (60%), capped at 40% by an unfinished story dependency and at 60% by an open type C/D/E dependency (`story_analysis.py`). 80% or more starts without a reason; below that, you must record an override reason. |
| Live console | Server-sent events from harness-db: phases, steps, agent text, thinking (off by default), tool calls, permission denials and validator output. |
| Tokens | Per step, per run, per story and in total. **Kiro does not report token usage over ACP** (it bills credits account-side), so figures are estimated at about 4 characters per token from prompts, replies and tool payloads. They undercount the context Kiro re-sends on each tool turn. If Kiro ever reports usage, the real figures are used and the "estimated" label disappears. |
| harness-db | SQLite at `harness/studio/data/harness.db` (git-ignored): runs, steps, loop and harness state, and every console event. Kiro's raw audit logs go to `harness/studio/data/audit/`. |
| Resume and re-run | Every step is checkpointed. A stopped, failed or interrupted run (including a server restart) resumes at the first unfinished step, on its branch. **Re-run from step** runs a chosen step and all later ones again. `commit` is skipped when nothing is left to commit. |
| Branch | Suggested as `story/<ID>-<title-slug>` (the CLI default is `story/<ID>`), editable, created in the story's `repo:` from its current branch. |
| Commits | As the harness intends: the builder commits the tests (`commit_tests`), then the change once the reviewer agent says APPROVE (`commit`), on the story branch. The run then waits at **human review**: commits, verdict, findings and diff. Approve (ready to push) or reject. Nothing is pushed. |

## Files

`server.py` (FastAPI and SSE), `runner.py` (step-by-step orchestration over the harness,
Kiro event capture), `catalog.py` (read-only story views for the page), `db.py`
(harness-db), `static/` (the page). Kiro agents may not edit this folder: it is in the
answer key (`harness/answer-key.txt`).
