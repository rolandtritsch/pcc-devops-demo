# Implementation stages and demo acceptance

## 1. Establish the service contract

Identify one existing cloud service, current IaC/deployment workflow, known-good
artifact, dependencies, objectives, recovery procedures, and delegated bounds.
Replace the service-contract placeholders. Capture a read-only baseline before
introducing a new controller. Define who owns each resource and data store.

Deliverable: populated contract, verified inventory, gap list, and action matrix.

## 2. Build the observer and action boundary

Integrate telemetry, inventory, release events, durable task/outbox state, and
GitHub. Implement typed policy-enforced actions with scoped credentials,
idempotency, leases, audit receipts, retry caps, and incident freezes. Wire
independent fallback alerting and deterministic recovery where appropriate.

Deliverable: read-only diagnosis and actionable tickets; denied/out-of-scope
actions proven to fail closed at the executor rather than only in prompts.

## 3. Qualify controlled releases and recovery

Add release reconciliation, provenance and compatibility checks, staging/canary
qualification, rollback/quarantine, and bounded infrastructure runbooks. Populate
`.paperclip.yaml` with the selected adapter configuration and initially disabled
schedules. Verify actual imported roles, credentials, and routines before
activation; import success alone is insufficient.

Deliverable: demonstrated release and recovery for the agreed target with
before/after evidence and measured impact within its service contract.

## 4. Complete ongoing assurance

Add security and performance exercises, backup/restore evidence, release-lag and
error-budget reporting, factory health observation, and postmortem feedback.
Exercise model, Paperclip, telemetry, GitHub, and cloud dependency failures.

Deliverable: unattended operation with measurable coverage and escalation paths.

## Acceptance scenarios

Run disruptive scenarios only in a named authorized test scope.

| Scenario | Required observable outcome |
| --- | --- |
| Healthy new artifact | Qualified rollout reaches expected digest with verification receipt |
| Release increases errors/latency | Candidate aborts/rolls back, bad digest quarantined, correlated defect recorded |
| Bad release event repeats | No duplicate rollout or duplicate defect |
| Event was missed | Periodic reconciliation discovers the eligible release |
| Schema-incompatible rollback | Image rollback denied; safe alternative or explicit escalation |
| Resource exhaustion | Capacity changes stay inside caps; customer journeys recover or escalation occurs |
| Active incident plus new release | Executor holds routine rollout; IC coordinates recovery |
| Missing telemetry | State is unknown, no blind promotion, monitoring failure escalated |
| Routine warning burst | Evidence-backed investigation without unjustified disruptive remediation |
| Out-of-scope action/test target | Executor denies it and records the policy reason |
| Broken backup | Restore drill detects failure and routes repair; no false recoverability claim |
| Budget/retry cap reached | Remediation stops and escalates without raising its own limits |
| GitHub unavailable | Durable defect outbox retries without delaying incident recovery |
| Development publishes repair | Fixed digest qualifies, deployed behavior is retested, follow-up is resolved |
| Paperclip/model unavailable | External detection and tested deterministic fallback/on-call still function |
| Restart after action completion | Durable receipts prevent replaying the mutation |

These are acceptance requirements, not tests that have already been executed.
