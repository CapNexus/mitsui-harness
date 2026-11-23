# Harness change: propose answers to analysis questions

Handoff note so the work survives a Kiro CLI restart. Written 2026-11-22. Not a story: this changes the harness itself, so it needs `HARNESS_UNLOCK=1` (the `guard-answer-key` hook reads it from the hook process environment only, `scripts/hooks/guard-answer-key.py` line 482).

## Request (Soma, 2026-11-22)

When the analysis raises questions, the harness proposes an answer to each one. It reads the knowledge documents, the architecture and ADRs, and earlier stories, and grounds each answer in the AWS Well-Architected Framework. The human sees the answer and changes it if needed.

## Decisions (Soma, 2026-11-22)

1. A "Propose answers" button runs it. It does not run automatically after every analysis.
2. Answers are stored in the Studio database, and also written into the story file on Accept.
3. The story is re-analyzed with the accepted answers, so confidence can rise.
4. Precedents are stories with `status: done` and stories that are partly done (`in-progress`).

## Acceptance criteria

1. Studio shall show a "Propose answers" button on a completed analysis that has questions.
2. The button shall start one read-only Kiro `reviewer` turn with the prompt `.kiro/prompts/propose_answers.md`, recorded as a run of kind `proposal` with the same console, stop and token tracking as other runs.
3. Each proposal shall carry: question number, kind (`answer` or `human_action`), proposal text, Well-Architected pillars with a one-line reason, sources as `path#section`, precedent story ids, confidence (`high`, `medium`, `low`), `needs_human` and owner.
4. The harness shall mark a source whose file does not exist in the repository as unverified, and shall show that mark.
5. A question about a Mitsui value, date, approval or confirmation shall come back as `human_action` with `needs_human` true. The prompt forbids inventing it.
6. The reading list shall contain the story, its feature file, the dependency register, the parameters, `adr/`, `knowledge/`, `harness/context/`, `.kiro/steering/`, and every story with status `done` or `in-progress` with its plan under `specs/` or a submodule `plans/` folder.
7. Each question shall have Accept, Edit and Clear in Studio. An edit shall be saved in the database and shall not overwrite the original proposal.
8. On Accept, the harness shall write the question and accepted answer into a `## Decisions` section of the story file, one line per question with date and "accepted by" text supplied by the user, and shall replace the line for the same question on a second accept. It shall not commit.
9. A re-run of the analysis shall pass the accepted answers to the reviewer as settled decisions, and `analyze_story.md` shall tell the reviewer not to raise a question already answered there.
10. Tests shall use a fake agent and shall not call Kiro, AWS or the network.

## Files

| File | Guarded | Change |
|---|---|---|
| `.kiro/prompts/propose_answers.md` | yes | New prompt, envelope `<<<PROPOSALS>>>` (JSON array). Full text drafted in the session; key rules are in criteria 3 and 5. |
| `.kiro/prompts/analyze_story.md` | yes | Add: treat the story's `## Decisions` section as settled. |
| `harness/studio/db.py` | yes | New table `answers (story_id, q, question, proposal_json, answer, status, accepted_by, updated_at)`, `CREATE TABLE IF NOT EXISTS`. |
| `harness/studio/runner.py` | yes | Run kind `proposal`, steps `gather`, `propose`, `check_sources`. |
| `harness/studio/server.py` | yes | `POST /api/stories/{sid}/propose`, `GET /api/stories/{sid}/answers`, `PUT /api/stories/{sid}/answers/{q}`, `POST .../accept`, `POST .../clear`. |
| `harness/studio/static/app.js`, `app.css` | yes | Proposal card under each question in the Analyze view. |
| `harness/run_story.py` | yes | Optional `analyze --propose` (prints proposals). |
| `harness/answer_proposals.py` | no | Reading list, render, parse, source check, write `## Decisions`. |
| `harness/tests/test_answer_proposals.py` | no | Unit tests with a fake agent. |

## How to continue in a new session

1. In PowerShell: `$env:HARNESS_UNLOCK = "1"`, then start Kiro CLI from that window in `C:\capnexus\repo\mitsui-harness`.
2. Tell Kiro: "Implement `specs/harness/answer-proposals.md`."
3. When done, `Remove-Item Env:HARNESS_UNLOCK`.
