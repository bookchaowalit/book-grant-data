---
title: Project grants Data Product Charter
status: local-source-pilot
created: 2026-08-08
updated: 2026-08-08
tags: [template, data-engineering, data-product, governance]
description: Outcome, consumers, ownership, contract, quality, privacy, and operating boundary for a data product.
---

# Data Product Charter

## Document control

| Field | Value |
|---|---|
| Data product ID/version | book-grant-data / grant.v1 demo and grant.v2 source pilot |
| Product owner | bookchaowalit |
| Data owner/steward | bookchaowalit |
| Producer team | Domain repository |
| Status/review date | Local source pilot / 2026-09-07 |
| Evidence boundary | schema.json, demo.json and tests in this repository |

## Product contract

- Decision or user outcome: Find non-equity project funding and its reporting obligations.
- Consumers and use cases: Discovery applications; integration planned.
- Source systems and lake layers: Synthetic fixtures only today; permitted source → landing → Bronze planned.
- In scope/out of scope: Project funding calls; individual tuition goes to scholarship and cohort admission to startup-program.
- Freshness, availability, and volume expectation: Target source review every 24h; open filter rejects checks older than 72h; no live SLA.
- Data classification, residency, retention, and access: Public synthetic fixtures; no user profile; raw retention must be set per future source before ingestion.
- Quality thresholds and incident route: All contract tests pass; live quality/replay gates pending; owner handles source failures.
- Cost/capacity guardrail: Offline only, zero provider calls; max 10,000 records per envelope.
- Versioning, deprecation, and migration policy: Draft v1; breaking changes version separately; no legacy migration or live consumer yet.

## Acceptance and ownership

| Gate | Evidence | Owner | Result/status |
|---|---|---|---|
| Contract | Versioned schema and compatibility rules |  |  |
| Quality | Checks and threshold report |  |  |
| Lineage | Source-to-consumer map |  |  |
| Access/privacy | Classification and access review |  |  |
| Operations | Runbook, alert, replay, and recovery |  |  |

## Approval

| Role | Name/date | Decision |
|---|---|---|
| Product/data owner |  | Approve charter / revise |
| Producer owner |  | Accept delivery boundary |
| Consumer representative |  | Accept use and SLA |
