from pathlib import Path

import pandas as pd

from igem_pipeline.config import load_config
from igem_pipeline.pipeline import run_pipeline


def test_example_pipeline_writes_stage_outputs(tmp_path: Path) -> None:
    config = load_config(Path("configs/example.yaml"))
    config.run.output_dir = tmp_path

    manifest = run_pipeline(config)

    assert manifest.run_dir == tmp_path / "demo-run"
    assert len(manifest.stages) == 4
    for stage in manifest.stages:
        assert stage.json_file.exists()
        assert stage.csv_file.exists()
        assert stage.record_count > 0

    m2_table = pd.read_csv(manifest.run_dir / "m2_fusion" / "fusion_assessments.csv")
    m3_table = pd.read_csv(
        manifest.run_dir / "m3_concentration" / "concentration_assessments.csv"
    )
    assert set(m2_table["candidate_id"]) == set(m3_table["candidate_id"])

    m4_table = pd.read_csv(manifest.run_dir / "m4_reaction" / "reaction_predictions.csv")
    assert {"drop", "iterate", "test"}.issuperset(set(m4_table["recommendation"]))
