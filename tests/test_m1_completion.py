"""Native format and policy contracts; fixtures are not authentic tool jobs."""
from hashlib import sha256
import json
from pathlib import Path
import pytest

from igem_drylab.fusion_tool_import import (NativeFusionArtifact, FusionImportInput, import_fusion_tools, parse_native_artifact)
from igem_drylab.constructs.linker_features import (FusionToolEvidence,M1FeatureDefinitions,M1V3Rules,
    compute_sequence_features,screen_sequence_v3)
from igem_drylab.m1_prioritization import (PrioritizationPolicy,M1PrioritizationInput,PrioritizationCandidate,prioritize_m1)


def native_files(tmp_path):
    sp=tmp_path/"prediction_results.txt"
    sp.write_text("# SignalP-6.0\n# ID\tPrediction\tOTHER\tSP(Sec/SPI)\tCS Position\nfixture\tOTHER\t0.99\t0.01\t\n")
    tm=tmp_path/"predicted_topologies.3line"
    tm.write_text(">fixture | GLOB\nGGGSSGGGSS\nIIIIIIIIII\n")
    agg=tmp_path/"fixture.out"
    agg.write_text("\n".join(f"{i}, {letter}, 0, 0, 0, {10 if i in {1,2,3,7,8,9} else 0}, 0" for i,letter in enumerate("GGGSSGGGSS",1)))
    return [NativeFusionArtifact(path=sp,format="signalp6_summary",tool_version="6.0",record_id="fixture"),
        NativeFusionArtifact(path=tm,format="deeptmhmm1_3line",tool_version="1.0",record_id="fixture"),
        NativeFusionArtifact(path=agg,format="tango_residue_out",tool_version="synthetic",record_id="fixture",
            aggregation_rule=dict(high_score_percent=5,minimum_run_length=3,source_reference="synthetic_rule_not_project_approval"))]


def test_native_import_derives_full_fusion_observations_and_reparses_raw_bytes(tmp_path):
    sequence="GGGSSGGGSS"
    imports=import_fusion_tools(FusionImportInput(sequence=sequence,artifacts=native_files(tmp_path),
        reviewer="synthetic_import_reviewer",source_reference="synthetic_format_fixture_not_actual_job",output_dir=tmp_path/"review"))
    fusion=FusionToolEvidence.model_validate(imports["fusion"])
    assert not fusion.signal_peptide_with_clear_cleavage and fusion.transmembrane_helix_count==0
    assert fusion.continuous_high_aggregation_hotspots==2
    root=Path(__file__).resolve().parents[1]
    definitions,digest=M1FeatureDefinitions.from_yaml(root/"configs/m1_feature_definitions.yaml")
    features=compute_sequence_features(sequence,definitions=definitions,definitions_sha256=digest)
    screen=screen_sequence_v3(features=features,sequence=sequence,sequence_kind="full_fusion",rules=M1V3Rules(rule_version="fixture"),
        fusion_evidence=fusion,full_fusion_sha256=features.sequence_sha256)
    assert screen.verdict=="reject" and not screen.missing_required_evidence
    fusion.continuous_high_aggregation_hotspots=0
    with pytest.raises(ValueError,match="summary_or_array_mismatch"):
        screen_sequence_v3(features=features,sequence=sequence,sequence_kind="full_fusion",rules=M1V3Rules(rule_version="fixture"),
            fusion_evidence=fusion,full_fusion_sha256=features.sequence_sha256)


def test_native_sequence_and_undefined_aggregation_rules_do_not_pass(tmp_path):
    sp,tm,agg=native_files(tmp_path)
    with pytest.raises(ValueError,match="sequence_or_length"):
        parse_native_artifact(tm,"AAAAAAAAAA")
    with pytest.raises(ValueError,match="requires_explicit"):
        NativeFusionArtifact(path=agg.path,format="tango_residue_out",tool_version="synthetic",record_id="fixture")
    sp.path.write_text("ID\tPrediction\tCS Position\nfixture\tSP\tCS pos: 3-5. Pr: 0.9\n")
    with pytest.raises(ValueError,match="cleavage"):
        parse_native_artifact(sp,"GGGSSGGGSS")


