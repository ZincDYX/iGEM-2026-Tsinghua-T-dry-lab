from __future__ import annotations

from pathlib import Path

from igem_drylab.constructs import assess_linker
from igem_drylab.scoring.m2_structure import load_m2_structure_metrics, score_m2_structure

from .adapters import create_tool_adapter
from .config import ConstructDefinition, ProjectConfig
from .io import write_models
from .models import M1Candidate, M2FusionAssessment, M3ConcentrationAssessment, M4ReactionPrediction, StageOutput


def run_m1(config: ProjectConfig, run_dir: Path) -> tuple[list[M1Candidate], StageOutput]:
    """Perform sequence/definition negative screening, not LLPS prediction."""
    stage_dir = run_dir / "m1_construct_screen"
    definitions = config.inputs.constructs or _legacy_demo_definitions(config)
    candidates: list[M1Candidate] = []
    for definition in definitions:
        linker_id = definition.linker_ids[0] if definition.linker_ids else None
        linker = next((item for item in config.inputs.linkers if item.id == linker_id), None)
        flags: list[str] = []
        features = None
        if linker is None:
            flags.append("linker_not_specified_or_not_found")
        else:
            result = assess_linker(linker.sequence, forbidden_motifs=tuple(config.stages.m1_llps.forbidden_motifs))
            features = result.as_dict()
            if result.forbidden_motifs:
                flags.append("forbidden_motif")
            if result.aggregation_risk_flag:
                flags.append("sequence_aggregation_risk_proxy")
        if config.inputs.idr_id is None:
            flags.append("idr_not_explicitly_specified")
        elif config.inputs.idr_id not in definition.components:
            flags.append("idr_not_in_construct_components")
        priority = None
        if config.execution.mode == "demo" and features is not None:
            priority = round(max(0.0, 1.0 - 0.45 * len(flags) - 0.55 * float(features["hydrophobic_fraction"])), 3)
        candidates.append(M1Candidate(
            candidate_id=f"M1-{definition.id}", construct_definition=definition.model_dump(), scaffold_id=definition.scaffold_id,
            linker_id=linker_id, idr_id=config.inputs.idr_id, linker_features=features, screen_flags=flags,
            engineering_priority_score=priority, recommended_for_m2=not flags,
            status="valid" if not flags else "insufficient_data",
            data_quality="demo_fixture" if config.execution.mode == "demo" else "heuristic",
            missing_inputs=[flag for flag in flags if "not_specified" in flag or "not_found" in flag],
            recommended_next_action=["specify IDR and construct components in config"] if flags else [],
            notes="Engineering sequence screen only; it is not an LLPS probability or proof.",
        ))
    candidates.sort(key=lambda item: item.engineering_priority_score if item.engineering_priority_score is not None else -1.0, reverse=True)
    candidates = candidates[:config.stages.m1_llps.top_n]
    write_models(stage_dir, "candidates", candidates)
    return candidates, _stage_output("m1_construct_screen", stage_dir, "candidates", len(candidates))


