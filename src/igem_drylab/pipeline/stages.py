from __future__ import annotations

from pathlib import Path
from dataclasses import replace
from hashlib import sha256
import numpy as np
import json
import yaml

from igem_drylab.constructs import (
    ConstructRegistry,
    DisorderEvidence,
    FusionToolEvidence,
    M1FeatureDefinitions,
    M1V3Rules,
    SecondaryStructureEvidence,
    compute_sequence_features,
    screen_sequence_v3,
)
from igem_drylab.enrichment import EnrichmentInput, RecruitmentInput, calculate_many, calculate_recruitment
from igem_drylab.kinetics import GlabridinKineticParameters, InductionGate, simulate_glabridin
from igem_drylab.galatea_m3_m4 import M3EffectiveRatioInputs, load_author_native_reactions, run_galatea_full_m4, run_m3_effective_ratio
from igem_drylab.full_network import PhaseDistribution, TemporalGate, TransportParameters
from igem_drylab.published_reference import run_published_reference, write_published_reference_reproduction
from igem_drylab.parameters import ParameterRecord, full_m4_kinetic_requirements, m3_requirements, m4_kinetic_requirements, recruitment_requirements, validate_parameters
from igem_drylab.parameters.requirements import requirement_name_to_kernel_key, requirements_for_stage
from igem_drylab.parameters.dimensions import normalize_concentration
from igem_drylab.scoring.m2_structure import load_m2_structure_metrics, score_m2_structure
from igem_drylab.wetlab import compare_prediction, diagnose_discrepancy, evaluate_residual_significance, load_wetlab_results, quality_control, replicate_variation, fit_mechanistic_parameter
from igem_drylab.wetlab.canonical import canonicalize_metabolite

from .config import ConstructDefinition, ProjectConfig, canonical_m4_condition_id
from .io import write_models
from .models import M1Candidate, M2FusionAssessment, M3ConcentrationAssessment, M4CandidateContext, M4ReactionPrediction, M5FeedbackAssessment, StageOutput


def run_m1(config: ProjectConfig, run_dir: Path) -> tuple[list[M1Candidate], StageOutput]:
    """Perform sequence/definition negative screening, not LLPS prediction."""
    stage_dir = run_dir / "m1_construct_screen"
    settings = config.stages.m1_llps
    feature_definitions, definitions_hash = M1FeatureDefinitions.from_yaml(settings.feature_definitions_file)
    rules = M1V3Rules.model_validate(yaml.safe_load(settings.rules_file.read_text(encoding="utf-8")))
    predictor_evidence = _load_m1_predictor_evidence(settings.predictor_evidence_file)
    construct_definitions = config.inputs.constructs + [_definition_from_registry(item) for item in ConstructRegistry(config.inputs.construct_records).query()]
    construct_definitions = construct_definitions or _legacy_demo_definitions(config)
    candidates: list[M1Candidate] = []
    for definition in construct_definitions:
        linker_id = definition.linker_ids[0] if definition.linker_ids else None
        linker = next((item for item in config.inputs.linkers if item.id == linker_id), None)
        flags: list[str] = []
        features = None
        if linker is None:
            flags.append("linker_not_specified_or_not_found")
        else:
            result = compute_sequence_features(
                linker.sequence,
                definitions=feature_definitions,
                definitions_sha256=definitions_hash,
                forbidden_motifs=tuple(settings.forbidden_motifs),
            )
            features = result.as_dict()
            evidence = predictor_evidence.get(linker.id, {})
            screen = screen_sequence_v3(
                features=result,
                sequence_kind=linker.sequence_kind,
                rules=rules,
                disorder=(
                    DisorderEvidence.model_validate(evidence["disorder"])
                    if isinstance(evidence.get("disorder"), dict)
                    else None
                ),
                secondary_structure=(
                    SecondaryStructureEvidence.model_validate(evidence["secondary_structure"])
                    if isinstance(evidence.get("secondary_structure"), dict)
                    else None
                ),
                fusion_evidence=(
                    FusionToolEvidence.model_validate(evidence["fusion"])
                    if isinstance(evidence.get("fusion"), dict)
                    else None
                ),
                localization_context=(
                    "er_anchored" if "ER" in (definition.fusion_orientation or "").upper() else "cytosolic"
                ),
                require_external_evidence=(
                    config.execution.mode == "real" and settings.require_external_evidence_in_real_mode
                ),
            )
            flags.extend(screen.hard_reject_reasons)
            if screen.verdict == "blocked":
                flags.append("missing_required_M1_predictor_evidence")
        if config.inputs.idr_id is None:
            flags.append("idr_not_explicitly_specified")
        elif config.inputs.idr_id not in definition.components:
            flags.append("idr_not_in_construct_components")
        priority = None
        screen_verdict = screen.verdict if linker is not None else "blocked"
        missing_predictors = screen.missing_required_evidence if linker is not None else []
        recommended = not flags or definition.experimental_baseline
        candidates.append(M1Candidate(
            candidate_id=f"M1-{definition.id}", construct_id=definition.id, construct_definition=definition.model_dump(), scaffold_id=definition.scaffold_id,
            linker_id=linker_id, idr_id=config.inputs.idr_id, linker_features=features, screen_flags=flags,
            formula_version=(result.formula_version if linker is not None else None),
            rule_version=rules.rule_version,
            feature_definitions_sha256=(result.feature_definitions_sha256 if linker is not None else None),
            sequence_sha256=(result.sequence_sha256 if linker is not None else None),
            sequence_screen_verdict=screen_verdict,
            missing_predictor_evidence=missing_predictors,
            engineering_priority_score=priority, recommended_for_m2=recommended,
            status=(
                "invalid_input"
                if screen_verdict == "reject"
                else ("insufficient_data" if flags or screen_verdict == "blocked" else "valid")
            ),
            data_quality="demo_fixture" if config.execution.mode == "demo" else "heuristic",
            missing_inputs=[
                *[flag for flag in flags if "not_specified" in flag or "not_found" in flag],
                *missing_predictors,
            ],
            recommended_next_action=(
                ["provide real versioned M1 predictor outputs for the exact sequence hash"]
                if missing_predictors and config.execution.mode == "real"
                else (["specify IDR and construct components in config"] if flags else [])
            ),
            notes=(
                "M1 V3 negative screen with exact feature equations. Soft-risk auto-grading and rank_score "
                "remain unavailable because the source does not define every risk direction or reviewed weights. "
                + (
                    "This measured experimental baseline remains eligible for retrospective M2 assessment; "
                    "that does not turn its missing M1 evidence into a pass."
                    if definition.experimental_baseline and flags
                    else ""
                )
            ),
        ))
    candidates.sort(key=lambda item: item.engineering_priority_score if item.engineering_priority_score is not None else -1.0, reverse=True)
    candidates = candidates[:config.stages.m1_llps.top_n]
    write_models(stage_dir, "candidates", candidates)
    return candidates, _stage_output("m1_construct_screen", stage_dir, "candidates", len(candidates))


def _load_m1_predictor_evidence(path: Path | None) -> dict[str, dict[str, object]]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not all(isinstance(key, str) and isinstance(value, dict) for key, value in payload.items()):
        raise ValueError("M1 predictor evidence must be an object keyed by linker/sequence id")
    return payload


