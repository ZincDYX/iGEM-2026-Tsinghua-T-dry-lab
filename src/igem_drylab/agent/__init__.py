"""Scientific planning types; the workbench uses the sole WorkflowEngine.

Historical AgentRuntime remains a compatibility interface, not the production
executor. Importing a decision/observation must not initialize that runtime,
its deprecated MCP registry or the optional language-model client.
"""
from importlib import import_module

_EXPORTS = {
    "artifacts": ("ArtifactRecord", "ArtifactStore"),
    "budget": ("BudgetManager", "BudgetState"),
    "context": ("ContextBuilder", "ContextBundle"),
    "human": ("ApprovalDecision", "HumanApprovalGate"),
    "hypothesis": ("HypothesisRecord",),
    "memory": ("AgentMemory", "MemoryRecord"),
    "llm_planner": ("OpenAICompatiblePlanningBackend",),
    "hybrid_planner": ("HybridLLMPlanningBackend",),
    "decision": ("PlanningDecision",),
    "plan_compiler": ("DeterministicPlanCompiler",),
    "models": ("AgentTask", "AgentTrace", "Plan", "PlanStep", "ResultBinding", "ResultCondition"),
    "observability": ("EventLogger",),
    "reflection": ("ReflectionEvaluator", "ReflectionReport"),
    "runtime": ("AgentRuntime",),
    "scheduler": ("StepScheduler",),
}
__all__ = [name for names in _EXPORTS.values() for name in names]


def __getattr__(name):
    module = next((module for module,names in _EXPORTS.items() if name in names),None)
    if module is None: raise AttributeError(name)
    value = getattr(import_module("."+module,__name__),name)
    globals()[name] = value
    return value
