# Feature map

Build order from the feature list: F1, F2, F3, F4, F5 and F6 (parallel), F7, F8, F9, then F10, F11 and F12 (parallel), then F13 and F14.

| ID | Feature | SOW | Due | Stories written | Folder |
|---|---|---|---|---|---|
| F1 | Mobilization, plan and governance | D1 | Nov 20 | 6 | [F01-mobilization-governance](F01-mobilization-governance/feature.md) |
| F2 | AWS landing zone and POC account as code | D2 | Nov 19 to 20 | 11 (4 ready, 7 blocked) | [F02-landing-zone-as-code](F02-landing-zone-as-code/feature.md) |
| F3 | Private connectivity (VPN and PrivateLink) | D2 | Nov 23 | 8 (3 ready, 5 blocked) | [F03-private-connectivity](F03-private-connectivity/feature.md) |
| F4 | Daily one-way data copy into S3 Tables | D3 | Nov 25 to Dec 11 | 13 (9 ready, 4 blocked) | [F04-daily-data-copy](F04-daily-data-copy/feature.md) |
| F5 | Data catalog with SME descriptions | D3 | Dec 10 | 6 (5 ready, 1 blocked) | [F05-data-catalog](F05-data-catalog/feature.md) |
| F6 | Identity federation (Entra to AWS) | D4 | Dec 1 to 2 | 8 (2 ready, 6 blocked) | [F06-identity-federation](F06-identity-federation/feature.md) |
| F7 | Data access control and column masking | D4 | Dec 2 to 4 | 7 (4 ready, 3 blocked) | [F07-access-control-masking](F07-access-control-masking/feature.md) |
| F8 | MCP tool layer behind AgentCore Gateway and Policy | D5 | Dec 3 | 6 (4 ready, 2 blocked) | [F08-mcp-tool-layer](F08-mcp-tool-layer/feature.md) |
| F9 | Well Data Assistant on AgentCore Runtime | D6 | Dec 7 | not started | |
| F10 | Microsoft Teams channel bot | D6 | Dec 8 | not started | |
| F11 | IT/PMO access from Claude Code and Claude Desktop | D7 | Dec 9 | not started | |
| F12 | Audit trail and monitoring | D8 | Dec 7 to 9 | not started | |
| F13 | Evaluation, security tests and pilot | D9 | Dec 14 to 24 | not started | |
| F14 | Readout, handover and runbook | D10, D11 | Dec 24 | not started | |

Known schedule conflict: F7, F8 and F9 are due before F5 (Dec 10), and they need its descriptions. Each of those features' stories should use placeholder descriptions until F5 is complete.
