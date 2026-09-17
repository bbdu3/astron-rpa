import json
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.workflow import Execution, Workflow
from app.schemas.workflow import ExecutionCreate
from app.security.workflow_authorization import WorkflowAccessError
from app.services.execution import ExecutionService
from app.services.execution_management import digest
from app.services.integration_policy import require_admission, workflow_profile
from app.services.workflow_control import WorkflowControlService
from app.services.workflow_schema import workflow_input_schema
from tests.test_workflow_control import AsyncSessionAdapter, database  # noqa: F401


@pytest.fixture
def policy(tmp_path, monkeypatch):
    path = tmp_path / "policy.json"
    monkeypatch.setattr(get_settings(), "INTEGRATION_POLICY_FILE", str(path))

    def write(workflow, **changes):
        declaration = {
            "userId": "owner",
            "projectId": workflow.project_id,
            "version": workflow.version,
            "revision": "review-1",
            "inputSchemaHash": digest(workflow_input_schema(workflow)),
            "capabilities": ["framework-fixture"],
            "fileInputs": False,
            "fileOutputs": False,
            "requiresGui": False,
            "requiresHuman": False,
            "environment": [],
            "sideEffects": [],
            "risk": "low",
            "executionType": "short",
            "exclusiveTerminal": True,
            "allowed": True,
        }
        declaration.update(changes)
        path.write_text(json.dumps({"schemaVersion": 1, "enforcedUsers": ["owner"], "declarations": [declaration]}))

    return write


def test_profile_unknown_is_not_false_or_admitted(monkeypatch):
    monkeypatch.setattr(get_settings(), "INTEGRATION_POLICY_FILE", "")
    workflow = Workflow(project_id="p", user_id="owner", version=1, parameters="[]")
    profile = workflow_profile(workflow, "owner")
    assert profile["admission"] == {"allowed": False, "reason": "PROFILE_UNKNOWN", "enforced": False}
    assert profile["requiresGui"] is None
    require_admission(workflow, "owner")  # documented, unenrolled legacy caller
    with pytest.raises(WorkflowAccessError, match="no valid integration admission"):
        require_admission(workflow, "owner", "invented")


def test_declaration_revision_binds_schema_and_every_policy_change(policy):
    workflow = Workflow(project_id="p", user_id="owner", version=1, parameters="[]")
    policy(workflow)
    revision = workflow_profile(workflow, "owner")["revision"]
    require_admission(workflow, "owner", revision)
    policy(workflow, requiresGui=True)
    assert workflow_profile(workflow, "owner")["revision"] != revision
    with pytest.raises(WorkflowAccessError) as error:
        require_admission(workflow, "owner", revision)
    assert error.value.code == "PROFILE_STALE"


def test_corrupt_policy_does_not_revert_to_legacy(tmp_path, monkeypatch):
    path = tmp_path / "invalid.json"
    path.write_text("{broken")
    monkeypatch.setattr(get_settings(), "INTEGRATION_POLICY_FILE", str(path))
    workflow = Workflow(project_id="p", user_id="owner", version=1, parameters="[]")
    with pytest.raises(WorkflowAccessError) as error:
        require_admission(workflow, "owner")
    assert error.value.code == "INTEGRATION_POLICY_UNAVAILABLE"


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"allowed": False}, "PROFILE_DENIED"),
        ({"requiresGui": None}, "PROFILE_INCOMPLETE"),
        ({"fileInputs": True}, "FILE_TRANSFER_UNSUPPORTED"),
        ({"inputSchemaHash": "0" * 64}, "PROFILE_STALE"),
        ({"version": 9}, "PROFILE_UNKNOWN"),
    ],
)
def test_scoped_denials_are_fail_closed(policy, change, reason):
    workflow = Workflow(project_id="p", user_id="owner", version=1, parameters="[]")
    policy(workflow, **change)
    with pytest.raises(WorkflowAccessError) as error:
        require_admission(workflow, "owner")
    assert error.value.code == reason


@pytest.mark.asyncio
async def test_all_execution_callers_share_admission(database, policy):
    with Session(database) as db:
        workflow = db.get(Workflow, "allowed")
        policy(workflow, allowed=False)
        service = ExecutionService(AsyncSessionAdapter(db))
        service.execute_workflow = AsyncMock()
        for request in [
            ExecutionCreate(project_id="allowed", version=2),
            ExecutionCreate(project_id="allowed", version=2, profile_revision="review-1"),
        ]:
            with pytest.raises(WorkflowAccessError) as error:
                await service.execute_authorized_workflow(request, "owner")
            assert error.value.code == "PROFILE_DENIED"
        service.execute_workflow.assert_not_awaited()
        assert len(db.execute(select(Execution)).scalars().all()) == 1


@pytest.mark.asyncio
async def test_running_execution_survives_republication(database):
    with Session(database) as db:
        db.get(Workflow, "allowed").version = 3
        db.commit()
        result = await WorkflowControlService(AsyncSessionAdapter(db)).get_execution("existing", "owner")
        assert result["executionId"] == "existing"
        assert result["version"] == 2
