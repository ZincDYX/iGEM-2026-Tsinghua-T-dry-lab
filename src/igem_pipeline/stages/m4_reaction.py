from pathlib import Path

from igem_pipeline.adapters import ExternalToolAdapter
from igem_pipeline.config import ProjectConfig
from igem_pipeline.io import write_models
from igem_pipeline.models import M3ConcentrationAssessment, M4ReactionPrediction, StageOutput


def run_m4(
    config: ProjectConfig,
    run_dir: Path,
    assessments: list[M3ConcentrationAssessment],
) -> tuple[list[M4ReactionPrediction], StageOutput]:
    stage_dir = run_dir / "m4_reaction"
    vina = ExternalToolAdapter("autodock_vina", config.tools.get("autodock_vina"))

    predictions: list[M4ReactionPrediction] = []
    for item in assessments:
        oc_first = round(
            min(1, item.oc_dmt_colocalization_score * 0.72 + (1 - item.leakage_risk) * 0.18),
            3,
        )
        dmt_later = round(
            min(1, item.local_concentration_fold_change / 10 * 0.55 + (1 - item.saturation_risk) * 0.25),
            3,
        )
        predicted_yield = round(
            min(
                1,
                config.stages.m4_reaction.oc_first_weight * oc_first
                + config.stages.m4_reaction.dmt_later_weight * dmt_later,
            ),
            3,
        )
        if predicted_yield >= 0.65 and item.recommended_for_m4:
            recommendation = "test"
        elif predicted_yield >= 0.4:
            recommendation = "iterate"
        else:
            recommendation = "drop"
        bottleneck = "saturation" if item.saturation_risk > item.leakage_risk else "leakage"
        predictions.append(
            M4ReactionPrediction(
                candidate_id=item.candidate_id,
                target_product=config.stages.m4_reaction.target_product,
                oc_first_feasibility=oc_first,
                dmt_later_feasibility=dmt_later,
                predicted_relative_yield=predicted_yield,
                bottleneck=bottleneck,
                recommendation=recommendation,
                notes=f"Docking placeholder for {vina.describe('vina --config <generated>').tool}.",
            )
        )

    write_models(stage_dir, "reaction_predictions", predictions)
    return predictions, StageOutput(
        stage="m4_reaction",
        directory=stage_dir,
        json_file=stage_dir / "reaction_predictions.json",
        csv_file=stage_dir / "reaction_predictions.csv",
        record_count=len(predictions),
    )