def run_m2(config: ProjectConfig, run_dir: Path, candidates: list[M1Candidate]) -> tuple[list[M2FusionAssessment], StageOutput]:
    """Report observed structural negative-screen metrics; never fill absent metrics."""
    stage_dir = run_dir / "m2_structure_screen"
    metrics = load_m2_structure_metrics(config.stages.m2_fusion.structure_metrics_file) if config.stages.m2_fusion.structure_metrics_file else {}
    assessments: list[M2FusionAssessment] = []
    for candidate in candidates:
        if not candidate.recommended_for_m2:
            assessments.append(M2FusionAssessment(
                candidate_id=candidate.candidate_id, construct_id=candidate.construct_id, construct_definition=candidate.construct_definition, status="insufficient_data",
                data_quality=candidate.data_quality, missing_inputs=["M1 construct screen must pass"],
                recommended_next_action=["resolve M1 screen flags before structural prediction"], notes="M2 skipped after M1 negative screen.",
            ))
            continue
        row = metrics.get(candidate.candidate_id)
        if row is None:
            assessments.append(M2FusionAssessment(
                candidate_id=candidate.candidate_id, construct_id=candidate.construct_id, construct_definition=candidate.construct_definition, status="insufficient_data",
                data_quality="demo_fixture" if config.execution.mode == "demo" else "predicted",
                structure_model=None,
                missing_inputs=["structure metrics: SASA, pocket RMSD, clashes, ipTM, pLDDT"],
                recommended_next_action=["supply parsed structure-prediction and pocket-screen metrics"], notes="No structure metrics were supplied; no risk score was generated.",
            ))
            continue
        scored = score_m2_structure(row)
        assessments.append(M2FusionAssessment(
            candidate_id=candidate.candidate_id, construct_id=candidate.construct_id, construct_definition=candidate.construct_definition, structure_model=row.source_model or row.source_tool,
            structure_source_tool=row.source_tool, structure_artifact_path=row.artifact_path, structure_artifact_sha256=row.artifact_sha256,
            status=scored.status, data_quality="predicted", available_metrics=scored.available_metrics, missing_metrics=scored.missing_metrics,
            confidence_level="complete" if not scored.missing_metrics else "partial", heuristic_structure_risk=scored.heuristic_structure_risk,
            pocket_sasa_retention=row.sasa_retention, pocket_rmsd_angstrom=row.pocket_rmsd_angstrom, clash_count=row.clash_count,
            recommended_for_m3=scored.recommended_for_m3, notes="; ".join(scored.reasons),
        ))
    write_models(stage_dir, "fusion_assessments", assessments)
    return assessments, _stage_output("m2_structure_screen", stage_dir, "fusion_assessments", len(assessments))


def run_m3(config: ProjectConfig, run_dir: Path, assessments: list[M2FusionAssessment]) -> tuple[list[M3ConcentrationAssessment], StageOutput]:
    """Calculate species-specific two-phase concentrations from reviewed inputs."""
    stage_dir = run_dir / "m3_enrichment"
    requirements = requirements_for_stage(config, "m3")
    core_requirements = [item for item in requirements if item.blocking]
    records: list[M3ConcentrationAssessment] = []
    for assessment in assessments:
        if not assessment.recommended_for_m3:
            continue
        construct_id = assessment.construct_id
        condition_id = config.stages.m4_reaction.condition_id or _condition_id_if_defined(config.stages.m4_reaction)
        selected, missing = validate_parameters(config.parameters, requirements=core_requirements, allow_assumptions=config.execution.allow_assumptions, host=config.experimental_context.host, strain=config.experimental_context.strain, assay_system=config.experimental_context.assay_system, pH=config.experimental_context.pH, temperature_c=config.experimental_context.temperature_c, construct_id=construct_id, condition_id=condition_id, require_provenance=config.execution.mode == "real" and config.execution.require_provenance)
        if missing:
            records.append(M3ConcentrationAssessment(candidate_id=assessment.candidate_id, construct_id=construct_id, status="insufficient_data", data_quality="heuristic",
                missing_inputs=missing, recommended_next_action=["add reviewed phi, total concentration, and Kp ParameterRecords"],
                notes="M3 does not infer partitioning from M1/M2 scores."))
            continue
        phi = selected["phi"].canonical_value
        if config.stages.m3_concentration.recruitment_mode == "effective_ratio":
            settings = config.stages.m3_concentration
            author_native = config.stages.m4_reaction.unit_mode == "author_native_sensitivity"
            if author_native:
                scales = settings.author_native_inputs
                if scales is None:  # ProjectConfig normally rejects this before execution.
                    records.append(M3ConcentrationAssessment(candidate_id=assessment.candidate_id, construct_id=construct_id, status="insufficient_data", data_quality="heuristic", missing_inputs=["author_native_inputs"], notes="Author-native sensitivity requires explicit nonphysical enzyme scales."))
                    continue
                ptr_total, pt_total = scales.ptr_scale, scales.pt_scale
                oc_total, dmt_total = scales.oc_scale, scales.dmt_scale
                scale_assumption = "author_native enzyme scale from explicit sensitivity input; not measured protein abundance"
            else:
                ptr_total = selected["ptr_total"].canonical_value
                pt_total = selected["pt_total"].canonical_value
                oc_total = selected["oc_total"].canonical_value
                dmt_total = selected["dmt_total"].canonical_value
                scale_assumption = "enzyme abundance is a reviewed physical concentration input"
            result = run_m3_effective_ratio(M3EffectiveRatioInputs(
                phi=phi,
                ptr_total=ptr_total,
                pt_total=pt_total,
                oc_total=oc_total,
                dmt_total=dmt_total,
                slot_ratio_sh3_to_pdz=settings.slot_ratio_sh3_to_pdz or 0.0,
                total_recruited_fraction=settings.total_recruited_fraction or 0.0,
                recruitment_bias_oc_vs_dmt=settings.recruitment_bias_oc_vs_dmt,
                ptr_pt_phase_handling=settings.ptr_pt_phase_handling,
                metabolite_kp={species: selected[f"partition_x{species}"].canonical_value for species in ("8", "9", "10", "11", "12", "13", "14", "15")},
            ))
            enzyme_distribution = {
                name: {"dense": value.dense, "dilute": value.dilute, "partition_coefficient": value.dense / value.dilute if value.dilute else 0.0}
                for name, value in result.enzyme_distributions.items()
            }
            oc, dmt = result.enzyme_distributions["OC"], result.enzyme_distributions["DMT"]
            recruited = {
                "OC": result.recruitment.oc_bound / oc_total if oc_total else 0.0,
                "DMT": result.recruitment.dmt_bound / dmt_total if dmt_total else 0.0,
            }
            context = M4CandidateContext(
                candidate_id=assessment.candidate_id, construct_id=construct_id, condition_id=condition_id, phi=phi,
                enzyme_distribution=enzyme_distribution, binding_recruited_fraction=recruited,
                metabolite_partition_coefficients=result.metabolite_kp,
                site_occupancy={}, parameter_ids=sorted(resolution.selected_parameter.parameter_id for resolution in selected.values() if resolution.selected_parameter),
                provenance_summary=_provenance_summary(selected.values()), assumptions=[*result.assumptions, scale_assumption],
            )
            records.append(M3ConcentrationAssessment(
                candidate_id=assessment.candidate_id, construct_id=construct_id, status="valid", data_quality=_data_quality(selected.values()),
                concentrations={name: {"dense_concentration": value.dense, "dilute_concentration": value.dilute} for name, value in result.enzyme_distributions.items()},
                dense_oc_dmt_ratio=oc.dense / dmt.dense if dmt.dense else None,
                whole_cell_oc_dmt_ratio=oc_total / dmt_total if dmt_total else None,
                fraction_in_dense={"OC": result.recruitment.oc_bound / oc_total if oc_total else 0.0, "DMT": result.recruitment.dmt_bound / dmt_total if dmt_total else 0.0},
                binding_recruitment_status="valid", binding_recruited_fraction=recruited, site_occupancy={}, recommended_for_m4=True,
                parameter_ids=sorted(resolution.selected_parameter.parameter_id for resolution in selected.values() if resolution.selected_parameter),
                provenance_summary=_provenance_summary(selected.values()), m4_candidate_context=context,
                notes=("Author-native M3 sensitivity: relative enzyme scale, not measured protein abundance."
                       if author_native else "Effective-ratio M3 mode: recruitment changes mass-conserving OC/DMT phase abundance, not kcat.")
            ))
            continue
        inputs = [EnrichmentInput(species_id=item, total_concentration=selected[f"{item.lower()}_total"].canonical_value,
            partition_coefficient=selected[f"partition_{item.lower()}"].canonical_value,
            partition_source=selected[f"partition_{item.lower()}"].selected_parameter.source_reference,
            partition_uncertainty=selected[f"partition_{item.lower()}"].selected_parameter.uncertainty) for item in ("PT", "OC", "DMT")]
        result = calculate_many(inputs, phi=phi)
        oc = result["OC"]
        dmt = result["DMT"]
        binding_recruitment = {}
        occupancy = {}
        auxiliary, _ = validate_parameters(config.parameters, requirements=[item for item in requirements if not item.blocking], allow_assumptions=config.execution.allow_assumptions, host=config.experimental_context.host, strain=config.experimental_context.strain, assay_system=config.experimental_context.assay_system, pH=config.experimental_context.pH, temperature_c=config.experimental_context.temperature_c, construct_id=construct_id, condition_id=condition_id, require_provenance=config.execution.mode == "real" and config.execution.require_provenance)
        for entry in config.stages.m3_concentration.recruitment:
            needed = [entry.enzyme_total_parameter, entry.site_total_parameter, entry.kd_parameter, *([entry.hill_coefficient_parameter] if entry.hill_coefficient_parameter else [])]
            if any(auxiliary.get(name) is None or auxiliary[name].status != "resolved" for name in needed):
                continue
            enzyme = entry.enzyme_id
            hill = auxiliary[entry.hill_coefficient_parameter].canonical_value if entry.hill_coefficient_parameter else config.stages.m3_concentration.hill_coefficient
            if config.stages.m3_concentration.binding_model == "hill" and hill is None:
                continue
            if config.stages.m3_concentration.binding_model == "hill" and entry.hill_coefficient_parameter is None and not config.execution.allow_assumptions:
                continue
            recruitment_result = calculate_recruitment(RecruitmentInput(enzyme_id=enzyme, enzyme_total=auxiliary[entry.enzyme_total_parameter].canonical_value, site_total=auxiliary[entry.site_total_parameter].canonical_value, kd=auxiliary[entry.kd_parameter].canonical_value, binding_model=config.stages.m3_concentration.binding_model, hill_coefficient=hill))
            binding_recruitment[enzyme] = recruitment_result.recruited_fraction; occupancy[enzyme] = recruitment_result.site_occupancy
        context = M4CandidateContext(candidate_id=assessment.candidate_id, construct_id=construct_id, condition_id=condition_id,
            phi=phi,
            enzyme_distribution={name: {"dense": value.dense_concentration, "dilute": value.dilute_concentration, "partition_coefficient": value.partition_coefficient} for name, value in result.items()},
            metabolite_partition_coefficients={species: selected[f"partition_x{species}"].canonical_value for species in ("8", "9", "10", "11", "12", "13", "14", "15") if f"partition_x{species}" in selected},
            binding_recruited_fraction=binding_recruitment, site_occupancy=occupancy,
            parameter_ids=sorted(resolution.selected_parameter.parameter_id for resolution in selected.values() if resolution.selected_parameter),
            provenance_summary=_provenance_summary(selected.values()),
            assumptions=["rapid_partition_equilibrium", "enzyme distribution is computed from approved abundance and Kp; recruitment is reported separately and does not modify kcat or abundance"],
        )
        records.append(M3ConcentrationAssessment(candidate_id=assessment.candidate_id, construct_id=construct_id, status="valid", data_quality=_data_quality(selected.values()),
            concentrations={key: value.model_dump() for key, value in result.items()},
            dense_oc_dmt_ratio=oc.dense_concentration / dmt.dense_concentration if dmt.dense_concentration else None,
            whole_cell_oc_dmt_ratio=selected["oc_total"].canonical_value / selected["dmt_total"].canonical_value if selected["dmt_total"].canonical_value else None,
            fraction_in_dense={key: value.fraction_in_dense for key, value in result.items()},
            binding_recruitment_status="not_requested" if not config.stages.m3_concentration.recruitment else ("valid" if binding_recruitment else "insufficient_data"),
            binding_recruited_fraction=binding_recruitment,
            site_occupancy=occupancy,
            recommended_for_m4=True, parameter_ids=sorted(result.selected_parameter.parameter_id for result in selected.values() if result.selected_parameter),
            provenance_summary=_provenance_summary(selected.values()),
            m4_candidate_context=context,
            notes="Rapid-equilibrium mass-conserving enrichment; Kp values are explicit inputs."))
    write_models(stage_dir, "concentration_assessments", records)
    return records, _stage_output("m3_enrichment", stage_dir, "concentration_assessments", len(records))


