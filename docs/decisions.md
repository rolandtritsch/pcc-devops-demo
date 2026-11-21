# Decisions and open questions

## November 19, 2026 — initial discussion

### Confirmed by the user

- Create `pcc-devops-demo` and populate it with the discussion's results.
- A separate Development Factory publishes libraries and container images.
- Operations is a Paperclip Company headed by the VP of Operations.
- The target is an existing cloud deployment.
- Delegate automatic bounded remediation and releases.
- Operate infrastructure, security, performance, and stability continuously.
- On severe incidents, first attempt deployment/infrastructure recovery.
- Send actionable defects to the Development Factory using GitHub tickets.
- Provide daily/weekly/monthly security assurance activities.

### Proposed design choices, open to refinement

- Interpret latest as latest eligible verified release, with quarantines,
  rollback, freshness measurement, and an error-budget release policy.
- Define seven operational roles; use Paperclip's built-in execution monitoring
  and opt-in task watchdogs rather than a dedicated Company monitoring agent.
- Assign incident command to the Incident Commander; serialize conflicting operational changes.
- Use deterministic continuous controls and a typed action executor. Agent
  prompts and Paperclip task ownership alone do not enforce cloud authority.
- Keep the initial package inactive until configuration and integrations exist.
- Separate routine scans from penetration exercises and document test coverage.
- Include data reliability and recovery exercises as first-class responsibilities.

### Questions asked, awaiting answers

1. What availability and calculation-cadence objectives, recovery-time target,
   and operational budget should the demo meet? It has no durable customer data
   and no public request/response latency objective.
2. Which restricted destination should receive security findings? Application
   defects can use `rolandtritsch/python-devops-demo`; infrastructure defects
   belong in `rolandtritsch/pulumi-devops-demo`.

## November 19, 2026 — concrete workload selected

The user requested a small Python worker in `python-devops-demo`: choose a random
N in 0–99, compute Fibonacci, log work/performance, and wait five seconds between
calculations. Create `pulumi-devops-demo` with a `devops-demo` stack, publish its
container to AWS ECR, and deploy it on ECS.

This refines the existing-cloud direction into a real AWS demo provisioned for
this purpose, rather than assuming another neighboring application's resources
are the target. AWS profile `roland`, account `519722017377`, region `eu-west-1`,
and the default VPC/subnet routes were verified before deployment.

Implementation choices: one 0.25-vCPU/512-MiB Fargate task, immutable digest,
CloudWatch JSON logs, loopback health/metrics endpoints, no inbound access,
no database, and no task-role AWS permissions. The workload is stateless;
missed calculations on replacement are disposable. Probe staleness is an
implemented threshold, not an agreed availability or recovery objective.

Cloud deployment does not activate the Operations Company. Role runtime,
executor bounds, GitHub routing, and SLOs remain separate implementation work.

Deployment was verified at 14:37 UTC: one HEALTHY task, completed rollout,
immutable image digest matching ECR/configuration, 24 correct recent calculations,
and no inbound security-group rules. The initial zlib finding was patched and
the replacement deployed; two HIGH glibc findings remain tracked in the
application repository. See the [deployment evidence][deployment]. No Company
activation or GitHub publication occurred.

## November 19, 2026 — public source publication authorized

The user requested public GitHub repositories for `pcc-devops-demo`,
`python-devops-demo`, and `pulumi-devops-demo`, with all current work committed
and pushed. Publish under `rolandtritsch`, use `main`, exclude generated/runtime
artifacts and credentials, and verify clean local/tracking/remote parity. Public
issue trackers are not a destination for sensitive security findings.

## November 19, 2026 — operational skills and runtime

The user requested application-ticket creation and infrastructure-change skills.
Selected implementation: a derived Paperclip image, direct infrastructure
commits/pushes to `main`, and automatic cloud actions limited to existing eligible
ECR digests plus zero/one desired worker. Other infrastructure applies require
review. The Incident Commander owns application tickets; Platform, Release, and
Incident Commander share the infrastructure skill.

The user also supplied a Pulumi token for `pulumi-paperclip`. Store it only as
encrypted stack configuration and in AWS Secrets Manager, then inject it into
ECS as `PULUMI_ACCESS_TOKEN`. The derived image contains tools and the Company
package, never the token. The operations role scopes AWS access to the demo;
helper checks constrain digest/count changes but do not provide process isolation.

### Further decisions for implementation

- Deployment environments and isolation; resource/data ownership boundaries.
- Recovery runbooks and rollback acceptance for the selected Pulumi/ECS tools.
- Release ordering/channel, maximum release lag, staging/canary support, and
  handling coordinated multi-service releases and schema changes.
- Exact allowed recovery actions, retry/cooldown windows, spending/scaling caps,
  and board exception/notification paths.
- Registry provenance/SBOM requirements and secrets/identity integration.
- Monitoring providers, baseline data, retention/redaction, and alert channels.
- Security test scope, production exclusions, and restricted finding destination.
- Paperclip runtime/adapter/models, schedules, and company operating budget.

No values or product names from neighboring projects have been assumed to be
the target. Existing cloud credentials are not authorization to mutate a stack.

## November 21, 2026 — withdraw the derived runtime image

The user rejected the derived Paperclip Docker image approach and requested its
removal. Remove the Dockerfile, image-specific installer, tool lock, preflight,
Docker build context exclusions, and runtime-image build target. The image
implementation was untracked, so it was removed before publication.

Operational helpers remain available locally. A replacement execution environment
has not been selected; tool provisioning, scoped identities, and isolation must
be designed and verified before activating the Company. This supersedes the
previous derived-image selection without choosing a replacement.

[deployment]: https://github.com/rolandtritsch/pulumi-devops-demo/blob/main/docs/deployment.md

## November 19, 2026 — minute-based release and rollback demo

The user requested ECR image discovery and deployment, intermittent-crash log
monitoring, and an incident assigned to Incident Commander to roll back to the
previous image. For now VP should wake Release Manager and log monitoring once
a minute. Release Engineer retains its slug and owns Release Manager duties;
Observability Engineer owns monitoring. Assignment wakes specialists because
agent-authenticated cross-agent heartbeat invocation is forbidden.

Added concrete role handoffs, disabled package heartbeat settings, demo loop
parameters/runbook, read-only stopped-task/log observation, and helper guards
for shared incident freeze/quarantine. The previous verified eligible digest is
preserved before deploying; a bad digest remains quarantined after recovery.
New pushes require policy eligibility, not merely ECR presence. Existing
uncommitted runtime/skill work was preserved.

Read-only Paperclip inspection found no deployed DevOps company. No company was
created, timer enabled, image published, cloud changed, or crash injected. Live
activation/acceptance remains necessary; role configuration alone is not proof
of the end-to-end recovery loop.
