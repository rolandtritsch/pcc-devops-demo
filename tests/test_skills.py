"""Check defect publication and narrow plan enforcement without external writes."""

import copy
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
INFRA = ROOT / "skills/manage-demo-infrastructure/scripts"
sys.path.insert(0, str(INFRA))
from guardrails import ACCOUNT, REGISTRY, validate_plan, validate_request  # noqa: E402
from operations import target_config  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "report_defect", ROOT / "skills/report-application-defect/scripts/report_defect.py"
)
ticket = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ticket)
DIGEST = "sha256:" + "a" * 64
IDENTITY = {
    "Account": ACCOUNT,
    "Arn": f"arn:aws:sts::{ACCOUNT}:assumed-role/devops-demo-operations/test",
}
POLICY = {
    "schema": "pcc-devops-demo/actions-v1",
    "mutations_enabled": True,
    "allowed_caller_arn_patterns": [
        f"arn:aws:sts::{ACCOUNT}:assumed-role/devops-demo-operations/*"
    ],
    "eligible_digests": [DIGEST],
    "quarantined_digests": [],
}


def defect():
    return {
        "fingerprint": "demo.calculation.failure",
        "title": "Calculation loop stops",
        "release_digest": DIGEST,
        "impact": "No completion events",
        "expected": "Continue every five seconds",
        "actual": "Observed an exception",
        "mitigation": "Previous eligible image retained",
        "reproduction": ["Run the supplied fixture"],
        "evidence": ["Sanitized incident trace"],
        "acceptance": ["Fixture completes and deployed loop remains healthy"],
    }


def task_plan(extra=None):
    old = [
        {
            "name": "devops-demo",
            "image": REGISTRY + "@sha256:" + "b" * 64,
            "readonlyRootFilesystem": True,
        }
    ]
    new = copy.deepcopy(old)
    new[0]["image"] = REGISTRY + "@" + DIGEST
    if extra:
        new[0].update(extra)
    urn = (
        "urn:pulumi:devops-demo::devops-demo::"
        "aws:ecs/taskDefinition:TaskDefinition::devops-demo"
    )
    return {
        "resourcePlans": {
            urn: {
                "steps": ["create-replacement", "replace", "delete-replaced"],
                "goal": {
                    "type": "aws:ecs/taskDefinition:TaskDefinition",
                    "name": "devops-demo",
                    "inputDiff": {"updates": {"containerDefinitions": json.dumps(new)}},
                },
                "state": {"containerDefinitions": json.dumps(old)},
            }
        }
    }


def test_defect_dry_render_is_network_free():
    with patch.object(ticket, "github", side_effect=AssertionError("network")):
        key, body = ticket.render(defect())
    assert key in body and DIGEST in body
    assert "Sanitized incident trace" in body


@pytest.mark.parametrize(
    "change",
    [
        {"category": "security"},
        {"release_digest": "latest"},
        {"evidence": []},
        {"actual": "-----BEGIN PRIVATE KEY-----"},
    ],
)
def test_incomplete_sensitive_or_mutable_ticket_rejected(change):
    value = defect()
    value.update(change)
    with pytest.raises(ValueError):
        ticket.render(value)


def test_existing_closed_issue_is_returned_without_a_new_write(tmp_path):
    _, body = ticket.render(defect())
    existing = {
        "body": body,
        "html_url": "https://github.com/example/issues/1",
        "state": "closed",
    }
    with patch.object(ticket, "github", return_value=[existing]) as api:
        result = ticket.publish(defect(), tmp_path)
    assert result["state"] == "existing" and result["issue_state"] == "closed"
    assert api.call_count == 1


def test_ambiguous_creation_cannot_be_blindly_repeated(tmp_path):
    with patch.object(ticket, "github", side_effect=[[], RuntimeError("network lost")]):
        with pytest.raises(RuntimeError, match="network lost"):
            ticket.publish(defect(), tmp_path)
    with patch.object(ticket, "github", return_value=[]) as api:
        with pytest.raises(RuntimeError, match="reconcile"):
            ticket.publish(defect(), tmp_path)
    assert api.call_count == 1


