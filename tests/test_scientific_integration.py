from __future__ import annotations

import json
from pathlib import Path

from igem_drylab.parameters import ParameterRecord, m4_requirements
from igem_drylab.pipeline import load_config, run_pipeline
from igem_drylab.pipeline.config import InductionGateConfig, InitialStateConfig


def test_software_fixture_workflow_blocks_external_network(tmp_path,monkeypatch):
    import socket
    def forbid_network(*args,**kwargs):
        raise AssertionError('software fixture workflow attempted network access')
    monkeypatch.setattr(socket.socket,'connect',forbid_network)
    monkeypatch.setattr(socket,'create_connection',forbid_network)
    config = load_config(Path("configs/m1_m4_real_scoring_example.yaml"))
    config.execution.mode = "demo"
    config.execution.require_provenance = False
    config.run.output_dir = tmp_path
    config.execution.allow_assumptions = True
    # Complete synthetic scaffold sequences for this offline integration test;
    # missing ORFs must not be waived by experimental_baseline.
    config.inputs.constructs[0].sequences = {"FTH1": "MA"}
    config.inputs.constructs[1].sequences = {"SpyTag_SpyCatcher": "MA"}
    config.stages.m3_concentration.recruitment_mode = "legacy_independent_partition"
    config.stages.m4_reaction.pt_gate = InductionGateConfig(on_time=0, basal=0, induced=1)
    config.stages.m4_reaction.oc_gate = InductionGateConfig(on_time=0, basal=0, induced=1)
    config.stages.m4_reaction.dmt_gate = InductionGateConfig(on_time=3, basal=0, induced=1)
    config.stages.m4_reaction.initial_state = InitialStateConfig(x9=10)
    values = {
        "phi": .1, "pt_total": 1, "oc_total": 1, "dmt_total": 1,
        "kcat_pt": 1, "km_pt": 1, "kcat_oc": 1, "km_oc": 1,
        "kcat_dmt_9": .4, "km_dmt_9": 1, "kcat_dmt_11": 1, "km_dmt_11": 1,
            **{f"partition_{name}": 1 for name in ("pt", "oc", "dmt", "x9", "x10", "x11")},
        **{f"activity_{phase}_{enzyme}": 1 for phase in ("dense", "dilute") for enzyme in ("pt", "oc", "dmt")},
    }
    requirements = {item.name: item for item in m4_requirements()}
    config.parameters = [ParameterRecord(parameter_id=name, name=name, value=value, unit=requirements[name].canonical_unit, parameter_type=requirements[name].parameter_type, enzyme_id=requirements[name].enzyme_id, substrate_id=requirements[name].substrate_id, product_id=requirements[name].product_id, source_type="assumption", source_reference="synthetic integration fixture", review_status="approved") for name, value in values.items()]
    wetlab = tmp_path / "wetlab.json"
    wetlab.write_text(json.dumps([{"experiment_id": "e", "construct_id": "M1-FTH1-pgl3_3x_ggggs", "condition_id": "c", "replicate_id": "1", "metabolite_time": [0, 1], "metabolite_concentration_unit": "uM", "metabolites": {"15": [0, 1]}, "control_available": True, "biological_replicate_count": 2}]), encoding="utf-8")
    config.stages.m5_feedback.wetlab_results_file = wetlab
    manifest = run_pipeline(config)
    assert [item.stage for item in manifest.stages] == ["m1_construct_screen", "m2_structure_screen", "m3_enrichment", "m4_glabridin_kinetics", "m5_wetlab_feedback"]
    assert '"status": "valid"' in (manifest.run_dir / "m4_glabridin_kinetics" / "reaction_predictions.json").read_text(encoding="utf-8")
    assert '"qc_passed": true' in (manifest.run_dir / "m5_wetlab_feedback" / "feedback.json").read_text(encoding="utf-8")
    # SERVER ONLY: inspect values actually emitted by M1->M5, not a hand-built
    # display sidecar. This fixture remains synthetic and assumption-based.
    from igem_drylab.wetlab.comparison import M5ComparisonSeries
    feedback = json.loads((manifest.run_dir / "m5_wetlab_feedback" / "feedback.json").read_text())
    series = M5ComparisonSeries.model_validate(feedback[0]["metabolite_comparisons"]["15"]["display_series"])
    assert (series.experiment_id, series.construct_id, series.condition_id, series.replicate_id) == ("e", "M1-FTH1-pgl3_3x_ggggs", "c", "1")
    assert series.time == [0, 1] and series.observed == [0, 1]
    assert series.parameter_approval == "not_granted_by_display"
