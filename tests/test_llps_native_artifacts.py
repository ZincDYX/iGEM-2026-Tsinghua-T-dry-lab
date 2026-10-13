"""Format/policy oracles only; synthetic values are not project evidence."""
from hashlib import sha256
import json

import pytest

from igem_drylab.llps_artifacts import (read_native_llps, import_llps_results, LLPSImportInput,
    verify_native_predictor_score)
from igem_drylab.m1_prioritization import PredictorScore


def test_original_cat_score_requires_exact_native_input_and_global_column(tmp_path):
    fasta = tmp_path/"prot.fa"; fasta.write_text(">sequence_input\nGSGS\n")
    score = tmp_path/"scores.txt"; score.write_text("sequence_input 4.23603\n")
    native = read_native_llps(score, format="catgranule2016_scores", sequence="GSGS", sequence_file=fasta)
    assert native["raw_score"] == 4.23603
    with pytest.raises(ValueError, match="sequence_mismatch"):
        read_native_llps(score, format="catgranule2016_scores", sequence="SGSG", sequence_file=fasta)
    with pytest.raises(ValueError, match="requires_native_input"):
        read_native_llps(score, format="catgranule2016_scores", sequence="GSGS")
    imported = import_llps_results(LLPSImportInput(candidate_id="fixture", sequence="GSGS",
        artifacts=[dict(path=score, sequence_file=fasta, format="catgranule2016_scores", tool_version="format fixture")],
        reviewer="fixture", source_reference="synthetic format oracle not actual execution"))
    observed = PredictorScore.model_validate(imported["predictor_scores"][0])
    verify_native_predictor_score(observed)
    observed.raw_score = 0.9
    with pytest.raises(ValueError, match="global_score_mismatch"):
        verify_native_predictor_score(observed)


def test_fuzdrop_tsv_is_profile_not_fabricated_global_score(tmp_path):
    path = tmp_path/"scores.tsv"
    path.write_text("position\tresidue\tpDP\tSbind\n1\tG\t0.8\t-1\n2\tS\t0.6\t0\n")
    native = read_native_llps(path, format="fuzdrop_scores_tsv", sequence="GS")
    assert native["raw_score"] is None and native["missing"] == ["native_global_pLLPS_not_in_TSV"]
    imported = import_llps_results(LLPSImportInput(candidate_id="fixture", sequence="GS",
        artifacts=[dict(path=path, format="fuzdrop_scores_tsv", tool_version="format fixture")],
        reviewer="fixture", source_reference="synthetic"))
    assert imported["predictor_scores"] == []
    with pytest.raises(ValueError, match="complete_contiguous"):
        read_native_llps(path, format="fuzdrop_scores_tsv", sequence="GSS")


def test_fuzdrop_original_response_keeps_explicit_global_not_profile_mean(tmp_path):
    path = tmp_path/"fuzdrop.json"
    data = dict(sequence="GS", pLLPS=0.3, result=[
        dict(position=0, aa="G", pDP=0.8, Shae=-1), dict(position=1, aa="S", pDP=0.6, Shae=0)])
    path.write_text(json.dumps(data))
    native = read_native_llps(path, format="fuzdrop_response_json", sequence="GS")
    assert native["raw_score"] == 0.3
    data["result"][1]["position"] = 3; path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="complete_contiguous"):
        read_native_llps(path, format="fuzdrop_response_json", sequence="GS")


def test_m1_workflow_sizes_call_budget_to_complete_actual_fanout():
    from igem_drylab.workflow.m1_checks import m1_workflow
    workflow = m1_workflow(sequence_count=272)
    assert workflow.execution_policy.max_tool_calls == 272*10+1


def test_batch_rank_does_not_invent_policy_and_rejects_unregistered_decisions(tmp_path):
    from igem_drylab.workflow.m1_checks import batch_rank, M1BatchRankInput
    from igem_drylab.workflow.tools import NodeContext
    payload = M1BatchRankInput(decisions=[{"candidate_id": "fixture"}])
    context = NodeContext("r", "n", tmp_path)
    with pytest.raises(ValueError, match="registered_decisions"):
        batch_rank(payload, context)
    context = NodeContext("r", "n", tmp_path, upstream_results=({"output": {"items": payload.decisions}},))
    result = batch_rank(payload, context)
    assert result["status"] == "blocked" and result["ranked_IDR_candidate_ids"] == []


def test_shared_native_batch_reviews_do_not_overwrite_other_candidates(tmp_path):
    fasta=tmp_path/'prot.fa';fasta.write_text('>first\nGS\n>second\nSG\n')
    output=tmp_path/'scores.txt';output.write_text('first 1.25\nsecond 2.5\n')
    observations=[]
    for identifier, sequence in [('first','GS'),('second','SG')]:
        result=import_llps_results(LLPSImportInput(candidate_id=identifier,sequence=sequence,
            artifacts=[dict(path=output,sequence_file=fasta,format='catgranule2016_scores',record_id=identifier,tool_version='synthetic batch fixture')],
            reviewer='fixture',source_reference='synthetic format oracle not actual execution'))
        observations.append(PredictorScore.model_validate(result['predictor_scores'][0]))
    assert observations[0].provenance.record_file!=observations[1].provenance.record_file
    for observed in observations:
        assert sha256(observed.provenance.record_file.read_bytes()).hexdigest()==observed.provenance.record_sha256
        verify_native_predictor_score(observed)
