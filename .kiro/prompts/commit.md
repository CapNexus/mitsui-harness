---
name: commit
description: "Stage and commit only the files for the given scope (tests, or the full change)."
mode: on-demand
---

# Commit the change for a given scope

You are the **builder** agent. Create one git commit that contains only the files belonging to the requested scope. Do not push, do not amend existing commits, and do not run any deploy or `cdk deploy` command.

## Variables

plan_file_path: $1
scope: $2

## Instructions

- Read the plan file at `$1`. It names the story id, the classification, the acceptance criteria and the files the plan expects to create or change.
- The requested scope is `$2`. The valid scopes are `tests` and `full`. If the requested scope is any other value, make no commit and report the problem.
  - Scope `tests`: commit only test files and test fixtures (paths under `test/`, and any script test files the plan lists). Do not stage implementation files, even if they already exist in the working tree.
  - Scope `full`: commit the complete change for the plan: implementation under `lib/`, `bin/` and `scripts/`, tests under `test/`, and documentation or evidence files the plan lists.
- Run `git status --porcelain` and `git diff --stat` to see what changed. Compare the changed paths with the plan's file list and with the requested scope (`$2`).
- Stage files by explicit path with `git add <path>`. Never use `git add -A`, `git add .` or `git commit -a`.
- Do not stage or commit any of the following. If one appears in the working tree, leave it unstaged and mention it in the report:
  - files unrelated to the plan, or changes you did not make for this plan;
  - `cdk.out/`, `node_modules/`, `coverage/` and other build output;
  - secrets, credentials, `.env` files, account or tenant identifiers that the plan marks as placeholders to be filled by a person.
- Before committing, run `git diff --cached --name-only` and confirm that every staged path belongs to the scope. Unstage anything that does not with `git restore --staged <path>`.
- If nothing in scope is changed, make no commit and report that nothing needed committing. Do not create an empty commit.
- Write the commit message in this form:
  - Subject line, at most 72 characters: `<story id>: <imperative summary>` for `full`, or `<story id>: add tests` for `tests`. Take the story id from the plan file.
  - A blank line, then a short body listing the acceptance criteria numbers the commit covers.
- Commit with `git commit -m "<subject>" -m "<body>"`. Do not use `--no-verify`. If a hook rejects the commit, report the hook's output and stop. Do not work around the hook.
- After committing, run `git show --stat --oneline HEAD` and `git status --porcelain` to confirm the commit holds only in-scope files.
- Do not modify any file's content while committing. The `tests_unchanged` check later requires that the files committed with scope `tests` stay byte-identical.

## Report

- The scope you committed and the commit hash.
- The list of files in the commit.
- Any files left unstaged, with the reason.
- If no commit was made, say why.
