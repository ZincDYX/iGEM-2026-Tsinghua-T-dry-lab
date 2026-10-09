"""Original M1 cheap -> predictor -> decision path on the durable DAG.

Only previously specified hard rules are applied. Fusion observations, soft
risk directions and ranking evidence are never synthesized by this path.
"""
from hashlib import sha256
from pathlib import Path

from pydantic import Field

from igem_drylab.constructs.linker_features import (M1FeatureDefinitions, M1V3Rules,
    DisorderEvidence, SegEvidence, SecondaryStructureEvidence, compute_sequence_features, compute_protparam_evidence,
    screen_sequence_v3, FusionToolEvidence)
from .models import Contract, SequenceRecord, Workflow, WorkflowNode, ProjectInput, NodeInput, MapSpec, LiteralInput
from .tools import NodeContext, ToolDefinition
from igem_drylab.resources import default_config_path


KINDS = {"idr", "enzyme_ligand_linker", "scaffold_linker", "rigid_linker", "full_fusion"}


class M1PrecheckInput(Contract):
    item: SequenceRecord
    feature_definitions: M1FeatureDefinitions
    rules: M1V3Rules


class M1DecisionInput(M1PrecheckInput):
    prechecks: list[dict] = Field(default_factory=list)
    disorder_results: list[dict] = Field(default_factory=list)
    seg_results: list[dict] = Field(default_factory=list)
    secondary_results: list[dict] = Field(default_factory=list)
    signalp_results: list[dict] = Field(default_factory=list)
    topology_results: list[dict] = Field(default_factory=list)
    aggregation_results: list[dict] = Field(default_factory=list)


def precheck(payload: M1PrecheckInput, context: NodeContext) -> dict:
    digest = sha256(payload.feature_definitions.model_dump_json().encode()).hexdigest()
    features = compute_sequence_features(payload.item.sequence, definitions=payload.feature_definitions,
                                         definitions_sha256=digest)
    result = dict(candidate_id=payload.item.id, input_sequence_sha256=features.sequence_sha256,
                  sequence_kind=payload.item.role, features=features.model_dump(mode="json"),
                  eligible_for_tools=False, hard_reject_reasons=[], missing=[])
    if payload.item.role not in KINDS:
        result["missing"] = ["Explicit M1 role: idr / enzyme_ligand_linker / scaffold_linker / rigid_linker / full_fusion"]
        return result
    observed = screen_sequence_v3(features=features, sequence=payload.item.sequence,
        sequence_kind=payload.item.role, rules=payload.rules, require_external_evidence=False)
    result["hard_reject_reasons"] = observed.hard_reject_reasons
    result["eligible_for_tools"] = not observed.hard_reject_reasons and payload.item.role != "full_fusion"
    return result


def decision(payload: M1DecisionInput, context: NodeContext) -> dict:
    observed = precheck(payload, context)
    # These file-bearing observations must be actual registered predecessors,
    # not browser-supplied literal dictionaries pointing at arbitrary files.
    for rows in (payload.prechecks, payload.disorder_results, payload.seg_results, payload.secondary_results,
                 *[r for r in (payload.signalp_results,payload.topology_results,payload.aggregation_results) if r]):
        if not any(parent["output"].get("items") == rows for parent in context.upstream_results):
            raise ValueError("M1_requires_registered_upstream_observations")
    def selected(rows):
        found = [row for row in rows if row.get("candidate_id") == payload.item.id]
        if len(found) != 1:
            raise ValueError("M1_each_candidate_requires_one_registered_predecessor_result")
        row = found[0]
        if row.get("input_sequence_sha256") != observed["input_sequence_sha256"]:
            raise ValueError("M1_predecessor_sequence_identity_mismatch")
        return row
    if selected(payload.prechecks) != observed:
        raise ValueError("M1_precheck_result_does_not_match_original_rules")
    from igem_drylab.constructs.linker_features import SequenceFeatures
    features = SequenceFeatures.model_validate(observed["features"])
    disorder = selected(payload.disorder_results)
    seg = selected(payload.seg_results)
    secondary = selected(payload.secondary_results)
    fusion = None
    if payload.item.role == "full_fusion":
        merged = {"input_sha256":observed["input_sequence_sha256"],"provenance":{},"native_formats":{},"native_rules":{}}
        for collection in (payload.signalp_results,payload.topology_results,payload.aggregation_results):
            if not collection:
                continue
            raw = selected(collection).get("parsed")
            if raw:
                for key,value in raw.items():
                    if key in {"provenance","native_formats","native_rules"}:
                        merged[key].update(value)
                    elif value is not None and value != []:
                        merged[key]=value
        fusion = FusionToolEvidence.model_validate(merged)
    if observed["missing"]:
        return dict(schema_version="m1-method-check-v1", candidate_id=payload.item.id,
                    verdict="blocked", precheck=observed, missing=observed["missing"], screen=None)
    screen = screen_sequence_v3(features=features, sequence=payload.item.sequence,
        sequence_kind=payload.item.role, rules=payload.rules,
        disorder=DisorderEvidence.model_validate(disorder["parsed"]) if disorder.get("parsed") else None,
        seg=SegEvidence.model_validate(seg["parsed"]) if seg.get("parsed") else None,
        secondary_structure=SecondaryStructureEvidence.model_validate(secondary["parsed"]) if secondary.get("parsed") else None,
        protparam=compute_protparam_evidence(payload.item.sequence, input_sha256=features.sequence_sha256),
        fusion_evidence=fusion,full_fusion_sha256=features.sequence_sha256 if fusion else None,
        require_external_evidence=True)
    return dict(schema_version="m1-method-check-v1", candidate_id=payload.item.id,
        verdict=screen.verdict, precheck=observed, screen=screen.model_dump(mode="json"),
        steps=[dict(step="1", name="Cheap sequence fields", status="reject" if observed["hard_reject_reasons"] else "completed"),
               dict(step="2", name="External fragment predictors", status="not_eligible" if not observed["eligible_for_tools"] else
                    "completed" if all(row.get("parse_status") == "succeeded" for row in (disorder, seg, secondary)) else "partial",
                    missing=[label for row, label in ((disorder, "IUPred"), (seg, "SEG"), (secondary, "exact-sequence PSIPRED/JPred secondary structure"))
                             if row.get("parse_status") != "succeeded"]),
               dict(step="3", name="Actual full fusion checks", status="completed" if payload.item.role=="full_fusion" and not screen.missing_required_evidence else "blocked",
                    missing=screen.missing_required_evidence if payload.item.role=="full_fusion" else
                        ["construct assembly binding", "SignalP", "DeepTMHMM", "TANGO/PASTA", "forbidden DNA sites"]),
               dict(step="4", name="Soft risk classification", status="blocked", missing=["reviewed risk directions"]),
               dict(step="5", name="Original-method ranking", status="blocked", missing=["raw LLPS predictions and reviewed normalization/rubric"])],
        claim_scope="original_M1_available_hard_checks_not_full_candidate_acceptance")


