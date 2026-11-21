#!/usr/bin/env python3
"""Preview or apply narrowly delegated demo changes and publish desired state."""

import argparse
import fcntl
import json
import os
import re
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import yaml
from guardrails import (
    ACCOUNT,
    ORIGIN,
    REGION,
    STACK,
    require,
    validate_loop_state,
    validate_plan,
    validate_request,
)


class Runner:
    def __init__(self, repo, profile=None):
        self.repo = repo.resolve()
        self.env = dict(os.environ)
        # Do not accidentally inherit the host's named profile inside ECS.
        self.env.pop("AWS_PROFILE", None)
        self.env.pop("AWS_DEFAULT_PROFILE", None)
        if profile:
            self.env["AWS_PROFILE"] = profile
        role = self.env.get("PCCD_AWS_ROLE_ARN")
        if role:
            require(
                role == f"arn:aws:iam::{ACCOUNT}:role/devops-demo-operations",
                "unexpected operations role",
            )
            assumed = self.aws(
                "sts",
                "assume-role",
                "--role-arn",
                role,
                "--role-session-name",
                "pcc-devops-demo",
                "--duration-seconds",
                "3600",
            )
            credentials = assumed["Credentials"]
            self.env.update(
                AWS_ACCESS_KEY_ID=credentials["AccessKeyId"],
                AWS_SECRET_ACCESS_KEY=credentials["SecretAccessKey"],
                AWS_SESSION_TOKEN=credentials["SessionToken"],
            )
            self.env.pop("AWS_PROFILE", None)
            self.env.pop("AWS_DEFAULT_PROFILE", None)

    def run(self, *args, timeout=600):
        return subprocess.run(
            list(args),
            cwd=self.repo,
            env=self.env,
            check=True,
            text=True,
            capture_output=True,
            timeout=timeout,
        ).stdout.rstrip("\n")

    def aws(self, *args):
        return json.loads(
            self.run("aws", "--region", REGION, *args, "--output", "json")
        )

    def git(self, *args):
        return self.run("git", *args)


def check_checkout(runner):
    require(
        Path(runner.git("rev-parse", "--show-toplevel")).resolve() == runner.repo,
        "wrong repository root",
    )
    require(
        runner.git("remote", "get-url", "origin") == ORIGIN,
        "wrong infrastructure origin",
    )
    require(
        runner.git("branch", "--show-current") == "main",
        "use the infrastructure main branch",
    )
    require(
        not runner.git("status", "--porcelain"),
        "checkout has unrelated/uncommitted work",
    )
    return runner.git("rev-parse", "HEAD")


def target_config(source, action, digest):
    config = yaml.safe_load(source)
    require(
        isinstance(config, dict) and isinstance(config.get("config"), dict),
        "missing stack config",
    )
    updated = json.loads(json.dumps(config))
    key, value = (
        ("imageDigest", digest)
        if action in {"deploy", "rollback"}
        else ("desiredCount", 0 if action == "suspend" else 1)
    )
    updated["config"][f"devops-demo:{key}"] = value
    runtime = json.loads(json.dumps(updated))
    runtime["config"].pop("aws:profile", None)
    require(runtime["config"].get("aws:region") == REGION, "wrong stack region")
    return updated, runtime


def verify_count(runner, expected):
    result = runner.aws(
        "ecs",
        "describe-services",
        "--cluster",
        "devops-demo",
        "--services",
        "devops-demo",
    )
    services = result["services"]
    require(len(services) == 1, "missing service")
    service = services[0]
    require(
        service["desiredCount"] == service["runningCount"] == expected
        and service["pendingCount"] == 0,
        "ECS count has not converged",
    )