def run_m4(config: ProjectConfig, run_dir: Path, assessments: list[M3ConcentrationAssessment]) -> tuple[list[M4ReactionPrediction], StageOutput]:
    if config.stages.m4_reaction.network_mode == "published_reference":
        return _run_published_reference_m4(config, run_dir)
    if config.stages.m4_reaction.network_mode == "galatea_full_competitive":
        return _run_full_network_m4(config, run_dir, assessments)
    stage_dir = run_dir / "m4_glabridin_kinetics"
    gates = config.stages.m4_reaction
    gate_missing = [name for name in ("pt_gate", "oc_gate", "dmt_gate") if getattr(gates, name) is None]
    records: list[M4ReactionPrediction] = []
    for item in assessments:
        if item.status != "valid":
            records.append(_m4_insufficient(item.candidate_id, config, ["validated M3 enrichment"], construct_id=item.construct_id))
            continue
        elif item.m4_candidate_context is None:
            records.append(_m4_insufficient(item.candidate_id, config, ["candidate-specific M3 context"], construct_id=item.construct_id))
            continue
        else:
            construct_id = item.m4_candidate_context.construct_id
            condition_id = item.m4_candidate_context.condition_id
            selected, missing = validate_parameters(config.parameters, requirements=m4_kinetic_requirements(include_degradation=gates.enable_degradation), allow_assumptions=config.execution.allow_assumptions, host=config.experimental_context.host, strain=config.experimental_context.strain, assay_system=config.experimental_context.assay_system, pH=config.experimental_context.pH, temperature_c=config.experimental_context.temperature_c, construct_id=construct_id, condition_id=condition_id, require_provenance=config.execution.mode == "real" and config.execution.require_provenance)
            explicit_condition_missing = config.execution.mode == "real" and not gates.condition_id
            if missing or gate_missing or explicit_condition_missing:
                records.append(_m4_insufficient(item.candidate_id, config, missing + gate_missing + (["explicit_condition_id"] if explicit_condition_missing else []), construct_id=construct_id))
                continue
            initial = gates.initial_state
            if initial is None:
                records.append(_m4_insufficient(item.candidate_id, config, ["initial_state"], construct_id=construct_id))
                continue
            if config.execution.mode == "real" and (initial.x13 != 0 or initial.x15 != 0):
                records.append(_m4_insufficient(item.candidate_id, config, ["real_mode_requires_zero_initial_x13_x15_for_net_production_semantics"], construct_id=construct_id))
                continue
            values = _glabridin_parameter_values(selected)
            values.update(_candidate_enzyme_values(item.m4_candidate_context))
            params = GlabridinKineticParameters(**values)
            pt_gate, oc_gate, dmt_gate = InductionGate(**gates.pt_gate.model_dump(exclude={"time_unit"})), InductionGate(**gates.oc_gate.model_dump(exclude={"time_unit"})), InductionGate(**gates.dmt_gate.model_dump(exclude={"time_unit"}))
            delayed = simulate_glabridin(params, pt_gate=pt_gate, oc_gate=oc_gate, dmt_gate=dmt_gate, initial=initial.as_tuple(), t_end=gates.t_end)
            baseline_off = max(0.0, dmt_gate.off_time - dmt_gate.on_time) if dmt_gate.off_time is not None else None
            baseline = simulate_glabridin(params, pt_gate=pt_gate, oc_gate=oc_gate, dmt_gate=InductionGate(on_time=0.0, basal=dmt_gate.basal, induced=dmt_gate.induced, off_time=baseline_off, mode=dmt_gate.mode, transition_width=dmt_gate.transition_width), initial=initial.as_tuple(), t_end=gates.t_end)
            final_15, final_13 = float(delayed.x15[-1]), float(delayed.x13[-1])
            baseline_13, baseline_15 = float(baseline.x13[-1]), float(baseline.x15[-1])
            delta_13, delta_15 = final_13 - initial.x13, final_15 - initial.x15
            side_product_fraction = delta_13 / (delta_13 + delta_15) if delta_13 + delta_15 > 0 else 0.0
            condition_fingerprint = sha256(condition_id.encode("utf-8")).hexdigest()[:10]
            trajectory = stage_dir / f"{item.candidate_id}_{condition_fingerprint}_trajectory.json"
            trajectory.parent.mkdir(parents=True, exist_ok=True)
            trajectory.write_text(json.dumps({"scientific_contract_version": "pre-real-data-frozen", "candidate_id": item.candidate_id, "construct_id": construct_id, "condition_id": condition_id, "parameter_ids": sorted({*item.m4_candidate_context.parameter_ids, *(result.selected_parameter.parameter_id for result in selected.values() if result.selected_parameter)}), "time_unit": "h", "concentration_unit": "uM", "time": delayed.time.tolist(), "x9": delayed.x9.tolist(), "x10": delayed.x10.tolist(), "x11": delayed.x11.tolist(), "x13": delayed.x13.tolist(), "x15": delayed.x15.tolist()}), encoding="utf-8")
            recommendation, recommendation_evidence = _recommend_m4(side_product_fraction, delta_15 / gates.t_end, baseline_13 - initial.x13, delta_13, delta_15, baseline_15 - initial.x15, gates)
            combined_provenance = _merge_provenance(item.m4_candidate_context.provenance_summary, _provenance_summary(selected.values()))
            records.append(M4ReactionPrediction(candidate_id=item.candidate_id, construct_id=construct_id, condition_id=condition_id, target_product=gates.target_product, status="valid", data_quality=_data_quality_from_summary(combined_provenance),
                final_15=final_15, final_13=final_13, side_product_fraction_13=side_product_fraction, leakage_fraction=side_product_fraction, productivity=delta_15 / gates.t_end,
                recommendation=recommendation, candidate_context=item.m4_candidate_context,
                simulation_inputs={"parameters": values, "initial": initial.model_dump(), "pt_gate": gates.pt_gate.model_dump(), "oc_gate": gates.oc_gate.model_dump(), "dmt_gate": gates.dmt_gate.model_dump(), "t_end": gates.t_end},
                baseline_comparison={"13_reduction": ((baseline_13 - initial.x13) - delta_13) / (baseline_13 - initial.x13) if baseline_13 != initial.x13 else 0.0, "15_improvement": (delta_15 - (baseline_15 - initial.x15)) / (baseline_15 - initial.x15) if baseline_15 != initial.x15 else 0.0, "peak_11_change": float(delayed.x11.max() - baseline.x11.max())},
                bottleneck="premature_dmt_side_reaction" if side_product_fraction > gates.max_side_product_fraction_13 else "review_time_course", trajectory_artifact=trajectory, recommendation_evidence=recommendation_evidence, assumptions=["rapid partition equilibrium", "competitive DMT kinetics", "no explicit metabolite export model", *( ["approved degradation rates enabled"] if gates.enable_degradation else ["degradation kernel disabled; all kdeg values set to zero"] )],
                parameter_ids=sorted({*item.m4_candidate_context.parameter_ids, *(result.selected_parameter.parameter_id for result in selected.values() if result.selected_parameter)}),
                provenance_summary=combined_provenance,
                notes=f"M4 consumed candidate-specific M3 enzyme distributions; {'modeled degradation loss=' + format(delayed.modeled_degradation_loss, '.3g') if gates.enable_degradation else 'mass-balance error=' + format(delayed.mass_balance_error, '.3g')}; compound 13 is a side-product proxy, not extracellular leakage; recruitment and docking were not converted into enzyme activity."))
    write_models(stage_dir, "reaction_predictions", records)
    return records, _stage_output("m4_glabridin_kinetics", stage_dir, "reaction_predictions", len(records))


