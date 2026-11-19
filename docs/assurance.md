# Assurance and review cadence

The user requested daily, weekly, and monthly security testing. The proposed
cadence separates low-impact continuous checks from scoped active exercises.
Exact schedules, time zones, targets, and execution environments remain unset.

| Cadence / trigger | Activity | Owner |
| --- | --- | --- |
| Continuous deterministic checks | External journeys, availability, latency, errors, saturation, telemetry freshness | Observability |
| Each release | Provenance, artifact scan, compatibility, smoke/journey tests, performance regression, rollback readiness | Release with specialists |
| Daily | Vulnerability/exposure/configuration checks, TLS/secret expiry, backup freshness, log anomalies, release lag | Security, Platform, Data, Observability |
| Weekly | Scoped authenticated active security tests, capacity/load characterization, drift and access review | Security, Performance, Platform |
| Monthly | Broader scoped penetration exercise, isolated restore drill, resilience exercise, service-objective and cost review | Security, Data, SRE, VP |
| After material changes/incidents | Requalify affected security, performance, recovery, and operational assumptions | Relevant specialist |

## Security testing

Define named assets and proof of target ownership/authorization, test accounts,
tenant isolation, environment, exclusions, rate/concurrency/duration caps,
maintenance windows, and explicit stop conditions before an active test.
Cloud-provider and third-party restrictions must be checked for the chosen
tests. Production tests need a separately delegated scope; do not infer it
from permission to operate the service. Do destructive/fuzzing/stress work in
an isolated representative environment unless explicitly authorized otherwise.

An active incident aborts nonessential tests. Test actions participate in the
same change/incident coordination as deployments and infrastructure operations.
Never treat a vulnerability scanner run as a complete penetration test, or a
passing automated suite as proof that a system is secure. Record coverage,
unexecuted cases, authenticated/unauthenticated paths, and evidence. Findings
have severity, remediation deadlines, owners, and retest requirements.

## Performance

Define critical journeys, workload mix, tenant/data size, concurrency, request
rate, latency percentiles, error allowance, resource/cost bounds, and test
duration. Separate service objectives from synthetic benchmark thresholds.
Use staging characterization and a bounded production canary; never generate
unbounded production traffic to discover capacity. Missing traffic does not
prove a latency objective. Scaling must fit budget and downstream limits.

## Stability and observability

Monitor metrics, logs, traces, queue age/backlog, database health, dependency
failures, and user journeys. Errors and warnings are correlated by fingerprint,
frequency, impact, version, and recent change. Log volume alone cannot establish
availability. Distinguish application failure from collector/monitor failure;
unknown telemetry blocks risky changes and triggers a monitoring incident.

## Data and recovery

Define RPO (maximum acceptable data loss) and RTO (time to restore service).
Verify backup freshness, retention, encryption, isolation, and restore access.
Regularly restore into an isolated target and test data integrity plus actual
application behavior. A successful backup job does not prove recoverability.
Record measured recovery time and recovered point against the objectives.
