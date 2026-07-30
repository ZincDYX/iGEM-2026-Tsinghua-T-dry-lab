from pathlib import Path

from igem_drylab.pipeline import load_config, run_pipeline


def test_m1_m4_pipeline_skeleton_writes_expected_outputs(tmp_path):
    config = load_config(Path("configs/m1_m4_example.yaml"))
    config.run.output_dir = tmp_path

    manifest = run_pipeline(config)

    assert manifest.run_id == "m1-m4-demo"
    assert [stage.stage for stage in manifest.stages] == [
        "m1_llps",
        "m2_fusion",
        "m3_concentration",
        "m4_reaction",
    ]
    assert (tmp_path / "m1-m4-demo" / "manifest.json").exists()
    assert (tmp_path / "m1-m4-demo" / "m4_reaction" / "reaction_predictions.csv").exists()
