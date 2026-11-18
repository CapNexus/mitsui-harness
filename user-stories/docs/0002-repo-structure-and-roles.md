# 0002. Repository structure and team roles

Status: accepted (Nov 17, 2026)

## Repository structure

This repository is the main (parent) repository. It holds planning only: features, stories, dependencies, config parameters, evidence and scripts for tracking.

The implementation lives in separate repositories added here as git submodules, under `code/`. Each submodule is versioned and can be handed over on its own (DEP-25 may move the code repository to Mitsui on Dec 17). Planning stays with CapNexus.

Proposed submodules (names to confirm):

| Path | Content | Features |
|---|---|---|
| `code/infra` | CDK: landing zone baseline, VPC, VPN, PrivateLink, DMS, pipeline, KMS, teardown | F2, F3, F4, F12 |
| `code/data` | Glue/Athena load jobs, catalog, Lake Formation | F4, F5, F7 |
| `code/gateway-tools` | MCP tools (Lambda), AgentCore Gateway and Policy | F8 |
| `code/assistant` | AgentCore Runtime agent, Guardrails, eval harness | F9, F13 |
| `code/teams-bot` | Bot endpoint, Teams app package | F10 |

Rules:
1. A story names the submodule it changes in a `repo:` front-matter field.
2. A story is `done` when its PR in the submodule is merged and the parent repo records the new submodule commit and the story status in one commit.
3. Planning files never go into a submodule.

## Roles

| Person | Role | Owns |
|---|---|---|
| Mike | Project manager | F1 stories, status report, RAID log, Mitsui follow-ups, human gates for approvals |
| Soma | Solution architect | Design decisions (type E dependencies), DEP-06 and DEP-27 tests, story review for F8, F9 and F13 |
| Venkat | DevOps | AWS landing zone, IaC, pipeline, network, load pipeline, submodule CI |

Stories use `owner:` for the accountable person. The harness does the work, and the owner reviews and approves.
