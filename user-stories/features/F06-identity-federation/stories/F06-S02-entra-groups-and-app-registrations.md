---
id: F06-S02
feature: F6
title: Create the Entra groups and app registrations
tier: integrate
executor: human
owner: Soma
repo: planning
status: blocked
sow: D4
due: 2026-11-30
blocked_by: [DEP-14]
depends_on_stories: [F06-S01]
params: [entra_groups, wda_api_audience, secret_bot_client, secret_wda_clients_id]
human_gates: [Matt Schiefelbein creates the groups and app registrations and grants admin consent]
---

## Story

As Soma (solution architect), I want the seven Entra security groups and the three app registrations created with admin consent, so that Identity Center, Lake Formation, the Gateway and the Claude clients have the identities they need.

## Context

Task list Week 3, Mon Nov 30: Entra administrator session 2 (items 5.3, 5.4). Only Mitsui's Entra administrator can do this. Group membership must be flat, because SCIM does not sync nested groups. WDA-Clients is a public client because Entra has no dynamic client registration. The redirect URIs for Claude Code (localhost loopback) and Claude Desktop depend on the connection method (DEP-20, F11). Add them later if not known on Nov 30.

Secrets (the bot client secret, the WDA-Clients ID if treated as secret) are entered by a human into Secrets Manager. The harness never sees the values.

Out of scope: test users A, B and C (F07-S06), the identity-source switch (F06-S03).

## Acceptance criteria

1. Given session 2, when the groups are created, then all seven groups in `entra_groups` exist as assigned security groups, with no nested groups, and are assigned to the AWS IAM Identity Center enterprise application.
   - gate: screenshot or export of the groups and the app assignment saved in `user-stories/evidence/F06/`.
2. Given session 2, when the app registrations are created, then WDA-API (Application ID URI and one delegated scope such as `access_as_user`), WDA-TeamsBot (single tenant) and WDA-Clients (public client flows allowed, delegated permission on the WDA-API scope) exist with admin consent.
   - gate: Matt Schiefelbein confirms admin consent. Export saved as evidence.
3. Given the apps exist, when the token configuration is checked, then optional claims `email`, `upn` and `groups` (limited to groups assigned to the application) are present.
   - gate: a decoded test token (with personal values redacted) saved as evidence.
4. Given the values are received, when the config is updated, then `wda_api_audience` is `set` and the two secret names exist in Secrets Manager with human-entered values.
   - verify: `grep wda_api_audience user-stories/config/parameters.md` shows status `set`.
   - gate: the person who entered the secrets confirms in the PR.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-14 | D+B+A | Entra admin session, app IDs, consent | `TBD` audience |
| DEP-20 | C+E | Redirect URIs for WDA-Clients | Loopback only, added later |

## Evidence

Group and app exports, decoded token sample, in `user-stories/evidence/F06/`.

## Status log

- 2026-11-19: created