def test_explicit_aggregation_exclusion_is_not_a_fabricated_negative_result(tmp_path):
    sequence='GGGSSGGGSS'
    imports=import_fusion_tools(FusionImportInput(sequence=sequence,artifacts=native_files(tmp_path)[:2],
        reviewer='fixture',source_reference='synthetic_format_contract_not_actual_job',output_dir=tmp_path/'review'))
    fusion=FusionToolEvidence.model_validate(imports['fusion'])
    root=Path(__file__).resolve().parents[1]
    definitions,digest=M1FeatureDefinitions.from_yaml(root/'configs/m1_feature_definitions.yaml')
    features=compute_sequence_features(sequence,definitions=definitions,definitions_sha256=digest)
    values=dict(features=features,sequence=sequence,sequence_kind='full_fusion',fusion_evidence=fusion,
        full_fusion_sha256=features.sequence_sha256)
    original=screen_sequence_v3(**values,rules=M1V3Rules(rule_version='original-fixture'))
    assert original.verdict=='blocked' and 'TANGO_or_PASTA2_full_fusion_output' in original.missing_required_evidence
    amended=screen_sequence_v3(**values,rules=M1V3Rules(rule_version='explicitly-amended-fixture',
        aggregation_exclusion_reference='User excludes aggregation prediction from this protocol'))
    assert amended.verdict=='pass' and not amended.missing_required_evidence
    assert amended.excluded_checks=={'full_fusion_aggregation':'User excludes aggregation prediction from this protocol'}
    assert amended.fusion_evidence.continuous_high_aggregation_hotspots is None
    assert original.excluded_checks=={}  # A skipped check never becomes a zero-hotspot observation.


def test_aggregation_exclusion_keeps_other_full_construct_checks_required(tmp_path):
    root=Path(__file__).resolve().parents[1]
    definitions,digest=M1FeatureDefinitions.from_yaml(root/'configs/m1_feature_definitions.yaml')
    features=compute_sequence_features('GGGSSGGGSS',definitions=definitions,definitions_sha256=digest)
    screen=screen_sequence_v3(features=features,sequence='GGGSSGGGSS',sequence_kind='full_fusion',
        rules=M1V3Rules(rule_version='amended',aggregation_exclusion_reference='Explicit fixture exclusion'))
    assert screen.verdict=='blocked'
    assert set(screen.missing_required_evidence)=={'SignalP_full_fusion_output','DeepTMHMM_full_fusion_output'}


def test_explicit_aggregation_exclusion_removes_only_the_native_aggregation_DAG_node():
    from igem_drylab.workflow.m1_checks import m1_workflow
    original=m1_workflow();amended=m1_workflow(aggregation_exclusion_reference='User cancelled TANGO/PASTA')
    assert 'm1_tango' in {node.id for node in original.nodes}
    assert 'm1_tango' not in {node.id for node in amended.nodes}
    assert {node.id for node in original.nodes}-{node.id for node in amended.nodes}=={'m1_tango'}
    decision=next(node for node in amended.nodes if node.id=='m1_decisions')
    assert decision.inputs['aggregation_results'].value==[]
    assert decision.inputs['rules'].value['aggregation_exclusion_reference']=='User cancelled TANGO/PASTA'


def test_soft_risk_count_and_undefined_feature_without_linker_composite(tmp_path):
    root=Path(__file__).resolve().parents[1]
    definitions,digest=M1FeatureDefinitions.from_yaml(root/"configs/m1_feature_definitions.yaml")
    features=compute_sequence_features("GGGSSGGGSS",definitions=definitions,definitions_sha256=digest)
    screen=screen_sequence_v3(features=features,sequence="GGGSSGGGSS",sequence_kind="enzyme_ligand_linker",
        rules=M1V3Rules(rule_version="fixture"),require_external_evidence=False)
    rules=[dict(rule_id="GS",feature="gs_fraction",transform="identity",operator="gt",lower=.8),
           dict(rule_id="charge",feature="net_charge_proxy",transform="absolute",operator="lt",lower=.1)]
    policy=PrioritizationPolicy(policy_version="fixture",reviewer="fixture",source_reference="explicit_synthetic_directions_not_project_policy",
        risk_rules={"enzyme_ligand_linker":rules})
    payload=M1PrioritizationInput(policy=policy,candidates=[PrioritizationCandidate(candidate_id="fixture",screen=screen)])
    row=prioritize_m1(payload)["candidates"][0]
    assert row["risk"]=="high" and row["rank_score"] is None
    policy.risk_rules["enzyme_ligand_linker"].append(type(policy.risk_rules["enzyme_ligand_linker"][0])(
        rule_id="undefined",feature="charge_blockiness",transform="identity",operator="gt",lower=0))
    row=prioritize_m1(payload)["candidates"][0]
    assert row["risk"] is None and row["missing"]==["defined_algorithm_or_observation:charge_blockiness"]


