"""Validate the small subset of Pulumi changes delegated to demo Operations."""

import copy
import fnmatch
import json
import re

ACCOUNT = "519722017377"
REGION = "eu-west-1"
STACK = "rolandtritsch/devops-demo/devops-demo"
ORIGIN = "https://github.com/rolandtritsch/pulumi-devops-demo.git"
REGISTRY = f"{ACCOUNT}.dkr.ecr.{REGION}.amazonaws.com/python-devops-demo"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_request(action, digest, policy, identity, applying):
    require(
        policy.get("schema") == "pcc-devops-demo/actions-v1",
        "unsupported action policy",
    )
    require(identity.get("Account") == ACCOUNT, "wrong AWS account")
    require(action in {"deploy", "rollback", "suspend", "resume"}, "unsupported action")
    if action in {"deploy", "rollback"}:
        require(
            isinstance(digest, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", digest),
            "immutable digest required",
        )
        require(
            digest in policy.get("eligible_digests", []),
            "image has no eligibility approval",
        )
        require(
            digest not in policy.get("quarantined_digests", []), "image is quarantined"
        )
    else:
        require(digest is None, "count changes cannot also change the image")
    if applying:
        require(
            policy.get("mutations_enabled") is True,
            "operator policy disables mutations",
        )
        require(
            any(
                fnmatch.fnmatchcase(identity.get("Arn", ""), pattern)
                for pattern in policy.get("allowed_caller_arn_patterns", [])
            ),
            "AWS caller is not delegated by the action policy",
        )


def validate_loop_state(action, digest, state):
    """Honor persistent incident state in addition to operator eligibility."""
    require(
        state.get("schema") == "pcc-devops-demo/loop-state-v1",
        "missing or unsupported shared loop state",
    )
    require(type(state.get("release_freeze")) is bool, "missing release freeze state")
    quarantine = state.get("quarantined_digests")
    require(
        isinstance(quarantine, list)
        and all(
            isinstance(value, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", value)
            for value in quarantine
        ),
        "invalid shared quarantine state",
    )
    if action == "deploy":
        require(not state["release_freeze"], "routine release is frozen by incident")
    if action in {"deploy", "rollback"}:
        require(digest not in quarantine, "image is quarantined in shared loop state")


def validate_plan(plan, action, digest):
    """Reject every resource/input mutation beyond the selected image or count."""
    resources = plan.get("resourcePlans")
    require(isinstance(resources, dict) and resources, "missing resource plan")
    for urn, resource in resources.items():
        require(
            urn.startswith("urn:pulumi:devops-demo::devops-demo::"),
            "plan targets another stack",
        )
        steps = resource.get("steps", [])
        if steps == ["same"]:
            continue
        goal = resource.get("goal") or {}
        kind = goal.get("type")
        diff = goal.get("inputDiff") or {}
        updates = diff.get("updates", {})
        adds, deletes = diff.get("adds", {}), diff.get("deletes", [])
        keys = set(updates) | set(adds) | set(deletes)
        if kind == "pulumi:pulumi:Stack":
            require(
                set(steps) <= {"same", "update"} and not keys,
                "unexpected stack mutation",
            )
            continue
        if kind == "pulumi:providers:aws":
            require(
                set(steps) <= {"same", "update"} and keys <= {"profile"},
                "provider scope/credentials changed unexpectedly",
            )
            continue
        require(goal.get("name") == "devops-demo", "unexpected resource identity")
        require(not adds and not deletes, "resource inputs added/deleted outside scope")
        if kind == "aws:ecs/service:Service":
            require(
                steps == ["update"],
                "service creation/replacement/deletion is not delegated",
            )
            if action in {"deploy", "rollback"}:
                require(
                    keys <= {"taskDefinition"}, "service changes exceed image rollout"
                )
            else:
                require(keys == {"desiredCount"}, "count action changed other inputs")
                require(
                    updates["desiredCount"] == (0 if action == "suspend" else 1),
                    "wrong desired count",
                )
        elif kind == "aws:ecs/taskDefinition:TaskDefinition":
            require(
                action in {"deploy", "rollback"},
                "count action cannot replace task definition",
            )
            require(
                steps
                in (["create-replacement", "replace", "delete-replaced"], ["update"]),
                "unexpected task definition lifecycle",
            )
            require(keys == {"containerDefinitions"}, "task inputs exceed image change")
            old = json.loads(resource["state"]["containerDefinitions"])
            new = json.loads(updates["containerDefinitions"])
            expected = copy.deepcopy(old)
            require(
                len(expected) == 1 and expected[0].get("name") == "devops-demo",
                "unexpected container layout",
            )
            expected[0]["image"] = f"{REGISTRY}@{digest}"
            require(new == expected, "task change modifies more than the image")
        else:
            raise ValueError(f"cloud plan changes undelegated resource type: {kind}")