def _run_full_network_m4(config: ProjectConfig, run_dir: Path, assessments: list[M3ConcentrationAssessment]) -> tuple[list[M4ReactionPrediction], StageOutput]:
    """Production Galatea M4: full 8-compound / 10-reaction competitive network."""
    stage_dir = run_dir / "m4_glabridin_full_network"
    settings = config.stages.m4_reaction
    author_native = settings.unit_mode == "author_native_sensitivity"
    requirements = requirements_for_stage(config, "m4")
    records: list[M4ReactionPrediction] = []
    for item in assessments:
        context = item.m4_candidate_context
        if item.status != "valid" or context is None:
            records.append(_m4_insufficient(item.candidate_id, config, ["valid effective-ratio or finite-site M3 context"], construct_id=item.construct_id))
            continue
        selected, missing = validate_parameters(
            config.parameters, requirements=requirements, allow_assumptions=config.execution.allow_assumptions,
            host=config.experimental_context.host, strain=config.experimental_context.strain,
            assay_system=config.experimental_context.assay_system, pH=config.experimental_context.pH,
            temperature_c=config.experimental_context.temperature_c, construct_id=context.construct_id,
            condition_id=context.condition_id, require_provenance=config.execution.mode == "real" and config.execution.require_provenance,
        )
        if missing or settings.full_network_initial_state is None or settings.reaction_network_file is None:
            records.append(_m4_insufficient(item.candidate_id, config, missing + (["full_network_initial_state"] if settings.full_network_initial_state is None else []) + (["reaction_network_file"] if settings.reaction_network_file is None else []), construct_id=context.construct_id))
            continue
        reactions = _full_network_reactions(settings, selected)
        distributions = {enzyme: PhaseDistribution(values["dense"], values["dilute"]) for enzyme, values in context.enzyme_distribution.items()}
        kp = context.metabolite_partition_coefficients
        if set(kp) != {"8", "9", "10", "11", "12", "13", "14", "15"} or any(value <= 0 for value in kp.values()):
            records.append(_m4_insufficient(item.candidate_id, config, ["M3 metabolite Kp8-Kp15 context"], construct_id=context.construct_id))
            continue
        if settings.activity_mode == "sensitivity_parameters":
            activity_dense = {enzyme: selected[f"activity_dense_{enzyme.lower()}"].canonical_value for enzyme in ("PTR", "PT", "OC", "DMT")}
            activity_dilute = {enzyme: selected[f"activity_dilute_{enzyme.lower()}"].canonical_value for enzyme in ("PTR", "PT", "OC", "DMT")}
            activity_assumption = "activity-sensitivity parameters resolved from registry"
        else:
            activity_dense = {enzyme: 1.0 for enzyme in ("PTR", "PT", "OC", "DMT")}
            activity_dilute = {enzyme: 1.0 for enzyme in ("PTR", "PT", "OC", "DMT")}
            activity_assumption = "assumption_sensitivity: unity activity"
        gate = TemporalGate()
        if settings.scenario_mode in {"homogeneous_published_like_temporal", "galatea_spatiotemporal_ablation"} and settings.dmt_gate is not None:
            gate = TemporalGate(mode="published_delayed_ramp", disable_time=settings.dmt_gate.on_time)
        transport = TransportParameters(
            enabled=settings.transport_enabled, access=settings.transport_access,
            rate=selected["transport_rate"].canonical_value if settings.transport_enabled else 0.0,
            outside_over_inside=settings.transport_outside_over_inside,
        )
        result = run_galatea_full_m4(
            enzyme_distributions=distributions, phi=context.phi, metabolite_kp=kp,
            reactions=reactions, initial_intracellular=settings.full_network_initial_state.intracellular,
            initial_extracellular=settings.full_network_initial_state.extracellular, t_end=settings.t_end,
            scenario=settings.scenario_mode, transport=transport, dmt_gate=gate,
            activity_dense=activity_dense, activity_dilute=activity_dilute,
            unit_mode=settings.unit_mode,
        )
        fingerprint = sha256(context.condition_id.encode("utf-8")).hexdigest()[:10]
        trajectory = stage_dir / f"{item.candidate_id}_{fingerprint}_full_trajectory.json"
        trajectory.parent.mkdir(parents=True, exist_ok=True)
        trajectory.write_text(json.dumps({
            "candidate_id": item.candidate_id, "construct_id": context.construct_id, "condition_id": context.condition_id,
            "time": result.time.tolist(), "intracellular_cell_average": {str(index + 8): result.intracellular[index].tolist() for index in range(8)},
            "extracellular": {str(index + 8): result.extracellular[index].tolist() for index in range(8)},
            "reaction_fluxes": {f"R{index + 1}": result.fluxes[index].tolist() for index in range(10)},
            "flux_integrals": result.flux_integrals, "diagnostics": result.diagnostics,
            "unit_mode": result.unit_mode,
            "units": _full_network_units(settings),
            "provenance": _full_network_provenance(author_native),
            "assumptions": ["rapid_partition_equilibrium", "phase-specific competing enzyme pools", "transport access is configured, not measured", activity_assumption],
        }), encoding="utf-8")
        provenance = _merge_provenance(context.provenance_summary, _provenance_summary(selected.values()))
        records.append(M4ReactionPrediction(
            candidate_id=item.candidate_id, construct_id=context.construct_id, condition_id=context.condition_id,
            target_product=settings.target_product, status="valid", data_quality=_data_quality_from_summary(provenance),
            final_15=None if author_native else result.diagnostics["final_15_total"], final_13=None if author_native else result.diagnostics["final_13_total"],
            side_product_fraction_13=result.diagnostics["final_13_total"] / (result.diagnostics["final_13_total"] + result.diagnostics["final_15_total"]) if result.diagnostics["final_13_total"] + result.diagnostics["final_15_total"] else 0.0,
            leakage_fraction=None, productivity=None if author_native else result.diagnostics["final_15_total"] / settings.t_end,
            recommendation="iterate", recommendation_evidence=["comparative_negative_screen_requires_control_comparison"],
            candidate_context=context, simulation_inputs={"scenario": settings.scenario_mode, "transport_access": settings.transport_access, "dmt_gate": gate.mode, "unit_mode": result.unit_mode},
            bottleneck="full_network_comparative_screen", trajectory_artifact=trajectory,
            flux_integrals=({f"relative_{key}": value for key, value in result.flux_integrals.items()} if author_native else result.flux_integrals),
            mechanistic_diagnostics=({key: result.diagnostics[key] for key in (
                "target_yield_fraction", "branch_9_to_13_fraction", "dmt_late_selectivity",
                "early_dmt_fraction", "oc_before_dmt_route_fraction", "side_product_fraction_13",
                "mass_balance_error",
            )} if author_native else result.diagnostics), parameter_ids=sorted({*context.parameter_ids, *(entry.selected_parameter.parameter_id for entry in selected.values() if entry.selected_parameter)}),
            provenance_summary=provenance, assumptions=["M1/M2 structural and docking scores are not kinetic inputs", "M4 is a mechanistic sensitivity model", activity_assumption],
            notes=("Full 8-compound / 10-reaction phase-specific competitive model. Values are not enzyme activity or yield predictions."
                   if result.unit_mode == "physical" else "Results are normalized mechanistic sensitivity outputs and must not be interpreted as absolute concentration, enzyme abundance, kinetic rate, productivity, or titer."),
        ))
    write_models(stage_dir, "reaction_predictions", records)
    return records, _stage_output("m4_glabridin_full_network", stage_dir, "reaction_predictions", len(records))