def test_native_import_is_callable_over_actual_stdio_transport(tmp_path):
    import asyncio
    import sys
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters
    root=Path(__file__).resolve().parents[1]
    payload=FusionImportInput(sequence="GGGSSGGGSS",artifacts=native_files(tmp_path),reviewer="fixture",
        source_reference="synthetic_format_fixture",output_dir=tmp_path/"review")
    async def exercise():
        params=StdioServerParameters(command=sys.executable,args=["-B","-m","igem_drylab.mcp.server"],cwd=root,
            env={"PYTHONPATH":str(root/"src")})
        async with Client(params,read_timeout_seconds=30) as client:
            result=await client.call_tool("igem.m1.import_fusion_results",{"payload":payload.model_dump(mode="json")})
            assert not result.is_error
            assert result.structured_content["result"]["fusion"]["continuous_high_aggregation_hotspots"]==2
    asyncio.run(exercise())


def test_original_IDR_ranking_uses_reviewed_ranges_consensus_and_three_keys(tmp_path):
    from igem_drylab.m1_prioritization import PredictorScore
    from igem_drylab.constructs.tool_evidence import ToolEvidenceProvenance
    root=Path(__file__).resolve().parents[1]
    definitions,digest=M1FeatureDefinitions.from_yaml(root/"configs/m1_feature_definitions.yaml")
    features=compute_sequence_features("GSGS"*50,definitions=definitions,definitions_sha256=digest)
    from igem_drylab.constructs.linker_features import M1ScreenResult
    # Constructed screen is an explicit numerical policy fixture, not M1 evidence.
    screen=M1ScreenResult(formula_version=features.formula_version,rule_version="synthetic",sequence_kind="idr",
        localization_context="cytosolic",features=features,verdict="pass")
    names=["FuzDrop","catGRANULE_2016","PScore","Mpipi_original"]
    observations=[]
    for name,value in zip(names,[.8,.6,.2,.4],strict=True):
        output=tmp_path/(name+".txt")
        output.write_text("PScore: 0.2" if name=="PScore" else str(value))
        record=dict(origin="manual_review",reviewer="synthetic",source_reference="synthetic_oracle_not_tool_job",decision="approved",
            tool_name=name,tool_version="fixture",input_sha256=features.sequence_sha256,
            output_sha256=sha256(output.read_bytes()).hexdigest(),reviewed_observations={"raw_score":value})
        path=output.with_suffix(".review.json")
        path.write_text(json.dumps(record))
        observations.append(PredictorScore(tool=name,tool_version="fixture",input_sequence_sha256=features.sequence_sha256,
            source_file=output,raw_score=value,provenance=ToolEvidenceProvenance(origin="manual_review",output_sha256=record["output_sha256"],
                record_file=path,record_sha256=sha256(path.read_bytes()).hexdigest())))
    policy=PrioritizationPolicy(policy_version="synthetic",source_reference="synthetic",reviewer="synthetic",
        risk_rules={"idr":[dict(rule_id="never",feature="pro_fraction",transform="identity",operator="gt",lower=1)]},
        predictor_rules=[dict(tool=name,normalization_minimum=0,normalization_maximum=1,high_direction="greater_equal",
            normalized_high_cutoff=.5,weight=weight) for name,weight in zip(names,[1,2,3,4],strict=True)],
        sort_keys=["risk","consensus","rank_score"],ranking_formula_reference="synthetic_explicit_weighted_formula")
    candidate=PrioritizationCandidate(candidate_id="fixture",screen=screen,predictors=observations)
    result=prioritize_m1(M1PrioritizationInput(candidates=[candidate],policy=policy))
    row=result["candidates"][0]
    assert row["risk"]=="low" and row["consensus"]==.5
    assert row["rank_score"]==pytest.approx(.42,abs=1e-12)
    assert row["sort_key"]==pytest.approx([0,-.5,-.42])
    candidate.predictors[-1].raw_score=1.5
    with pytest.raises(ValueError,match="summary_or_array_mismatch"):
        prioritize_m1(M1PrioritizationInput(candidates=[candidate],policy=policy))
