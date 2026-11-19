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

## What it does

| Feature | How |
|---|---|
| Features, stories and next story | Read from `user-stories/features/*`. "Next" uses the same rule as `run_story.py list`: `ready`, executor `agent` or `mixed`, all `depends_on_stories` done, earliest due first. |
| Confidence score | **Readiness** (40%): deterministic facts from front-matter, the dependency register and `config/parameters.md`. **Analysis** (60%): Kiro's read-only `reviewer` reads the story, ADRs, knowledge, `harness/context` and steering (`prompts/analyze_story.md`). Open type C/D/E dependencies cap the score at 60%, unfinished story dependencies at 40%. 80% or more starts without a reason; below that, you must record an override reason. |
| Live console | Server-sent events from harness-db: phases, steps, agent text, thinking (off by default), tool calls, permission denials and validator output. |
| Tokens | Per step, per run, per story and in total. **Kiro does not report token usage over ACP** (it bills credits account-side), so figures are estimated at about 4 characters per token from prompts, replies and tool payloads. They undercount the context Kiro re-sends on each tool turn. If Kiro ever reports usage, the real figures are used and the "estimated" label disappears. |
| harness-db | SQLite at `harness/studio/data/harness.db` (git-ignored): runs, steps, loop context and every console event. Kiro's raw audit logs go to `harness/studio/data/audit/`. |
| Resume | Every step is checkpointed. A stopped, failed or interrupted run (including a server restart) resumes at the first unfinished step, on its branch, with its saved context. A failed check such as `green` can be fixed by hand and then resumed. |
| Branch | Suggested as `story/<ID>-<title-slug>`, editable, created in the story's `repo:` from the current branch. |
| Commits | The agent never commits. The run ends at **human review**: diff, reviewer verdict and a suggested message. Commit from the page, or commit in your terminal and press "I committed it myself". Nothing is pushed. |

## How it differs from `run_story.py run`

The shipped drivers, `run_story.py`, `.kiro/` and `scripts/validate.sh` are in the answer
key and are only imported, never edited. Studio's own step wiring (`runner.py`):

1. **Renders prompts with their declared variables** (`issue`, `classification`,
   `plan_file_path`, `base_ref`). `run_plan_build.py` passes a bare `ARGUMENTS`, which every
   template in `.kiro/prompts` rejects, so `run_story.py run` currently fails at `classify`.
2. **Reads the plan path from `<<<SPEC>>>`**, because the plan templates write the plan file
   and return its path. The shipped driver writes the path itself into `plan.md`.
3. **Replaces `commit_tests` with a hash snapshot** of the files `write_tests` changed, and
   `tests_unchanged` compares against it, so implementation cannot edit tests. It drops the
   final agent `commit` in favour of the human review gate.
4. Implements `plan_exists` (story id plus numbered "shall" criteria) instead of a no-op.

`red`, `green` and `validate` run `scripts/validate.sh` exactly as the shipped driver does
(fail twice, pass twice, pass once).

## Files

`server.py` (FastAPI and SSE), `runner.py` (analysis and loop, Kiro event capture),
`catalog.py` (stories, dependencies, parameters, readiness), `db.py` (harness-db),
`prompts/analyze_story.md`, `static/` (the page).
