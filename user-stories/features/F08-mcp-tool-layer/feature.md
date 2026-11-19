---
id: F8
title: MCP tool layer behind AgentCore Gateway and Policy
sow: D5
due: 2026-12-03
status: draft
depends_on_features: [F3, F4, F5, F6, F7]
blocked_by: [DEP-06, DEP-14, DEP-27]
---

## Description

Publish four read-only tools (`list_tables`, `describe_columns`, `sample_rows`, `run_select`) through AgentCore Gateway with a JWT authorizer for the WDA-API audience. AgentCore Policy allows only the approved tools, only SELECT statements, and enforces row limits and timeouts. The tools query Athena as the signed-in user.

Source: `WDA-POC-Feature-List.md`, F8 and Section 6 (tool compute and Policy limits). Workflow steps Q6 to Q9 and C1 in `adr/WDA-POC-Data-Workflow.md`.

## Feature-level acceptance criteria

| # | Criterion | Covered by |
|---|---|---|
| 1 | A request without a token, with a wrong audience, or with a bad signature is refused at the Gateway. | F08-S03, F08-S06 |
| 2 | With a valid Entra token, each of the four tools returns correct results for User A. | F08-S02, F08-S06 |
| 3 | A write attempt (INSERT, UPDATE, DELETE, DROP, CREATE, multi-statement SQL with a write) is refused by AgentCore Policy, and the refusal is logged. | F08-S04 |
| 4 | A SELECT above the row limit is capped, and a query above the timeout is cancelled, using the values in Section 6 (or the values Mitsui changes them to). The limits are recorded in the runbook. | F08-S02, F08-S04 |
| 5 | The tools have no network path to the source databases. | F08-S05 |
| 6 | Tool names are consistent in code, policy and documentation (`run_select`, not `run_select_query`). | F08-S01 |

## Stories

| ID | Title | Tier | Executor | Blocked by | Status |
|---|---|---|---|---|---|
| [F08-S01](stories/F08-S01-tool-contract-and-names.md) | Define the tool contract, limits and names | build | agent | none | ready |
| [F08-S02](stories/F08-S02-tool-lambdas.md) | Build the four read-only tool Lambdas | build | agent | none | ready |
| [F08-S03](stories/F08-S03-gateway-jwt-authorizer.md) | Publish the tools through AgentCore Gateway with a JWT authorizer | build | agent | none | ready |
| [F08-S04](stories/F08-S04-agentcore-policy-select-only.md) | Enforce SELECT-only, row limits and timeouts with AgentCore Policy | build | agent | none | ready |
| [F08-S05](stories/F08-S05-tool-network-isolation.md) | Place the tools in the VPC with no path to the source databases | integrate | mixed | DEP-07 | blocked |
| [F08-S06](stories/F08-S06-gateway-poc-deployment.md) | Deploy the Gateway and tools to the POC account with Entra | integrate | mixed | DEP-06, DEP-14 | blocked |

## Open points

- Feature List Section 5, gap 2: the Week 3 task list (Wed Dec 2) says `run_select_query`. Use `run_select`. F08-S01 adds a name check, and the task list line should be corrected by whoever owns the task list.
- Feature List Section 6 proposes one Lambda per tool as a Gateway Lambda target. This is a proposal, not a signed decision. F08-S01 records it as a decision for Soma to approve.
- Schedule conflict: `describe_columns` needs SME descriptions (F5, DEP-17), due Dec 10. Until then it returns placeholder descriptions from `sme_descriptions_file`.
- DEP-27 (type E): the tools must work in both `identity_mode` values. In `group_fallback`, the tool assumes the role for the caller's highest-privilege permitted group and writes the user's identity to the audit log (F12).
- DEP-06: AgentCore Gateway and Policy availability in us-east-1 was to be confirmed on Tue Nov 17. F08-S06 stays blocked until it is.
- Gap 8: if the bot compute is in the VPC, an AgentCore interface endpoint may be needed. That is F10's concern, but F08-S05 records whether the endpoint exists.
- Proposed new parameters, not yet in `config/parameters.md`: `identity_mode`, `test_users`.
