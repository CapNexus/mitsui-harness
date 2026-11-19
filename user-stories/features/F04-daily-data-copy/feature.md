---
id: F4
title: Daily one-way data copy into S3 Tables
sow: D3
due: 2026-12-24
status: draft
depends_on_features: [F2, F3]
blocked_by: [DEP-03, DEP-05, DEP-07, DEP-08, DEP-09, DEP-10, DEP-11, DEP-12, DEP-13]
---

## Description

Copy approved tables from MEPWELL (about 0.2 GB), SDEDBPROD (about 10 GB) and MEPS_ARIES (about 5 GB) once a day. DMS reads over the VPN with a read-only SQL login and writes CSV or Parquet to an S3 staging bucket. A Glue or Athena job loads S3 Tables with lowercase table and column names, keeps a source-to-target name map, compares row counts with the source, and raises an alarm on any mismatch or failed task. SDEDBPROD must reflect current edits (compressed to state 0 or read through versioned `_evw` views).

Dates: first loads Wed Nov 25, four clean daily loads by Fri Dec 4, stable by Fri Dec 11 (hard target), unattended window Mon Dec 14 to Fri Dec 25 with the evidence export on Thu Dec 24.

Source: `WDA-POC-Feature-List.md`, F4. Data flow steps D1 to D6 and the load run in `adr/WDA-POC-Data-Workflow.md`.

## Feature-level acceptance criteria

| # | Criterion | Covered by |
|---|---|---|
| 1 | DMS test connection succeeds for all three endpoints, and credentials are in Secrets Manager under the customer-managed KMS key. | F04-S02, F04-S09 |
| 2 | Only tables on the signed approved list are loaded, and nothing else appears in S3 Tables. | F04-S01, F04-S03, F04-S09 |
| 3 | After each load, target row counts equal source row counts for every approved table. | F04-S06, F04-S09 |
| 4 | All table and column names in S3 Tables are lowercase, and the name mapping table covers 100% of them. | F04-S03, F04-S05 |
| 5 | A known recent SDEDBPROD edit appears in the AWS copy after the next load. | F04-S10 |
| 6 | Fault test: stopping the DMS task or dropping the connection mid-load raises the partial-load alarm and an email reaches the Mitsui distribution list. | F04-S07, F04-S12 |
| 7 | The load runs on schedule inside the agreed window with no manual action. Four consecutive clean daily loads by Fri Dec 4, five by Fri Dec 11. | F04-S08, F04-S11, F04-S12 |
| 8 | The unattended window runs Mon Dec 14 to Fri Dec 25 with no manual loads. DMS task and alarm history exported on Thu Dec 24. The Dec 25 load is checked on the next business day. | F04-S13 |
| 8a | The load pipeline is frozen from Dec 14. Only fixes for a failed load are allowed. | F04-S13 |
| 9 | Nothing writes back to the source databases (`dms_wda_ro` has only `db_datareader`, `VIEW DATABASE STATE`, `VIEW DEFINITION`). | F04-S02, F04-S09 |
| 10 | Shape columns arrive as text only where DMS supports the type, and the size cap is documented. | F04-S03, F04-S10 |

## Stories

| ID | Title | Tier | Executor | Repo | Blocked by | Status |
|---|---|---|---|---|---|---|
| [F04-S01](stories/F04-S01-approved-table-list.md) | Pre-fill and sign off the approved table list | integrate | mixed | planning | DEP-08, DEP-10 | blocked |
| [F04-S02](stories/F04-S02-dms-staging-and-secrets-infra.md) | Define DMS, staging bucket and source secrets as code | build | agent | project-mep-AWS-Infrastructure | none | ready |
| [F04-S03](stories/F04-S03-dms-table-mappings.md) | Generate DMS table mappings from the approved list | build | agent | project-mep-AWS-Infrastructure | none | ready |
| [F04-S04](stories/F04-S04-sandbox-source-databases.md) | Build sandbox source databases with synthetic data | build | agent | project-mep-AWS-Code | none | ready |
| [F04-S05](stories/F04-S05-load-staging-into-s3-tables.md) | Load staged files into S3 Tables with a name map | build | agent | project-mep-AWS-Code | none | ready |
| [F04-S06](stories/F04-S06-row-count-check.md) | Compare row counts after each load | build | agent | project-mep-AWS-Code | none | ready |
| [F04-S07](stories/F04-S07-load-alarms-and-notifications.md) | Add load alarms and the email topic | build | agent | project-mep-AWS-Infrastructure | none | ready |
| [F04-S08](stories/F04-S08-daily-load-orchestration.md) | Orchestrate and schedule the daily load | build | agent | project-mep-AWS-Code | none | ready |
| [F04-S09](stories/F04-S09-connect-sources-and-first-loads.md) | Connect to Mitsui sources and run the first full loads | integrate | mixed | project-mep-AWS-Infrastructure | DEP-05, DEP-07, DEP-08, DEP-09 | blocked |
| [F04-S10](stories/F04-S10-sdedbprod-currency-and-geometry.md) | Decide the SDEDBPROD approach and prove current edits load | integrate | mixed | planning | DEP-11 | blocked |
| [F04-S11](stories/F04-S11-scheduled-load-four-clean-runs.md) | Schedule the load in the agreed window and reach four clean runs | integrate | mixed | project-mep-AWS-Code | DEP-12 | ready |
| [F04-S12](stories/F04-S12-fault-test-and-stable-load.md) | Run the partial-load fault test and reach a stable load | integrate | mixed | project-mep-AWS-Code | DEP-24 | ready |
| [F04-S13](stories/F04-S13-unattended-window-and-evidence.md) | Run the unattended window and export the evidence | integrate | mixed | planning | DEP-04, DEP-12 | blocked |

Build order: S04, S02, S03, S05, S06, S07, S08 can start now in the CapNexus sandbox. S01 and S10 run in parallel with Mitsui. S09 needs F3 (VPN tunnels up) and S01. Then S11, S12, S13.

## Open points

- DEP-11 (SDEDBPROD approach, type E) is undecided. S03 and S08 build both options behind `sdedbprod_mode`. If there is no decision by Mon Nov 23, load MEPWELL and MEPS_ARIES first and raise the SDEDBPROD-skipped alarm (DEP-11 step 6).
- Glue or Athena for the load job (workflow assumption 2) is the Data & Platform Engineer's choice. S05 records it.
- DMS Serverless is the proposed default (Feature List Section 6, cost notes). S02 uses it unless sizing shows otherwise.
- The Dec 25 load cannot be exported before the readout (Feature List Section 5, gap 1, and Section 7, question 3). Mitsui must accept the next-business-day check. S13 holds the gate.
- F4 depends on F2 (POC account, KMS key) and F3 (VPC, DMS subnet, VPN). The stories reference those features, not story IDs, because F2 and F3 stories were written in parallel.