def run_m2(config: ProjectConfig, run_dir: Path, candidates: list[M1Candidate]) -> tuple[list[M2FusionAssessment], StageOutput]:
    """Report observed structural negative-screen metrics; never fill absent metrics."""
    stage_dir = run_dir / "m2_structure_screen"
    adapter = create_tool_adapter("abcfold", config.tools.get("abcfold"))
    metrics = load_m2_structure_metrics(config.stages.m2_fusion.structure_metrics_file) if config.stages.m2_fusion.structure_metrics_file else {}
    assessments: list[M2FusionAssessment] = []
    for candidate in candidates:
        if not candidate.recommended_for_m2:
            assessments.append(M2FusionAssessment(
                candidate_id=candidate.candidate_id, construct_definition=candidate.construct_definition, status="insufficient_data",
                data_quality=candidate.data_quality, missing_inputs=["M1 construct screen must pass"],
                recommended_next_action=["resolve M1 screen flags before structural prediction"], notes="M2 skipped after M1 negative screen.",
            ))
            continue
        row = metrics.get(candidate.candidate_id)
        if row is None:
            assessments.append(M2FusionAssessment(
                candidate_id=candidate.candidate_id, construct_definition=candidate.construct_definition, status="insufficient_data",
                data_quality="demo_fixture" if config.execution.mode == "demo" else "predicted",
                structure_model=adapter.describe("abcfold predict <input>").tool,
                missing_inputs=["structure metrics: SASA, pocket RMSD, clashes, ipTM, pLDDT"],
                recommended_next_action=["supply parsed structure-prediction and pocket-screen metrics"], notes="No structure metrics were supplied; no risk score was generated.",
            ))
            continue
        scored = score_m2_structure(row)
        assessments.append(M2FusionAssessment(
            candidate_id=candidate.candidate_id, construct_definition=candidate.construct_definition, structure_model=adapter.describe("abcfold predict <input>").tool,
            status=scored.status, data_quality="predicted", available_metrics=scored.available_metrics, missing_metrics=scored.missing_metrics,
            confidence_level="complete" if not scored.missing_metrics else "partial", heuristic_structure_risk=scored.heuristic_structure_risk,
            pocket_sasa_retention=row.sasa_retention, pocket_rmsd_angstrom=row.pocket_rmsd_angstrom, clash_count=row.clash_count,
            recommended_for_m3=scored.recommended_for_m3, notes="; ".join(scored.reasons),
        ))
    write_models(stage_dir, "fusion_assessments", assessments)
    return assessments, _stage_output("m2_structure_screen", stage_dir, "fusion_assessments", len(assessments))


def run_m3(config: ProjectConfig, run_dir: Path, assessments: list[M2FusionAssessment]) -> tuple[list[M3ConcentrationAssessment], StageOutput]:
    """Temporary explicit block until the Kp/phi model is supplied by the next stage."""
    stage_dir = run_dir / "m3_enrichment"
    records = [M3ConcentrationAssessment(candidate_id=item.candidate_id, status="insufficient_data", data_quality="heuristic",
        missing_inputs=["phi", "species-specific partition coefficients", "enzyme abundance", "binding inputs"],
        recommended_next_action=["provide reviewed M3 parameter records"], notes="M3 does not infer concentration from M2 structure scores.") for item in assessments if item.recommended_for_m3]
    write_models(stage_dir, "concentration_assessments", records)
    return records, _stage_output("m3_enrichment", stage_dir, "concentration_assessments", len(records))


def run_m4(config: ProjectConfig, run_dir: Path, assessments: list[M3ConcentrationAssessment]) -> tuple[list[M4ReactionPrediction], StageOutput]:
    stage_dir = run_dir / "m4_glabridin_kinetics"
    records = [M4ReactionPrediction(candidate_id=item.candidate_id, target_product=config.stages.m4_reaction.target_product,
        status="insufficient_data", data_quality="heuristic", missing_inputs=["validated M3 enrichment", "reviewed kinetic parameters"],
        recommended_next_action=["run M3 with provenance before M4"], notes="M4 does not convert docking or structure proxy scores into enzyme activity.") for item in assessments]
    write_models(stage_dir, "reaction_predictions", records)
    return records, _stage_output("m4_glabridin_kinetics", stage_dir, "reaction_predictions", len(records))


def _legacy_demo_definitions(config: ProjectConfig) -> list[ConstructDefinition]:
    """Compatibility fixture only; real projects must declare constructs explicitly."""
    if config.execution.mode != "demo":
        return []
    return [ConstructDefinition(id=f"{scaffold.id}-{linker.id}", components=[scaffold.id, linker.id], linker_ids=[linker.id], scaffold_id=scaffold.id) for scaffold in config.inputs.scaffolds for linker in config.inputs.linkers]


def _stage_output(stage: str, directory: Path, stem: str, count: int) -> StageOutput:
    return StageOutput(stage=stage, directory=directory, json_file=directory / f"{stem}.json", csv_file=directory / f"{stem}.csv", record_count=count)
