from pathlib import Path

from igem_drylab.pipeline import load_config, run_pipeline


def test_software_fixture_artifact_manifest_smoke(tmp_path):
    config = load_config(Path("configs/m1_m4_example.yaml"))
    config.run.output_dir = tmp_path

    manifest = run_pipeline(config)

    assert manifest.run_id == "m1-m4-demo"
    assert [stage.stage for stage in manifest.stages] == [
        "m1_construct_screen",
        "m2_structure_screen",
        "m3_enrichment",
        "m4_glabridin_kinetics",
        "m5_wetlab_feedback",
    ]
    assert (tmp_path / "m1-m4-demo" / "manifest.json").exists()
    assert (tmp_path / "m1-m4-demo" / "m4_glabridin_kinetics" / "reaction_predictions.csv").exists()
