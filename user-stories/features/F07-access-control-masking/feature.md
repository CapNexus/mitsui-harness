---
id: F7
title: Data access control and column masking
sow: D4
due: 2026-12-04
status: draft
depends_on_features: [F4, F5, F6]
blocked_by: [DEP-14, DEP-16, DEP-27]
---

## Description

Lake Formation grants table access by Entra group, hides restricted tables, and masks at least one column for users outside `sg-wda-econ-sensitive`. The masking and access matrix (Appendix E3) is signed by Mitsui.

Source: `WDA-POC-Feature-List.md`, F7. Workflow step D8 and section 6.2 in `adr/WDA-POC-Data-Workflow.md`.

## Feature-level acceptance criteria

| # | Criterion | Covered by |
|---|---|---|
| 1 | Three test users exist: User A (all groups, including `sg-wda-econ-sensitive`), User B (permitted groups, not `sg-wda-econ-sensitive`), User C (no groups). | F07-S06 |
| 2 | User A sees all approved tables and the unmasked column. | F07-S01, F07-S02, F07-S05, F07-S06 |
| 3 | User B sees approved tables and the column is masked. | F07-S02, F07-S05, F07-S06 |
| 4 | User C sees no restricted tables and no masked column. | F07-S01, F07-S05, F07-S06 |
| 5 | Results in criteria 2 to 4 are identical through the Gateway, Teams, Claude Code and Claude Desktop. | F07-S06 (Gateway and direct Athena). Teams, Claude Code and Claude Desktop runs belong to F10, F11 and F13, which reuse the F07-S05 test harness. |
| 6 | An INSERT, UPDATE, DELETE or DDL attempt is refused by Lake Formation when sent directly to Athena (this is the second layer after F8). | F07-S07, F07-S06 |
| 7 | The masking and access matrix is signed by Noah Jackson (tables) and Matt Schiefelbein (groups). | F07-S03 |

## Stories

| ID | Title | Tier | Executor | Blocked by | Status |
|---|---|---|---|---|---|
| [F07-S01](stories/F07-S01-lake-formation-grants-as-code.md) | Build Lake Formation table grants by Entra group as code | build | agent | none | ready |
| [F07-S02](stories/F07-S02-column-masking-data-filter.md) | Build the column-masking data filter as code | build | agent | none | ready |
| [F07-S03](stories/F07-S03-access-matrix-signoff.md) | Pre-fill and sign the masking and access matrix (Appendix E3) | integrate | mixed | DEP-16 | blocked |
| [F07-S04](stories/F07-S04-apply-access-matrix-poc.md) | Apply the access matrix in the POC account | integrate | mixed | DEP-14, DEP-16 | blocked |
| [F07-S05](stories/F07-S05-permission-test-harness.md) | Build the A/B/C permission test harness | build | agent | none | ready |
| [F07-S06](stories/F07-S06-test-users-and-first-permission-test.md) | Create test users A, B, C and run the first permission test | integrate | mixed | DEP-14 | blocked |
| [F07-S07](stories/F07-S07-lake-formation-write-refusal.md) | Prove Lake Formation refuses writes sent directly to Athena | build | agent | none | ready |

## Open points

- Schedule conflict: F7 is due Dec 2 to Dec 4, but SME descriptions (F5, DEP-17) are due Dec 10. F7 does not need descriptions to grant access, but the matrix (F07-S03) is easier to fill with them. Use the table inventory and placeholder descriptions.
- Task list conflict: Lake Formation is configured on Wed Dec 2, but the matrix is signed on Fri Dec 4. F07-S04 applies the pre-filled (proposed) matrix on Dec 2 and re-applies the signed one on Dec 4.
- DEP-27 (type E): grants must work in both `identity_mode` values. In `group_fallback`, grants go to one IAM role per Entra group instead of to Identity Center groups.
- DEP-16 (masked column) was blank at kickoff. Build with a dummy column until it is named.
- Proposed new parameters, not yet in `config/parameters.md`: `identity_mode`, `test_users`, `access_matrix_file` (`config/access-matrix.yaml`).