def _full_network_reactions(settings: object, selected: dict[str, object]) -> tuple[object, ...]:
    """Keep physical and author-native kinetic acquisition paths disjoint."""
    source_reactions = load_author_native_reactions(settings.reaction_network_file)  # type: ignore[attr-defined]
    if settings.unit_mode == "author_native_sensitivity":  # type: ignore[attr-defined]
        return source_reactions
    return tuple(
        reaction.__class__(
            reaction.reaction_id, reaction.enzyme, reaction.substrate, reaction.product,
            selected[f"kcat_{reaction.reaction_id.lower()}"].canonical_value,  # type: ignore[index,union-attr]
            selected[f"km_{reaction.reaction_id.lower()}"].canonical_value,  # type: ignore[index,union-attr]
        )
        for reaction in source_reactions
    )


def _full_network_units(settings: object) -> dict[str, object]:
    if settings.unit_mode == "author_native_sensitivity":  # type: ignore[attr-defined]
        return {
            "time": settings.author_native_time_label,  # type: ignore[attr-defined]
            "concentration": "author_native",
            "enzyme_scale": "author_native",
            "kinetics": "author_native",
            "absolute_titer_supported": False,
            "physical_rate_supported": False,
        }
    return {"time": "h", "concentration": "uM", "kinetics": "1/h and uM"}


def _full_network_provenance(author_native: bool) -> dict[str, str]:
    if author_native:
        return {
            "kinetics": "Zhang_author_model",
            "unit_status": "author_native_only",
            "enzyme_scale": "explicit_author_native_inputs",
            "phi_and_Kp": "reviewed_dimensionless_records",
            "recruitment": "project_design_and_sensitivity_inputs",
        }
    return {
        "kinetics": "reviewed_ParameterRegistry",
        "enzyme_scale": "reviewed_ParameterRegistry",
        "phi_and_Kp": "reviewed_ParameterRegistry",
    }


def _run_published_reference_m4(config: ProjectConfig, run_dir: Path) -> tuple[list[M4ReactionPrediction], StageOutput]:
    """Route the published baseline only through its isolated immutable adapter."""
    stage_dir = run_dir / "m4_published_reference"
    root = Path(__file__).resolve().parents[3]
    output = write_published_reference_reproduction(root, stage_dir / "published_reference_author_native.csv")
    reference = run_published_reference(root)
    record = M4ReactionPrediction(
        candidate_id="published_reference", construct_id="published_reference", condition_id="published_reference",
        target_product=config.stages.m4_reaction.target_product, status="valid", data_quality="heuristic",
        final_15=float(reference.state[7, -1]), final_13=float(reference.state[5, -1]),
        productivity=None, recommendation="iterate", bottleneck="published_reference_adapter",
        trajectory_artifact=output, simulation_inputs={"network_mode": "published_reference", "unit_mode": "author_native_sensitivity"},
        assumptions=["author_native_sensitivity: no physical concentration, time, rate, or titer units are assigned"],
        notes="Independent Zhang author-code reproduction; it does not enter the Galatea full-network kernel.",
    )
    write_models(stage_dir, "reaction_predictions", [record])
    return [record], _stage_output("m4_published_reference", stage_dir, "reaction_predictions", 1)


