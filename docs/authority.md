# Authority and enforcement

## Operating principle

The user selected automatic bounded remediation and releases. Once the service
contract is complete, its permitted actions proceed without repeated human
approval. Actions outside that contract require an explicit exception from the
board; missing scope or missing evidence does not expand authority.

The initial repository grants no live cloud or testing permissions. It defines
the authorization design to implement for the named deployment.

## Example delegation matrix

| Action | Proposed authority | Required evidence and limits |
| --- | --- | --- |
| Read telemetry and deployed inventory | Automatic | Named accounts, redacted output, bounded queries |
| Deploy a new eligible artifact | Automatic | Provenance, compatibility, staging/canary checks, healthy error budget |
| Roll back application deployment | Automatic | Known-good digest, schema compatibility, incident/change record |
| Restart unhealthy stateless tasks | Automatic | Named service, healthy dependency checks, retry/cooldown cap |
| Adjust replicas or instance capacity | Automatic | Defined min/max, cost ceiling, quota, stabilization window |
| Reapply known-good configuration/IaC | Automatic | Reviewed plan, no forbidden deletion, drift baseline, state lock |
| Execute a known failover | Automatic only when delegated | Fencing, data integrity checks, measured RPO/RTO, tested runbook |
| Rotate service credentials | Automatic only when delegated | Named secrets, dual-key transition, consumer verification, audit |
| Block abusive traffic or isolate workload | Automatic only when delegated | Scoped selectors, customer-impact bound, expiry and rollback |
| Run active security/load testing | Automatic within named scope | Target/environment allowlist, test identity, rate/time bounds, stop conditions |
| Destructive migration, data overwrite, or disaster restore | Exception by default | Explicit data-loss decision and recovery plan |
| Expand IAM, spend ceiling, account, or network exposure | Exception | Board decision; agent cannot enlarge its own authority |

These are proposed categories. Numeric caps, permitted runbooks, IAM resources,
and the particular SaaS's exceptions remain unset.

## Required enforcement outside prompts

1. Agents submit typed actions to an executor. Do not give every agent an
   unrestricted production shell or administrator credentials.
2. The executor verifies identity, target, permission, plan, action parameters,
   current state, service contract revision, expiry, and evidence requirements.
3. Use separate read, deploy, infrastructure, security-test, and data identities.
   Credentials are short-lived and constrained by cloud IAM and tool policy.
4. Serialize conflicting changes with a per-service/environment lease. IaC
   state locking alone does not coordinate deployments and incident recovery.
5. An incident freezes routine releases. The executor rejects stale plans and
   non-incident changes; emergency preemption explicitly transfers ownership.
6. Persist action IDs and idempotency keys. Replayed events and resumed agents
   must not repeat an already executed mutation.
7. Capture before/after state, tool results, policy decision, rollback, and cost.
   Persist outcomes across failed runs; never infer execution from model text.
8. Stop on exhausted retry/time/cost budgets. Escalate with evidence and retain
   deterministic emergency fallback and the board's kill switch.

Agent separation is useful for responsibility, but is not a security boundary
when agents share the same credentials, writable state, or executor privileges.

## Priority and exceptional security situations

Protect data integrity and security while restoring availability. A known
compromised previous image is not a valid rollback target. During a breach,
containment and evidence preservation may take precedence over restoring public
traffic. Incident Commander and Security coordinate the incident; a business tradeoff beyond
delegated authority escalates to the board.

Emergency console changes are recorded immediately and reconciled into IaC.
Routine drift reconciliation must not undo active incident mitigations.
