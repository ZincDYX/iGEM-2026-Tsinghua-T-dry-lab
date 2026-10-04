from __future__ import annotations

from pathlib import Path
import json

from igem_drylab.pipeline import load_config, run_pipeline


def test_pipeline_uses_real_metrics_when_configured(tmp_path):
    config = load_config(Path("configs/m1_m4_real_scoring_example.yaml"))
    config.run.output_dir = tmp_path

    manifest = run_pipeline(config)
    m2_text = (manifest.run_dir / "m2_structure_screen" / "fusion_assessments.json").read_text(encoding="utf-8")
    m4_text = manifest.stages[3].json_file.read_text(encoding="utf-8")

    m2_records = json.loads(m2_text)
    assert all(record["screen_verdict"] == "blocked" for record in m2_records)
    assert all(not record["recommended_for_m3"] for record in m2_records)
    assert all("M1 construct screen must pass" in record["missing_inputs"] for record in m2_records)
    assert '"status": "insufficient_data"' in m4_text
