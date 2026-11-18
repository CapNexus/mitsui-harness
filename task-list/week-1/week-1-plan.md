# Week 1: Mobilize, access and AWS foundation

Dates: Nov 16 to Nov 20

**Goal:** Owners named, management account and cross-account role in place, Control Tower landing zone and POC workload account built, VPN started, source inventories requested, Deliverable 1 (project plan and question set outline) sent.

## Mon 2026-11-16: Kick-off day

| Done | Owner | Task |
|---|---|---|
| [ ] | Engagement Manager | Run the kick-off meeting. Confirm named owners and backups for every Week 1 dependency (item 1.1). Written confirmation of the kick-off date and owners. |
| [ ] | Engagement Manager | Create the RAID (risks, assumptions, issues and dependencies) log and dependency tracker from the Client Dependencies document. Create the shared Teams channel. |
| [ ] | Solution Architect | Hand over the cross-account role inputs to Mitsui: CapNexus AWS account ID, principal ARNs (Amazon Resource Names) and external ID. |
| [ ] | Solution Architect | Send the architecture summary and data-flow diagram to Mitsui InfoSec (item 1.3). |
| [ ] | Data & Platform Engineer | Send the Appendix A SQL scripts to Mitsui database administrators and the Appendix C network sheet to Matt Schiefelbein. |
| [ ] | Noah Jackson (Mitsui) | Due today: new management account created as root user, root MFA (multi-factor authentication) on, three account email addresses supplied. |
| [ ] | Engagement Manager | Ask Mitsui for the holiday and change-freeze calendar (item 1.2). Confirm whether a change advisory board ticket is needed for VPN, firewall, SQL and Entra changes. |

## Tue 2026-11-17: Cross-account role and region checks

| Done | Owner | Task |
|---|---|---|
| [ ] | Matt Schiefelbein / Noah Jackson (Mitsui) | Create the temporary cross-account role (AdministratorAccess, MFA and external ID required, 4-hour sessions, 7-day expiry). Send back the role ARN. |
| [ ] | Solution Architect | Test assuming the role. Complete Appendix B pre-flight checks: Organizations all-features mode, Config trusted access, STS endpoints in us-east-1. |
| [ ] | Solution Architect | Confirm in us-east-1: AgentCore Gateway, Identity, Runtime and Policy, S3 Tables with Lake Formation, identity-aware Athena workgroups, Claude model access (risk 17). |
| [ ] | Data & Platform Engineer | Prepare the Control Tower configuration: home Region us-east-1, Region-deny control allowing us-east-1, us-east-2 and us-west-2 for Claude cross-region inference. |
| [ ] | Solution Architect | Send the Anthropic first-use text and quota-increase request to Mitsui for submission (item 2.6). |
| [ ] | Engagement Manager | Send the monthly AWS cost estimate and ask for budget approval (item 1.5). |
| [ ] | CapNexus Integration & Test Engineer | Send Entra guest invitation list for the five CapNexus roles (item 1.6). |

## Wed 2026-11-18: Launch Control Tower

| Done | Owner | Task |
|---|---|---|
| [ ] | Solution Architect and Data & Platform Engineer | Launch the Control Tower landing zone in the management account. Create Log Archive and Audit accounts from the supplied emails. |
| [ ] | Data & Platform Engineer | Create the Workloads organizational unit. |
| [ ] | Engagement Manager | Draft the project plan and the question set outline (Deliverable 1). |
| [ ] | Solution Architect | Request the Palo Alto model, PAN-OS version, public IP, routing type and CIDR (Classless Inter-Domain Routing) ranges from Matt Schiefelbein (items 3.1, 3.2). |
| [ ] | Engagement Manager | Confirm the SDEDBPROD owner is being named (item 4.4, on hold). Escalate to Noah Jackson if still blank. |

## Thu 2026-11-19: POC workload account and IaC foundation

| Done | Owner | Task |
|---|---|---|
| [ ] | Data & Platform Engineer | Create the POC workload account through Account Factory. Confirm enrollment and no drift. |
| [ ] | Solution Architect | Enable the IAM Identity Center organization instance in the management account (item 2.7). Do not switch identity source yet. |
| [ ] | Data & Platform Engineer | Create the infrastructure-as-code repository (TypeScript or Python with AWS CDK) and the pipeline skeleton using AWS CodeConnections to Mitsui's repository, once the repository home is confirmed (item 1.7). |
| [ ] | Data & Platform Engineer | Deploy the AWS Budgets alert to the billing contact. |
| [ ] | Solution Architect | Create the AWS side of the VPN: workload VPC from the Mitsui-assigned CIDR, virtual private gateway, customer gateway. Send the Palo Alto configuration file. |
| [ ] | Whole CapNexus team | Confirm each engineer can sign in to the AWS access portal and Teams (item 1.6). |

## Fri 2026-11-20: Close out the management account and Week 1 review

| Done | Owner | Task |
|---|---|---|
| [ ] | Matt Schiefelbein (Mitsui) | Due today: VPN configured on the Palo Alto side, firewall rules to SQL Server ports, read-only SQL logins, Entra administrator available. |
| [ ] | Noah Jackson (Mitsui) | Delete the cross-account role once Control Tower and the Identity Center preparation are done. Send CloudTrail review confirmation. |
| [ ] | Data & Platform Engineer | Review returned inventory scripts (A1, A3, A4). List unsupported column types and tables. |
| [ ] | Engagement Manager | Submit Deliverable 1. Start the 8-business-day review clock. |
| [ ] | Engagement Manager | Update the RAID log. Record any Week 1 dependency that slipped, with date and cause. Under SOW Assumption 8 the timeline moves day for day. |
| [ ] | Engagement Manager | Book Entra administrator sessions for Week 2 and Week 3. Book SME (subject matter expert) data-model session for Monday. |

## Exit criteria

- [ ] Landing zone shows Active, POC workload account enrolled, no drift
- [ ] Cross-account role used and then deleted by Mitsui
- [ ] VPN (virtual private network) tunnels up, or blocker logged with a date
- [ ] Read-only SQL logins and source inventories received, or chased with an owner
- [ ] Entra administrator sessions booked for Weeks 2 and 3
- [ ] Deliverable 1 submitted
