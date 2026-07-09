from pathlib import Path

from igem_pipeline.adapters import ExternalToolAdapter
from igem_pipeline.config import ProjectConfig
from igem_pipeline.io import read_fasta, write_models
from igem_pipeline.models import M1Candidate, StageOutput


def run_m1(config: ProjectConfig, run_dir: Path) -> tuple[list[M1Candidate], StageOutput]:
    stage_dir = run_dir / "m1_llps"
    fasta = read_fasta(config.inputs.protein_fasta)
    idr_id = "IDR" if "IDR" in fasta else next(iter(fasta))
    calvados = ExternalToolAdapter("calvados", config.tools.get("calvados"))

    candidates: list[M1Candidate] = []
    for scaffold_index, scaffold in enumerate(config.inputs.scaffolds):
        for linker_index, linker in enumerate(config.inputs.linkers):
            base = 0.52 + 0.06 * scaffold_index + 0.03 * linker_index
            oligomer_bonus = min(scaffold.oligomeric_state / 48, 0.25)
            llps_score = min(0.95, round(base + oligomer_bonus, 3))
            if llps_score < config.stages.m1_llps.min_llps_score:
                state = "reject"
            elif llps_score < 0.7:
                state = "borderline"
            else:
                state = "promising"
            candidates.append(
                M1Candidate(
                    candidate_id=f"M1-{scaffold.id}-{linker.id}",
                    scaffold_id=scaffold.id,
                    linker_id=linker.id,
                    idr_id=idr_id,
                    llps_score=llps_score,
                    oligomeric_state=scaffold.oligomeric_state,
                    predicted_state=state,
                    adapter=calvados.describe("calvados run --config <generated>").tool,
                    notes="Mock score combines scaffold oligomeric state and linker length.",
                )
            )

    candidates = sorted(candidates, key=lambda item: item.llps_score, reverse=True)
    candidates = candidates[: config.stages.m1_llps.top_n]
    write_models(stage_dir, "candidates", candidates)
    return candidates, StageOutput(
        stage="m1_llps",
        directory=stage_dir,
        json_file=stage_dir / "candidates.json",
        csv_file=stage_dir / "candidates.csv",
        record_count=len(candidates),
    )
