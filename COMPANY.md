---
name: Dark DevOps Factory Demo
description: Operate an existing SaaS cloud deployment through bounded autonomous release, infrastructure, assurance, and recovery workflows.
slug: devops-demo
schema: agentcompanies/v1
version: 0.1.0
authors:
  - name: Roland Tritsch
goals:
  - Maintain service availability, data integrity, security, and performance within the agreed service contract
  - Converge production on the latest eligible verified release
  - Restore service through bounded infrastructure and deployment remediation
  - Send reproducible evidence-backed defects to the Development Factory through GitHub
  - Prove recovery readiness and report unknown or degraded monitoring coverage
---

The VP of Operations leads this Company. The board sets business objectives,
resource and spending boundaries, deployment scope, and risk acceptance.
Specialists operate within an executable service contract. The SRE acts as
Incident Commander and coordinates all changes during an incident.

The Development Factory owns application implementation and artifact publishing.
Operations owns the deployed service and its infrastructure. Operations can
restore service without waiting for an application repair, then validate and
deploy the repaired artifact through the normal release process.

This is a design-stage package. No cloud target, service-level objective,
credential scope, model runtime, or operational schedule has been configured.
All agents must follow `operations-contract`. Its policy requirements still
need implementation and integration testing before autonomous operation.
