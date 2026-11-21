# Dark DevOps Factory

A Paperclip Company led by a **VP of Operations** that operates an existing
cloud-hosted SaaS system. The Development Factory publishes artifacts; this
Company owns deployment, infrastructure, service health, security operations,
performance, recovery, and evidence-backed feedback to Development.

**Status: initial design, November 19, 2026.** This repository contains a draft
Company package, role instructions, operating contracts, and demonstration
scenarios. Ticketing and guarded infrastructure helpers are implemented;
the execution environment remains to be selected. The Company has no deployed
agents, schedules, or autonomous remediation loop yet.

## Release/crash/rollback loop

The [concrete demo runbook][demo-loop] and [loop settings][loop-settings] specify
minute-based VP dispatch, Release Engineer as Release Manager, CloudWatch/ECS
monitoring by Observability, and incidents assigned to Incident Commander for
verified rollback. A read-only observer includes stopped tasks and crash logs;
the deployment helper checks shared freeze/quarantine state. The package stages
disabled heartbeat settings; the DevOps company is not deployed or activated.
New ECR pushes still need operator-policy eligibility before deployment.

## Agreed direction

- Operate an existing cloud deployment.
- Permit automatic releases and bounded remediation once their limits are
  configured and enforced.
- Restore service during incidents before pursuing a permanent application fix.
- Create GitHub issues for defects the Development Factory needs to fix.
- Run recurring security checks and scoped penetration exercises.

The proposed release objective is **the latest eligible, verified version**.
An unhealthy new release is quarantined; a known-good version can remain in
production while Development repairs it. Availability, security, and data
integrity take precedence over version freshness.

## Proposed Company

| Agent | Accountability |
| --- | --- |
| VP of Operations | Service objectives, priorities, budgets, risk, and escalation |
| Release Engineer | Artifact intake, staged rollout, promotion, and rollback |
| Platform Engineer | Infrastructure as code, configuration, capacity, and drift |
| Incident Commander | Incident ownership, diagnosis, recovery, and development handoff |
| Observability Engineer | Signals, service-level indicators, anomaly correlation, and alert quality |
| Security Engineer | Vulnerabilities, exposure, access, and scoped security testing |
| Performance Engineer | Latency, throughput, saturation, and capacity characterization |

These are responsibility boundaries. They need not all consume model calls on
a timer. Deterministic monitors and controllers perform continuous checks;
agents handle meaningful events, diagnosis, planning, and exceptional decisions.

## Read the design

- [Company charter][company] and [organization and ownership][organization].
- [Operational workflows][workflows] and [authority and enforcement][authority].
- [Development-to-Operations contract][handoff].
- [Security and performance testing cadence][assurance].
- [Decision log and questions][decisions].
- [Implementation stages and demo acceptance scenarios][roadmap].
- [Supporting references][sources].

The [service contract example][contract] lists the configuration needed before
the first deployment can be operated. Unknown values are deliberately unset.
The [templates][] define incident, release, and GitHub defect records.

## Concrete demonstration target

The selected target is [python-devops-demo][python-demo], a stateless Fibonacci
worker that chooses N in 0–99, logs the result and performance data, and waits
five seconds between calculations. [pulumi-devops-demo][pulumi-demo] provisions
private ECR, ECS/Fargate, CloudWatch logging, and the necessary IAM/security
group in AWS `eu-west-1`. It does not expose a public API or retain customer data.

The target's [baseline inventory][baseline] records the chosen cloud resources.
It is not an authorization policy or an agreed SLO. The Company remains inactive
until runtime bindings, action policy, objectives, and schedules are configured
and verified.

## Execution environment

The derived Paperclip Docker image was withdrawn on November 21, 2026.
This repository does not supply a custom runtime image. Tool provisioning,
credential delivery, and execution isolation remain to be designed and verified
before the Company is activated.

## Working with this repository

Start with the decision log and replace the service-contract placeholders with
verified facts. Keep role instructions under `agents/`, shared operating rules
under `skills/`, and design rationale under `docs/`. Keep credentials, customer
data, and raw production logs out of Git.

## Operational skills and runtime

| Skill | Assigned agents | Capability |
| --- | --- | --- |
| `operations-contract` | All agents | Shared operating rules |
| `observe-demo` | Release, Observability | Read-only ECR/ECS inventory and CloudWatch crash evidence |
| `report-application-defect` | Incident Commander | Validate, deduplicate, and publish sanitized application tickets to `python-devops-demo` |
| `manage-demo-infrastructure` | Platform, Release, Incident Commander | Infrastructure source changes, guarded Pulumi previews, existing-image deployment/rollback, and zero/one worker count |

The [runtime guide][runtime] describes required tools and credential bindings.
Provisioning those tools and credentials remains to be designed. No derived
Paperclip image is supplied. No Docker daemon is needed to operate already
published images.
Helpers default to rendering/preview; execution uses explicit delegated policy,
scoped credentials, persistent receipts, and a shared change lock. Infrastructure
source changes commit/push directly to `main`; cloud changes outside digest/count
bounds remain review-required.

`COMPANY.md` and `agents/*/AGENTS.md` follow the local Paperclip package
conventions. The shared `operations-contract` skill carries the minimum rules
that must travel with imported agents. It is an instruction contract, not an
implemented authorization mechanism.

The `.paperclip.yaml` extension stages disabled heartbeat settings, including a
60-second VP interval. Adapter/model choices, runtime paths, and secret bindings
remain to be configured. The local
Paperclip importer defaults unspecified adapters to `process`; do not treat
package discovery or successful import as runtime readiness. No Company import
or activation is part of this initial design work.

[company]: COMPANY.md
[organization]: docs/organization.md
[workflows]: docs/workflows.md
[authority]: docs/authority.md
[handoff]: docs/development-handoff.md
[assurance]: docs/assurance.md
[decisions]: docs/decisions.md
[roadmap]: docs/roadmap.md
[sources]: docs/sources.md
[contract]: config/service-contract.example.yaml
[templates]: templates/
[python-demo]: https://github.com/rolandtritsch/python-devops-demo
[pulumi-demo]: https://github.com/rolandtritsch/pulumi-devops-demo
[baseline]: config/demo-target.yaml
[runtime]: skills/manage-demo-infrastructure/references/runtime.md

[demo-loop]: docs/demo-loop.md
[loop-settings]: config/demo-loop.yaml
