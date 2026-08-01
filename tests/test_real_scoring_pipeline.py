from __future__ import annotations

from pathlib import Path

from igem_drylab.pipeline import load_config, run_pipeline


def test_pipeline_uses_real_metrics_when_configured(tmp_path):
    config = load_config(Path("configs/m1_m4_real_scoring_example.yaml"))
    config.run.output_dir = tmp_path

    manifest = run_pipeline(config)
    m2_text = (manifest.run_dir / "m2_fusion" / "fusion_assessments.json").read_text(encoding="utf-8")
    m4_text = (manifest.run_dir / "m4_reaction" / "reaction_predictions.json").read_text(encoding="utf-8")

    assert "Rule-based real M2 score" in m2_text
    assert "Lightweight ODE score" in m4_text
