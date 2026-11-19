# Dark DevOps Factory

A Paperclip Company led by a **VP of Operations** that operates an existing
cloud-hosted SaaS system. The Development Factory publishes artifacts; this
Company owns deployment, infrastructure, service health, security operations,
performance, recovery, and evidence-backed feedback to Development.

**Status: initial design, November 19, 2026.** This repository contains a draft
Company package, role instructions, operating contracts, and demonstration
scenarios. It does not yet contain cloud integrations, executable policy gates,
deployed agents, scheduled jobs, or a working remediation harness.

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
| Factory Watchdog | Independent observation of the operating Company's own health |

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
until the operating contract, executor, agent runtime, and integration work exist.

## Working with this repository

Start with the decision log and replace the service-contract placeholders with
verified facts. Keep role instructions under `agents/`, shared operating rules
under `skills/`, and design rationale under `docs/`. Keep credentials, customer
data, and raw production logs out of Git.

`COMPANY.md` and `agents/*/AGENTS.md` follow the local Paperclip package
conventions. The shared `operations-contract` skill carries the minimum rules
that must travel with imported agents. It is an instruction contract, not an
implemented authorization mechanism.

Adapter/model choices, runtime paths, secret bindings, and schedules will be
added in `.paperclip.yaml` after the target and runtime are known. The local
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
