"""Exercise crash detection and incident guards without cloud mutations."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/manage-demo-infrastructure/scripts"))
from guardrails import validate_loop_state  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "inspect_demo", ROOT / "skills/observe-demo/scripts/inspect_demo.py"
)
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)
GOOD = "sha256:" + "a" * 64
BAD = "sha256:" + "b" * 64


def event(identifier, stream, message, timestamp=1000):
    return {
        "eventId": identifier,
        "logStreamName": stream,
        "message": message,
        "timestamp": timestamp,
    }


def state(frozen=False, quarantine=None):
    return {
        "schema": "pcc-devops-demo/loop-state-v1",
        "release_freeze": frozen,
        "quarantined_digests": quarantine or [],
    }


def test_crash_survives_restart_and_blocks_redeployment():
    crash = event("failure", "worker/stopped", '{"event":"calculation_failed"}')
    signals = observer.summarize(
        [
            crash,
            crash,
            event("ok", "worker/replacement", '{"event":"calculation_completed"}'),
        ]
    )
    assert len(signals["failures"]) == 1
    assert signals["failures"][0]["stream"] == "worker/stopped"
    assert signals["completed_by_stream"]["worker/replacement"]["count"] == 1
    incident_state = state(True, [BAD])
    with pytest.raises(ValueError, match="frozen"):
        validate_loop_state("deploy", GOOD, incident_state)
    validate_loop_state("rollback", GOOD, incident_state)
    with pytest.raises(ValueError, match="quarantined"):
        validate_loop_state("rollback", BAD, incident_state)
    incident_state["release_freeze"] = False
    with pytest.raises(ValueError, match="quarantined"):
        validate_loop_state("deploy", BAD, incident_state)


def test_malformed_or_raw_logs_do_not_leak_exception_text():
    signals = observer.summarize(
        [
            event("bad", "worker/old", "Traceback: secret"),
            event("array", "worker/old", "[]"),
            event("error", "worker/old", '{"level":"ERROR","error":"secret"}'),
        ]
    )
    assert signals["malformed_events"] == 2
    assert len(signals["failures"]) == 1
    assert "secret" not in str(signals)


def test_collect_queries_stopped_tasks_and_full_log_window():
    def aws(*parts):
        if parts[:2] == ("sts", "get-caller-identity"):
            return {"Account": observer.ACCOUNT}
        if parts[:2] == ("ecr", "describe-images"):
            return {"imageDetails": []}
        if parts[:2] == ("ecs", "describe-services"):
            return {"services": [{"runningCount": 1}]}
        if parts[:2] == ("ecs", "list-tasks"):
            return {"taskArns": [parts[-1]]}
        if parts[:2] == ("ecs", "describe-tasks"):
            return {"tasks": [{"taskArn": parts[-1]}]}
        if parts[:2] == ("logs", "filter-log-events"):
            assert "--log-stream-names" not in parts
            assert parts[-4:] == ("--start-time", "100", "--end-time", "200")
            return {"events": []}
        raise AssertionError(parts)

    snapshot = observer.collect(aws, 100, 200)
    assert {t["taskArn"] for t in snapshot["tasks"]} == {"RUNNING", "STOPPED"}
    assert snapshot["window_end_ms"] == 200


def test_query_failure_cannot_return_successful_snapshot():
    with pytest.raises(RuntimeError, match="unavailable"):
        observer.collect(Mock(side_effect=RuntimeError("unavailable")), 100, 200)


@pytest.mark.parametrize(
    "value",
    [{}, {"release_freeze": False}, state("false"), state(quarantine=["latest"])],
)
def test_missing_or_invalid_state_fails_closed(value):
    with pytest.raises(ValueError):
        validate_loop_state("deploy", GOOD, value)


def test_apply_honors_incident_freeze_before_git_or_cloud_mutation(tmp_path):
    import json
    from types import SimpleNamespace

    from operations import execute

    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "schema": "pcc-devops-demo/actions-v1",
                "mutations_enabled": True,
                "eligible_digests": [GOOD],
                "quarantined_digests": [],
                "allowed_caller_arn_patterns": ["arn:aws:sts::*:assumed-role/demo/*"],
            }
        )
    )
    (tmp_path / "loop-state.json").write_text(json.dumps(state(True, [BAD])))
    runner = Mock()
    runner.aws.return_value = {
        "Account": observer.ACCOUNT,
        "Arn": f"arn:aws:sts::{observer.ACCOUNT}:assumed-role/demo/test",
    }
    args = SimpleNamespace(
        action="deploy",
        digest=GOOD,
        policy=policy_path,
        state_dir=tmp_path,
        apply=True,
    )
    with pytest.raises(ValueError, match="frozen"):
        execute(args, runner)
    runner.aws.assert_called_once_with("sts", "get-caller-identity")
    runner.git.assert_not_called()
    runner.run.assert_not_called()
