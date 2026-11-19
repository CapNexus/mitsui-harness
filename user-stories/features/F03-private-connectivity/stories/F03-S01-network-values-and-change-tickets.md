---
id: F03-S01
feature: F3
title: Collect the network values and change tickets from Mitsui
tier: integrate
executor: human
owner: Mike
repo: planning
status: blocked
sow: D2
due: 2026-11-18
blocked_by: [DEP-07, DEP-04]
depends_on_stories: [F01-S01]
params: [vpc_cidr, onprem_cidrs, palo_alto_public_ip, palo_alto_routing_type, sql_server_endpoints]
human_gates: [Matt Schiefelbein completes the Appendix C network sheet, Mitsui confirms CAB ticket numbers]
---

## Story

As Mike (project manager), I want every network value from the Appendix C sheet recorded as a parameter, so that the VPC and VPN code can switch from placeholders to real values with a config change.

## Context

Task list Wed Nov 18 (Solution Architect requests the Palo Alto details, items 3.1 and 3.2). Mitsui's side is due Fri Nov 20. Mike chases. Soma reviews the values. Changes to VPN, firewall and SQL may need CAB tickets (DEP-04).

## Acceptance criteria

1. Given the Appendix C sheet, when Matt returns it, then the Palo Alto model and PAN-OS version, public IP, routing type (and ASN for BGP), VPC CIDR, on-prem CIDRs (SQL Server subnets only), and the IP, instance and fixed port of each SQL Server are filled in.
   - gate: Matt Schiefelbein returns the sheet. Saved in `evidence/F03/appendix-c.md`.
2. Given the returned values, when they are entered in `config/parameters.md`, then `vpc_cidr`, `onprem_cidrs`, `palo_alto_public_ip`, `palo_alto_routing_type` and `sql_server_endpoints` have status `set`, and the VPC CIDR does not overlap the on-prem CIDRs.
   - verify: `scripts/check-network-params.sh` exits 0. Script is created by this story.
3. Given the change calendar, when VPN, firewall and SQL changes need a CAB ticket, then each ticket number and approved date is in the RAID log.
   - gate: Mitsui confirms the ticket numbers or that no ticket is needed.
4. Given the DNS question (item 3.4), when Mitsui answers, then the decision (IP addresses or on-prem DNS servers) is recorded.
   - gate: Matt confirms. Recorded in the RAID log.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-07 | A+D | VPN details, IP plan, DNS, firewall rules | `TBD` values in `config/parameters.md` |
| DEP-04 | C | CAB rules and change-freeze dates | None. |

## Evidence

`evidence/F03/appendix-c.md` and the RAID log entries.

## Status log

- 2026-11-19: created
