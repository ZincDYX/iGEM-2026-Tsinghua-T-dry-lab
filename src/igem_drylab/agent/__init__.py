"""Agent framework skeleton for dry-lab orchestration.

This package intentionally contains the full architectural slots expected in a
research/industry agent system, while leaving project-specific policies as TODOs.
"""

from .artifacts import ArtifactRecord, ArtifactStore
from .budget import BudgetManager, BudgetState
from .context import ContextBuilder, ContextBundle
from .human import ApprovalDecision, HumanApprovalGate
from .hypothesis import HypothesisRecord
from .memory import AgentMemory, MemoryRecord
from .llm_planner import OpenAICompatiblePlanningBackend
from .hybrid_planner import HybridLLMPlanningBackend
from .decision import PlanningDecision
from .plan_compiler import DeterministicPlanCompiler
from .models import AgentTask, AgentTrace, Plan, PlanStep, ResultBinding, ResultCondition
from .observability import EventLogger
from .reflection import ReflectionEvaluator, ReflectionReport
from .runtime import AgentRuntime
from .scheduler import StepScheduler

__all__ = [
    "AgentRuntime",
    "AgentMemory",
    "AgentTask",
    "AgentTrace",
    "ArtifactRecord",
    "ArtifactStore",
    "ApprovalDecision",
    "BudgetManager",
    "BudgetState",
    "ContextBuilder",
    "ContextBundle",
    "EventLogger",
    "HumanApprovalGate",
    "HypothesisRecord",
    "MemoryRecord",
    "OpenAICompatiblePlanningBackend",
    "HybridLLMPlanningBackend",
    "PlanningDecision",
    "DeterministicPlanCompiler",
    "Plan",
    "PlanStep",
    "ResultBinding",
    "ResultCondition",
    "ReflectionEvaluator",
    "ReflectionReport",
    "StepScheduler",
]
