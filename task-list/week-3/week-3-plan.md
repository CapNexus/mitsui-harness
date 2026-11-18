# Week 3: Data governance, identity, Teams approval and tool layer

Dates: Nov 30 to Dec 4

**Goal:** Glue catalog and Lake Formation permissions in place, Entra federation and trusted token issuer working, Teams pilot channel approved, MCP (Model Context Protocol) tool layer behind AgentCore Gateway.

## Mon 2026-11-30: Teams approval deadline and Entra groups

| Done | Owner | Task |
|---|---|---|
| [ ] | Engagement Manager | Weekly status call, 3:00 PM Eastern. Report the Week 2 outcome. |
| [ ] | Noah Jackson (Mitsui) | Due today: Teams administrator approval for one pilot channel (item 7.2). Escalate on Monday morning if not confirmed. |
| [ ] | Solution Architect | Entra administrator session 2: create security groups (item 5.3) and app registrations WDA-API, WDA-TeamsBot, WDA-Clients with admin consent (item 5.4). |
| [ ] | Data & Platform Engineer | Register tables and columns in the Glue Data Catalog. Load descriptions already received from SMEs. |
| [ ] | Engagement Manager | Request the masked column and the royalty owner and lessor classification rules from Noah Jackson (item 6.2, due this week). |

## Tue 2026-12-01: Identity Center and federation

| Done | Owner | Task |
|---|---|---|
| [ ] | Solution Architect | Switch the IAM Identity Center identity source to Microsoft Entra ID. Configure SAML (Security Assertion Markup Language) and SCIM with the Entra administrator (item 5.2). Do the switch once, in one session. |
| [ ] | Solution Architect | Create the trusted token issuer for the Entra tenant and map the email claim (item 5.4). |
| [ ] | Solution Architect | Assign groups to the POC workload account. Confirm the CapNexus engineers sign in through Entra. |
| [ ] | Data & Platform Engineer | Set the daily load schedule inside the agreed window. Check the first scheduled run. |

## Wed 2026-12-02: Lake Formation and masking

| Done | Owner | Task |
|---|---|---|
| [ ] | Data & Platform Engineer | Configure Lake Formation permissions by Entra group for the approved tables. Implement the masked column as a data filter. |
| [ ] | Solution Architect | Test identity propagation to Athena. If it does not work, record the fallback (permissions by Entra group, user logged at the application layer, Assumption 8) and get written acceptance from Noah Jackson. |
| [ ] | CapNexus Integration & Test Engineer | Create the three test users and verify group membership (item 5.6). User A in all groups, User B without the sensitive group, User C in none. |
| [ ] | CapNexus AI Engineer | Start the MCP tool layer: list_tables, describe_columns, sample_rows, run_select_query. |

## Thu 2026-12-03: AgentCore Gateway and Azure Bot

| Done | Owner | Task |
|---|---|---|
| [ ] | CapNexus AI Engineer | Deploy the tools behind AgentCore Gateway with the JWT (JSON Web Token) authorizer for the WDA-API audience. Apply AgentCore Policy so every write attempt is refused. |
| [ ] | CapNexus Integration & Test Engineer | Create the Azure Bot resource (single tenant) in the Mitsui Azure subscription (item 7.1). Prepare the Teams app package. |
| [ ] | Solution Architect | Review Conditional Access policies that apply to the pilot, test and IT/PMO users (item 5.5). Identify policies that block loopback or device-code sign-in. |
| [ ] | Engagement Manager | Chase the SME table and column descriptions and the question set draft. |

## Fri 2026-12-04: Permission tests and Week 3 review

| Done | Owner | Task |
|---|---|---|
| [ ] | CapNexus Integration & Test Engineer | Run the first permission test with users A, B and C through the Gateway. Out-of-group users must not see restricted tables or the masked column. |
| [ ] | Engagement Manager with Noah Jackson and Matt Schiefelbein | Sign off the masking and access matrix (Appendix E3). |
| [ ] | Data & Platform Engineer | Confirm four consecutive daily loads have run and row counts match. The two-week unattended-load window starts Monday Dec 14 and ends Fri Dec 25. Dec 7 to Dec 11 is for stabilizing the load, and Dec 11 is the hard target. |
| [ ] | Engagement Manager | Week 3 exit review. Update the RAID log. Confirm the Week 4 dates for the Teams bot, client access and test environment. |

## Exit criteria

- [ ] Teams administrator approval for the pilot channel received by Mon Nov 30 (SOW)
- [ ] Entra users and groups visible in IAM Identity Center and a test sign-in works
- [ ] Lake Formation permissions and one masked column enforced per Entra group
- [ ] AgentCore Gateway accepts an Entra token and runs read-only tools
- [ ] Test users A, B and C exist and are in the right groups
- [ ] Group-to-table access matrix signed off
