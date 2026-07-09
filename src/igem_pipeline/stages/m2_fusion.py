from pathlib import Path

from igem_pipeline.adapters import ExternalToolAdapter
from igem_pipeline.config import ProjectConfig
from igem_pipeline.io import write_models
from igem_pipeline.models import M1Candidate, M2FusionAssessment, StageOutput


def run_m2(
    config: ProjectConfig,
    run_dir: Path,
    candidates: list[M1Candidate],
) -> tuple[list[M2FusionAssessment], StageOutput]:
    stage_dir = run_dir / "m2_fusion"
    abcfold = ExternalToolAdapter("abcfold", config.tools.get("abcfold"))
    enzyme_pair = "+".join(enzyme.id for enzyme in config.inputs.enzymes)

    assessments: list[M2FusionAssessment] = []
    for index, candidate in enumerate(candidates):
        activity_risk = round(max(0.05, 0.38 - 0.08 * candidate.llps_score + index * 0.02), 3)
        clash_risk = round(max(0.05, 0.22 + 0.04 * len(candidate.linker_id) / 10 - 0.03 * index), 3)
        weighted_penalty = (
            config.stages.m2_fusion.activity_penalty_weight * activity_risk
            + config.stages.m2_fusion.clash_penalty_weight * clash_risk
        )
        score = round(max(0, min(1, candidate.llps_score - weighted_penalty)), 3)
        assessments.append(
            M2FusionAssessment(
                candidate_id=candidate.candidate_id,
                scaffold_id=candidate.scaffold_id,
                linker_id=candidate.linker_id,
                enzyme_pair=enzyme_pair,
                fusion_topology="N-OC-linker-scaffold-linker-DMT-C",
                structure_model=abcfold.describe("abcfold predict <generated.yaml>").tool,
                activity_risk=activity_risk,
                clash_risk=clash_risk,
                m2_score=score,
                recommended_for_m3=score >= 0.45 and clash_risk < 0.5,
                notes="Mock score leaves room for ABCFold/Boltz/Chai structural replacement.",
            )
        )

    write_models(stage_dir, "fusion_assessments", assessments)
    return assessments, StageOutput(
        stage="m2_fusion",
        directory=stage_dir,
        json_file=stage_dir / "fusion_assessments.json",
        csv_file=stage_dir / "fusion_assessments.csv",
        record_count=len(assessments),
    )
