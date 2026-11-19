---
id: F03-S03
feature: F3
title: Build the site-to-site VPN to the Palo Alto
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Infrastructure
status: ready
sow: D2
due: 2026-11-19
blocked_by: []
depends_on_stories: [F03-S02]
params: [palo_alto_public_ip, palo_alto_routing_type, onprem_cidrs]
human_gates: []
---

## Story

As Venkat (DevOps), I want the virtual private gateway, customer gateway and VPN connection defined in code, so that the AWS side of the VPN is ready to deploy as soon as Matt sends the Palo Alto values.

## Context

Task list Thu Nov 19 and item 3.1. Two IPsec tunnels. Routing is static or BGP (`palo_alto_routing_type`), so the construct supports both. Direct Connect and Transit Gateway are out of scope.

## Acceptance criteria

1. Given the network stack, when it is synthesized, then it has a virtual private gateway attached to the VPC, a customer gateway at `palo_alto_public_ip`, and one VPN connection.
   - verify: CDK assertion test passes.
2. Given `palo_alto_routing_type` is `static`, when it is synthesized, then a static route exists for each entry in `onprem_cidrs` and route propagation is on only for the DMS route table. Given `bgp`, then the customer gateway uses the BGP ASN and no static routes are created.
   - verify: unit tests for both routing types pass.
3. Given a deployed VPN connection, when the helper script runs, then it downloads the Palo Alto sample configuration file for the given device and PAN-OS version.
   - verify: `scripts/get-palo-alto-config.sh --dry-run` prints the matching device type ID. Script is created by this story.
4. Given the VPN, when tunnel options are checked, then both tunnels use IKEv2 and AWS-recommended encryption settings, and tunnel logs go to a log group encrypted with the F02 KMS key.
   - verify: assertion test on tunnel options and the log group passes.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-07 | A+D | Palo Alto public IP, routing type, ASN, device model | `palo_alto_public_ip`, `palo_alto_routing_type`. Proposed new parameters `palo_alto_device_model`, `palo_alto_bgp_asn`. |

## Evidence

PR and test output.

## Status log

- 2026-11-19: created
