# Organization and ownership

## Reporting structure

```mermaid
flowchart TD
    Board[Human board / service owner] --> VP[VP of Operations]
    VP --> Release[Release Engineer]
    VP --> Platform[Platform Engineer]
    VP --> IC[Incident Commander]
    VP --> Observe[Observability Engineer]
    VP --> Security[Security Engineer]
    VP --> Performance[Performance Engineer]
    Development[Development Factory] -->|Immutable artifacts and release contract| Release
    IC -->|Evidence-backed GitHub defects| Development
```

The VP is accountable for results, but does not approve each routine operation.
During incidents, the Incident Commander coordinates the specialists. The
board remains the escalation authority for actions outside delegated limits.

## Responsibilities

| Responsibility | Accountable agent | Supporting agents |
| --- | --- | --- |
| Service contract, priorities, exception ownership | VP of Operations | All specialists |
| Desired release and deployed artifact inventory | Release Engineer | Security, Incident Commander, Platform |
| Infrastructure and configuration desired state | Platform Engineer | Performance, Security |
| Incidents and customer-impact recovery | Incident Commander | All operational specialists |
| Metrics, logs, traces, probes, alert routing | Observability Engineer | Incident Commander, Performance |
| Security findings, test scope, containment guidance | Security Engineer | Platform, Release, Incident Commander |
| Performance qualification and capacity forecasts | Performance Engineer | Platform, Observability |
| Backup, restore, and stateful resource integrity, when applicable | Platform Engineer | Release, Incident Commander |
| Migration and rollback compatibility, when applicable | Release Engineer | Platform, Incident Commander |
| Unresolved factory work, budget, and escalation reviews | VP of Operations | Incident Commander |
| Telemetry pipelines, tool integrations, and delivery health | Observability Engineer | Platform, Incident Commander |
| Application defect tracking and acceptance | Incident Commander | Finding specialist, Release |

Each finding specialist owns evidence. Incident Commander owns the cross-factory defect
lifecycle and deduplication. A dedicated ticket-writing manager is unnecessary.
Infrastructure defects are normally repaired by Operations in its own IaC
repository; application defects are routed to Development. Unknown ownership
goes to the Incident Commander for triage rather than generating competing tickets.

## Continuous machinery versus agents

Health checks, telemetry ingestion, autoscaling, event delivery, deployment
controllers, policy checks, and emergency fallback run without LLM inference.
Paperclip coordinates durable tasks, ownership, scheduled reviews, and evidence.
The harness connects those tasks to tools and enforces the operating contract.

Use Paperclip's built-in run monitoring and liveness recovery for execution
health. Its [task watchdogs][task-watchdogs] are opt-in per issue and can use an
existing agent, such as the VP or Incident Commander, to review stopped work.
No separate monitoring agent is defined by this Company. These mechanisms still
need to be configured and verified for the deployed Paperclip version.

An external alert must have a deterministic path to recovery/on-call even if
Paperclip, the model provider, or its cloud environment is unavailable. Hosting
the only observer in the service's own failure domain is insufficient.

## Suggested first implementation

Define all seven roles now, but initially activate VP, Release, Platform,
Incident Commander, and Observability for one service. Add Security and
applicable recovery assurance before accepting production readiness. Performance
can initially run on demand. Independent external monitoring is required before
unattended operation. Dedicated roles can share a model runtime, but permissions
and action ownership remain distinct.

Use event-driven wakes and bounded scheduled reviews. Do not wake every agent
every minute or create tasks simply to keep agents busy.

[task-watchdogs]: https://docs.paperclip.ing/guides/projects-workflow/task-watchdogs/
