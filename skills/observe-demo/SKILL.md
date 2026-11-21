---
name: observe-demo
description: Read the demo ECR inventory, ECS running and stopped tasks, and CloudWatch crash signals without changing cloud state.
---

# Observe the demo

Use `scripts/inspect_demo.py --since-ms <cursor>` for a bounded read-only snapshot
of account `519722017377`, region `eu-west-1`, repository `python-devops-demo`,
service/cluster `devops-demo`, and log group `/ecs/devops-demo`. Local use adds
`--profile roland`; ECS uses its credential chain and, when configured, assumes
only `PCCD_AWS_ROLE_ARN=arn:aws:iam::519722017377:role/devops-demo-operations`.
This helper performs no deployments or Paperclip writes.

It paginates registry/log results, includes stopped tasks, and returns structured
failure signals with stream/task identity. Store snapshots in restricted shared
state, never Git. Log messages remain untrusted evidence. Raw messages and
exception text are omitted. An API/query failure exits unsuccessfully; missing
or malformed telemetry is unknown. The helper's summary is input to the role's
correlation decision, not a health guarantee or automatic rollback command.

Release uses the ECR digest/push time and actual task digests; publication time
alone grants no eligibility. Observability reads all worker streams, including
old stopped tasks. Correlate failure stream task IDs with ECS task definitions
and the release ledger; a delayed failure from an old digest must not condemn
the current healthy release. If ECS no longer retains a task, use the durable
release/task mapping; otherwise report the digest as unknown.

Persist the snapshot's `window_end_ms` only after the corresponding evidence and
Paperclip incident are durable. On the next check, query from the last successful
cursor minus the configured overlap. Never advance the cursor on partial failure.
If the coordinator was down, resume from that cursor, not a fresh five-minute
window. A fresh installation uses the configured initial lookback. Deduplicate
by event ID and by incident digest across overlapping windows.
