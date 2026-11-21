# Minute-based release and recovery demo

The requested sequence is: ECR push → Release Manager deploys → intermittent
worker crash → log detection → Paperclip incident assigned to Incident Commander
→ rollback to the previous verified image. Release Engineer owns the Release
Manager responsibility; Observability Engineer monitors the logs.

The roles now specify this sequence. This is **prepared configuration, not a
live demonstration**. A read-only Paperclip check on November 19, 2026 found no
DevOps company. No agents, timers, cloud changes, or fault injections were
activated by this update. [Loop settings][settings] are proposed demo defaults,
not business SLOs. They can be tuned before activation.

## Dispatch and task handoffs

Configure the VP's heartbeat at 60 seconds after binding a working adapter.
Specialists have no periodic timer; enable assignment wakes and one concurrent
run per agent. The [package extension][extension] stages these settings with all
heartbeats disabled. Import sanitizes heartbeat enablement, so verify real agent
runtime settings after activation. A disabled heartbeat also disables assignment
processing: enable the participating roles, with `intervalSec: 0` for specialists.

The VP creates bounded `todo` check issues assigned to Release and Observability
using `POST /api/companies/{companyId}/issues`. Include project, service/environment,
check kind, and a link to this runbook. Query open check issues by assignee and
kind before creating; retain an unfinished check rather than queueing every tick.
Serial VP runs avoid competing dispatchers. End each check after its decision or
handoff. Blocked checks need a visible owner and escalation, not duplicate work.

An agent cannot invoke another agent's `/heartbeat/invoke` or `/wakeup` endpoint
in the inspected Paperclip implementation. Assignment is the supported wake path.
The VP should not use a recurring routine assigned to another agent either:
agent-authenticated routine management is limited to self-assigned routines.

Observability creates a high-priority incident explicitly assigned to Incident
Commander. Release does the same immediately if rollout verification fails.
Deduplicate by service/environment/bad digest, including prior resolved incidents;
when an existing incident is open, append only meaningful new evidence. IC owns
recovery and the freeze. The VP never becomes an extra rollback approval gate.
Scheduling once a minute does not guarantee completion in a minute: agent queue,
inference, AWS, log delivery, and Pulumi each add latency.

## Shared durable state

All participating agents need a shared persistent `PCCD_STATE_DIR`. Maintain:

- `loop-state.json`: schema `pcc-devops-demo/loop-state-v1`, boolean
  `release_freeze`, and a `quarantined_digests` list. Create this explicitly as
  `{"schema":"pcc-devops-demo/loop-state-v1","release_freeze":false,"quarantined_digests":[]}`
  only after baseline verification. Never reset an existing state file on restart.
- A release ledger with candidate, running, previous verified and current
  known-good tuples; deployment time, task/digest history, IaC/config revisions,
  evidence, and linked Paperclip issue IDs. Candidate is distinct from known-good.
- A monitoring cursor and event IDs; advance only after durable incident delivery.
  Resume from the last successful cursor minus 120 seconds, including downtime.
- An incident index keyed by service/environment/bad digest; freeze owner,
  rollback target, operation ID, attempts, timeline, and verification outcome.
- Existing helper operation receipts and GitHub defect outbox receipts.

Update shared state atomically under the same `devops-demo.lock` used by the
infrastructure helper. On detection, acquire the lock, freeze and quarantine,
write atomically, then release it before calling the helper. If a rollout holds
the lock, persist pending detection evidence and retry the state update after
that action; inspect its receipt/current digest first. Never hold the lock across
a second helper invocation. Preserve freeze/quarantine through process restarts.
Paperclip issue status alone is not the durable cloud change lock.

The helper reads shared freeze/quarantine before applying and again after its
preview. It denies routine `deploy` while frozen and both deploy/rollback to a
quarantined digest. Rollback to another eligible digest is allowed during a
freeze. The operator policy's eligibility and quarantine restrictions still
apply. These guards prevent accidental misuse; shared-shell agents are not an
isolated authorization boundary. Ledger/cursor/task management remains work for
the instructed roles, not an implemented deterministic controller.

