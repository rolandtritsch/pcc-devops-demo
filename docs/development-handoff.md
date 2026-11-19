# Development and Operations contract

## Ownership boundary

Development publishes immutable application artifacts and owns application code,
dependency upgrades, and migration implementation. Operations qualifies and runs
those artifacts, owns infrastructure/configuration, and returns defect evidence.
Operations may edit its IaC and runbooks; it does not patch application binaries
in production or rebuild a release locally under the same version.

Libraries are not independently deployed services. A library update reaches
production through an application build that declares its dependency versions.
Operations routes required library upgrades to Development unless a specific
runtime-loaded library mechanism is part of the service contract.

## Required release information

| Field | Purpose |
| --- | --- |
| Service, release ID, channel, source commit | Traceability and ordered eligibility |
| Image/package URIs and immutable digests | Exact deployment and rollback identity |
| Publisher identity, provenance, verification material | Artifact authenticity and origin |
| Dependency inventory / SBOM and security results | Exposure and policy evaluation |
| Required configuration and secret references | Repeatable runtime setup without secret values |
| Dependency/API/schema compatibility ranges | Mixed-version and rollout safety |
| Migration plan, reversibility, expand/contract requirements | Safe state transitions and rollback limits |
| Resource expectations and infrastructure prerequisites | Capacity and infrastructure planning |
| Health probes, synthetic journeys, acceptance tests | Operational qualification |
| Known issues, release notes, rollback procedure | Diagnosis and recovery readiness |

Reject incomplete release metadata with a concrete missing-field report. Database
changes need a coordinated migration contract: rolling back an image does not
undo a migration or restore lost data. Maintain a known-good deployment tuple of
image digests, config, IaC revision, dependency versions, and compatible schema.

## GitHub defect lifecycle

Use the [defect template][defect]. Search by correlation fingerprint and affected
release before creating an issue. Use a repository allowlist and a narrowly
scoped GitHub identity. Tickets contain sanitized summaries; restricted raw
evidence remains in controlled storage. Security findings go to the configured
private security channel/repository rather than a public issue.

Record observed impact, first/last seen, expected/actual behavior, affected
versions, reproducible steps or replay fixture, queries and timestamps,
mitigation, suspected cause with confidence, and acceptance criteria. Link
incident, release, trace, and evidence IDs without leaking tokens or tenant data.

Development owns implementing the fix and publishing a new artifact. Operations
owns runtime verification and the incident record. GitHub ticket closure alone
does not prove recovery or a deployed fix. Record the verified fixed digest and
post-deployment evidence before closing the operational follow-up.

If GitHub is unavailable, persist a local durable outbox, retain the incident
link, and retry delivery with an idempotency fingerprint. An outage recovery
must not depend on GitHub availability.

[defect]: ../templates/github-defect.md
