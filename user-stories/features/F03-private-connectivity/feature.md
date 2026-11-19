---
id: F3
title: Private connectivity (VPN and PrivateLink)
sow: D2
due: 2026-11-23
status: draft
depends_on_features: [F2]
blocked_by: [DEP-02, DEP-04, DEP-05, DEP-07]
---

## Description

Build the AWS side of a site-to-site IPsec VPN to Mitsui's Palo Alto: workload VPC from the Mitsui-assigned CIDR, virtual private gateway, customer gateway, two tunnels. Route to the VPN only from the DMS subnet. Add PrivateLink endpoints for Bedrock, Athena and logging. The assistant must have no network path to the source databases.

Source: `WDA-POC-Feature-List.md`, F3. Data workflow steps D2 and D3.

## Feature-level acceptance criteria

| # | Criterion | Covered by |
|---|---|---|
| 1 | Both VPN tunnels show UP. | F03-S03, F03-S06 |
| 2 | TCP tests from the DMS subnet to each of the three SQL Servers succeed on each server's fixed port. | F03-S06 |
| 3 | Route table and firewall rule exports show that only the DMS subnet can reach the on-premises databases. | F03-S02, F03-S07 |
| 4 | A connection attempt from the assistant or tool compute subnets to a SQL Server port fails. | F03-S07 |
| 5 | PrivateLink endpoints for Bedrock, Athena and logging resolve inside the VPC, and a Bedrock call from the VPC succeeds without internet egress. | F03-S04, F03-S08 |
| 6 | The route and firewall exports are saved as evidence for InfoSec and Network. | F03-S07 |

## Stories

| ID | Title | Tier | Executor | Blocked by | Status |
|---|---|---|---|---|---|
| [F03-S01](stories/F03-S01-network-values-and-change-tickets.md) | Collect the network values and change tickets from Mitsui | integrate | human | DEP-07, DEP-04 | blocked |
| [F03-S02](stories/F03-S02-workload-vpc-and-subnets.md) | Build the workload VPC with isolated DMS and tool subnets | build | agent | none | ready |
| [F03-S03](stories/F03-S03-site-to-site-vpn-construct.md) | Build the site-to-site VPN to the Palo Alto | build | agent | none | ready |
| [F03-S04](stories/F03-S04-privatelink-endpoints.md) | Build the PrivateLink endpoints | build | agent | none | ready |
| [F03-S05](stories/F03-S05-deploy-network-and-send-palo-alto-config.md) | Deploy the network to the POC account and send the Palo Alto configuration | integrate | mixed | DEP-07, DEP-05 | blocked |
| [F03-S06](stories/F03-S06-validate-tunnels-and-tcp-reachability.md) | Validate both tunnels and TCP reachability from the DMS subnet | integrate | mixed | DEP-07 | blocked |
| [F03-S07](stories/F03-S07-no-path-proof-and-evidence.md) | Prove the assistant has no path to the databases and save the evidence | integrate | mixed | DEP-07 | blocked |
| [F03-S08](stories/F03-S08-bedrock-over-privatelink.md) | Prove Bedrock, Athena and logs work over PrivateLink with no internet | integrate | mixed | DEP-06 | blocked |

Order: S02, then S03 and S04 (build, can start now). S01 in parallel. S05 needs S01 to S04 and F02-S09. S06 needs S05. S07 needs S06. S08 needs S05 and F02-S08.

## Open points

- DMS replication subnet groups need subnets in at least two Availability Zones. The cost estimate assumes interface endpoints in one AZ. Proposal: DMS subnets in two AZs, endpoints in one AZ. Confirm with Soma.
- Gap 8: if the Teams bot compute or tools need AgentCore Runtime privately, an AgentCore interface endpoint is needed. Confirm availability in us-east-1 (F02-S01) before F8 and F10. F03-S04 makes the endpoint list configurable.
- Gap 7: the bot endpoint must be public (API Gateway with WAF), outside these private subnets. Not in F3 scope.
- DNS (item 3.4): IP addresses are simplest. If Mitsui gives names, a Route 53 Resolver outbound endpoint is needed. Proposed new parameter `onprem_dns_servers`.
- Values not yet in `config/parameters.md`: Palo Alto model and PAN-OS version (needed to download the right config file) and BGP ASN if routing is BGP. Proposed new parameters `palo_alto_device_model` and `palo_alto_bgp_asn`.
- Task list Mon Nov 23 puts tunnel validation on Soma. F3 criterion 5's Bedrock call also depends on DEP-06 (F02-S08).
