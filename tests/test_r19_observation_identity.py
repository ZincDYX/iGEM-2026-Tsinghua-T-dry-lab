"""Software state oracles: no biological calculation or simulated evidence."""
from uuid import uuid4

from igem_drylab.agent.context import _find_conflicts
from igem_drylab.agent.memory import MemoryRecord, ScientificClaim
from igem_drylab.agent.models import AgentTask, AgentTrace, Plan, PlanStep, ResultCondition, ToolCallRecord
from igem_drylab.agent.runtime import AgentRuntime


def test_retry_uses_current_committed_attempt_not_first_call_or_old_plan():
    source = PlanStep(step_id="prediction", objective="Software operation", status="succeeded", attempts=2)
    downstream = PlanStep(step_id="next", objective="Software follow-up", run_conditions=[
        ResultCondition(source_step_id="prediction", source_path=["ready"], allowed_values=[True])])
    trace = AgentTrace(task=AgentTask(task_id="software", objective="Software fixture"),
        plan=Plan(task_id="software", plan_id="current", steps=[source, downstream]))
    def call(plan, attempt, status, ready):
        return ToolCallRecord(plan_id=plan, attempt=attempt, result_id=str(uuid4()), step_id="prediction",
            tool_name="software.fixture", arguments={}, result={"ready":ready}, status=status)
    trace.calls = [call("current", 1, "failed", False), call("current", 2, "succeeded", True),
                   call("obsolete", 9, "succeeded", False)]
    assert AgentRuntime._conditions_met(trace, downstream) == (True, "conditions_met")
    trace.calls = [call("current", 1, "succeeded", True), call("obsolete", 2, "succeeded", True)]
    assert AgentRuntime._conditions_met(trace, downstream)[0] is False
    trace.calls = [call("current", 2, "failed", True)]
    assert AgentRuntime._conditions_met(trace, downstream)[0] is False


def test_history_and_different_conditions_are_not_scientific_conflicts():
    events = [MemoryRecord(record_id="failed", kind="tool_call", content="failed", tags=["same-step"]),
              MemoryRecord(record_id="retry", kind="tool_call", content="succeeded", tags=["same-step"])]
    assert _find_conflicts(events) == []
    scope = dict(subject_ref="software-entity", quantity="software-property", construct_ref="fixture",
        condition_ref="a", model_version="fixture-v1", canonical_unit="fixture-unit", entity_basis="fixture")
    first = MemoryRecord(record_id="a", content="one assertion", claim=ScientificClaim(**scope, value=1))
    other = MemoryRecord(record_id="b", content="different condition", claim=ScientificClaim(**{**scope, "condition_ref":"b"}, value=2))
    assert _find_conflicts([first, other]) == []
    conflict = other.model_copy(update={"claim":ScientificClaim(**scope, value=2)})
    assert _find_conflicts([first, conflict]) == ["conflicting_scientific_claim:a,b"]
    corrected = conflict.model_copy(update={"claim":ScientificClaim(**scope, value=2, supersedes_record_id="a")})
    assert _find_conflicts([first, corrected]) == []