## Release and monitoring behavior

ECR discovery uses paginated image metadata ordered by `imagePushedAt`, with
immutable digests for identity. First verify the current baseline and record its
compatible rollback tuple. Deploy only existing policy-eligible images. The
current policy is an explicit digest allowlist: **a new push alone does not grant
eligibility**. An operator/trusted qualification workflow must add each candidate;
roles must not expand their own operator policy. Auto-qualifying arbitrary new
pushes is outside this implementation.

This one-worker demo uses the existing ECS rolling deployment, not a staging or
canary environment. Keep its count/resource bounds. Require 120 seconds of fresh
candidate behavior, at least three completions, correct actual digest, one healthy
unchanged task, and no candidate errors/exits/restarts before promotion. Continue
monitoring afterward; any finite window can miss a random crash.

The observer queries all log streams and RUNNING/STOPPED tasks. Detect explicit
`calculation_failed` errors/nonzero application exits even when ECS has already
restarted the worker. Track freshness on the current task (30-second demo limit),
and preserve historical task/digest mapping for old logs. Delayed old-release
errors must not roll back a different healthy digest. Query failures, malformed
logs, or unknown mappings remain coverage gaps. No monitoring cursor advances
past a failed delivery or partial query.

IC rolls back at most once to the preserved verified eligible digest, using the
infrastructure helper and a stable operation ID. Reconcile ambiguous receipts
rather than repeating a mutation. Verify the restored digest, completed rollout,
one healthy unchanged task, fresh calculations, and no new errors/restarts for
120 seconds with at least three completions. Persist quarantine, reconcile Git
and Pulumi, then lift the freeze. File the Development defect after stabilization.

## Activation and acceptance

Before enabling the VP timer, bind a real model/adapter, shared writable checkout
and state, read-only operator policy, AWS/GitHub/Pulumi credentials, project,
company/agent IDs, and escalation route. Enable mutations only for the delegated
scope and qualified candidate/rollback digests. Build/deploy the updated package
runtime and import/sync the role instructions and skill assignments; files on the
workstation do not update a running container or managed instructions bundle.
Verify tools and online reads, initialize the known-good baseline, then verify
assignment wakes and the actual VP interval through Paperclip.

Run a controlled acceptance exercise in the named demo environment:

1. Publish/qualify a healthy digest; verify one rollout and baseline promotion.
2. Development publishes/qualifies a deliberately intermittent-crash image.
   The current application logs uncaught calculation failures and exits, but has
   no deliberate random-fault switch. Operations must not edit application code
   to manufacture the faulty image.
3. Capture push, discovery, deploy, crash, detection, incident assignment, IC wake,
   rollback, and sustained recovery timestamps plus digests/tasks/receipts.
4. Repeat the event/check, restart the coordinator, and publish another image
   during the freeze. Prove no duplicate rollback or redeployment of the bad digest.
5. Exercise stale old-task errors, missing logs, denied eligibility, failed incident
   delivery, and ambiguous apply/publication. Each must retain safe state and a
   visible next owner rather than declare recovery.

Local tests cover observation and guard behavior. The live fault/rollback exercise
and its measured recovery time remain unverified until activation and execution.

[settings]: ../config/demo-loop.yaml
[extension]: ../.paperclip.yaml

## Verification for this update

`make check test` passed: lint/format checks and 30 tests, including stopped-task
crash evidence, duplicate events, malformed log redaction, query failure, persistent
quarantine, safe rollback during freeze, and denial before an apply can mutate.
YAML and assigned skill references were also validated.

A read-only observer snapshot at 16:09 UTC on November 19, 2026 found two ECR
images, one HEALTHY running worker at digest
`sha256:c8bedab999e6cb5104a4ad68c396cf5b759b97319c87c47c4397ee2de199188f`,
60 calculation completions in the preceding five minutes, no failure signals,
and no malformed log events. This confirms the observer's workstation read path;
it does not verify ECS runtime credentials or a disruptive recovery exercise.