def run_m5(config: ProjectConfig, run_dir: Path, predictions: list[M4ReactionPrediction] | None = None) -> tuple[list[M5FeedbackAssessment], StageOutput]:
    """Ingest wet-lab records and emit deterministic QC/diagnostic feedback."""
    stage_dir = run_dir / "m5_wetlab_feedback"
    path = config.stages.m5_feedback.wetlab_results_file
    if path is None:
        records = [M5FeedbackAssessment(experiment_id="unavailable", construct_id="unavailable", status="insufficient_data", data_quality="heuristic", missing_inputs=["wetlab_results_file"], recommended_next_action=["provide structured wet-lab measurements"], notes="No wet-lab feedback file was configured.")]
    else:
        results = load_wetlab_results(path); reports = quality_control(results); records = []; variations = replicate_variation(results)
        prediction_by_context = {(item.candidate_context.construct_id, item.condition_id): item for item in predictions or [] if item.status == "valid" and item.candidate_context is not None}
        prepared = []
        for result, report in zip(results, reports):
            prediction = prediction_by_context.get((result.construct_id, result.condition_id))
            try:
                comparisons = compare_prediction(prediction.trajectory_artifact, result) if prediction and prediction.trajectory_artifact else {}
            except ValueError as error:
                comparisons = {}
                report.flags.append(f"comparison_contract_error:{error}")
            usable = [item for item in comparisons.values() if item.comparison_status in {"trajectory_aligned", "endpoint_only"}]
            evidence = _joint_diagnosis_evidence(result, comparisons, variations)
            significance = evaluate_residual_significance(
                evidence,
                absolute_tolerance=config.stages.m5_feedback.absolute_residual_tolerance,
                relative_tolerance=config.stages.m5_feedback.relative_residual_tolerance,
                tolerance_configured=config.stages.m5_feedback.discrepancy_threshold_configured,
                require_interpretable_uncertainty=config.execution.mode == "real",
            )
            for metabolite, item in evidence.items():
                metabolite_significance = evaluate_residual_significance(
                    {metabolite: item},
                    absolute_tolerance=config.stages.m5_feedback.absolute_residual_tolerance,
                    relative_tolerance=config.stages.m5_feedback.relative_residual_tolerance,
                    tolerance_configured=config.stages.m5_feedback.discrepancy_threshold_configured,
                    require_interpretable_uncertainty=config.execution.mode == "real",
                )
                item["significant"] = metabolite_significance.significant
                item["significance_reason"] = metabolite_significance.reason
                item["significance_threshold"] = metabolite_significance.threshold
            residuals = [item["residual_final"] for item in evidence.values() if item["residual_final"] is not None]
            trends = [item["trend_agreement"] for item in evidence.values() if item["trend_agreement"] is not None]
            variations_for_result = [item["replicate_variation"] for item in evidence.values() if item["replicate_variation"] is not None]
            residual = sum(residuals) / len(residuals) if residuals else None
            trend = all(trends) if trends else None
            variation = max(variations_for_result) if variations_for_result else None
            comparison_status = "joint_13_15" if set(evidence) == {"13", "15"} else (next(iter(evidence.values()))["comparison_status"] if evidence else ("unmatched_condition" if prediction is None else "no_observed_metabolite"))
            prepared.append((result, report, comparisons, evidence, residual, trend, variation, comparison_status, usable, significance))
        systematic = _condition_level_systematic(prepared, config)
        fit_groups = _aggregate_fit_groups([result for result, report, *_ in prepared if report.passed and _fit_eligible(result)])
        fitted_by_group: dict[tuple[str, str], dict[str, object] | None] = {}
        for result, report, comparisons, evidence, residual, trend, variation, comparison_status, usable, significance in prepared:
            systematic_error = significance.significant is True and any((result.construct_id, metabolite) in systematic for metabolite in comparisons)
            diagnosis = diagnose_discrepancy(qc_passed=report.passed, replicate_variation=variation, trend_agreement=trend, systematic_directional_error=systematic_error, significant_residual=significance.significant)
            joint_diagnosis = _joint_diagnosis_label(evidence, diagnosis.category)
            group_key = (result.construct_id, result.condition_id)
            if group_key not in fitted_by_group:
                aggregate = fit_groups.get(group_key)
                aggregate_prediction = prediction_by_context.get(group_key)
                aggregate_comparisons = compare_prediction(aggregate_prediction.trajectory_artifact, aggregate) if aggregate and aggregate_prediction and aggregate_prediction.trajectory_artifact else {}
                fitted_by_group[group_key] = _fit_plan_candidate(config, aggregate_prediction, aggregate, aggregate_comparisons) if aggregate else None
            fitted = fitted_by_group[group_key]
            records.append(M5FeedbackAssessment(experiment_id=result.experiment_id, construct_id=result.construct_id, condition_id=result.condition_id, replicate_id=result.replicate_id, status="valid" if report.passed and usable else "insufficient_data", data_quality="measured", qc_passed=report.passed, qc_flags=report.flags, diagnosis=joint_diagnosis, prediction_residual=residual, trend_agreement=trend, replicate_variation=variation, fit=fitted.get("fit") if fitted else None, metabolite_comparisons={key: value.model_dump() for key, value in comparisons.items()}, diagnosis_evidence=evidence, fitted_parameter_candidate=fitted.get("candidate") if fitted else None, next_measurement="measure OC/DMT abundance and metabolite time course" if joint_diagnosis not in {"INSUFFICIENT_INFORMATION", "NO_SIGNIFICANT_DISCREPANCY"} else None, notes=f"Raw outliers retained; comparison={comparison_status}; diagnosis_metabolites={','.join(item.metabolite_id for item in usable)}."))
    write_models(stage_dir, "feedback", records)
    return records, _stage_output("m5_wetlab_feedback", stage_dir, "feedback", len(records))


def _legacy_demo_definitions(config: ProjectConfig) -> list[ConstructDefinition]:
    """Compatibility fixture only; real projects must declare constructs explicitly."""
    if config.execution.mode != "demo":
        return []
    return [ConstructDefinition(id=f"{scaffold.id}-{linker.id}", components=[scaffold.id, linker.id], linker_ids=[linker.id], scaffold_id=scaffold.id) for scaffold in config.inputs.scaffolds for linker in config.inputs.linkers]


def _definition_from_registry(record: object) -> ConstructDefinition:
    return ConstructDefinition.model_validate(record.candidate_definition())  # type: ignore[attr-defined]


def _stage_output(stage: str, directory: Path, stem: str, count: int) -> StageOutput:
    return StageOutput(stage=stage, directory=directory, json_file=directory / f"{stem}.json", csv_file=directory / f"{stem}.csv", record_count=count)


def _parameter_key(species: str) -> str:
    return f"x{species}" if species.isdigit() else species.lower()


def _m4_insufficient(candidate_id: str, config: ProjectConfig, missing: list[str], construct_id: str = "unresolved") -> M4ReactionPrediction:
    action = (
        "supply reviewed full-network kinetics, metabolite Kp values, and explicit M3/M4 states"
        if config.stages.m4_reaction.network_mode == "galatea_full_competitive"
        else "supply reviewed glabridin kinetics and explicit induction gates"
    )
    return M4ReactionPrediction(candidate_id=candidate_id, construct_id=construct_id, condition_id=canonical_m4_condition_id(config.stages.m4_reaction) or "unresolved", target_product=config.stages.m4_reaction.target_product,
        status="insufficient_data", data_quality="heuristic", missing_inputs=sorted(set(missing)),
        recommended_next_action=[action],
        notes="M4 does not use docking, M2, or M3 proxy scores as enzyme kinetic parameters.")


