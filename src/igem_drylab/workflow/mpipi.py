"""Original author benchmark jobs on the existing durable workflow engine."""
from pathlib import Path
from typing import Literal

from igem_drylab import mpipi
from igem_drylab.pipeline.adapters import create_tool_adapter
from igem_drylab.pipeline.config import ToolConfig
from .models import Contract
from .tools import NodeContext, ToolDefinition


class MpipiBenchmarkInput(Contract):
    case: Literal["rg", "coexistence"]


def run_original_mpipi(payload: MpipiBenchmarkInput, context: NodeContext) -> dict:
    """Runtime command must select the verified original runner/archive.

    The node selects an author case, not project biological parameters. The
    existing engine records state/artifacts; interrupted MD is not silently
    rerun or presented as checkpoint continuation.
    """
    config = ToolConfig.model_validate(context.runtime_tools.get("mpipi", {}))
    adapter = create_tool_adapter("mpipi", config)
    if not adapter.is_available():
        return {"tool_status": "not_configured", "blocker": "Private original Mpipi executable/archive route required."}
    output = context.work_dir / "simulation"
    run = adapter.run(output_dir=output, case=payload.case,
        timeout_seconds=config.extra.get("timeout_seconds", 144000))
    result = {"method": "Mpipi_original_2021", "tool_status": run.status,
        "scientific_status": "author_benchmark_not_project_LLPS_acceptance"}
    if run.status != "succeeded":
        result["blocker"] = "Original simulation did not finish; actual partial files/manifest retained, no shortened replacement."
        return result
    parsed = mpipi.parse_mpipi(mpipi.MpipiAnalysisInput(output_dir=output, case=payload.case, origin="executed_job"))
    result["parsed"] = parsed
    return result


def original_mpipi_tool():
    return ToolDefinition("simulation.mpipi_original", "Original Mpipi author benchmark",
        "Run the unchanged author K25 or hnRNPA1 example using a private original deployment. Not a project score.",
        "1", MpipiBenchmarkInput, run_original_mpipi, "scientific_project", idempotent=False,
        implementation_files=(Path(__file__), Path(mpipi.__file__), Path(__file__).parents[1]/"pipeline/adapters.py"))