def m1_check_tools():
    implementation = (Path(__file__), Path(__file__).parents[1] / "constructs/linker_features.py")
    return [ToolDefinition("method.m1.precheck", "M1 Step 1 — cheap sequence veto", "Original hard boundaries; rejected parts skip expensive predictions.",
                "1", M1PrecheckInput, precheck, "scientific_project", implementation_files=implementation),
            ToolDefinition("method.m1.decision", "M1 evidence and missing-step decision", "Consume exact real IUPred/SEG outputs; missing evidence is not a pass.",
                "1", M1DecisionInput, decision, "scientific_project", implementation_files=implementation)]


def m1_workflow() -> Workflow:
    import yaml
    definitions, _ = M1FeatureDefinitions.from_yaml(default_config_path("m1_feature_definitions.yaml"))
    rules = M1V3Rules.model_validate(yaml.safe_load(default_config_path("m1_rules_v3.yaml").read_text()))
    inputs = dict(feature_definitions=LiteralInput(value=definitions.model_dump(mode="json")),
                  rules=LiteralInput(value=rules.model_dump(mode="json")))
    batch = MapSpec(items=ProjectInput(path=["sequences"]))
    checks = NodeInput(node_id="m1_fields", path=["items"])
    nodes = [WorkflowNode(id="m1_fields", label="M1 Step 1 — cheap sequence veto", tool_id="method.m1.precheck", inputs=inputs, map=batch)]
    for tool in ("iupred2a", "seg", "jpred"):
        nodes.append(WorkflowNode(id="m1_"+tool, label="M1 Step 2 — real "+tool,
            tool_id="prediction."+tool, inputs={"prechecks": checks}, map=batch))
    for tool in ("signalp","deeptmhmm","tango"):
        nodes.append(WorkflowNode(id="m1_"+tool,label="M1 Step 3 — full-fusion "+tool,
            tool_id="prediction."+tool,map=batch))
    nodes.append(WorkflowNode(id="m1_decisions", label="M1 decisions and explicit unfinished steps", tool_id="method.m1.decision",
        inputs={**inputs, "prechecks": checks, "disorder_results": NodeInput(node_id="m1_iupred2a", path=["items"]),
                "seg_results": NodeInput(node_id="m1_seg", path=["items"]),
                "secondary_results": NodeInput(node_id="m1_jpred", path=["items"]),
                "signalp_results":NodeInput(node_id="m1_signalp",path=["items"]),
                "topology_results":NodeInput(node_id="m1_deeptmhmm",path=["items"]),
                "aggregation_results":NodeInput(node_id="m1_tango",path=["items"])}, map=batch))
    return Workflow(id="m1-sequence-checks", name="M1 original hard checks", nodes=nodes,
        description="Real durable sequence checks, not a full fusion/ranking approval. Assign explicit M1 roles before running.")
