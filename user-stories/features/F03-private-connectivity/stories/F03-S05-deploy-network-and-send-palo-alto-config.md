---
id: F03-S05
feature: F3
title: Deploy the network to the POC account and send the Palo Alto configuration
tier: integrate
executor: mixed
owner: Venkat
repo: project-mep-AWS-Infrastructure
status: blocked
sow: D2
due: 2026-11-19
blocked_by: [DEP-07, DEP-05]
depends_on_stories: [F03-S01, F03-S02, F03-S03, F03-S04, F02-S09]
params: [vpc_cidr, onprem_cidrs, palo_alto_public_ip, palo_alto_routing_type]
human_gates: [InfoSec has the architecture summary before traffic opens, Matt Schiefelbein applies the configuration]
---

## Story

As Venkat (DevOps), I want the VPC, VPN and endpoints deployed through the pipeline with Mitsui's real values, so that Matt can configure the Palo Alto and bring the tunnels up.

## Context

Task list Thu Nov 19 (Solution Architect creates the AWS side and sends the config file). Mitsui configures its side by Fri Nov 20. Deployment goes through the F2 pipeline. InfoSec must have the architecture summary (DEP-05, sent Mon Nov 16) before traffic opens.

## Acceptance criteria

1. Given the real network values, when the pipeline runs, then the network, VPN and endpoint stacks deploy to the POC account, and a second run makes no changes.
   - verify: `cdk diff` against the POC account shows no difference after the run.
2. Given the deployed VPN connection, when the Palo Alto configuration is generated for Mitsui's model and PAN-OS version, then it is sent to Matt through an agreed secure channel.
   - verify: `scripts/get-palo-alto-config.sh` exits 0 and writes the file.
   - gate: Matt confirms receipt. The pre-shared keys are not stored in the repository.
3. Given InfoSec and change control, when traffic is about to open, then the architecture review status and any CAB ticket are recorded.
   - gate: Mike confirms in the RAID log that InfoSec has the architecture summary and that the CAB ticket (if needed) is approved.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-07 | A+D | Real network values and Mitsui's device configuration | None. Real values needed. |
| DEP-05 | C | InfoSec has reviewed the architecture | None. |

## Evidence

Pipeline run link and `cdk diff` output in `evidence/F03/deploy/`. The config file itself is not stored.

## Status log

- 2026-11-19: created
