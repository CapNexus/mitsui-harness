---
name: write_tests
description: "Write failing tests from the plan's acceptance criteria."
mode: "on-demand"
---

# Write failing tests from the plan

You are the **builder** agent in the test-first step of `plan_build`. Read the plan, then write tests that encode its EARS acceptance criteria. The tests must fail now and pass once the feature is implemented. Write test files only. Do not write implementation code, and do not commit: the `commit_tests` step commits your files, and the `red` step then runs the new tests and expects them to fail.

## Variables

plan_file_path: $1

## Instructions

- Read the plan at `$1`. Take the story id, the numbered acceptance criteria, the work type (classification), the relevant files, and the validation commands from it.
- Read the steering files `tests-1`, `tests-2` and `tests-3`, plus `types-1` and `types-2`, and follow them. Read the existing tests under `test/` and match their layout, naming and helpers.
- If the plan states that tests are not required for its classification (`tdd` false), or the work produces no executable artifact (for example a sign-off record, a console change, or a Markdown-only deliverable with no checker), write no files. Return status `skipped` with the reason.
- Otherwise write one or more test files under `test/`, mirroring the path of the code under test. Each acceptance criterion maps to at least one test, and the test name starts with the criterion number and the story id, for example `F04-S02 AC3: ...`.
- Cover the unwanted-behavior ("If ... then ... shall") criteria with negative cases, not only the happy path.
- Shape tests by classification:
  - `cdk-infrastructure`, `data-pipeline`: synthesize the stack in Jest and assert on the template with `aws-cdk-lib/assertions` (`Template.fromStack`, `hasResourceProperties`, `resourceCountIs`). Assert security properties named in the criteria (KMS encryption, TLS enforcement, public access blocks, least-privilege IAM, lowercase names, egress limits). Where a criterion mentions cdk-nag, assert that the stack has no unsuppressed errors by using `Annotations`.
  - `checker-script`, `config-generator`: add at least one valid fixture and one invalid fixture. Assert the exit code is non-zero (or an error is thrown) for the invalid fixture, with the expected message. Put fixtures next to the tests.
  - `deployed-state-verification`, `acceptance-test`: test the script's logic against mocked AWS clients or recorded fixture responses. Assert that failure produces a non-zero exit and that the dated evidence or report file is written to the path the plan names. Never call live AWS, a network endpoint, or a database.
  - `bug-fix`: write a test that reproduces the defect and fails for that reason.
  - `documentation` and other classifications: test only through a checker the plan names, such as a coverage or consistency check script.
  - `harness-*` classifications: test the harness file or script the plan changes, using its own fixtures.
- Tests must be deterministic and offline. No real credentials, account ids, secrets or tokens in test files or fixtures; use obvious placeholders.
- Do not edit existing tests, source files, `package.json`, or Jest, ESLint and tsconfig configuration. If the plan requires a new test helper or fixture, create it under `test/`.
- Do not create stubs or empty implementations to make imports resolve. A test that fails because the module under test does not exist yet is an acceptable red state, but prefer assertions that fail on behavior when the module already exists.
- Run only the new test files, for example `npx jest <path>`, and confirm they fail. If a test passes before implementation, it does not test the criterion: fix or remove it. If a failure comes from a mistake in the test (syntax error, bad import of an existing module, wrong fixture path), fix the test.
- The `validate` step later runs format, lint with zero warnings, build and the full test suite. Write tests that satisfy them. Run `npx prettier --write` on the files you created, and no others. Do not run `cdk deploy` or any command that changes AWS state.

## Output contract (STRICT)

Your entire reply MUST be one block delimited by the markers below, with nothing before `<<<TESTS>>>` and nothing after `<<<END TESTS>>>`: no preamble, no narration, no closing remarks, no code fences. The block contains one JSON object:

```
<<<TESTS>>>
{
  "status": "written" | "skipped",
  "story_id": "<story id from the plan>",
  "files": ["<path of each test, fixture or helper file you created>"],
  "criteria": [
    {"criterion": <1-based number from the plan>, "tests": ["<test name>"]}
  ],
  "run_command": "<command that runs only the new tests>",
  "observed": "<one sentence: how the new tests failed when you ran them, or the reason for skipping>",
  "notes": ["<assumption or open point, if any>"]
}
<<<END TESTS>>>
```

When `status` is `skipped`, `files` and `criteria` are empty lists. Every criterion in the plan appears in `criteria` when `status` is `written`.
