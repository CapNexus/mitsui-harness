# 0002. Repository structure and team roles

Status: accepted (Nov 17, 2026)

## Repository structure

This repository is the main (parent) repository. It holds planning only: features, stories, dependencies, config parameters, evidence and scripts for tracking.

The implementation lives in separate repositories on Mitsui's GitHub Enterprise (`MEPUSA.ghe.com`), added here as git submodules at the repository root. Each submodule is versioned and can be handed over on its own. Planning stays with CapNexus.

Updated Nov 19, 2026: the five proposed `code/` submodules were replaced by the two repositories Mitsui created.

| Path (`repo:` value) | Content | Features |
|---|---|---|
| `project-mep-AWS-Infrastructure` | CDK: landing zone baseline, VPC, VPN, PrivateLink, DMS resources, S3 buckets, KMS, pipeline, monitoring, teardown | F2, F3, F4 (DMS and buckets), F12 |
| `project-mep-AWS-Code` | Glue/Athena load jobs, catalog, Lake Formation, MCP tools, AgentCore Gateway and Policy, assistant, Teams bot, eval harness | F4 (load jobs), F5, F6 (app config), F7, F8, F9, F10, F11, F13 |
| `planning` (this repo) | Stories, evidence, tracking scripts | F1, F13 (evidence), F14 |

A story that would touch both submodules is split so each story names one repository.

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
