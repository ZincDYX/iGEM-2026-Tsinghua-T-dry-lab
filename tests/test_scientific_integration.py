from __future__ import annotations

import json
from pathlib import Path

from igem_drylab.parameters import ParameterRecord
from igem_drylab.pipeline import load_config, run_pipeline


def test_synthetic_m1_to_m5_workflow_has_no_network(tmp_path):
    config = load_config(Path("configs/m1_m4_real_scoring_example.yaml"))
    config.run.output_dir = tmp_path
    config.execution.allow_assumptions = True
    config.stages.m4_reaction.pt_gate = {"on_time": 0, "basal": 0, "induced": 1}
    config.stages.m4_reaction.oc_gate = {"on_time": 0, "basal": 0, "induced": 1}
    config.stages.m4_reaction.dmt_gate = {"on_time": 3, "basal": 0, "induced": 1}
    values = {
        "phi": .1, "pt_total": 1, "oc_total": 1, "dmt_total": 1,
        "kcat_pt": 1, "km_pt": 1, "kcat_oc": 1, "km_oc": 1,
        "kcat_dmt_9": .4, "km_dmt_9": 1, "kcat_dmt_11": 1, "km_dmt_11": 1,
        **{f"partition_{name}": 1 for name in ("pt", "oc", "dmt", "x9", "x10", "x11", "x13", "x15")},
        **{f"activity_{phase}_{enzyme}": 1 for phase in ("dense", "dilute") for enzyme in ("pt", "oc", "dmt")},
        **{f"x{name}_total": 10 for name in ("9", "10", "11", "13", "15")},
    }
    config.parameters = [ParameterRecord(parameter_id=name, name=name, value=value, unit="arbitrary", source_type="assumption", source_reference="synthetic integration fixture", review_status="approved") for name, value in values.items()]
    wetlab = tmp_path / "wetlab.json"
    wetlab.write_text(json.dumps([{"experiment_id": "e", "construct_id": "M1-FTH1-pgl3_3x_ggggs", "condition_id": "c", "replicate_id": "1", "metabolite_time": [0, 1], "metabolites": {"15": [0, 1]}, "control_available": True, "biological_replicate_count": 2}]), encoding="utf-8")
    config.stages.m5_feedback.wetlab_results_file = wetlab
    manifest = run_pipeline(config)
    assert [item.stage for item in manifest.stages] == ["m1_construct_screen", "m2_structure_screen", "m3_enrichment", "m4_glabridin_kinetics", "m5_wetlab_feedback"]
    assert '"status": "valid"' in (manifest.run_dir / "m4_glabridin_kinetics" / "reaction_predictions.json").read_text(encoding="utf-8")
    assert '"qc_passed": true' in (manifest.run_dir / "m5_wetlab_feedback" / "feedback.json").read_text(encoding="utf-8")
