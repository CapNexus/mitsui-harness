# Configuration parameters

Every Mitsui-supplied value (dependency types A and B) is a named parameter. Stories list the parameter names they use. The harness builds against the placeholder, and swapping in the real value is a config change, not a code change.

Rules:
- Type B values (secrets) are never stored here. Only the Secrets Manager secret name is.
- `status` is `placeholder` until the real value is received, then `set`.
- Values in "Proposed default" come from Feature List Section 6 and are not yet agreed with Mitsui.

## Values (type A)

| Parameter | Source DEP | Placeholder or proposed default | Status |
|---|---|---|---|
| `aws_home_region` | DEP-06 | `us-east-1` | set |
| `aws_allowed_regions` | DEP-06 | `us-east-1, us-east-2, us-west-2` | set |
| `account_email_log_archive` | DEP-03 | `TBD` | placeholder |
| `account_email_audit` | DEP-03 | `TBD` | placeholder |
| `account_email_poc` | DEP-03 | `TBD` | placeholder |
| `billing_contact_email` | DEP-26 | `TBD` | placeholder |
| `budget_monthly_usd` | DEP-26 | `TBD` | placeholder |
| `repo_home_url` | DEP-25 | `TBD` | placeholder |
| `vpc_cidr` | DEP-07 | `TBD (Mitsui-assigned)` | placeholder |
| `onprem_cidrs` | DEP-07 | `TBD` | placeholder |
| `palo_alto_public_ip` | DEP-07 | `TBD` | placeholder |
| `palo_alto_routing_type` | DEP-07 | `TBD (static or BGP)` | placeholder |
| `sql_server_endpoints` | DEP-07, DEP-08 | `TBD (host, fixed port for MEPWELL, SDEDBPROD, MEPS_ARIES)` | placeholder |
| `approved_table_list` | DEP-10 | `config/approved-tables.yaml` (Appendix E1), empty until signed | placeholder |
| `sdedbprod_mode` | DEP-11 | `undecided` (`compress_state0` or `evw_views`) | placeholder |
| `load_window` | DEP-12 | `01:00-04:00 America/Chicago` (example only) | placeholder |
| `load_blackout_dates` | DEP-04, DEP-12 | `TBD` | placeholder |
| `crosswalk_rules` | DEP-13 | `config/crosswalk.yaml` | placeholder |
| `masked_column` | DEP-16 | `TBD (use a dummy column in the sandbox)` | placeholder |
| `classification_rules` | DEP-16 | `TBD` | placeholder |
| `sme_descriptions_file` | DEP-17 | `config/descriptions.yaml` (Appendix E2) | placeholder |
| `question_set_file` | DEP-21 | `config/questions.yaml` | placeholder |
| `pilot_users` | DEP-22 | `TBD (about 15)` | placeholder |
| `alarm_distribution_list` | DEP-24 | `TBD` | placeholder |
| `log_reader_principals` | DEP-24 | `TBD` | placeholder |
| `entra_tenant_id` | DEP-14 | `TBD` | placeholder |
| `entra_issuer_url` | DEP-14 | `TBD (sandbox: any OIDC provider)` | placeholder |
| `wda_api_audience` | DEP-14 | `TBD` | placeholder |
| `entra_groups` | DEP-14 | `sg-wda-users-well, sg-wda-users-geo, sg-wda-users-econ, sg-wda-econ-sensitive, sg-wda-itpmo-tools, sg-wda-admins, sg-wda-capnexus-engineers` | set |
| `identity_mode` | DEP-27 | `propagated` (or `group_fallback`, SOW Assumption 8). Set by F06-S07 | placeholder |
| `test_users` | DEP-14 | `TBD (Entra UPNs for test users A, B, C)` | placeholder |
| `access_matrix_file` | DEP-16 | `config/access-matrix.yaml` (Appendix E3) | placeholder |
| `s3_tables_namespace` | none | `wda` (proposed default) | placeholder |
| `geometry_lob_max_kb` | DEP-11 | `64` (proposed DMS limited-LOB cap for shape columns) | placeholder |
| `bedrock_model_id` | DEP-06 | `TBD (Claude Sonnet-class inference profile)` | placeholder |
| `codeconnections_connection_arn` | DEP-25 | `TBD (connection to MEPUSA.ghe.com)` | placeholder |
| `palo_alto_device_model` | DEP-07 | `TBD (model and PAN-OS version)` | placeholder |
| `palo_alto_bgp_asn` | DEP-07 | `TBD (only if routing is BGP)` | placeholder |
| `onprem_dns_servers` | DEP-07 | `TBD (only if SQL Servers are given by name)` | placeholder |
| `endpoint_az_count` | none | `1` (cost estimate; DMS subnets still span 2 AZs) | placeholder |

## Limits (proposed, Feature List Section 6)

| Parameter | Proposed default |
|---|---|
| `limit_list_tables_rows` | 200 |
| `limit_describe_columns_rows` | 300 |
| `limit_sample_rows_default` / `_max` | 10 / 50 |
| `limit_run_select_rows` | 1000 |
| `timeout_list_describe_sample_s` | 10 |
| `timeout_run_select_s` | 30 |
| `timeout_question_s` | 55 |
| `athena_scan_cutoff_gb` | 10 |

## Secrets (type B). Names only

| Parameter | Source DEP | Secret name (placeholder) |
|---|---|---|
| `secret_dms_mepwell` | DEP-09 | `wda/dms/mepwell` |
| `secret_dms_sdedbprod` | DEP-09 | `wda/dms/sdedbprod` |
| `secret_dms_meps_aries` | DEP-09 | `wda/dms/meps_aries` |
| `secret_bot_client` | DEP-14 | `wda/bot/client` |
| `secret_wda_clients_id` | DEP-14 | `wda/entra/wda-clients` |
| `crossaccount_role_arn` | DEP-02 | provided by Mitsui, not stored. Temporary role, deleted after Nov 20. |
