"""Typed module workflows, shared by local registry and real stdio transport."""
from .types import McpTool, McpToolResult
from igem_drylab.m4_workflow import M4ReportInput, run_m4_report
from igem_drylab.m3_workflow import M3EnsembleInput, solve_m3_ensemble
from igem_drylab.structural_workflow import M2EnzymeComparisonInput, compare_fusion_to_reference
from igem_drylab.pocket_preparation import PocketPreparationInput, prepare_pocket
from igem_drylab.dssp_context import DsspContextInput, assess_dssp_context
from igem_drylab.template_geometry import AssemblyPreparationInput, prepare_actual_fusion_copies
from igem_drylab.template_geometry import (AssemblyExpansionInput, expand_actual_fusion,
    RecruitmentGeometryInput, calculate_recruitment_geometry, RecruitmentEnsembleInput, calculate_recruitment_ensemble)
from igem_drylab.fusion_tool_import import FusionImportInput, import_fusion_tools
from igem_drylab.m1_prioritization import M1PrioritizationInput, prioritize_m1
from igem_drylab.mpipi import MpipiAnalysisInput, parse_mpipi
from igem_drylab.membrane_geometry import MembraneGeometryInput, calculate_membrane_geometry
from igem_drylab.m3_er import ERRecruitmentInput, solve_er_recruitment
from igem_drylab.m4_compartments import CompartmentNetworkInput, solve_compartment_network, CompartmentComparisonInput, compare_compartment_controls


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
BINDINGS.extend([
    binding("igem.m2.prepare_assembly", "Prepare exact fusion copies without invented interface thresholds", AssemblyPreparationInput, prepare_actual_fusion_copies),
    binding("igem.m2.secondary_context", "Read native DSSP auxiliary full-fusion assignments", DsspContextInput, assess_dssp_context),
    binding("igem.m2.prepare_pocket", "Derive pocket contacts from a sourced reference-frame ligand pose", PocketPreparationInput, prepare_pocket),
    binding("igem.m2.compare_enzyme", "Calculate original M2 Q1/Q2 reference comparisons", M2EnzymeComparisonInput, compare_fusion_to_reference),
    binding("igem.m2.expand_fusion", "Map actual fusion cores to assembly template", AssemblyExpansionInput, expand_actual_fusion),
    binding("igem.m2.place_recruitment", "Place recruitment templates and derive actual conflict graph", RecruitmentGeometryInput, calculate_recruitment_geometry),
    binding("igem.m2.recruitment_ensemble", "Retain independent conformation uncertainty", RecruitmentEnsembleInput, calculate_recruitment_ensemble),
])
BINDINGS.extend([
    binding("igem.m1.import_fusion_results","Import actual native full-fusion results",FusionImportInput,import_fusion_tools),
    binding("igem.m1.prioritize","Apply reviewed original risk and ranking policy",M1PrioritizationInput,prioritize_m1),
    binding("igem.m1.parse_mpipi", "Inspect original Mpipi raw observations without inventing an LLPS score", MpipiAnalysisInput, parse_mpipi),
    binding("igem.m2.membrane_geometry", "Evaluate sourced ER membrane and tether conformations", MembraneGeometryInput, calculate_membrane_geometry),
    binding("igem.m3.er_recruitment", "Solve proposed ER amount-conserving graph recruitment", ERRecruitmentInput, solve_er_recruitment),
    binding("igem.m4.compartment_amounts", "Solve explicit compartment amounts and exchange", CompartmentNetworkInput, solve_compartment_network),
    binding("igem.m4.compare_compartments", "Compare matched physical four-enzyme controls", CompartmentComparisonInput, compare_compartment_controls),
])
