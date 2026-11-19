---
id: F04-S09
feature: F4
title: Connect to Mitsui sources and run the first full loads
tier: integrate
executor: mixed
owner: Venkat
repo: project-mep-AWS-Infrastructure
status: blocked
sow: D3
due: 2026-11-25
blocked_by: [DEP-05, DEP-07, DEP-08, DEP-09]
depends_on_stories: [F04-S01, F04-S02, F04-S03, F04-S05, F04-S06]
params: [sql_server_endpoints, approved_table_list, secret_dms_mepwell, secret_dms_sdedbprod, secret_dms_meps_aries]
human_gates: [InfoSec approves the data copy, a human enters the SQL credentials, DBAs confirm the login is not privileged]
---

## Story

As Venkat (DevOps), I want DMS connected to the three Mitsui SQL Servers and the first full loads landed in S3 Tables, so that Week 2 ends with real data in AWS and verified row counts.

## Context

Week 2 plan: DMS setup Tue Nov 24, first loads Wed Nov 25, in the order MEPWELL, then MEPS_ARIES, then SDEDBPROD (only once the approach is in place, F04-S10). Needs F3 (VPN tunnels up, TCP tests passing from the DMS subnet) and F2 (POC account, KMS key).

This story swaps the placeholders for the real values: `sql_server_endpoints`, the signed `approved_table_list`, and the three secrets. The harness never sees the credentials. A human enters them in Secrets Manager.

## Acceptance criteria

1. Given the real endpoint values and secrets, when DMS test connection runs, then all three endpoints show `successful`.
   - gate: a human enters the three secret values from the DBAs' secure channel.
   - verify: `aws dms describe-connections` shows status `successful` for all three endpoints. Output saved as evidence.
2. Given the DMS login, when the DBAs run the Appendix A2 check, then `IS_SRVROLEMEMBER('sysadmin', 'dms_wda_ro')` returns 0 and the login has only `db_datareader`, `VIEW DATABASE STATE` and `VIEW DEFINITION` in each database.
   - gate: DBA sends the query output, saved as evidence.
3. Given the signed approved list, when the first full loads run, then MEPWELL and MEPS_ARIES load, and the S3 Tables namespace contains exactly the approved tables and the name map.
   - verify: `make check-approved-only` compares S3 Tables with `config/approved-tables.yaml` and exits 0.
4. Given the first loads, when the row-count check runs, then source and target counts match for every loaded table.
   - verify: `wda_meta.load_runs` shows status `ok` for every table of the run.
5. Given the data copy leaves Mitsui's data center, when the first load is started, then InfoSec's written approval of the data copy is on file.
   - gate: DEP-05 approval saved as evidence before the first load.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-05 | C | InfoSec and data-copy approval | None. Hard stop before the first load. |
| DEP-07 | A+D | VPN, firewall rules, endpoints | None. Needs F3 done. |
| DEP-08 | D+A | Mixed-mode authentication, TDE status | None |
| DEP-09 | B | Read-only SQL logins | None |

## Evidence

`evidence/F04/first-loads/`: test-connection output, DBA permission check, `make check-approved-only` output, `load_runs` export for Nov 25.

## Status log

- 2026-11-19: created
