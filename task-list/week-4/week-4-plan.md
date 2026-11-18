# Week 4: Assistant, Teams bot, Claude clients and stable load

Dates: Dec 7 to Dec 11

**Goal:** The assistant runs on AgentCore Runtime, answers in Teams, and is reachable from Claude Code and Claude Desktop. Descriptions complete, question set frozen, core build delivered to the Mitsui test environment, daily load stable.

## Mon 2026-12-07: Assistant on AgentCore Runtime

| Done | Owner | Task |
|---|---|---|
| [ ] | Engagement Manager | Weekly status call, 3:00 PM Eastern. |
| [ ] | CapNexus AI Engineer | Deploy the assistant on AgentCore Runtime with Claude on Bedrock. Wire it to the Gateway tools. |
| [ ] | CapNexus AI Engineer | Prompt design: schema discovery, join rules from the crosswalk, row limits, refusal of non-SELECT requests. |
| [ ] | Data & Platform Engineer | Stabilize the daily load this week (fixes allowed). Tell Mitsui database administrators and the network team that the unattended-load window starts Mon Dec 14 and that the servers and VPN must not change until Dec 25. |
| [ ] | Data & Platform Engineer | Turn on the audit trail: question, tool call, SQL, user, time and result size. Encrypt logs with the customer-managed KMS key. |
| [ ] | Engagement Manager | Confirm the pilot user names and the pilot lead with Noah Jackson (item 9.3, due Week 4). |

## Tue 2026-12-08: Teams bot

| Done | Owner | Task |
|---|---|---|
| [ ] | CapNexus Integration & Test Engineer | Deploy the bot messaging endpoint with Bot Framework JWT validation and AWS WAF (web application firewall). Set it in the Azure Bot resource (item 7.1). |
| [ ] | CapNexus Integration & Test Engineer | Run Test in Web Chat. Then install the app in the pilot channel and test with a Mitsui test user. |
| [ ] | CapNexus AI Engineer | Format Teams answers as a short table plus the SQL. Check the 60-second response target. |
| [ ] | Solution Architect | Send the connection-method options for Claude Code and Claude Desktop to InfoSec (item 8.1). |

## Wed 2026-12-09: Claude Code and Claude Desktop

| Done | Owner | Task |
|---|---|---|
| [ ] | CapNexus AI Engineer | Configure the pre-registered WDA-Clients app and the Gateway access for Claude Code and Claude Desktop (Entra has no dynamic client registration). |
| [ ] | CapNexus Integration & Test Engineer | Test sign-in from a Mitsui-managed laptop. Record Conditional Access or proxy problems and send them to Matt Schiefelbein. |
| [ ] | Noah Jackson (Mitsui) | Due: IT/PMO (information technology and project management office) user list and device readiness (items 8.1, 8.2). |
| [ ] | Data & Platform Engineer | Add observability: latency, error and throttling dashboards, and alarm routing to the Mitsui distribution list (item 10.1). |

## Thu 2026-12-10: Descriptions, question set and test environment

| Done | Owner | Task |
|---|---|---|
| [ ] | Engagement Manager | Collect the SME descriptions. Load them into the Glue Data Catalog as table and column comments. |
| [ ] | CapNexus AI Engineer | Freeze the question set with SME sign-off. Hold back about 10 questions from tuning (item 9.2). |
| [ ] | Engagement Manager | Deliver the core build to the Mitsui test environment. Notify Noah Jackson that the 2-week UAT window and the 8-business-day review clock start. |
| [ ] | CapNexus Integration & Test Engineer | Confirm the 15 pilot users are in the Entra groups, the Team and the pilot channel. |
| [ ] | Engagement Manager | Run the 30-minute enablement session for pilot users and send the one-page guide. Pilot access opens Monday Dec 14, earlier than the original Week 6 start. |

## Fri 2026-12-11: Stable daily load and Week 4 review

| Done | Owner | Task |
|---|---|---|
| [ ] | Data & Platform Engineer | Confirm five days of clean daily loads (Dec 7 to Dec 11). Hard target: stable daily load by today. |
| [ ] | Solution Architect | Review the audit trail, permission tests and Region-deny control for any gaps. |
| [ ] | Engagement Manager | Week 4 exit review. Update the RAID log. Confirm the unattended-load window starts Mon Dec 14 and runs through Fri Dec 25, and that the load pipeline is frozen from Dec 14. |
| [ ] | Whole CapNexus team | Fix list for Week 5 from everything found this week. |

## Exit criteria

- [ ] Assistant answers a question in the Teams pilot channel with a table and the SQL
- [ ] IT/PMO connection method approved and a test question works from Claude Code and Claude Desktop
- [ ] SME descriptions loaded for all tables used in the question set
- [ ] Question set frozen and pilot users named
- [ ] Core build delivered to the Mitsui test environment (UAT, user acceptance testing, starts)
- [ ] Daily load stable by Fri Dec 11 (hard target) and the unattended-load window (Dec 14 to Dec 25) confirmed with Mitsui DBAs and the network team
- [ ] Pilot users trained and given access
