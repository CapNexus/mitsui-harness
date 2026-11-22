# F02-S01 service availability in us-east-1

Checked 2026-11-22 against AWS documentation (no AWS account call). Home Region `aws_home_region` = us-east-1. Result values: `available`, `limited`, `missing`. "Limited" means the service exists in us-east-1 with a constraint that affects the design. Account-level proof (quotas, model access, a working call) comes later in F02-S08 and the F06 spikes.

| # | Service | Result | Note | Source |
|---|---|---|---|---|
| 1 | AgentCore Gateway | available | Listed as supported in us-east-1, us-east-2 and us-west-2. | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html |
| 2 | AgentCore Identity | available | Listed as supported in all three Regions. | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html |
| 3 | AgentCore Runtime | available | Both microVM and Instances forms are listed as supported in us-east-1. | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html |
| 4 | AgentCore Policy | available | "Policy in AgentCore" is listed as supported in us-east-1, us-east-2 and us-west-2. Closes the Policy part of risk 17. | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html |
| 5 | S3 Tables | available | The `s3tables.us-east-1.amazonaws.com` endpoint exists. Default quota: 100 table buckets per Region and account. | https://docs.aws.amazon.com/general/latest/gr/s3.html |
| 6 | Lake Formation with S3 Tables | available | The S3 Tables catalog integration supports table-level, column-level and row-level grants. No Regional restriction is documented. Enabling Lake Formation control removes existing IAM-based access to the tables, so grants must be in place first. Not proven in the account until F05-S05. | https://docs.aws.amazon.com/lake-formation/latest/dg/create-s3-tables-catalog.html and https://docs.aws.amazon.com/lake-formation/latest/dg/change-access-iam-to-lf.html |
| 7 | Identity-aware Athena workgroups | limited | us-east-1 is a supported Region. Constraints: queries cannot run from the Athena console and run through EMR Studio or SageMaker Unified Studio; no support for federated access with the JDBC and ODBC drivers or for Athena for Spark; default query timeout 30 minutes (maximum 1 hour); entitlement changes can take up to an hour; the workgroup type cannot be changed after creation. Whether the tool Lambdas can call Athena with a propagated identity is tested in the F06-S06 spike. | https://docs.aws.amazon.com/athena/latest/ug/workgroups-identity-center.html |
| 8 | Claude model access in Bedrock | limited | Claude models are documented for us-east-1, and the US geographic inference profile routes inside US Regions. Account-level access (Anthropic first-use form, default quotas) is not confirmed. A model listed as legacy in us-east-1 has an end-of-life date of 2026-11-26, so the model choice must avoid it. Confirmed by a real call in F02-S08. | https://docs.aws.amazon.com/bedrock/latest/userguide/models-region-compatibility.html and https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html |

Eight services: the task list names seven items ("S3 Tables with Lake Formation" is one). It is split into rows 5 and 6 to match the story's eight.

## Gaps for the RAID log

- Row 7: RAID R-02.
- Row 8: RAID R-03.

Soma records the design response for each gap in the RAID log (F02-S01 gate).
