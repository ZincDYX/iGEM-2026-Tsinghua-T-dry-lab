from __future__ import annotations

from pathlib import Path

from igem_drylab.kinetics import CascadeParameters
from igem_drylab.scoring.m2_structure import load_m2_structure_metrics, score_m2_structure
from igem_drylab.scoring.m4_reaction import load_docking_penalties, score_m4_ode

from .adapters import create_tool_adapter
from .config import ProjectConfig
from .io import read_fasta, write_models
from .models import (
    M1Candidate,
    M2FusionAssessment,
    M3ConcentrationAssessment,
    M4ReactionPrediction,
    StageOutput,
)


def run_m1(config: ProjectConfig, run_dir: Path) -> tuple[list[M1Candidate], StageOutput]:
    stage_dir = run_dir / "m1_llps"
    fasta = read_fasta(config.inputs.protein_fasta)
    idr_id = "IDR" if "IDR" in fasta else next(iter(fasta))
    calvados = create_tool_adapter("calvados", config.tools.get("calvados"))

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
                    notes="Mock score combines scaffold oligomeric state and linker order.",
                )
            )

    candidates = sorted(candidates, key=lambda item: item.llps_score, reverse=True)
    candidates = candidates[: config.stages.m1_llps.top_n]
    write_models(stage_dir, "candidates", candidates)
    return candidates, _stage_output("m1_llps", stage_dir, "candidates", len(candidates))


def run_m2(
    config: ProjectConfig,
    run_dir: Path,
    candidates: list[M1Candidate],
) -> tuple[list[M2FusionAssessment], StageOutput]:
    stage_dir = run_dir / "m2_fusion"
    abcfold = create_tool_adapter("abcfold", config.tools.get("abcfold"))
    enzyme_pair = "+".join(enzyme.id for enzyme in config.inputs.enzymes)
    real_metrics = (
        load_m2_structure_metrics(config.stages.m2_fusion.structure_metrics_file)
        if config.stages.m2_fusion.structure_metrics_file
        else {}
    )

    assessments: list[M2FusionAssessment] = []
    for index, candidate in enumerate(candidates):
        real_score = score_m2_structure(real_metrics[candidate.candidate_id]) if candidate.candidate_id in real_metrics else None
        if real_score is None:
            activity_risk = round(max(0.05, 0.38 - 0.08 * candidate.llps_score + index * 0.02), 3)
            clash_risk = round(max(0.05, 0.22 + 0.04 * len(candidate.linker_id) / 10 - 0.03 * index), 3)
            weighted_penalty = (
                config.stages.m2_fusion.activity_penalty_weight * activity_risk
                + config.stages.m2_fusion.clash_penalty_weight * clash_risk
            )
            score = round(max(0, min(1, candidate.llps_score - weighted_penalty)), 3)
            recommended = score >= 0.45 and clash_risk < 0.5
            notes = "Mock score fallback: no M2 structure metrics file entry for this candidate."
        else:
            activity_risk = real_score.activity_risk
            clash_risk = real_score.clash_risk
            score = real_score.m2_score
            recommended = real_score.recommended_for_m3
            notes = "Rule-based real M2 score: " + "; ".join(real_score.reasons)
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
                recommended_for_m3=recommended,
                notes=notes,
            )
        )

    write_models(stage_dir, "fusion_assessments", assessments)
    return assessments, _stage_output("m2_fusion", stage_dir, "fusion_assessments", len(assessments))


def run_m3(
    config: ProjectConfig,
    run_dir: Path,
    assessments: list[M2FusionAssessment],
) -> tuple[list[M3ConcentrationAssessment], StageOutput]:
    stage_dir = run_dir / "m3_concentration"
    freesasa = create_tool_adapter("freesasa", config.tools.get("freesasa"))

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
    return outputs, _stage_output("m3_concentration", stage_dir, "concentration_assessments", len(outputs))


def run_m4(
    config: ProjectConfig,
    run_dir: Path,
    assessments: list[M3ConcentrationAssessment],
) -> tuple[list[M4ReactionPrediction], StageOutput]:
    stage_dir = run_dir / "m4_reaction"
    vina = create_tool_adapter("autodock_vina", config.tools.get("autodock_vina"))
    docking_penalties = (
        load_docking_penalties(config.stages.m4_reaction.docking_penalties_file)
        if config.stages.m4_reaction.docking_penalties_file
        else {}
    )

    predictions: list[M4ReactionPrediction] = []
    for item in assessments:
        ode_score = score_m4_ode(
            candidate_id=item.candidate_id,
            params=CascadeParameters(
                oc_total=item.oc_dmt_colocalization_score,
                dmt_total=item.oc_dmt_colocalization_score,
                partition_oc=max(1.0, item.local_concentration_fold_change),
                partition_dmt=max(1.0, item.local_concentration_fold_change),
                activity_ratio_oc=max(0.1, 1.0 - item.leakage_risk),
                activity_ratio_dmt=max(0.1, 1.0 - item.saturation_risk),
            ),
            docking_penalty=docking_penalties.get(item.candidate_id),
            t_end=config.stages.m4_reaction.t_end,
        )
        oc_first = round(min(1, item.oc_dmt_colocalization_score * 0.72 + (1 - item.leakage_risk) * 0.18), 3)
        dmt_later = round(min(1, 1.0 - ode_score.leakage_proxy), 3)
        predicted_yield = ode_score.relative_yield
        recommendation = ode_score.recommendation if item.recommended_for_m4 else "iterate"
        bottleneck = "saturation" if item.saturation_risk > item.leakage_risk else "leakage"
        docking_note = (
            f"docking activity multiplier={docking_penalties[item.candidate_id].activity_multiplier}; "
            if item.candidate_id in docking_penalties
            else "no docking penalty supplied; "
        )
        predictions.append(
            M4ReactionPrediction(
                candidate_id=item.candidate_id,
                target_product=config.stages.m4_reaction.target_product,
                oc_first_feasibility=oc_first,
                dmt_later_feasibility=dmt_later,
                predicted_relative_yield=predicted_yield,
                bottleneck=bottleneck,
                recommendation=recommendation,
                notes=(
                    f"Lightweight ODE score with {docking_note}"
                    f"product_final={ode_score.product_final}, leakage_proxy={ode_score.leakage_proxy}; "
                    f"adapter={vina.describe('vina --config <generated>').tool}."
                ),
            )
        )

    write_models(stage_dir, "reaction_predictions", predictions)
    return predictions, _stage_output("m4_reaction", stage_dir, "reaction_predictions", len(predictions))


def _stage_output(stage: str, directory: Path, stem: str, count: int) -> StageOutput:
    return StageOutput(
        stage=stage,
        directory=directory,
        json_file=directory / f"{stem}.json",
        csv_file=directory / f"{stem}.csv",
        record_count=count,
    )
