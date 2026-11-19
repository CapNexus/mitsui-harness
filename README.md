# mitsui-harness

Planning repository and agent harness for the **Mitsui E&P USA Well Data Assistant POC**
(SOW Mitsui.CapNexus.SOW2026001). It holds the features, user stories, decisions and
dependencies, and runs a **Kiro** agent harness that builds the stories into two code
repositories. **Harness Studio** is a local web app for analyzing, implementing and
reviewing one story at a time.

- [Repository layout](#repository-layout)
- [One-time setup](#one-time-setup)
- [Start Harness Studio](#start-harness-studio)
- [Work a story: analyze, implement, review](#work-a-story-analyze-implement-review)
- [After you approve: push, PR and record](#after-you-approve-push-pr-and-record)
- [Command line](#command-line-same-harness-no-ui)
- [Rules the harness enforces](#rules-the-harness-enforces)
- [Troubleshooting](#troubleshooting)

## Repository layout

| Path | What it is |
|---|---|
| `user-stories/` | Features F1–F14 and their stories (`features/F*/stories/*.md`, the source of truth), the dependency register, config parameters, and decision records (`docs/0001`, `docs/0002`) |
| `adr/`, `knowledge/`, `task-list/` | Architecture and data-flow decisions, client documents, and the week-by-week plan |
| `project-mep-AWS-Infrastructure/` | Submodule: the **AWS baseline** the project runs on (landing zone, Identity Center, VPC, VPN, PrivateLink, shared KMS key). It publishes its values under SSM `/mep/baseline/*`. |
| `project-mep-AWS-Code/` | Submodule: **the project**, meaning all application code plus every AWS resource that exists only for it (DMS, load jobs, catalog, Lake Formation, tools, assistant, Teams bot). It reads the baseline and never changes it. |
| `.kiro/` | Kiro agents (`builder`, read-only `reviewer`), steering rules, prompt templates and safety hooks |
| `harness/` | Drivers, workflows, reservoir and converted context. `harness/studio/` is the web app. |
| `scripts/validate.sh` | The validator every change must pass (format, lint, typecheck, tests with 80% coverage, `cdk synth`, freezes) |
| `HARNESS.md` | Harness reference: classifications, workflows, answer key, open decisions |

Each story's `repo:` field says which repository it changes: `planning` (this repository),
`project-mep-AWS-Infrastructure` or `project-mep-AWS-Code`. The split is explained in
[`user-stories/docs/0002-repo-structure-and-roles.md`](user-stories/docs/0002-repo-structure-and-roles.md).

## One-time setup

### 1. Install the tools

| Tool | Why | Windows | macOS |
|---|---|---|---|
| Git | Repository and submodules. Git Bash runs the validator on Windows. | [Git for Windows](https://git-scm.com/download/win) or `winget install Git.Git` | `xcode-select --install` or `brew install git` |
| uv | Runs Studio, the drivers and the hooks with the right Python packages | `winget install astral-sh.uv` | `brew install uv` |
| Node.js LTS with npm | CDK projects and the validator (`npm ci`, `cdk synth`) | `winget install OpenJS.NodeJS.LTS` | `brew install node` |
| Kiro CLI | The agent that analyzes and implements stories | Install from [kiro.dev](https://kiro.dev) | Install from [kiro.dev](https://kiro.dev) |

Then **open a new terminal** so the tools are on your PATH, and check them:

```bash
git --version
uv --version
node --version
npm --version
kiro-cli --version
```

On Windows, use Git for Windows' bash for the validator, not WSL's. Studio finds it for you.
On macOS the built-in `/bin/bash` is fine.

### 2. Sign in to Kiro

```bash
kiro-cli login
kiro-cli whoami      # should print your sign-in
```

### 3. Clone with the submodules

```bash
git clone --recurse-submodules https://github.com/CapNexus/mitsui-harness.git
cd mitsui-harness
```

If you already cloned without them, run `git submodule update --init`. The submodules live
on Mitsui's GitHub Enterprise (`MEPUSA.ghe.com`). If the clone asks for credentials, sign in
with `gh auth login --hostname MEPUSA.ghe.com` and `gh auth setup-git --hostname MEPUSA.ghe.com`.

You do not need to install Python packages by hand. The first Studio start downloads them
(FastAPI, uvicorn, the Agent Client Protocol library) into uv's cache.

## Start Harness Studio

From the repository root:

| Windows (PowerShell or cmd) | macOS / Linux |
|---|---|
| `.\studio` (or double-click `studio.cmd`) | `./studio.sh` |

Studio opens at **http://127.0.0.1:8765**. Stop it with **Ctrl+C**. Use `.\studio 8780` or
`./studio.sh 8780` for another port.

The top bar must show three green badges:

- **kiro-cli**: Kiro is installed and on PATH.
- **AEW_AUTO_APPROVE**: the launcher sets this. Without it, Kiro is denied every file write and command, so implementation cannot run (analysis still works).
- **npm**: needed for stories in the two code submodules.

A yellow badge shows uncommitted changes in this repository. Implementation needs a clean
working tree in the repository the story changes, so commit or stash first.

## Work a story: analyze, implement, review

### 1. Pick a story

The left panel lists every feature and story with its state: **runnable**, **waiting**
(on other stories), **blocked** (on a Mitsui dependency), **human** (a person does it) or
**done**. The **Suggested next story** card shows the one to do first: `ready`, executor
`agent` or `mixed`, every `depends_on_stories` done, earliest due date. Use the filters and
search to find another.

The **Story** tab shows the story text and its dependencies. The **Readiness** tab shows the
facts the harness checked: status, unfinished story dependencies, open DEP rows and
parameter placeholders.

### 2. Analyze and get a confidence score

Open **Analysis & confidence** and click **Run analysis** (the same as `run_story.py analyze`,
implemented in `harness/story_analysis.py`). Kiro's read-only `reviewer` reads
the story, its feature, the dependency register, parameters, ADRs, knowledge documents,
task-list context and steering, then scores readiness. Watch it work in the **Live console**.

| Part | Weight | What it measures |
|---|---|---|
| Kiro analysis | 60% | Requirement clarity, decided design, available inputs, testability, scope |
| Readiness | 40% | Facts from front-matter, `dependencies/README.md` and `config/parameters.md` |

Caps: an unfinished story dependency limits the score to 40%, and an open approval, access
or design dependency (DEP type C, D or E) limits it to 60%.

**80% or more is a good start.** The page also lists the risks, the questions a human should
answer, and the documents that matter. If the score is low, answer the questions in the
story or its sources and run the analysis again.

### 3. Implement

Open **Implement**:

1. Check the **branch** name. It is suggested from the story ID (`story/F02-S02-create-the-cdk-app-and-pipeline-skeleton`) and created in the story's repository from its current branch.
2. Tick **Scaffold unlock** only for the first story in a submodule: **F02-S02** (Infrastructure) and **F02-S12** (Code). It lets that run add the toolchain configs.
3. If confidence is below 80%, enter a reason to override. It is saved with the run.
4. Click **Check preflight**, then **Start implementation**.

The run follows the harness `plan_build` workflow (`harness/workflows/plan_build.json`). Every
step is executed by the harness itself (`harness/drivers/run_plan_build.py`), exactly as
`run_story.py run` does; Studio only runs the steps one at a time so it can checkpoint,
stream and resume. Each step shows in the step bar and the console:

```
classify → plan → plan_exists → write_tests → commit_tests → red → implement
         → tests_unchanged → green → validate → review → commit → human review
```

| Step | What happens |
|---|---|
| classify | The read-only reviewer picks the work type (for example `cdk-infrastructure`, `checker-script`) |
| plan | The builder writes a plan file with numbered "shall" criteria |
| plan_exists | Checks that the plan cites the story and has those criteria |
| write_tests | The builder writes tests first |
| commit_tests | The builder commits only the tests (skipped for documentation and other TDD-free work types) |
| red | The validator must **fail** twice, which shows the new tests test something |
| implement | The builder writes the code |
| tests_unchanged | The committed tests must be unchanged: the implementation may not weaken them |
| green, validate | The validator must **pass** (twice, then once) |
| review | The reviewer checks the real diff against the plan and steering: `APPROVE` or `REVISE` |
| commit | Only after `APPROVE`, the builder commits the change on the story branch |
| human review | You decide (next section) |

The console shows agent text, tool calls, validator output and, optionally, the agent's
thinking. Token counts are shown per step, per run, per story and in total. Kiro does not
report token usage to the app (it bills credits to your account), so these are
**estimates** from text size.

**Stop, resume and re-run.** **Stop** ends the current step. **Resume** continues from the
first unfinished step on the same branch. This also works after a crash or a Studio restart,
because every step is saved in harness-db (`harness/studio/data/harness.db`). When a check
such as `green` fails, you can fix the problem by hand and resume. **Re-run from step** runs
a chosen step and everything after it again, for example `review` after you changed
something yourself.

If the reviewer answers `REVISE`, `commit` refuses and the run stops there with the findings
in the console. Fix the code on the branch, or re-run from `implement`.

### 4. Review (you)

When the run reaches **Human review**, the builder's commits are on the story branch and
nothing is pushed. Studio shows the commits, the reviewer's verdict and findings, the full
diff against the base, and anything the agent left uncommitted. Then either:

- click **Approve: ready to push**, or
- click **Reject**. The commits stay on the branch.

You can amend or add commits on the branch yourself before you approve.

## After you approve: push, PR and record

For a story in a submodule:

```bash
git -C project-mep-AWS-Code push -u origin story/<branch>     # or project-mep-AWS-Infrastructure
# open a pull request in that repository on MEPUSA.ghe.com and merge it after review
```

After it is merged, record the story as done. This commits the new submodule pointer and
`status: done` together in this repository (ADR 0002, rule 2):

```bash
uv run --with-requirements harness/drivers/requirements.txt python harness/run_story.py record F02-S02
```

For a `planning` story, the commits are on its branch in this repository. Push it and open a
pull request into `main` (`main` only accepts pull requests).

## Command line (same harness, no UI)

Studio and these commands run the same harness code and give the same results:

```bash
uv run --with-requirements harness/drivers/requirements.txt python harness/run_story.py list               # runnable stories, next first
uv run --with-requirements harness/drivers/requirements.txt python harness/run_story.py analyze F02-S02    # confidence; exit 2 below 80
uv run --with-requirements harness/drivers/requirements.txt python harness/run_story.py run F02-S02 --scaffold [--branch story/...]
uv run --with-requirements harness/drivers/requirements.txt python harness/run_story.py record F02-S02     # after the PR is merged
```

Set `AEW_AUTO_APPROVE=1` in the shell first for `run`. The driver checks run without Kiro:

```bash
uv run --with-requirements harness/drivers/requirements.txt python -m unittest discover -s harness/tests -v
```

## Rules the harness enforces

- **One story, one repository.** A story changes only the repository in its `repo:` field.
- **Baseline vs project.** Infrastructure is the AWS baseline. Code is the project and its own resources, and it reads the baseline from SSM `/mep/baseline/*` without changing it. Deploy Infrastructure first; tear down Code first. See ADR 0002 and `.kiro/steering/project-context.md`, rule context-6.
- **No deploys from agents.** Hooks block `cdk deploy`, `destroy`, `bootstrap`, `diff` and any AWS call that changes resources. `cdk synth` runs locally with credentials removed. Deploys go through the pipelines and a person.
- **Frozen harness files.** Kiro agents may not edit `.kiro/`, `scripts/hooks/`, `scripts/validate.sh`, `harness/drivers/`, `harness/workflows/`, `harness/run_story.py`, `harness/context/` or `HARNESS.md` (see `harness/answer-key.txt`).
- **No secrets.** Mitsui values are named parameters in `user-stories/config/parameters.md`. Secrets are referenced by Secrets Manager name only, and a hook blocks secret-looking content.
- **Tests first, 80% coverage**, TypeScript CDK v2 with cdk-nag (`.kiro/steering/engineering-standards.md`).
- **Freezes.** No load-pipeline changes from Dec 14, 2026 and no code changes from Dec 18, 2026 except fixes for failed tests.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `kiro-cli` badge is red | Install Kiro CLI, open a new terminal, run `kiro-cli login` |
| `npm` badge is red | Install Node.js LTS, then open a **new** terminal (old terminals keep the old PATH) |
| Preflight: "has uncommitted changes" | Commit or stash in the repository the story changes |
| Preflight: "branch already exists" | Delete the old `story/...` branch in that repository, or open its run and resume it |
| Preflight: "is not checked out" | `git submodule update --init` |
| Validator fails with `$'\r': command not found` | A shell script got Windows line endings. `.gitattributes` prevents this on a fresh checkout. Run `git add --renormalize . && git checkout -- .` |
| Studio port is busy | `.\studio 8780` or `./studio.sh 8780` |
| A run shows **interrupted** | Studio stopped while it was running. Open the run and click **Resume**. |

More detail: [`harness/studio/README.md`](harness/studio/README.md) (Studio internals) and
[`HARNESS.md`](HARNESS.md) (harness reference).