def execute(args, runner):
    policy = json.loads(args.policy.read_text())
    identity = runner.aws("sts", "get-caller-identity")
    validate_request(args.action, args.digest, policy, identity, args.apply)
    if args.apply:
        validate_loop_state(
            args.action,
            args.digest,
            json.loads((args.state_dir / "loop-state.json").read_text()),
        )
    revision = check_checkout(runner)
    if args.apply:
        runner.git("fetch", "origin", "main")
        runner.git("merge", "--ff-only", "origin/main")
        revision = check_checkout(runner)
        require(
            revision == runner.git("rev-parse", "origin/main"),
            "main has unpublished local commits",
        )
    config_path = runner.repo / "Pulumi.devops-demo.yaml"
    original = config_path.read_text()
    updated, runtime = target_config(original, args.action, args.digest)
    if args.digest:
        images = runner.aws(
            "ecr",
            "describe-images",
            "--repository-name",
            "python-devops-demo",
            "--image-ids",
            f"imageDigest={args.digest}",
        )
        require(
            len(images["imageDetails"]) == 1, "eligible image is absent from demo ECR"
        )
    # A preview also exercises backend authentication and provider installation.
    with tempfile.TemporaryDirectory(prefix="devops-preview-") as folder:
        folder = Path(folder)
        runtime_path, plan_path = folder / "config.yaml", folder / "plan.json"
        runtime_path.write_text(yaml.safe_dump(runtime, sort_keys=False))
        runtime_path.chmod(0o600)
        runner.run(
            "pulumi",
            "preview",
            "--stack",
            STACK,
            "--config-file",
            str(runtime_path),
            "--save-plan",
            str(plan_path),
            "--non-interactive",
            "--refresh",
        )
        validate_plan(json.loads(plan_path.read_text()), args.action, args.digest)
        if not args.apply:
            return {
                "dry_run": True,
                "action": args.action,
                "digest": args.digest,
                "source_commit": revision,
                "plan_validated": True,
            }
        validate_loop_state(
            args.action,
            args.digest,
            json.loads((args.state_dir / "loop-state.json").read_text()),
        )
        require(
            check_checkout(runner) == revision and config_path.read_text() == original,
            "source changed after preview",
        )
        state = args.state_dir
        state.mkdir(parents=True, exist_ok=True, mode=0o700)
        receipt = state / f"operation-{args.operation_id}.json"
        require(
            not receipt.exists(),
            "operation ID already has a receipt; reconcile instead of replaying",
        )
        record = {
            "operation_id": args.operation_id,
            "action": args.action,
            "digest": args.digest,
            "reason": args.reason,
            "source_commit": revision,
            "created_at": datetime.now(UTC).isoformat(),
            "state": "applying",
        }
        # Keep the exact plan/evidence for reconciliation after a process failure.
        saved_plan = state / f"operation-{args.operation_id}.plan.json"
        saved_plan.write_bytes(plan_path.read_bytes())
        saved_plan.chmod(0o600)
        receipt.write_text(json.dumps(record, indent=2) + "\n")
        try:
            runner.run(
                "pulumi",
                "up",
                "--stack",
                STACK,
                "--config-file",
                str(runtime_path),
                "--plan",
                str(plan_path),
                "--non-interactive",
                "--yes",
                timeout=1200,
            )
            record["state"] = "applied_verification_pending"
            receipt.write_text(json.dumps(record, indent=2) + "\n")
            expected_count = updated["config"].get("devops-demo:desiredCount", 1)
            if expected_count == 1:
                runner.run(
                    "uv",
                    "run",
                    "--locked",
                    "python",
                    "scripts/verify.py",
                    "--wait-seconds",
                    "180",
                )
            else:
                verify_count(runner, 0)
            config_path.write_text(yaml.safe_dump(updated, sort_keys=False))
            require(
                runner.git("status", "--porcelain")
                in ("", " M Pulumi.devops-demo.yaml"),
                "unexpected source changes after apply",
            )
            runner.git("add", "--", "Pulumi.devops-demo.yaml")
            if runner.git("diff", "--cached", "--name-only"):
                runner.git("diff", "--cached", "--check")
                runner.git(
                    "commit",
                    "-m",
                    f"{args.action.capitalize()} demo: {args.operation_id}",
                )
            record["state"] = "verified_publication_pending"
            record["result_commit"] = runner.git("rev-parse", "HEAD")
            receipt.write_text(json.dumps(record, indent=2) + "\n")
            runner.git("push", "origin", "main")
            require(
                runner.git("ls-remote", "origin", "refs/heads/main").split()[0]
                == record["result_commit"],
                "remote parity not verified",
            )
            require(
                not runner.git("status", "--porcelain"),
                "checkout not clean after publication",
            )
            record["state"] = "complete"
        except Exception as error:
            record["error_type"] = type(error).__name__
            record["reconciliation_required"] = True
            raise
        finally:
            receipt.write_text(json.dumps(record, indent=2) + "\n")
        return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["deploy", "rollback", "suspend", "resume"])
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--digest")
    parser.add_argument("--profile", help="optional workstation profile; omit in ECS")
    parser.add_argument("--state-dir", type=Path, default=os.getenv("PCCD_STATE_DIR"))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--operation-id")
    parser.add_argument("--reason")
    args = parser.parse_args()
    if args.apply:
        require(args.state_dir is not None, "apply requires persistent state directory")
        require(
            args.operation_id
            and re.fullmatch(r"[a-zA-Z0-9_.-]{1,80}", args.operation_id),
            "bounded operation ID required",
        )
        require(args.reason and args.reason.strip(), "incident/change reason required")
        args.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (args.state_dir / "devops-demo.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            print(json.dumps(execute(args, Runner(args.repo, args.profile)), indent=2))
    else:
        print(json.dumps(execute(args, Runner(args.repo, args.profile)), indent=2))


if __name__ == "__main__":
    main()
