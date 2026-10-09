"""Typed module workflows, shared by local registry and real stdio transport."""
from .types import McpTool, McpToolResult
from igem_drylab.m4_workflow import M4ReportInput, run_m4_report
from igem_drylab.m3_workflow import M3EnsembleInput, solve_m3_ensemble


def binding(name, title, contract, calculate):
    schema = contract.model_json_schema()
    definitions = schema.pop("$defs", {})
    arguments = {"type": "object", "properties": {"payload": schema},
                 "required": ["payload"], "additionalProperties": False, "$defs": definitions}
    tool = McpTool(name=name, title=title, description=contract.__doc__ or title,
                  input_schema=arguments,
                  output_schema={"type": "object", "properties": {"ok": {"type": "boolean"},
                                  "result": {"type": "object"}}, "required": ["ok", "result"]})
    def invoke(arguments):
        result = calculate(contract.model_validate(arguments["payload"]))
        return McpToolResult.ok({"ok": True, "result": result})
    return tool, invoke


BINDINGS = [binding("igem.m4.report", "Run original M4 three scenarios and F2/F3 report", M4ReportInput, run_m4_report)]
BINDINGS.append(binding("igem.m3.ensemble", "Propagate M3 measured expression and parameter ranges", M3EnsembleInput, solve_m3_ensemble))
