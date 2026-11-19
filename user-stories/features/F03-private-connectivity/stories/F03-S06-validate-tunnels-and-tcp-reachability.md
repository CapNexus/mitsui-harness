---
id: F03-S06
feature: F3
title: Validate both tunnels and TCP reachability from the DMS subnet
tier: integrate
executor: mixed
owner: Soma
repo: project-mep-AWS-Infrastructure
status: blocked
sow: D2
due: 2026-11-23
blocked_by: [DEP-07]
depends_on_stories: [F03-S05]
params: [sql_server_endpoints]
human_gates: [Matt Schiefelbein confirms the Palo Alto side is configured]
---

## Story

As Soma (solution architect), I want a repeatable test that shows both tunnels are up and each SQL Server port answers from the DMS subnet, so that DMS setup on Tue Nov 24 starts on a working network.

## Context

Task list Mon Nov 23 (item 3.3). The TCP probe runs as a short-lived Lambda function in the DMS subnet, so no EC2 instance is needed. The same probe is reused in F03-S07 from the tool subnet.

## Acceptance criteria

1. Given the VPN connection, when the status check runs, then both tunnels report UP.
   - verify: `scripts/check-vpn-tunnels.sh` exits 0 only when both tunnels are `UP`. Script is created by this story.
2. Given the probe deployed in the DMS subnet, when it connects to each host and fixed port in `sql_server_endpoints`, then all three TCP connections succeed.
   - verify: `scripts/tcp-probe.sh --subnet dms` exits 0 and reports success for MEPWELL, SDEDBPROD and MEPS_ARIES. Script is created by this story.
3. Given a failed probe, when the result is reported, then the failing host and port and the time are written to the output, so Matt can check the firewall.
   - verify: unit test for the probe's failure output passes.
   - gate: if a probe fails, Mike logs the blocker with a date in the RAID log (DEP-07 step 5).

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-07 | A+D | Palo Alto configured and firewall rules open for the DMS subnet | `sql_server_endpoints` |

## Evidence

Tunnel status and probe output in `evidence/F03/reachability/`.

## Status log

- 2026-11-19: created
