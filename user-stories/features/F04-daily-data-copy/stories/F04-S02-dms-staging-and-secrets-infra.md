---
id: F04-S02
feature: F4
title: Define DMS, staging bucket and source secrets as code
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Infrastructure
status: ready
sow: D3
due: 2026-11-24
blocked_by: []
depends_on_stories: []
params: [sql_server_endpoints, onprem_cidrs, secret_dms_mepwell, secret_dms_sdedbprod, secret_dms_meps_aries, aws_home_region]
human_gates: []
---

## Story

As Venkat (DevOps), I want the DMS replication, the three source endpoints, the S3 staging bucket and the source credentials defined in CDK, so that the copy can be deployed and rebuilt from the repository with no console work.

## Context

Data flow steps D1 to D4. DMS reads with a SQL-authenticated, read-only login. Credentials live in Secrets Manager under the customer-managed KMS key from F2. DMS runs only in the DMS subnet from F3, which is the only subnet with a route to the VPN. DMS Serverless is the proposed default (bills only while a task runs). DMS cannot write to S3 Tables, so it writes CSV or Parquet to a regular staging bucket.

Endpoints and secrets use placeholders from `config/parameters.md`. The harness never sees the secret values. A human enters them in F04-S09.

Out of scope: table mappings (F04-S03), the load into S3 Tables (F04-S05), alarms (F04-S07).

## Acceptance criteria

1. Given the CDK app, when it is synthesized, then it contains one DMS replication config (Serverless), three SQL Server source endpoints and one S3 target endpoint, and each source endpoint reads its credentials from the matching secret name (`wda/dms/mepwell`, `wda/dms/sdedbprod`, `wda/dms/meps_aries`).
   - verify: `npm test` (CDK assertion tests) passes in `project-mep-AWS-Infrastructure`.
2. Given the synthesized template, when it is checked, then the staging bucket blocks public access, enforces TLS, and is encrypted with the customer-managed KMS key, and the three secrets use the same key.
   - verify: CDK assertion tests and `cdk-nag` (AwsSolutions pack) run with no unsuppressed errors.
3. Given the synthesized template, when it is checked, then DMS runs only in the DMS subnet and its security group allows outbound traffic only to `onprem_cidrs` on the SQL Server ports and to the S3 endpoint.
   - verify: CDK assertion test on the replication subnet group and security group rules.
4. Given the synthesized template, when it is checked, then no DMS endpoint has SQL Server as a target, so nothing can write back to the sources (feature criterion 9).
   - verify: CDK assertion test fails if any endpoint with engine `sqlserver` has type `target`.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-07 | A+D | SQL Server hosts, ports, on-prem CIDRs | `sql_server_endpoints`, `onprem_cidrs` placeholders |
| DEP-09 | B | Read-only SQL logins | Secret names only. Values entered by a human in F04-S09. |

Needs the KMS key (F2) and the VPC with a DMS subnet (F3). If they are not merged yet, use a stub construct with the same interface and say so in the PR.

## Evidence

PR with passing tests and the `cdk-nag` report.

## Status log

- 2026-11-19: created
