"""Stage routing probes; run with the server scientific regression suite."""
from igem_drylab.pipeline.config import ProjectConfig
from igem_drylab.pipeline.models import M2FusionAssessment, M3ConcentrationAssessment
from igem_drylab.pipeline.stages import run_m3, run_m4
from igem_drylab.compartments import scenario_for_construct


def config(tmp_path):
    source = tmp_path / "software.fasta"
    source.write_text(">SYNTHETIC_ROUTING_ONLY\nMAGSGS\n")
    return ProjectConfig.model_validate({"run":{"id":"routing-only"},
        "inputs":{"protein_fasta":source,"enzymes":[],"scaffolds":[],"linkers":[],
            "constructs":[{"id":"anchored_scaffold","components":["SYNTHETIC_ROUTING_ONLY"],"localization_context":"er_anchored"},
                          {"id":"soluble_enzyme","components":["SYNTHETIC_ROUTING_ONLY"],"localization_context":"cytosolic"}],
            "designs":[{"id":"whole_design","protein_construct_ids":["anchored_scaffold","soluble_enzyme"]}]}})


def test_whole_design_er_localization_cannot_be_lost_by_default_upstream_result(tmp_path):
    project = config(tmp_path)
    assert scenario_for_construct(project, "whole_design") == "er_anchored"
    upstream = M2FusionAssessment(candidate_id="software-fixture", construct_id="whole_design", construct_definition={},
        recommended_for_m3=True)  # Old record has the historical cytosolic default.
    result, output = run_m3(project, tmp_path, [upstream])
    assert result[0].compartment_scenario == "er_anchored"
    assert result[0].missing_inputs == ["unsupported_compartment_model:er_anchored"]
    assert not result[0].concentrations and not result[0].recommended_for_m4
    assert output.json_file.is_file()
    forged = M3ConcentrationAssessment(candidate_id="software-fixture", construct_id="whole_design",
        status="valid", recommended_for_m4=True)
    predictions, output = run_m4(project, tmp_path, [forged])
    assert predictions[0].compartment_scenario == "er_anchored"
    assert predictions[0].status == "insufficient_data"
    assert predictions[0].missing_inputs == ["unsupported_compartment_model:er_anchored"]
    assert output.record_count == 1 and output.json_file.is_file()


def test_explicit_er_result_cannot_be_reinterpreted_as_cytosolic_config(tmp_path):
    project = config(tmp_path)
    upstream = M2FusionAssessment(candidate_id="software-fixture", construct_id="soluble_enzyme", construct_definition={},
        compartment_scenario="er_anchored", recommended_for_m3=True)
    result, _ = run_m3(project, tmp_path, [upstream])
    assert result[0].missing_inputs == ["unsupported_compartment_model:er_anchored"]
