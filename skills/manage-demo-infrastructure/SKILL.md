---
name: manage-demo-infrastructure
description: Edit and publish pulumi-devops-demo infrastructure changes, preview cloud plans, and deploy or roll back approved existing ECR digests or suspend/resume the single demo ECS task.
---

# Manage demo infrastructure

The target is only `rolandtritsch/pulumi-devops-demo`, stack
`rolandtritsch/devops-demo/devops-demo`, account `519722017377`, region
`eu-west-1`. The Python application is owned by Development. Report its defects
with `report-application-defect`; do not repair application code here.

Read [runtime setup][runtime] before first use. The selected execution environment
needs AWS CLI, Pulumi, uv, Python/PyYAML, Git, and gh; authenticated backend
access; the infrastructure checkout; and a scoped AWS role. A workstation AWS
profile is not a portable ECS credential. The helper sanitizes the runtime
config copy while preserving the repository's local profile setting.

## Existing artifact operations

Use `scripts/operations.py` from this skill directory. Provide `--repo` with the
infrastructure checkout, `--policy` with the operator-managed action policy, and
`--state-dir` with persistent shared state. `deploy` and `rollback` require an
explicit eligible `--digest`; `suspend` and `resume` select zero or one worker.
No operation builds or publishes an application image, changes IAM/networking,
or allows scaling beyond one steady-state task. Rolling deployment can briefly
have two tasks, as defined by the existing stack.

Default execution creates and checks a saved Pulumi preview without applying.
`--apply --operation-id <id> --reason <text>` executes that plan only when the
operator policy enables mutations and the caller identity is allowed. Leases,
receipts, source-state checks, existing-image eligibility, and narrow resource
diff checks prevent accidental replay or a broader apply. Retain plan and
receipts in restricted state storage. No raw secrets or customer logs in Git.

After a successful apply, the helper updates only `imageDigest` or `desiredCount`
in the tracked stack config and commits/pushes directly to `main`, as requested
by the user. A failed verification or Git publication remains an explicit
reconciliation state; do not repeat the cloud action to fix a push failure.
Do not use `scripts/deploy.py`: that builds application images and defaults to a
workstation profile. Do not use `aws ecs update-service` for ordinary rollback;
it leaves Pulumi/Git desired state out of sync.

Apply also requires `loop-state.json` in the shared state directory, initialized
from a verified baseline as described in [the demo loop][demo-loop]. The helper
checks persistent incident freeze and quarantine before applying and after
preview. Routine deploy is denied while frozen; rollback to an eligible,
nonquarantined digest remains allowed. Keep state updates atomic under the same
change lock. Never reset quarantine to make a release pass.

During incidents, the Incident Commander owns the action and change lease.
Quarantined/ineligible images remain prohibited even when they ran previously.
The original unpatched zlib image is quarantined in the example policy.

## Other infrastructure source changes

Use a clean `main` checkout with the exact origin above. Fetch and fast-forward;
never discard unrelated work or force-push. Make the smallest change, run
`make check test`, and capture a full-stack Pulumi preview with runtime role
credentials. Changes outside digest/count bounds require review before cloud
apply, even when the source change can be committed/pushed to `main`. The user
selected direct commits rather than PRs for this repository. Record source
commit, preview findings, review requirement, and verification in Paperclip.

For approved broader applies, use a separately authorized workflow; this helper
deliberately rejects them. Source publication alone does not authorize changes
to AWS or the Paperclip control plane. Never delete state, destroy the stack,
grant the Company new permissions, or raise budget/scale limits through this skill.

[runtime]: references/runtime.md

[demo-loop]: ../../docs/demo-loop.md
