---
id: F08-S05
feature: F8
title: Place the tools in the VPC with no path to the source databases
tier: integrate
executor: mixed
owner: Venkat
repo: project-mep-AWS-Code
status: blocked
sow: D5
due: 2026-12-03
blocked_by: [DEP-07]
depends_on_stories: [F08-S02]
params: [vpc_cidr, onprem_cidrs, sql_server_endpoints]
human_gates: [Venkat approves the deployment to the POC account]
---

## Story

As Venkat (DevOps), I want the tool Lambdas in their own subnets of the workload VPC, with interface endpoints to Athena and logs and no route to the VPN, so that the assistant layer can never reach Mitsui's databases.

## Context

Feature List Section 6: tools in the workload VPC with interface endpoints to Athena and logs. F3 builds the VPC, VPN and endpoints, and routes only the DMS subnet to the VPN. This story places the tools and proves isolation from the tool side. Needs F3 deployed in the POC account.

Also record whether an AgentCore interface endpoint exists in us-east-1 (Feature List Section 5, gap 8). F10 needs the answer.

## Acceptance criteria

1. Given the tool subnets, when the route tables are checked, then no route points to the virtual private gateway, and the security group allows outbound HTTPS to the VPC endpoints only.
   - verify: `scripts/check-tool-network.sh --env poc` exits 0. Script created by this story.
2. Given a test Lambda in the tool subnets, when it opens a TCP connection to each SQL Server endpoint and port, then every connection fails.
   - verify: the same script runs the probe and expects failure for all three servers.
3. Given the tools, when they call Athena, Glue and CloudWatch Logs, then the calls go through the interface endpoints and succeed without internet egress.
   - verify: the same script checks a tool call succeeds with no NAT route.
4. Given the evidence, when saved, then the route and security group exports are in the evidence folder, and the AgentCore endpoint answer is in the RAID log.
   - gate: Venkat approves.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-07 | A+D | VPC CIDR, on-prem CIDRs, VPN up (F3) | Sandbox VPC with a fake on-prem CIDR for the unit test |

## Evidence

Route and security group exports, probe output, in `user-stories/evidence/F08/`.

## Status log

- 2026-11-19: created