def _glabridin_parameter_values(selected: dict[str, object]) -> dict[str, float]:
    accepted = {
        "kcat_pt", "km_pt", "kcat_oc", "km_oc", "kcat_dmt_9", "km_dmt_9", "kcat_dmt_11", "km_dmt_11",
        "partition_x9", "partition_x10", "partition_x11",
        "activity_dense_pt", "activity_dilute_pt", "activity_dense_oc", "activity_dilute_oc", "activity_dense_dmt", "activity_dilute_dmt", "kdeg_9", "kdeg_10", "kdeg_11", "kdeg_13", "kdeg_15",
    }
    values = {name: float(getattr(record, "canonical_value")) for name, record in selected.items() if name in accepted}
    return {requirement_name_to_kernel_key(name): value for name, value in values.items()}


def _candidate_enzyme_values(context: M4CandidateContext) -> dict[str, float]:
    """Recover cell-average totals/Kp from M3's explicit mass-conserving distribution."""
    values: dict[str, float] = {"phi": context.phi}
    for enzyme, target in (("PT", "pt"), ("OC", "oc"), ("DMT", "dmt")):
        distribution = context.enzyme_distribution[enzyme]
        dense, dilute = distribution["dense"], distribution["dilute"]
        values[f"{target}_total"] = context.phi * dense + (1.0 - context.phi) * dilute
        values[f"partition_{target}"] = distribution["partition_coefficient"]
    return values


def _data_quality(records: object) -> str:
    return _data_quality_from_summary(_provenance_summary(records))


def _data_quality_from_summary(summary: dict[str, int]) -> str:
    kinds = {key for key, value in summary.items() if value}
    if len(kinds) > 1:
        return "mixed"
    if kinds == {"wetlab"}:
        return "measured"
    if kinds == {"fitted"}:
        return "fitted"
    if kinds == {"literature"}:
        return "literature"
    if kinds == {"prediction"}:
        return "predicted"
    return "heuristic"


def _provenance_summary(records: object) -> dict[str, int]:
    summary: dict[str, int] = {}
    for item in records:  # type: ignore[union-attr]
        record = getattr(item, "selected_parameter", item)
        key = getattr(record, "source_type", "unknown")
        if getattr(record, "derivation_type", None) == "model_fit":
            key = "fitted"
        summary[key] = summary.get(key, 0) + 1
    return summary


def _merge_provenance(*summaries: dict[str, int]) -> dict[str, int]:
    merged: dict[str, int] = {}
    for summary in summaries:
        for key, value in summary.items():
            merged[key] = merged.get(key, 0) + value
    return merged


def _recommend_m4(side_product_fraction: float, productivity: float, baseline_13: float, final_13: float, final_15: float, baseline_15: float, gates: object) -> tuple[str, list[str]]:
    reduction = (baseline_13 - final_13) / baseline_13 if baseline_13 else 0.0
    improvement = (final_15 - baseline_15) / baseline_15 if baseline_15 else 0.0
    if side_product_fraction > gates.max_side_product_fraction_13: return "drop", ["side_product_fraction_13_exceeds_project_heuristic"]
    if productivity < gates.min_productivity: return "iterate", ["productivity_below_project_heuristic"]
    if reduction >= gates.min_13_reduction and improvement >= gates.min_15_improvement: return "test", ["13_reduction_and_15_preservation_pass_project_heuristics"]
    return "iterate", ["baseline_improvement_criteria_not_met"]


def _condition_id_if_defined(gates: object) -> str:
    return canonical_m4_condition_id(gates) or "unresolved"


def _joint_diagnosis_evidence(result: object, comparisons: dict[str, object], variations: dict[tuple[str, str, str, float], float | None]) -> dict[str, dict[str, object]]:
    evidence: dict[str, dict[str, object]] = {}
    for metabolite in ("13", "15"):
        comparison = comparisons.get(metabolite)
        if comparison is None:
            continue
        time_h = comparison.final_quantified_time_h
        evidence[metabolite] = {
            "metabolite_id": metabolite,
            "comparison_status": comparison.comparison_status,
            "residual_final": comparison.residual_final,
            "observed_final": comparison.observed_final,
            "predicted_final": comparison.predicted_final,
            "measurement_uncertainty": normalize_concentration(result.metabolite_uncertainty[metabolite][comparison.final_quantified_index], result.metabolite_concentration_unit) if result.metabolite_uncertainty.get(metabolite) and result.metabolite_concentration_unit and comparison.final_quantified_index is not None else None,
            "measurement_uncertainty_type": result.metabolite_uncertainty_type,
            "trend_agreement": comparison.trend_agreement,
            "replicate_variation": variations.get((result.construct_id, result.condition_id, metabolite, time_h)) if time_h is not None else None,
            "fit_status": "descriptive_scale_fit" if comparison.fit else None,
        }
    return evidence


def _joint_diagnosis_label(evidence: dict[str, dict[str, object]], fallback: str) -> str:
    usable = {name: item for name, item in evidence.items() if item["comparison_status"] in {"trajectory_aligned", "endpoint_only"}}
    if not usable:
        return "INSUFFICIENT_INFORMATION"
    if set(usable) != {"13", "15"}:
        return fallback
    mismatched = {name for name, item in usable.items() if item["trend_agreement"] is False and item.get("significant") is True}
    if not mismatched:
        return fallback
    if mismatched == {"13"}:
        return "SIDE_REACTION_OR_PARTITION_PARAMETER_MISMATCH"
    if mismatched == {"15"}:
        return "PRODUCTIVE_BRANCH_PARAMETER_MISMATCH"
    signs = [item["residual_final"] for item in usable.values()]
    if all(value is not None and value > 0 for value in signs) or all(value is not None and value < 0 for value in signs):
        return "POSSIBLE_GLOBAL_PARAMETER_OR_MODEL_MISMATCH"
    return fallback


def _condition_level_systematic(prepared: list[tuple[object, ...]], config: ProjectConfig) -> set[tuple[str, str]]:
    """Detect systematic error from condition means, never selected replicates."""
    grouped: dict[tuple[str, str, str], list[dict[str, object]]] = {}
    for row in prepared:
        result, report, _comparisons, evidence, *_ = row
        if not report.passed:
            continue
        for metabolite, item in evidence.items():
            if item.get("residual_final") is not None:
                grouped.setdefault((result.construct_id, result.condition_id, metabolite), []).append(item)
    condition_signs: dict[tuple[str, str], list[float]] = {}
    for (construct_id, _condition_id, metabolite), items in grouped.items():
        observed = sum(float(item["observed_final"]) for item in items) / len(items)
        predicted = sum(float(item["predicted_final"]) for item in items) / len(items)
        uncertainties = [item.get("measurement_uncertainty") for item in items]
        types = {item.get("measurement_uncertainty_type") for item in items}
        uncertainty = None
        uncertainty_type = None
        if len(types) == 1 and all(isinstance(value, (int, float)) for value in uncertainties):
            uncertainty = float(np.sqrt(sum(float(value) ** 2 for value in uncertainties)) / len(items))
            uncertainty_type = next(iter(types))
        summary = {metabolite: {"residual_final": observed - predicted, "observed_final": observed, "predicted_final": predicted, "measurement_uncertainty": uncertainty, "measurement_uncertainty_type": uncertainty_type}}
        evaluation = evaluate_residual_significance(summary, absolute_tolerance=config.stages.m5_feedback.absolute_residual_tolerance, relative_tolerance=config.stages.m5_feedback.relative_residual_tolerance, tolerance_configured=config.stages.m5_feedback.discrepancy_threshold_configured, require_interpretable_uncertainty=config.execution.mode == "real")
        if evaluation.significant is True:
            condition_signs.setdefault((construct_id, metabolite), []).append(observed - predicted)
    return {
        key for key, values in condition_signs.items()
        if len(values) >= 2 and (all(value > 0 for value in values) or all(value < 0 for value in values))
    }


