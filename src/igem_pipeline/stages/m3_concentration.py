from pathlib import Path

from igem_pipeline.adapters import ExternalToolAdapter
from igem_pipeline.config import ProjectConfig
from igem_pipeline.io import write_models
from igem_pipeline.models import M2FusionAssessment, M3ConcentrationAssessment, StageOutput


def run_m3(
    config: ProjectConfig,
    run_dir: Path,
    assessments: list[M2FusionAssessment],
) -> tuple[list[M3ConcentrationAssessment], StageOutput]:
    stage_dir = run_dir / "m3_concentration"
    freesasa = ExternalToolAdapter("freesasa", config.tools.get("freesasa"))
    _mdanalysis = ExternalToolAdapter("mdanalysis", config.tools.get("mdanalysis"))

    outputs: list[M3ConcentrationAssessment] = []
    for assessment in assessments:
        fold_change = round(1.0 + 8.5 * assessment.m2_score, 3)
        saturation_risk = round(min(1, 0.22 + 0.58 * assessment.m2_score), 3)
        leakage_risk = round(max(0, 0.46 - 0.33 * assessment.m2_score + assessment.clash_risk * 0.2), 3)
        colocalization = round(min(1, 0.35 + assessment.m2_score * 0.55), 3)
        outputs.append(
            M3ConcentrationAssessment(
                candidate_id=assessment.candidate_id,
                local_concentration_fold_change=fold_change,
                binding_equilibrium_hint="mock Kp/Kd proxy from M2 score",
                saturation_risk=saturation_risk,
                leakage_risk=leakage_risk,
                oc_dmt_colocalization_score=colocalization,
                recommended_for_m4=(
                    saturation_risk <= config.stages.m3_concentration.saturation_threshold
                    and leakage_risk <= config.stages.m3_concentration.leakage_threshold
                ),
                notes=f"Accessibility placeholder for {freesasa.describe('freesasa <model.pdb>').tool}.",
            )
        )

    write_models(stage_dir, "concentration_assessments", outputs)
    return outputs, StageOutput(
        stage="m3_concentration",
        directory=stage_dir,
        json_file=stage_dir / "concentration_assessments.json",
        csv_file=stage_dir / "concentration_assessments.csv",
        record_count=len(outputs),
    )