def test_new_issue_uses_structured_payload_and_keeps_receipt(tmp_path):
    created = {"html_url": "https://github.com/example/issues/2", "state": "open"}
    with patch.object(ticket, "github", side_effect=[[], created]) as api:
        result = ticket.publish(defect(), tmp_path)
    assert result["state"] == "created"
    arguments, payload = api.call_args.args
    assert "POST" in arguments and payload["title"] == defect()["title"]
    assert DIGEST in payload["body"]
    receipt = json.loads(next(tmp_path.glob("defect-*.json")).read_text())
    assert receipt["url"] == created["html_url"]


def test_narrow_digest_replacement_allowed():
    validate_request("rollback", DIGEST, POLICY, IDENTITY, True)
    validate_plan(task_plan(), "rollback", DIGEST)


@pytest.mark.parametrize(
    "change",
    [
        {"readonlyRootFilesystem": False},
        {"environment": [{"name": "DANGEROUS", "value": "1"}]},
    ],
)
def test_image_change_cannot_smuggle_container_changes(change):
    with pytest.raises(ValueError, match="more than the image"):
        validate_plan(task_plan(change), "deploy", DIGEST)


def test_count_action_cannot_replace_image():
    with pytest.raises(ValueError, match="count action"):
        validate_plan(task_plan(), "suspend", None)


@pytest.mark.parametrize(
    "modification",
    [
        {"mutations_enabled": False},
        {"eligible_digests": []},
        {"quarantined_digests": [DIGEST]},
    ],
)
def test_disabled_ineligible_or_quarantined_request_rejected(modification):
    policy = {**POLICY, **modification}
    with pytest.raises(ValueError):
        validate_request("deploy", DIGEST, policy, IDENTITY, True)


def test_wrong_identity_rejected():
    with pytest.raises(ValueError):
        validate_request("deploy", DIGEST, POLICY, {"Account": "other"}, True)
    with pytest.raises(ValueError):
        validate_request(
            "deploy", DIGEST, POLICY, {"Account": ACCOUNT, "Arn": "arn:personal"}, True
        )


def test_unrelated_cloud_resource_change_rejected():
    plan = task_plan()
    plan["resourcePlans"][
        "urn:pulumi:devops-demo::devops-demo::aws:ec2/securityGroup:SecurityGroup::devops-demo"
    ] = {
        "steps": ["update"],
        "goal": {"type": "aws:ec2/securityGroup:SecurityGroup", "name": "devops-demo"},
    }
    with pytest.raises(ValueError, match="undelegated"):
        validate_plan(plan, "deploy", DIGEST)


def test_runtime_profile_removed_without_rewriting_source_profile():
    source = "config:\n  aws:profile: roland\n  aws:region: eu-west-1\n"
    updated, runtime = target_config(source, "suspend", None)
    assert updated["config"]["aws:profile"] == "roland"
    assert "aws:profile" not in runtime["config"]
    assert runtime["config"]["devops-demo:desiredCount"] == 0


@pytest.mark.parametrize("count,allowed", [(0, True), (1, False), (2, False)])
def test_suspend_plan_cannot_resume_or_scale_out(count, allowed):
    urn = "urn:pulumi:devops-demo::devops-demo::aws:ecs/service:Service::devops-demo"
    plan = {
        "resourcePlans": {
            urn: {
                "steps": ["update"],
                "goal": {
                    "type": "aws:ecs/service:Service",
                    "name": "devops-demo",
                    "inputDiff": {"updates": {"desiredCount": count}},
                },
            }
        }
    }
    if allowed:
        validate_plan(plan, "suspend", None)
    else:
        with pytest.raises(ValueError):
            validate_plan(plan, "suspend", None)
