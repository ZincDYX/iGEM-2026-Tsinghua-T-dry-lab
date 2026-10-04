"""Shared local-agent and transport MCP bindings for the new research workflow."""
from pathlib import Path

from .types import McpTool,McpToolResult


def analyze(prediction_contract,analysis_config):
    from igem_drylab.design_analysis import M4AnalysisConfig,analyze_prediction
    return analyze_prediction(prediction_contract,M4AnalysisConfig.model_validate(analysis_config))


def scan(design_plan,output_dir):
    from igem_drylab.design_analysis import FiniteDesignPlan,scan_scaffold_designs
    return scan_scaffold_designs(FiniteDesignPlan.model_validate(design_plan),Path(output_dir))


def freeze(prediction_file,parameter_file,calibration_datasets,freeze_id,construct_id,condition_id,claim_scope):
    from igem_drylab.research_validation import freeze_prediction
    return freeze_prediction(Path(prediction_file),Path(parameter_file),{k:Path(v) for k,v in calibration_datasets.items()},
        freeze_id=freeze_id,construct_id=construct_id,condition_id=condition_id,claim_scope=claim_scope)


def validate(snapshot,dataset_id,dataset_file):
    from igem_drylab.research_validation import validate_holdout
    return validate_holdout(snapshot,dataset_id,Path(dataset_file))


def _binding(name,title,properties,call):
    tool = McpTool(name=name,title=title,description=title,
        input_schema={"type":"object","properties":properties,"required":list(properties),"additionalProperties":False},
        output_schema={"type":"object"})
    return tool,lambda arguments:McpToolResult.ok(call(**arguments))


OBJECT = {"type":"object"}
STRING = {"type":"string"}
BINDINGS = [
    _binding("igem.m4.analyze_prediction","Evidence-declared original F2 sensitivity",
             {"prediction_contract":OBJECT,"analysis_config":OBJECT},analyze),
    _binding("igem.design.scan_scaffolds","Fresh M1-M4 finite construct scan",
             {"design_plan":OBJECT,"output_dir":STRING},scan),
    _binding("igem.research.freeze_prediction","Freeze calibration lineage without claiming validation",
             {**{key:STRING for key in ("prediction_file","parameter_file","freeze_id","construct_id","condition_id","claim_scope")},
              "calibration_datasets":{"type":"object","additionalProperties":STRING}},freeze),
    _binding("igem.research.validate_holdout","Frozen held-out error report without refitting",
             {"snapshot":OBJECT,"dataset_id":STRING,"dataset_file":STRING},validate),
]
