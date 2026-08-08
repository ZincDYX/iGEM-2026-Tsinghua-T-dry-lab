from pathlib import Path

from igem_drylab.pipeline import load_config, run_pipeline


def test_real_mode_never_falls_back_to_mock_scores(tmp_path):
    config = load_config(Path("configs/m1_m4_real_scoring_example.yaml"))
    config.run.output_dir = tmp_path
    manifest = run_pipeline(config)
    m1 = (manifest.run_dir / "m1_construct_screen" / "candidates.json").read_text(encoding="utf-8")
    m3 = (manifest.run_dir / "m3_enrichment" / "concentration_assessments.json").read_text(encoding="utf-8")
    assert "llps_score" not in m1
    assert "Mock score" not in m1
    assert '"status": "insufficient_data"' in m3
