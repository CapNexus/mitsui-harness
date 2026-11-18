# Well Data Assistant POC: AWS run-cost estimate (draft)

Draft input for Deliverable 10 (readout). Region us-east-1. USD per month, on-demand list prices, before tax, credits and discounts. AWS bills Mitsui directly (SOW Assumption 3).

## Method and limits

- Unit prices come from the AWS public price list files (`pricing.us-east-1.amazonaws.com`) read on Nov 17, 2026. The AWS CLI session had expired, so I used the public files. The last column shows which lines were checked there.
- Lines marked "not verified" or "placeholder" use rough figures that need checking in the AWS Pricing Calculator.
- Volumes are my assumptions, not measurements. Replace them with actual usage from the dashboards in Week 5 (the readout needs an estimate "from actual usage").
- Bedrock is the largest and most uncertain line. The model is not chosen yet ("Claude is default"). I assumed a Sonnet-class model. A smaller model or prompt caching lowers the line.
- Not included: Microsoft licences, Azure Bot (free tier per the diagram), data transfer over the VPN beyond a few GB, support plan, Direct Connect (out of scope), taxes.

## Monthly estimate

| Line | Low | Base | High | Basis | Price source |
|---|---:|---:|---:|---|---|
| Site-to-site VPN (1 connection) | $36 | $36 | $36 | $0.05 per connection-hour | price list |
| Interface endpoints (Bedrock, Athena, Logs, plus AgentCore if used) | $22 | $29 | $73 | $0.01 per endpoint-AZ-hour. Low 3 endpoints x 1 AZ, base 4 x 1 AZ, high 5 x 2 AZ | price list |
| DMS Serverless | $10 | $29 | $79 | $0.0819 per DCU-hour. Low 2 DCU x 2 h/day, base 4 DCU x 3 h/day, high 8 DCU x 4 h/day | price list |
| Athena queries from the assistant | $2 | $4 | $20 | $5 per TB scanned. Low 0.3 TB, base 0.9 TB, high 4 TB per month | price list |
| Athena load job into S3 Tables | $2 | $2 | $5 | About 15 GB scanned per daily load x 30 days at $5 per TB | price list |
| Bedrock Claude (Sonnet class, US regional/cross-Region rate) | $56 | $191 | $653 | $3.30 in / $16.50 out per 1M tokens. Low 1,000 questions at 12k in / 1k out, base 1,650 at 25k / 2k, high 3,300 at 40k / 4k | Marketplace listing; model-to-price mapping not confirmed |
| AgentCore Runtime | $1 | $3 | $10 | $0.1276 per vCPU-hour and $0.0169 per GB-hour while active. About 40 s of 1 vCPU and 2 GB per question | price list |
| AgentCore Gateway and Policy | $0 | $1 | $2 | $0.000005 per Gateway call and $0.000025 per Policy check, about 6 calls per question | price list |
| AWS WAF (1 web ACL, 3 rules) | $8 | $9 | $9 | $5 per web ACL, $1 per rule, $0.60 per million requests | price list |
| API Gateway and Lambda (bot endpoint and tools) | $0 | $1 | $3 | Request-based, at pilot volume | price list |
| S3 staging and S3 Tables | $3 | $5 | $10 | S3 Tables storage $0.0253 per GB-month, compaction $0.005 per GB processed, plus staging bucket | price list |
| Secrets Manager (3 to 4 secrets) | $1 | $1 | $2 | $0.40 per secret-month | price list |
| KMS customer-managed keys (2 to 3) | $2 | $3 | $4 | About $1 per key-month | not verified |
| CloudWatch logs, dashboard, alarms | $5 | $10 | $25 | $0.50 per GB ingested plus a dashboard and alarms | logs from price list; dashboard and alarm prices not verified |
| Control Tower baseline (Config, org trail, Log Archive storage) | $10 | $20 | $40 | Mostly AWS Config recorded items across 3 accounts. No charge for Control Tower itself | not verified; depends on resource count |
| Bedrock Guardrails | $1 | $5 | $15 | Per text unit processed | not priced; placeholder |
| **Total per month** | **$161** | **$350** | **$986** | | |

## Over the POC (Nov 16 to Dec 24, about 1.3 months)

Build-phase services (VPN, DMS, endpoints, Control Tower baseline) start in Weeks 1 to 3. Assistant and Bedrock usage starts in Week 4. A rough POC total is about **$161 to $1,282**, with a base around **$420**. Treat this as an order of magnitude until usage data exists.

## What drives the number

1. Bedrock tokens: base $191 of $350 per month. Cost scales with questions per month and context size per question.
2. Fixed network costs: the VPN and interface endpoints (about $60 to $110 a month) bill whether or not anyone asks a question.
3. DMS: Serverless bills only while the load runs. Wider windows or bigger capacity raise it.

## Savings already assumed in the base case

- DMS Serverless instead of an always-on instance.
- Interface endpoints in one Availability Zone.
- Parquet tables and a 10 GB per-query Athena scan cutoff.
- Lambda and API Gateway instead of a container service.

## After the readout

If Mitsui keeps the environment running, the fixed lines (VPN, endpoints, WAF, Secrets, KMS, baseline) continue at roughly $90 to $140 a month, plus the daily DMS load and any usage. Pausing means stopping the DMS schedule. Tearing down uses the teardown scripts (F2 criterion 8).

## To finish before the readout

1. Replace assumed volumes with real figures: questions per month, tokens per question (Bedrock invocation logs), Athena bytes scanned, DMS DCU-hours (task history).
2. Confirm the Claude model and its price in the Bedrock console.
3. Price the unverified lines in the AWS Pricing Calculator.
4. Add Mitsui's support plan and any credits.