def _fit_plan_candidate(config: ProjectConfig, prediction: M4ReactionPrediction | None, result: object, comparisons: dict[str, object]) -> dict[str, object] | None:
    plan = config.stages.m5_feedback.fit_plan
    if plan is None:
        return None
    if prediction is None or not prediction.simulation_inputs:
        return {"fit": None, "candidate": None, "warning": "missing_production_m4_simulation_inputs"}
    if plan.parameter_name in {"recruitment_fraction", "site_occupancy", "docking_score", "structure_score"}:
        return {"fit": None, "candidate": None, "warning": "FitPlan parameter is not a mechanistic M4 parameter"}
    observed: list[float] = []
    fit_points: list[tuple[str, float]] = []
    for observable in plan.observables:
        values = result.metabolites.get(observable)
        comparison = comparisons.get(observable)
        if values is None or comparison is None or result.metabolite_concentration_unit is None:
            continue
        for value, time_h, censor in zip(values, result.time_hours(), comparison.censor_mask, strict=True):
            if censor == "quantified":
                observed.append(normalize_concentration(value, result.metabolite_concentration_unit))
                fit_points.append((observable, time_h))
    if len(observed) < 4 or len(fit_points) != len(observed):
        return {"fit": None, "candidate": None, "warning": "identifiability_warning:fewer_than_four_declared_observations"}
    values = dict(prediction.simulation_inputs["parameters"])
    kernel_key = requirement_name_to_kernel_key(plan.parameter_name)
    fixed_kernel_keys = {requirement_name_to_kernel_key(name) for name in plan.fixed_parameter_names}
    if kernel_key not in values or kernel_key in fixed_kernel_keys:
        return {"fit": None, "candidate": None, "warning": "FitPlan parameter absent_or_declared_fixed"}
    inputs = prediction.simulation_inputs
    def predictor(value: float) -> np.ndarray:
        changed = dict(values); changed[kernel_key] = value
        simulation = simulate_glabridin(GlabridinKineticParameters(**changed), pt_gate=InductionGate(**{k: v for k, v in inputs["pt_gate"].items() if k != "time_unit"}), oc_gate=InductionGate(**{k: v for k, v in inputs["oc_gate"].items() if k != "time_unit"}), dmt_gate=InductionGate(**{k: v for k, v in inputs["dmt_gate"].items() if k != "time_unit"}), initial=tuple(inputs["initial"][f"x{key}"] for key in ("9", "10", "11", "13", "15")), t_end=inputs["t_end"])
        return np.asarray([np.interp(time_h, simulation.time, getattr(simulation, f"x{observable}")) for observable, time_h in fit_points])
    try:
        # The input is an aggregate trajectory. Time points are correlated, so they
        # are not valid IID bootstrap units. A replicate-block bootstrap requires
        # retained individual replicate trajectories and is intentionally withheld.
        fit = fit_mechanistic_parameter(parameter_name=plan.parameter_name, initial_value=values[kernel_key], bounds=plan.bounds, observed=observed, predictor=predictor, bootstrap_samples=0)
        fit = fit.model_copy(update={"confidence_interval": None, "identifiability_warning": "replicate_block_bootstrap_unavailable_from_aggregated_trajectory"})
    except ValueError as error:
        return {"fit": None, "candidate": None, "warning": str(error)}
    requirement = next((item for item in m4_kinetic_requirements(include_degradation=True) if item.name == plan.parameter_name), None)
    if requirement is None:
        return {"fit": None, "candidate": None, "warning": "FitPlan parameter is not an approved M4 requirement"}
    source_lineage = result.notes or result.experiment_id
    fingerprint_input = {"construct": prediction.construct_id, "condition": prediction.condition_id, "requirement": requirement.name, "source_lineage": source_lineage, "fit_points": fit_points, "parameter_ids": sorted(prediction.parameter_ids), "bounds": plan.bounds, "observables": plan.observables, "contract": "pre-real-data-frozen"}
    dataset_hash = sha256(json.dumps(fingerprint_input, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    candidate = ParameterRecord(parameter_id=f"fit:{dataset_hash}", name=requirement.name, value=fit.best_fit, unit=requirement.canonical_unit, parameter_type=requirement.parameter_type, enzyme_id=requirement.enzyme_id, substrate_id=requirement.substrate_id, product_id=requirement.product_id, species_id=requirement.species_id, source_type="wetlab", derivation_type="model_fit", source_reference=source_lineage, review_status="validated", construct_id=prediction.candidate_context.construct_id if prediction.candidate_context else None, condition_id=prediction.condition_id, conditions={"phase": requirement.phase} if requirement.phase else {}, derived_from=prediction.parameter_ids, notes=f"model_fit dataset_hash={dataset_hash}; target_requirement={requirement.name}; fit_bounds={plan.bounds}; observables={plan.observables}; source_lineage={source_lineage}; human approval is required before registry use.")
    return {"fit": fit.model_dump(), "candidate": candidate.model_dump(mode="json")}


def _aggregate_fit_groups(results: list[object]) -> dict[tuple[str, str], object]:
    """Create a canonical fit dataset only from aligned, fully quantified replicates.

    Censored values are intentionally not replaced by a LOD/2 heuristic.  A
    metabolite lacking a complete quantified biological-replicate series is
    withheld from fitting rather than silently averaged as though quantified.
    """
    groups: dict[tuple[str, str], list[object]] = {}
    for result in results:
        groups.setdefault((result.construct_id, result.condition_id), []).append(result)
    aggregated: dict[tuple[str, str], object] = {}
    for key, records in groups.items():
        reference = records[0]
        if len(records) < 2 or any(record.time_hours() != reference.time_hours() for record in records[1:]):
            continue
        shared = set.intersection(*(set(record.metabolites) for record in records))
        metabolites: dict[str, list[float]] = {}
        uncertainties: dict[str, list[float]] = {}
        uncertainty_type: str | None = None
        for name in shared:
            canonical = [canonicalize_metabolite(record, name) for record in records]
            if any(series.time_h != canonical[0].time_h for series in canonical[1:]):
                continue
            if any(censor != "quantified" for series in canonical for censor in series.censor_mask):
                continue
            metabolites[name] = [float(np.mean([series.concentration_uM[index] for series in canonical])) for index in range(len(canonical[0].time_h))]
            if all(series.uncertainty_uM is not None and series.uncertainty_type == canonical[0].uncertainty_type for series in canonical):
                uncertainty_type = canonical[0].uncertainty_type
                uncertainties[name] = [float(np.sqrt(sum(series.uncertainty_uM[index] ** 2 for series in canonical if series.uncertainty_uM is not None)) / len(canonical)) for index in range(len(canonical[0].time_h))]
        if metabolites:
            lineage = sorted(f"{record.experiment_id}/{record.replicate_id}" for record in records)
            aggregated[key] = reference.model_copy(update={"experiment_id": f"fit_group:{key[0]}:{key[1]}", "replicate_id": "biological_mean", "metabolites": metabolites, "metabolite_concentration_unit": "uM", "metabolite_uncertainty": uncertainties, "metabolite_uncertainty_type": uncertainty_type, "metabolite_lod": {}, "metabolite_loq": {}, "biological_replicate_count": len(records), "notes": json.dumps({"source_replicates": lineage}, sort_keys=True)})
    return aggregated


def _fit_eligible(result: object) -> bool:
    """FitPlan only receives QC-valid records with a declared usable unit."""
    if getattr(result, "metabolite_concentration_unit", None) is None:
        return False
    try:
        return any("quantified" in canonicalize_metabolite(result, species).censor_mask for species in result.metabolites)
    except ValueError:
        return False
