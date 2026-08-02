"""Agent framework skeleton for dry-lab orchestration.

This package intentionally contains the full architectural slots expected in a
research/industry agent system, while leaving project-specific policies as TODOs.
"""

from .artifacts import ArtifactRecord, ArtifactStore
from .budget import BudgetManager, BudgetState
from .context import ContextBuilder, ContextBundle
from .human import HumanApprovalGate
from .models import AgentTask, AgentTrace, Plan, PlanStep
from .observability import EventLogger
from .reflection import ReflectionEvaluator, ReflectionReport
from .runtime import AgentRuntime
from .scheduler import StepScheduler

__all__ = [
    "AgentRuntime",
    "AgentTask",
    "AgentTrace",
    "ArtifactRecord",
    "ArtifactStore",
    "BudgetManager",
    "BudgetState",
    "ContextBuilder",
    "ContextBundle",
    "EventLogger",
    "HumanApprovalGate",
    "Plan",
    "PlanStep",
    "ReflectionEvaluator",
    "ReflectionReport",
    "StepScheduler",
]
