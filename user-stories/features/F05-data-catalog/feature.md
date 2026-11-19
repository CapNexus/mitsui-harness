---
id: F5
title: Data catalog with SME descriptions
sow: D3
due: 2026-12-10
status: draft
depends_on_features: [F4]
blocked_by: [DEP-10, DEP-13, DEP-17, DEP-21]
---

## Description

Register every approved table in the Glue Data Catalog with table and column descriptions written with Mitsui SMEs, including join hints and well-identifier crosswalk rules. The `describe_columns` tool reads these descriptions, so they drive SQL quality.

Dates: SME data-model session Mon Nov 23, description sheet pre-filled and sent Wed Nov 25, first registration with the descriptions received so far Mon Nov 30, all descriptions loaded Thu Dec 10.

Source: `WDA-POC-Feature-List.md`, F5. Data flow step D7 in `adr/WDA-POC-Data-Workflow.md`.

## Feature-level acceptance criteria

| # | Criterion | Covered by |
|---|---|---|
| 1 | Every approved table and column is registered in the Glue Data Catalog. | F05-S03, F05-S05 |
| 2 | Every table and column used by the frozen question set has an SME-written description. Missing descriptions are listed and approved as exceptions. | F05-S01, F05-S06 |
| 3 | Descriptions identify the join keys between MEPWELL, SDEDBPROD and MEPS_ARIES and cite the crosswalk table. | F05-S02, F05-S03 |
| 4 | `describe_columns` returns the description text for a sample of 10 tables. | F05-S06 |
| 5 | After a schema change in a source table, the catalog updates after the next load (or the difference is reported by an alarm). | F05-S04 |

## Stories

| ID | Title | Tier | Executor | Repo | Blocked by | Status |
|---|---|---|---|---|---|---|
| [F05-S01](stories/F05-S01-prefill-description-sheet.md) | Pre-fill the description sheet and send it to the SMEs | build | mixed | planning | none | ready |
| [F05-S02](stories/F05-S02-crosswalk-and-join-rules.md) | Capture the crosswalk and join rules from the SMEs | integrate | mixed | planning | DEP-13 | ready |
| [F05-S03](stories/F05-S03-catalog-registration-and-descriptions-loader.md) | Register tables in the catalog and load descriptions | build | agent | project-mep-AWS-Code | none | ready |
| [F05-S04](stories/F05-S04-schema-change-detection.md) | Detect schema changes after each load | build | agent | project-mep-AWS-Code | none | ready |
| [F05-S05](stories/F05-S05-first-catalog-load-in-poc.md) | Register the real tables and load the first descriptions | integrate | mixed | project-mep-AWS-Code | DEP-10, DEP-17 | blocked |
| [F05-S06](stories/F05-S06-complete-descriptions-and-coverage.md) | Complete the descriptions and prove coverage | integrate | mixed | project-mep-AWS-Code | DEP-17, DEP-21 | ready |

Build order: S01, S03 and S04 can start now with the sandbox tables from F04-S04. S02 follows the Nov 23 SME session. S05 needs F4 first loads (F04-S09) and the signed table list. S06 closes by Dec 10.

## Open points

- Known schedule conflict (features README): F7, F8 and F9 are due before F5 completes on Dec 10 and need its descriptions. They use the descriptions loaded on Nov 30 (F05-S05) and placeholder text for the rest.
- Criterion 4 needs the `describe_columns` tool from F8 (due Dec 3). F05-S06 checks it after F8 is deployed. Until then, the same check runs against the Glue API.
- Where join hints are stored (column comment text or Glue column parameters) is decided in F05-S03, and F8's `describe_columns` must read the same place. Soma reviews.
- The question set (DEP-21) is frozen on Dec 10, the same day descriptions are due. Coverage in F05-S06 uses the latest draft until then.
