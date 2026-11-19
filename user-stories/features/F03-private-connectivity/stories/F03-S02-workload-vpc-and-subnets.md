---
id: F03-S02
feature: F3
title: Build the workload VPC with isolated DMS and tool subnets
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Infrastructure
status: ready
sow: D2
due: 2026-11-19
blocked_by: []
depends_on_stories: [F02-S02]
params: [vpc_cidr, onprem_cidrs]
human_gates: [Soma approves the subnet layout in the PR]
---

## Story

As Venkat (DevOps), I want a workload VPC where only the DMS subnets have a route to the data center, so that the assistant and tools have no network path to Mitsui's databases by design.

## Context

Task list Thu Nov 19. Data workflow D3: only the DMS subnet routes to the VPN. Proposed layout: DMS subnets (two AZs, required by DMS subnet groups), tool and assistant subnets, and an endpoint subnet. No internet gateway and no NAT gateway. Built against a placeholder CIDR in the sandbox.

Out of scope: the VPN itself (F03-S03) and the endpoints (F03-S04).

## Acceptance criteria

1. Given `vpc_cidr`, when the network stack is synthesized, then it creates the VPC and the DMS, tool and endpoint subnets inside that CIDR, with DMS subnets in two Availability Zones.
   - verify: CDK assertion test on subnets and CIDRs passes.
2. Given the route tables, when they are checked, then only the DMS route table may hold routes to `onprem_cidrs`, and the tool and endpoint route tables have no route to the virtual private gateway.
   - verify: assertion test on route tables passes.
3. Given the VPC, when it is checked, then it has no internet gateway and no NAT gateway.
   - verify: assertion test passes.
4. Given the security groups, when they are checked, then the DMS security group allows outbound only to `onprem_cidrs` on the SQL Server ports and to the VPC endpoints on 443.
   - verify: assertion test on security group rules passes.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-07 | A+D | VPC CIDR and on-prem CIDRs | `vpc_cidr`, `onprem_cidrs` (sandbox values) |

## Evidence

PR and test output.

## Status log

- 2026-11-19: created
