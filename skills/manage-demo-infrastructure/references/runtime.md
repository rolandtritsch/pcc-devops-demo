# Execution environment requirements

The derived Paperclip image approach was withdrawn on November 21, 2026.
A replacement execution environment has not been selected. The helpers do not
activate the Company or grant cloud/backend permissions on their own.

## Toolchain

The future environment needs AWS CLI, Pulumi, uv, Python/PyYAML, Git, and gh.
The Dockerfile, image installer, tool lock, and image preflight were removed.
Tool installation, execution isolation, and credential delivery must be chosen
and verified before the Company is activated. Do not bake tokens, host CLI
logins, AWS profiles, Pulumi state, or infrastructure source into an image.

Provision a writable infrastructure checkout under
`/paperclip/workspaces/pulumi-devops-demo`, persistent operation state under
`PCCD_STATE_DIR`, and an operator-managed, read-only policy file outside the
agent-writable checkout. Copy `config/action-policy.example.json`, configure
eligible/nonquarantined digests and the allowed AWS caller, then enable its
mutation flag when binding the authorized runtime. Initialize the shared
`loop-state.json` from a verified baseline using [the demo loop][demo-loop];
apply fails closed if it is absent. The example flag is false
so importing a package cannot accidentally grant access.

## Credentials and state

- **GitHub:** repository-scoped Issues read/write for ticketing. Infrastructure
  source publication additionally needs Contents read/write on
  `rolandtritsch/pulumi-devops-demo`. Git must use a credential helper such as
  `gh auth setup-git`, with bot author identity configured in that checkout.
  Do not include credentials in origin URLs, files, receipts, or commit bodies.
- **AWS:** use ECS task-role credentials or a dedicated assumed operations role,
  with account and service/family restrictions. The Paperclip *execution* role
  pulls its image/logs; it does not grant the agents AWS privileges. The current
  Paperclip task role only has its existing exec/secret permissions and needs an
  explicit DevOps role binding before these actions work. `pulumi-paperclip`
  supports `enable_devops_demo` to create the scoped `devops-demo-operations`
  role and inject `PCCD_AWS_ROLE_ARN`; the helper assumes it per invocation.
- **Pulumi:** a token/service identity with access only to
  `rolandtritsch/devops-demo/devops-demo`, backend egress, and any required secret
  decryption access. The user supplied a token, stored through the encrypted
  `pulumi_access_token` setting in `pulumi-paperclip` and AWS Secrets Manager,
  with ECS injection as `PULUMI_ACCESS_TOKEN`. No token belongs in this package.
  Never mount the host's personal `~/.pulumi` credentials as a shortcut.
- **Dependencies:** `uv sync --locked` in the infrastructure checkout installs
  the pinned Python SDK/provider dependencies. The AWS Pulumi plugin is installed
  on first use; its cache must be writable and its download host reachable.
- **Profiles:** the committed config contains `aws:profile: roland`. The helper
  removes that key only from its temporary runtime config and uses the ECS
  credential chain. Local preview can explicitly pass `--profile roland`.
- **Verification compatibility:** publish the accompanying change in
  `pulumi-devops-demo/scripts/verify.py` before runtime cloning; it allows omitted
  `--profile` to use task-role credentials. Makefile's local `--profile roland`
  behavior is preserved.

CLI access and a helper are not complete process isolation. Agents sharing one
container/task role can reach the same credentials and bypass a Python wrapper
with a shell. IAM must constrain resources; a separate executor/identity boundary
is needed before asserting strong per-agent authorization. In this demo, the
helper guards accidental plan expansion, replay, and state drift. Its saved plan
is used for `pulumi up`; unrelated IAM, networking, log, registry, or service
configuration changes are rejected. Provider profile-only changes are permitted
to move from workstation authentication to task-role authentication.

## Narrow action examples

```bash
python3 skills/manage-demo-infrastructure/scripts/operations.py \
  rollback --repo /paperclip/workspaces/pulumi-devops-demo \
  --policy /paperclip/policies/devops-demo.json \
  --digest sha256:c8bedab999e6cb5104a4ad68c396cf5b759b97319c87c47c4397ee2de199188f
```

That produces a guarded preview. To execute an already delegated action, add
`--apply --operation-id INC-42-rollback-1 --reason "restore calculation freshness"`.
The operation ID is a persistent replay fence, not a retry counter. Keep the
same receipt for a single action; if an apply/publication response is ambiguous,
inspect the receipt, live ECS/Pulumi state, and Git before deciding what remains.

Do not run the image-building deployment script to roll back an existing
artifact. No Docker daemon/socket is required for these operating skills. The
image publication process stays with Development.

## Activation still needed

This repository supplies skill helpers, not a provisioned toolchain or live
Company deployment. Select an execution environment, bind scoped GitHub/AWS/Pulumi
identities, persistent checkout, policy and receipts, then import/configure the
Company. Verify connectivity and required permissions in that environment.
Never test activation by manufacturing a public defect or rolling back the live
worker without a real authorized reason.

[demo-loop]: ../../../docs/demo-loop.md
