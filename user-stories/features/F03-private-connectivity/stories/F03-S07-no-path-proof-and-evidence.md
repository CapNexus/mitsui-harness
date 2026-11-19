---
id: F03-S07
feature: F3
title: Prove the assistant has no path to the databases and save the evidence
tier: integrate
executor: mixed
owner: Soma
repo: project-mep-AWS-Infrastructure
status: blocked
sow: D2
due: 2026-11-23
blocked_by: [DEP-07]
depends_on_stories: [F03-S06]
params: [onprem_cidrs, sql_server_endpoints]
human_gates: [Matt Schiefelbein sends the Palo Alto firewall rule export]
---

## Story

As Soma (solution architect), I want route table and firewall exports plus a failing connection test from the tool subnet, so that InfoSec and Network can verify the acceptance criterion "the assistant has no network path to the on-premises databases".

## Context

F3 criteria 3, 4 and 6. First run Mon Nov 23 after the tunnels are up. It is repeated on Tue Dec 15 (task list Week 5) and used again in the Week 6 InfoSec verification on Tue Dec 22.

## Acceptance criteria

1. Given the deployed VPC, when the route export runs, then only the DMS route table has routes to `onprem_cidrs` or the virtual private gateway.
   - verify: `scripts/export-routes.sh --assert` exits 0 and writes the export. Script is created by this story.
2. Given the probe deployed in the tool subnet, when it connects to each SQL Server host and port, then every connection fails.
   - verify: `scripts/tcp-probe.sh --subnet tools --expect-fail` exits 0.
3. Given Mitsui's firewall, when Matt exports the rules for the SQL Server ports, then only the DMS subnet addresses are allowed.
   - gate: Matt sends the export. Soma checks it and saves it.
4. Given the three outputs, when they are saved, then the evidence folder has a dated copy of each, ready for InfoSec and Network.
   - verify: `evidence/F03/no-path/` holds the route export, probe output and firewall export with the same date.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-07 | A+D | Firewall rule export from Mitsui | None. |

## Evidence

`evidence/F03/no-path/<date>/`: route export, tool-subnet probe output, firewall export.

## Status log

- 2026-11-19: created
