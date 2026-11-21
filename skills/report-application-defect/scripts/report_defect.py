#!/usr/bin/env python3
"""Render a sanitized defect, or explicitly publish it to the fixed demo repo."""

import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

REPO = "rolandtritsch/python-devops-demo"
FIELDS = ("impact", "expected", "actual", "mitigation")
ARRAYS = ("reproduction", "evidence", "acceptance")


def render(record: dict) -> tuple[str, str]:
    if not isinstance(record, dict):
        raise ValueError("record must be a JSON object")
    if record.get("category", "application") != "application":
        raise ValueError(
            "only sanitized application defects belong in this public repo"
        )
    fingerprint = record.get("fingerprint", "")
    if not isinstance(fingerprint, str) or not re.fullmatch(
        r"[a-zA-Z0-9_.:-]{3,128}", fingerprint
    ):
        raise ValueError("fingerprint must be a stable 3-128 character identifier")
    title = record.get("title", "")
    if not isinstance(title, str) or not 1 <= len(title) <= 180 or "\n" in title:
        raise ValueError("title must be a single nonempty line, at most 180 characters")
    digest = record.get("release_digest", "")
    if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError("release_digest must identify the observed immutable image")
    for name in FIELDS:
        if not isinstance(record.get(name), str) or not record[name].strip():
            raise ValueError(f"{name} must be a nonempty sanitized string")
    for name in ARRAYS:
        items = record.get(name)
        if (
            not isinstance(items, list)
            or not items
            or any(not isinstance(x, str) or not x.strip() for x in items)
        ):
            raise ValueError(f"{name} must contain sanitized evidence/steps/criteria")
    key = hashlib.sha256(fingerprint.encode()).hexdigest()
    marker = f"<!-- pcc-devops-defect:{key} -->"
    sections = [marker, f"Affected image: `{digest}`"]
    for name in (*FIELDS, *ARRAYS):
        value = record[name]
        body = (
            "\n".join(f"- {item}" for item in value)
            if isinstance(value, list)
            else value
        )
        sections.append(f"## {name.title()}\n\n{body}")
    body = "\n\n".join(sections) + "\n"
    if len(body) > 20000:
        raise ValueError("defect report exceeds bounded public report size")
    if re.search(
        r"-----BEGIN .*PRIVATE KEY|\b(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{12,}"
        r"|\b(?:AKIA|ASIA)[A-Z0-9]{16}|\bpul-[a-f0-9]{20,}",
        body + title,
    ):
        raise ValueError(
            "potential credential in public report; redact before publishing"
        )
    return key, body


def github(arguments: list[str], payload: dict | None = None):
    result = subprocess.run(
        ["gh", "api", *arguments],
        input=None if payload is None else json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        timeout=60,
    )
    return json.loads(result.stdout)


def find_existing(marker: str):
    for page in range(1, 11):
        issues = github([f"repos/{REPO}/issues?state=all&per_page=100&page={page}"])
        for issue in issues:
            if "pull_request" not in issue and marker in (issue.get("body") or ""):
                return issue
        if len(issues) < 100:
            return None
    raise RuntimeError("issue scan exceeded 1000 entries; reconcile before publication")


def publish(record: dict, state_dir: Path):
    key, body = render(record)
    marker = f"<!-- pcc-devops-defect:{key} -->"
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    receipt = state_dir / f"defect-{key}.json"
    with (state_dir / "github-defects.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        existing = find_existing(marker)
        if existing:
            result = {
                "state": "existing",
                "url": existing["html_url"],
                "issue_state": existing["state"],
            }
            receipt.write_text(json.dumps(result) + "\n")
            return result
        if receipt.exists():
            raise RuntimeError(
                "prior receipt exists without a matching issue; "
                "reconcile it before retrying"
            )
        receipt.write_text(
            json.dumps(
                {
                    "state": "creating",
                    "repository": REPO,
                    "fingerprint": record["fingerprint"],
                }
            )
            + "\n"
        )
        issue = github(
            [f"repos/{REPO}/issues", "--method", "POST", "--input", "-"],
            {"title": record["title"], "body": body},
        )
        result = {
            "state": "created",
            "url": issue["html_url"],
            "issue_state": issue["state"],
        }
        receipt.write_text(json.dumps(result) + "\n")
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--state-dir", type=Path, default=os.getenv("PCCD_STATE_DIR"))
    args = parser.parse_args()
    record = json.loads(args.record.read_text())
    _, body = render(record)
    if not args.apply:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "repository": REPO,
                    "title": record["title"],
                    "body": body,
                },
                indent=2,
            )
        )
        return
    if args.state_dir is None:
        parser.error(
            "--apply requires --state-dir or PCCD_STATE_DIR for durable receipts"
        )
    print(json.dumps(publish(record, args.state_dir)))


if __name__ == "__main__":
    main()
