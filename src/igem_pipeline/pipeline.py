from pathlib import Path

from .config import ProjectConfig
from .io import ensure_dir
from .models import PipelineManifest
from .stages.m1_llps import run_m1
from .stages.m2_fusion import run_m2
from .stages.m3_concentration import run_m3
from .stages.m4_reaction import run_m4


def run_pipeline(config: ProjectConfig) -> PipelineManifest:
    run_dir = ensure_dir(Path(config.run.output_dir) / config.run.id)

    m1_records, m1_output = run_m1(config, run_dir)
    m2_records, m2_output = run_m2(config, run_dir, m1_records)
    m3_records, m3_output = run_m3(config, run_dir, m2_records)
    _m4_records, m4_output = run_m4(config, run_dir, m3_records)

    manifest = PipelineManifest(
        run_id=config.run.id,
        run_dir=run_dir,
        stages=[m1_output, m2_output, m3_output, m4_output],
    )
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return manifest
