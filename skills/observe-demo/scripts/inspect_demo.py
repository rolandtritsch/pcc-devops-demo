#!/usr/bin/env python3
"""Read scoped demo inventory and crash evidence; never mutate the service."""

import argparse
import json
import os
import subprocess
import time

ACCOUNT = "519722017377"
REGION = "eu-west-1"


def collect(aws, since_ms, end_ms):
    identity = aws("sts", "get-caller-identity")
    if identity.get("Account") != ACCOUNT:
        raise ValueError("wrong AWS account")
    images = aws("ecr", "describe-images", "--repository-name", "python-devops-demo")
    service = aws(
        "ecs",
        "describe-services",
        "--cluster",
        "devops-demo",
        "--services",
        "devops-demo",
    )
    if service.get("failures") or len(service.get("services", [])) != 1:
        raise ValueError("missing demo service")
    tasks = []
    for status in ("RUNNING", "STOPPED"):
        arns = aws(
            "ecs",
            "list-tasks",
            "--cluster",
            "devops-demo",
            "--service-name",
            "devops-demo",
            "--desired-status",
            status,
        )["taskArns"]
        for offset in range(0, len(arns), 100):
            batch = aws(
                "ecs",
                "describe-tasks",
                "--cluster",
                "devops-demo",
                "--tasks",
                *arns[offset : offset + 100],
            )
            if batch.get("failures"):
                raise ValueError("incomplete ECS task inventory")
            tasks.extend(batch["tasks"])
    # Do not filter only ERROR: completion freshness and malformed logs matter too.
    events = aws(
        "logs",
        "filter-log-events",
        "--log-group-name",
        "/ecs/devops-demo",
        "--start-time",
        str(since_ms),
        "--end-time",
        str(end_ms),
    )["events"]
    return {
        "window_start_ms": since_ms,
        "window_end_ms": end_ms,
        "images": images["imageDetails"],
        "service": service["services"][0],
        "tasks": tasks,
        "signals": summarize(events),
    }


def summarize(events):
    signals = {"failures": [], "completed_by_stream": {}, "malformed_events": 0}
    seen = set()
    for event in events:
        event_id = event["eventId"]
        if event_id in seen:
            continue
        seen.add(event_id)
        try:
            message = json.loads(event["message"])
            if not isinstance(message, dict):
                raise ValueError("non-object log")
        except (ValueError, TypeError):
            signals["malformed_events"] += 1
            continue
        stream = event["logStreamName"]
        if message.get("event") == "calculation_failed" or message.get("level") in {
            "ERROR",
            "CRITICAL",
            "FATAL",
        }:
            signals["failures"].append(
                {
                    "event_id": event_id,
                    "stream": stream,
                    "timestamp_ms": event["timestamp"],
                    "event": message.get("event"),
                }
            )
        if message.get("event") == "calculation_completed":
            completed = signals["completed_by_stream"].setdefault(
                stream, {"count": 0, "last_timestamp_ms": 0}
            )
            completed["count"] += 1
            completed["last_timestamp_ms"] = max(
                completed["last_timestamp_ms"], event["timestamp"]
            )
    return signals


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile")
    parser.add_argument("--since-ms", required=True, type=int)
    args = parser.parse_args()
    end_ms = int(time.time() * 1000)
    if not 0 <= args.since_ms < end_ms:
        raise ValueError("invalid observation window")
    env = dict(os.environ)
    env.pop("AWS_PROFILE", None)
    env.pop("AWS_DEFAULT_PROFILE", None)
    if args.profile:
        env["AWS_PROFILE"] = args.profile

    def aws(*parts):
        # AWS CLI automatically paginates; do not use --max-items/--no-paginate.
        result = subprocess.run(
            ["aws", "--region", REGION, "--output", "json", *parts],
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return json.loads(result.stdout)

    role = env.get("PCCD_AWS_ROLE_ARN")
    if role:
        if role != f"arn:aws:iam::{ACCOUNT}:role/devops-demo-operations":
            raise ValueError("unexpected operations role")
        credentials = aws(
            "sts",
            "assume-role",
            "--role-arn",
            role,
            "--role-session-name",
            "pcc-devops-observer",
        )["Credentials"]
        env.update(
            AWS_ACCESS_KEY_ID=credentials["AccessKeyId"],
            AWS_SECRET_ACCESS_KEY=credentials["SecretAccessKey"],
            AWS_SESSION_TOKEN=credentials["SessionToken"],
        )
        env.pop("AWS_PROFILE", None)
    print(json.dumps(collect(aws, args.since_ms, end_ms), indent=2))


if __name__ == "__main__":
    main()
