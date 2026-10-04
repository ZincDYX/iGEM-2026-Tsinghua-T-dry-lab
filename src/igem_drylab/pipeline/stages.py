from __future__ import annotations

from pathlib import Path
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
    ProtParamEvidence,
    SegEvidence,
    SecondaryStructureEvidence,
    assemble_and_validate_construct,
    compute_sequence_features,
    screen_sequence_v3,
)
from igem_drylab.enrichment import EnrichmentInput, RecruitmentInput, calculate_enrichment, calculate_many, calculate_recruitment
from igem_drylab.kinetics import GlabridinKineticParameters, InductionGate, simulate_glabridin
from igem_drylab.m3_equilibrium import M3EquilibriumInput, solve_m3_equilibrium
from igem_drylab.m4_steady_state import M4PhaseEnzymeInput, M4ReactionInput, M4SteadyStateInput, load_m4_reaction_identities, solve_m4_steady_state
from igem_drylab.galatea_m3_m4 import M3EffectiveRatioInputs, load_author_native_reactions, run_galatea_full_m4, run_m3_effective_ratio
from igem_drylab.full_network import PhaseDistribution, ReactionKinetics, TemporalGate, TransportParameters, FullNetworkParameters, FULL_NETWORK_FORMULA_VERSION, simulate_full_network
from igem_drylab.prediction import dynamic_contract, steady_contract, replay_prediction, observe_prediction
from igem_drylab.published_reference import run_published_reference, write_published_reference_reproduction
from igem_drylab.parameters import ParameterRecord, ParameterResolution, full_m4_kinetic_requirements, m3_requirements, m4_kinetic_requirements, recruitment_requirements, validate_parameters
from igem_drylab.parameters.requirements import requirement_name_to_kernel_key, requirements_for_stage
from igem_drylab.parameters.dimensions import normalize_concentration
from igem_drylab.scoring.m2_structure import M2StructureMetrics, load_m2_structure_metrics, score_m2_structure
from igem_drylab.wetlab import compare_prediction, diagnose_discrepancy, evaluate_residual_significance, load_wetlab_results, quality_control, replicate_variation, fit_mechanistic_parameter
from igem_drylab.wetlab.canonical import canonicalize_metabolite

from .config import ConstructDefinition, ProjectConfig, canonical_m4_condition_id
from .io import write_models
from .models import M1Candidate, M2FusionAssessment, M3ConcentrationAssessment, M4CandidateContext, M4ReactionPrediction, M5FeedbackAssessment, StageOutput


def run_m1(config: ProjectConfig, run_dir: Path) -> tuple[list[M1Candidate], StageOutput]:
    """Screen every declared ORF/IDR/linker; retain all audits, then budget eligibility."""
    stage_dir = run_dir / "m1_construct_screen"
    settings = config.stages.m1_llps
    definitions, digest = M1FeatureDefinitions.from_yaml(settings.feature_definitions_file)
    rules = M1V3Rules.model_validate(yaml.safe_load(settings.rules_file.read_text(encoding="utf-8")))
    evidence = _load_m1_predictor_evidence(settings.predictor_evidence_file)
    constructs = [*config.inputs.constructs, *[_definition_from_registry(record) for record in ConstructRegistry(config.inputs.construct_records).query()]]
    constructs = constructs or _legacy_demo_definitions(config)
    sequences = _read_fasta_sequences(config.inputs.protein_fasta)
    def merge(identifier: str, sequence: str) -> None:
        normalized = "".join(sequence.split()).upper()
        if identifier in sequences and "".join(sequences[identifier].split()).upper() != normalized:
            raise ValueError(f"conflicting_sequence_for_part:{identifier}")
        sequences[identifier] = normalized
    for linker in config.inputs.linkers:
        merge(linker.id, linker.sequence)
    for construct in constructs:
        for identifier, sequence in construct.sequences.items():
            merge(identifier, sequence)
        for part in construct.parts:
            if part.sequence is not None:
                merge(part.id, part.sequence)
    candidates = []
    qc_records = []
    full_sequences = {}
    linker_kinds = {item.id: item.sequence_kind for item in config.inputs.linkers}
    for construct in constructs:
        ordered = _ordered_construct_parts(construct)
        qc = assemble_and_validate_construct(construct_id=construct.id, ordered_part_ids=ordered,
            part_sequences=sequences, coding_dna=construct.coding_dna,
            forbidden_restriction_sites=construct.forbidden_restriction_sites,
            require_sequence_evidence=config.execution.mode == "real")
        qc_records.append(qc.model_dump(mode="json"))
        if qc.full_protein_sequence is not None:
            full_sequences[construct.id] = qc.full_protein_sequence
        flags = list(qc.errors)
        if config.execution.mode == "real":
            flags.extend(qc.missing_inputs)
            if construct.localization_context is None:
                flags.append("localization_context_not_specified")
            if construct.localization_context == "er_anchored" and not construct.localization_design_evidence:
                flags.append("ER_localization_design_evidence_not_specified")
            if not construct.sequence_source_ref:
                flags.append("construct_sequence_source_not_specified")
            if construct.oc_n_terminal_truncation and construct.oc_truncation_mapping is None:
                flags.append("OC_truncation_reference_and_residue_mapping_not_specified")
        if qc.restriction_hits:
            flags.append("wetlab_forbidden_DNA_site_present")
        kinds = {identifier: linker_kinds.get(identifier, "enzyme_ligand_linker") for identifier in construct.linker_ids}
        kinds.update({identifier: "idr" for identifier in construct.idr_ids})
        kinds.update({part.id: part.kind for part in construct.parts if part.kind in {"idr", "enzyme_ligand_linker", "scaffold_linker", "rigid_linker"}})
        if config.inputs.idr_id in ordered:
            kinds[config.inputs.idr_id] = "idr"
        screens = {}
        missing_predictors = []
        for identifier, kind in kinds.items():
            if identifier not in ordered:
                flags.append(f"declared_screen_part_not_in_ORF:{identifier}")
                continue
            if identifier not in sequences:
                flags.append(f"sequence_not_found:{identifier}")
                continue
            screened = _screen_m1_sequence(sequences[identifier], kind, evidence.get(identifier, {}),
                evidence.get(construct.id, {}), definitions, digest, rules, settings, config, qc.protein_sha256, construct)
            screens[identifier] = screened.model_dump(mode="json")
            flags.extend(f"{identifier}:{reason}" for reason in screened.hard_reject_reasons)
            if screened.verdict == "blocked":
                flags.append(f"{identifier}:missing_required_M1_predictor_evidence")
            missing_predictors.extend(f"{identifier}:{name}" for name in screened.missing_required_evidence)
        fusion_screen = {}
        if qc.full_protein_sequence is not None:
            full = _screen_m1_sequence(qc.full_protein_sequence, "full_fusion", evidence.get(construct.id, {}),
                evidence.get(construct.id, {}), definitions, digest, rules, settings, config, qc.protein_sha256, construct)
            fusion_screen = full.model_dump(mode="json")
            flags.extend(f"full_fusion:{reason}" for reason in full.hard_reject_reasons)
            if full.verdict == "blocked":
                flags.append("full_fusion:missing_required_M1_predictor_evidence")
            missing_predictors.extend(f"full_fusion:{name}" for name in full.missing_required_evidence)
        rejected = qc.status == "invalid" or bool(qc.restriction_hits) or any(row["verdict"] == "reject" for row in [*screens.values(), *([fusion_screen] if fusion_screen else [])])
        review_reasons = sorted({reason for row in [*screens.values(), *([fusion_screen] if fusion_screen else [])]
                                for reason in row.get("review_reasons", [])})
        if config.execution.mode == "real" and review_reasons:
            review = construct.m1_review or {}
            fingerprint = sha256(json.dumps({"full_sequence_sha256": qc.protein_sha256,
                "localization_context": construct.localization_context, "screens": screens,
                "full_fusion_screen": fusion_screen}, sort_keys=True).encode()).hexdigest()
            if not (review.get("reviewer") and review.get("source_reference") and
                    review.get("decision") == "approved" and review.get("screen_sha256") == fingerprint and
                    set(review_reasons) <= set(review.get("approved_reasons", []))):
                flags.append("M1_review_pending:" + fingerprint)
        status = "invalid_input" if rejected else ("insufficient_data" if flags else "valid")
        retrospective = construct.experimental_baseline and status != "valid"
        eligible = status == "valid"
        first_linker = next((identifier for identifier in construct.linker_ids if identifier in screens), None)
        first_features = screens[first_linker]["features"] if first_linker else None
        candidates.append(M1Candidate(candidate_id=f"M1-{construct.id}", construct_id=construct.id,
            construct_definition=construct.model_dump(mode="json"), scaffold_id=construct.scaffold_id,
            linker_id=first_linker, idr_id=next((identifier for identifier, kind in kinds.items() if kind == "idr"), None),
            linker_features=first_features, part_screens=screens, full_fusion_screen=fusion_screen,
            formula_version=next((row["formula_version"] for row in screens.values()), None), rule_version=rules.rule_version,
            feature_definitions_sha256=digest, sequence_sha256=first_features["sequence_sha256"] if first_features else None,
            full_sequence_sha256=qc.protein_sha256, sequence_qc=qc.model_dump(mode="json"),
            sequence_screen_verdict="reject" if rejected else ("review" if any(flag.startswith("M1_review_pending") for flag in flags) else ("blocked" if flags else ("review" if missing_predictors else "pass"))),
            screen_flags=sorted(set(flags)), missing_predictor_evidence=sorted(set(missing_predictors)),
            engineering_priority_score=None, recommended_for_m2=eligible, retrospective_only=retrospective,
            eligibility="eligible" if eligible else ("retrospective_only" if retrospective else ("rejected" if rejected else "blocked")),
            status=status, numerically_solved=qc.full_protein_sequence is not None, evidence_ready=eligible,
            claim_scope="sequence_negative_screen", data_quality="demo_fixture" if config.execution.mode == "demo" else "heuristic",
            missing_inputs=sorted(set(flags + (missing_predictors if config.execution.mode == "real" else []))),
            notes="All ORFs and declared fragments audited. No ranking weights invented; eligible budget follows user input order. Baseline is diagnostic only when blocked/rejected."))
    eligible = [item for item in candidates if item.eligibility == "eligible"]
    for item in eligible[settings.top_n:]:
        item.eligibility = "budget_deferred"
        item.recommended_for_m2 = False
        item.notes += " Deferred by top_n compute budget, not a scientific rejection."
    write_models(stage_dir, "candidates", candidates)
    (stage_dir / "construct_sequence.fasta").write_text("".join(f">{identifier}\n{sequence}\n" for identifier, sequence in full_sequences.items()), encoding="utf-8")
    (stage_dir / "sequence_qc.json").write_text(json.dumps(qc_records, indent=2), encoding="utf-8")
    (stage_dir / "part_boundaries.json").write_text(json.dumps({row["construct_id"]: row["part_boundaries"] for row in qc_records}, indent=2), encoding="utf-8")
    (stage_dir / "m1_survivors.fasta").write_text("".join(f">{item.construct_id}\n{full_sequences[item.construct_id]}\n" for item in candidates if item.recommended_for_m2 and item.construct_id in full_sequences), encoding="utf-8")
    return candidates, _stage_output("m1_construct_screen", stage_dir, "candidates", len(candidates))


def _screen_m1_sequence(sequence, kind, fragment_evidence, fusion_evidence, definitions, digest, rules, settings, config, fusion_hash, construct):
    features = compute_sequence_features(sequence, definitions=definitions, definitions_sha256=digest,
                                         forbidden_motifs=tuple(settings.forbidden_motifs))
    def parsed(key, model):
        payload = fragment_evidence.get(key)
        return model.model_validate(payload) if isinstance(payload, dict) else None
    fusion = fusion_evidence.get("fusion", fragment_evidence.get("fusion"))
    return screen_sequence_v3(features=features, sequence=sequence, sequence_kind=kind, rules=rules,
        disorder=parsed("disorder", DisorderEvidence), secondary_structure=parsed("secondary_structure", SecondaryStructureEvidence),
        seg=parsed("seg", SegEvidence), protparam=parsed("protparam", ProtParamEvidence),
        fusion_evidence=FusionToolEvidence.model_validate(fusion) if isinstance(fusion, dict) else None,
        full_fusion_sha256=fusion_hash,
        localization_context=construct.localization_context or "cytosolic",
        require_external_evidence=config.execution.mode == "real" and settings.require_external_evidence_in_real_mode)


def _load_m1_predictor_evidence(path: Path | None) -> dict[str, dict[str, object]]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not all(isinstance(key, str) and isinstance(value, dict) for key, value in payload.items()):
        raise ValueError("M1 predictor evidence must be an object keyed by linker/sequence id")
    return payload


def _ordered_construct_parts(definition: ConstructDefinition) -> list[str]:
    if definition.parts:
        return [part.id for part in definition.parts]
    tokens = definition.domain_order or definition.components
    ordered: list[str] = []
    for token in tokens:
        if token.lower() == "linker" and len(definition.linker_ids) == 1:
            ordered.append(definition.linker_ids[0])
        else:
            ordered.append(token)
    return ordered


def _read_fasta_sequences(path: Path) -> dict[str, str]:
    records: dict[str, list[str]] = {}
    current: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(">"):
            current = line[1:].split()[0]
            if current in records:
                raise ValueError(f"duplicate_fasta_id:{current}")
            records[current] = []
        elif current is None:
            raise ValueError("FASTA_sequence_before_header")
        else:
            records[current].append(line)
    return {identifier: "".join(parts) for identifier, parts in records.items()}


def run_m2(config: ProjectConfig, run_dir: Path, candidates: list[M1Candidate]) -> tuple[list[M2FusionAssessment], StageOutput]:
    """Report observed structural negative-screen metrics; never fill absent metrics."""
    stage_dir = run_dir / "m2_structure_screen"
    metrics = load_m2_structure_metrics(config.stages.m2_fusion.structure_metrics_file) if config.stages.m2_fusion.structure_metrics_file else {}
    assessments: list[M2FusionAssessment] = []
    for candidate in candidates:
        if not candidate.recommended_for_m2 or candidate.status != "valid" or candidate.retrospective_only:
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
                missing_inputs=["structure metrics: core/pocket C-alpha RMSD, pocket SASA retention, clashes with cutoff, folded-region pLDDT"],
                recommended_next_action=["supply parsed structure-prediction and audited pocket-screen metrics"], notes="No structure metrics were supplied; M2 is blocked and no risk score was generated.",
            ))
            continue
        if config.execution.mode == "real":
            provenance_missing = _missing_m2_formal_evidence(
                row,
                config.stages.m2_fusion.structure_metrics_file,
                require_m3_geometry=config.stages.m3_concentration.recruitment_mode == "finite_site",
                expected_sequence_sha256=candidate.full_sequence_sha256,
            )
            if provenance_missing:
                assessments.append(M2FusionAssessment(
                    candidate_id=candidate.candidate_id,
                    construct_id=candidate.construct_id,
                    construct_definition=candidate.construct_definition,
                    status="insufficient_data",
                    data_quality="predicted",
                    structure_model=row.source_model or row.source_tool,
                    structure_source_tool=row.source_tool,
                    structure_source_tool_version=row.source_tool_version,
                    structure_artifact_path=row.artifact_path,
                    structure_artifact_sha256=row.artifact_sha256,
                    reference_structure_id=row.reference_structure_id,
                    reference_artifact_sha256=row.reference_artifact_sha256,
                    geometry_input_sha256=row.geometry_input_sha256,
                    sasa_configuration_hash=row.sasa_configuration_hash,
                    clash_rule_provenance=row.clash_rule_provenance,
                    s_sh3=row.s_sh3, s_pdz=row.s_pdz,
                    eta_acc_sh3=row.eta_acc_sh3, eta_acc_pdz=row.eta_acc_pdz,
                    eta_bind_sh3=row.eta_bind_sh3, eta_bind_pdz=row.eta_bind_pdz,
                    site_count_basis=row.site_count_basis,
                    joint_occupancy_independent=row.joint_occupancy_independent,
                    m2_geometry_id=row.m2_geometry_id,
                    v_scaffold_nm3=row.v_scaffold_nm3, v_enzyme_nm3=row.v_enzyme_nm3,
                    volume_method=row.volume_method,
                    screen_verdict="blocked",
                    missing_inputs=provenance_missing,
                    recommended_next_action=["supply hash-verified M2 structures, reviewed residue mappings, and tool/config provenance"],
                    notes="Formal M2 evidence gate failed; supplied numeric metrics were not scored.",
                ))
                continue
        scored = score_m2_structure(row)
        assessments.append(M2FusionAssessment(
            candidate_id=candidate.candidate_id, construct_id=candidate.construct_id, construct_definition=candidate.construct_definition, structure_model=row.source_model or row.source_tool,
            enzyme_sequence_sha256={enzyme: candidate.full_sequence_sha256 for enzyme in candidate.construct_definition.get("enzyme_ids", []) if candidate.full_sequence_sha256},
            structure_source_tool=row.source_tool, structure_source_tool_version=row.source_tool_version,
            structure_artifact_path=row.artifact_path, structure_artifact_sha256=row.artifact_sha256,
            reference_structure_id=row.reference_structure_id, reference_artifact_sha256=row.reference_artifact_sha256,
            geometry_input_sha256=row.geometry_input_sha256, sasa_configuration_hash=row.sasa_configuration_hash,
            clash_rule_provenance=row.clash_rule_provenance,
            s_sh3=row.s_sh3, s_pdz=row.s_pdz,
            eta_acc_sh3=row.eta_acc_sh3, eta_acc_pdz=row.eta_acc_pdz,
            eta_bind_sh3=row.eta_bind_sh3, eta_bind_pdz=row.eta_bind_pdz,
            site_count_basis=row.site_count_basis,
            joint_occupancy_independent=row.joint_occupancy_independent,
            m2_geometry_id=row.m2_geometry_id,
            v_scaffold_nm3=row.v_scaffold_nm3, v_enzyme_nm3=row.v_enzyme_nm3,
            volume_method=row.volume_method,
            status=scored.status, data_quality="predicted", available_metrics=scored.available_metrics, missing_metrics=scored.missing_metrics,
            screen_verdict=scored.verdict, confidence_gate=scored.confidence_gate, formula_version=scored.formula_version,
            core_ca_rmsd_angstrom=row.core_ca_rmsd_angstrom, heuristic_structure_risk=None,
            pocket_sasa_retention=row.sasa_retention, pocket_rmsd_angstrom=row.pocket_rmsd_angstrom,
            tail_pocket_min_distance_angstrom=row.tail_pocket_min_distance_angstrom,
            clash_count=row.clash_count, clash_cutoff_angstrom=row.clash_cutoff_angstrom,
            recommended_for_m3=scored.recommended_for_m3, threshold_origin=scored.threshold_origin, notes="; ".join(scored.reasons),
        ))
    _append_design_assessments(config, candidates, metrics, assessments)
    write_models(stage_dir, "fusion_assessments", assessments)
    return assessments, _stage_output("m2_structure_screen", stage_dir, "fusion_assessments", len(assessments))


def _missing_m2_formal_evidence(
    row: M2StructureMetrics,
    metrics_file: Path | None,
    *,
    require_m3_geometry: bool,
    expected_sequence_sha256: str | None = None,
    expected_design_hashes: dict[str, str] | None = None,
) -> list[str]:
    required = {
        "source_tool": row.source_tool,
        "source_tool_version": row.source_tool_version,
        "artifact_path": row.artifact_path,
        "artifact_sha256": row.artifact_sha256,
        "prediction_input_sequence_sha256": row.prediction_input_sequence_sha256,
        "chain_sequence_sha256": row.chain_sequence_sha256,
        "reference_structure_id": row.reference_structure_id,
        "reference_artifact_path": row.reference_artifact_path,
        "reference_artifact_sha256": row.reference_artifact_sha256,
        "geometry_input_sha256": row.geometry_input_sha256,
        "geometry_input_path": row.geometry_input_path,
        "sasa_configuration_hash": row.sasa_configuration_hash,
        "sasa_configuration_path": row.sasa_configuration_path,
        "clash_rule_provenance": row.clash_rule_provenance,
        "pocket_definition_source_ref": row.pocket_definition_source_ref,
        "residue_mapping_source_ref": row.residue_mapping_source_ref,
        "core_residue_ids": row.core_residue_ids,
        "pocket_residue_ids": row.pocket_residue_ids,
        "core_mean_plddt": row.core_mean_plddt,
        "pocket_mean_plddt": row.pocket_mean_plddt,
        "ligand_buried_assessment": row.ligand_buried,
        "recruitment_domain_buried_assessment": row.recruitment_domain_buried,
        "scaffold_interface_disrupted_assessment": row.scaffold_interface_disrupted,
    }
    if row.v_scaffold_nm3 is not None or row.v_enzyme_nm3 is not None:
        required.update({
            "v_scaffold_nm3": row.v_scaffold_nm3,
            "v_enzyme_nm3": row.v_enzyme_nm3,
            "volume_method": row.volume_method,
        })
    if require_m3_geometry:
        required.update({
            "s_sh3": row.s_sh3,
            "s_pdz": row.s_pdz,
            "eta_acc_sh3": row.eta_acc_sh3,
            "eta_acc_pdz": row.eta_acc_pdz,
            "eta_bind_sh3": row.eta_bind_sh3,
            "eta_bind_pdz": row.eta_bind_pdz,
            "site_count_basis": row.site_count_basis,
            "joint_occupancy_independent": row.joint_occupancy_independent,
            "m2_geometry_id": row.m2_geometry_id,
        })
    missing = [f"M2 provenance: {name}" for name, value in required.items() if value in (None, "", [])]
    if expected_design_hashes is not None:
        if row.design_protein_sequence_sha256 != expected_design_hashes:
            missing.append("M2 assembly input protein hashes matching all design ORFs")
        if not set(expected_design_hashes.values()) <= set(row.chain_sequence_sha256.values()):
            missing.append("M2 assembly chain mapping matching all design ORFs")
    elif not expected_sequence_sha256 or row.prediction_input_sequence_sha256 != expected_sequence_sha256:
        missing.append("M2 prediction input sequence SHA-256 matching M1")
    if expected_sequence_sha256 and expected_sequence_sha256 not in row.chain_sequence_sha256.values():
        missing.append("M2 chain mapping matching the current protein construct")
    for label, path, digest in (
        ("structure", row.artifact_path, row.artifact_sha256),
        ("reference", row.reference_artifact_path, row.reference_artifact_sha256),
        ("geometry input", row.geometry_input_path, row.geometry_input_sha256),
        ("SASA configuration", row.sasa_configuration_path, row.sasa_configuration_hash),
    ):
        if not path or not digest:
            continue
        artifact = Path(path)
        if not artifact.is_absolute() and metrics_file is not None:
            artifact = metrics_file.parent / artifact
        if not artifact.is_file():
            missing.append(f"M2 {label} artifact file")
        else:
            if sha256(artifact.read_bytes()).hexdigest() != digest:
                missing.append(f"M2 {label} artifact SHA-256 match")
    if row.clash_count is not None and row.clash_count > 0:
        collision_evidence = {
            "independent_conformation_count": row.independent_conformation_count,
            "severe_clash_conformation_count": row.severe_clash_conformation_count,
            "persistent_severe_clash": row.persistent_severe_clash,
            "direct_pocket_occlusion": row.direct_pocket_occlusion,
        }
        missing.extend(
            f"M2 collision evidence: {name}"
            for name, value in collision_evidence.items()
            if value is None
        )
    return sorted(set(missing))


def _append_design_assessments(config, candidates, metrics, assessments):
    candidate_by_id = {item.construct_id: item for item in candidates}
    assessment_by_id = {item.construct_id: item for item in assessments}
    for design in config.inputs.designs:
        missing = [f"design protein M2 ready: {identifier}" for identifier in design.protein_construct_ids
                   if identifier not in assessment_by_id or not assessment_by_id[identifier].recommended_for_m3]
        candidate_id = f"Design-{design.id}"
        row = metrics.get(candidate_id)
        hashes = {identifier: candidate_by_id[identifier].full_sequence_sha256 for identifier in design.protein_construct_ids}
        if row is None:
            missing.append("design-level assembly geometry metrics")
        elif config.execution.mode == "real":
            missing.extend(_missing_m2_formal_evidence(row, config.stages.m2_fusion.structure_metrics_file,
                require_m3_geometry=True, expected_design_hashes=hashes))
        if _is_formal(config) and (not design.host or design.host != config.experimental_context.host or
                                  not design.condition_id or design.condition_id != config.stages.m4_reaction.condition_id):
            missing.append("design host and condition matching the formal experiment")
        if missing:
            assessments.append(M2FusionAssessment(candidate_id=candidate_id, construct_id=design.id,
                construct_definition=design.model_dump(mode="json"), status="insufficient_data", missing_inputs=missing,
                notes="No single protein pass can stand in for an entire design."))
            continue
        scored = score_m2_structure(row)
        values = {key: value for key, value in row.model_dump().items() if key in M2FusionAssessment.model_fields}
        values.update(candidate_id=candidate_id, construct_id=design.id, construct_definition=design.model_dump(mode="json"),
            enzyme_sequence_sha256={enzyme: digest for identifier in design.protein_construct_ids for enzyme, digest in assessment_by_id[identifier].enzyme_sequence_sha256.items()},
            status=scored.status, screen_verdict=scored.verdict, recommended_for_m3=scored.recommended_for_m3,
            evidence_ready=scored.recommended_for_m3, claim_scope="structure_negative_screen",
            notes="All necessary ORFs and assembly input bindings checked; design-level geometry remains predicted evidence.")
        assessments.append(M2FusionAssessment(**values))


def run_m3(config: ProjectConfig, run_dir: Path, assessments: list[M2FusionAssessment]) -> tuple[list[M3ConcentrationAssessment], StageOutput]:
    """Calculate species-specific two-phase concentrations from reviewed inputs."""
    stage_dir = run_dir / "m3_enrichment"
    requirements = requirements_for_stage(config, "m3")
    core_requirements = [item for item in requirements if item.blocking]
    records: list[M3ConcentrationAssessment] = []
    for assessment in assessments:
        if any(assessment.construct_id in design.protein_construct_ids for design in config.inputs.designs):
            records.append(M3ConcentrationAssessment(candidate_id=assessment.candidate_id, construct_id=assessment.construct_id,
                status="insufficient_data", missing_inputs=["use the complete design-level M2 assessment"],
                notes="Individual ORF is not an entire multi-protein cellular design."))
            continue
        if not assessment.recommended_for_m3:
            records.append(M3ConcentrationAssessment(
                candidate_id=assessment.candidate_id,
                construct_id=assessment.construct_id,
                status="insufficient_data",
                data_quality=assessment.data_quality,
                missing_inputs=assessment.missing_inputs or assessment.missing_metrics or [f"M2 verdict: {assessment.screen_verdict}"],
                recommended_next_action=["resolve the recorded M2 block/review/reject before quantitative M3"],
                notes="M3 preserved the candidate record but did not calculate concentrations from an ineligible M2 result.",
            ))
            continue
        construct_id = assessment.construct_id
        formal_missing = _formal_analysis_missing(config)
        if _is_formal(config) and config.stages.m3_concentration.recruitment_mode != "finite_site":
            formal_missing.append("formal M3 requires finite_site; effective ratios are sensitivity-only")
        if formal_missing:
            records.append(M3ConcentrationAssessment(candidate_id=assessment.candidate_id, construct_id=construct_id,
                status="insufficient_data", missing_inputs=formal_missing, notes="Formal evidence boundary is not satisfied."))
            continue
        condition_id = config.stages.m4_reaction.condition_id or _condition_id_if_defined(config.stages.m4_reaction)
        selected, missing = validate_parameters(config.parameters, requirements=core_requirements, allow_assumptions=config.execution.allow_assumptions, host=config.experimental_context.host, strain=config.experimental_context.strain, assay_system=config.experimental_context.assay_system, pH=config.experimental_context.pH, temperature_c=config.experimental_context.temperature_c, construct_id=construct_id, condition_id=condition_id, require_provenance=config.execution.mode == "real" and config.execution.require_provenance)
        if missing:
            records.append(M3ConcentrationAssessment(candidate_id=assessment.candidate_id, construct_id=construct_id, status="insufficient_data", data_quality="heuristic",
                missing_inputs=missing, recommended_next_action=["add reviewed phi, total concentration, and Kp ParameterRecords"],
                notes="M3 does not infer partitioning from M1/M2 scores."))
            continue
        phi = selected["phi"].canonical_value if "phi" in selected else None
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
        if config.stages.m3_concentration.recruitment_mode == "finite_site":
            geometry_missing = [
                name
                for name in (
                    "s_sh3", "s_pdz", "eta_acc_sh3", "eta_acc_pdz", "eta_bind_sh3", "eta_bind_pdz",
                    "site_count_basis", "joint_occupancy_independent", "m2_geometry_id",
                )
                if getattr(assessment, name) is None
            ]
            if geometry_missing:
                records.append(M3ConcentrationAssessment(
                    candidate_id=assessment.candidate_id,
                    construct_id=construct_id,
                    status="insufficient_data",
                    data_quality="predicted",
                    missing_inputs=[f"M2 geometry: {name}" for name in geometry_missing],
                    recommended_next_action=["supply the reviewed M2 site-count/accessibility/co-occupancy contract"],
                    notes="M3 S1 could not be evaluated; no concentration was generated.",
                ))
                continue
            c_dense_record = selected["c_dense_scaffold"].selected_parameter
            assert c_dense_record is not None
            declared_c_dense_basis = c_dense_record.conditions.get("entity_basis")
            if declared_c_dense_basis is not None and declared_c_dense_basis != assessment.site_count_basis:
                records.append(M3ConcentrationAssessment(
                    candidate_id=assessment.candidate_id,
                    construct_id=construct_id,
                    status="insufficient_data",
                    data_quality="mixed",
                    missing_inputs=["c_dense_scaffold entity_basis matching M2 site_count_basis"],
                    recommended_next_action=["reconcile scaffold monomer versus complete-assembly concentration units"],
                    notes="M3 did not insert an implicit scaffold oligomer multiplier.",
                ))
                continue
            if config.execution.mode == "real":
                source_violations = _m3_formal_source_violations(selected, assessment.site_count_basis)
                if source_violations:
                    records.append(M3ConcentrationAssessment(
                        candidate_id=assessment.candidate_id,
                        construct_id=construct_id,
                        status="insufficient_data",
                        data_quality="mixed",
                        missing_inputs=source_violations,
                        recommended_next_action=["replace predicted/underspecified M3 inputs with matching measured or verified evidence"],
                        notes="Formal M3 source gate rejected an otherwise numeric input set.",
                    ))
                    continue
            exact = solve_m3_equilibrium(M3EquilibriumInput(
                candidate_id=assessment.candidate_id,
                construct_id=construct_id,
                s_sh3=assessment.s_sh3,
                s_pdz=assessment.s_pdz,
                eta_acc_sh3=assessment.eta_acc_sh3,
                eta_acc_pdz=assessment.eta_acc_pdz,
                eta_bind_sh3=assessment.eta_bind_sh3,
                eta_bind_pdz=assessment.eta_bind_pdz,
                site_count_basis=assessment.site_count_basis,
                c_dense_basis=declared_c_dense_basis or assessment.site_count_basis,
                joint_occupancy_independent=assessment.joint_occupancy_independent,
                m2_geometry_id=assessment.m2_geometry_id,
                phi=phi,
                c_dense_um=selected["c_dense_scaffold"].canonical_value,
                c_scaffold_total_um=selected["c_total_scaffold"].canonical_value if "c_total_scaffold" in selected else None,
                c_sat_um=selected["c_sat_scaffold"].canonical_value if "c_sat_scaffold" in selected else None,
                r_target=selected[config.stages.m3_concentration.target_enzyme_ratio_parameter].canonical_value
                    if config.stages.m3_concentration.target_enzyme_ratio_parameter else None,
                kd_sh3_um=selected["kd_sh3"].canonical_value,
                kd_pdz_um=selected["kd_pdz"].canonical_value,
                k_oc=selected["partition_oc"].canonical_value,
                k_dmt=selected["partition_dmt"].canonical_value,
                c_oc_total_um=selected["oc_total"].canonical_value,
                c_dmt_total_um=selected["dmt_total"].canonical_value,
                v_scaffold_nm3=assessment.v_scaffold_nm3,
                v_enzyme_nm3=assessment.v_enzyme_nm3,
                volume_method=assessment.volume_method,
                input_parameter_ids=sorted(
                    resolution.selected_parameter.parameter_id
                    for resolution in selected.values()
                    if resolution.selected_parameter
                ),
            ))
            if exact.status != "valid" or exact.oc is None or exact.dmt is None:
                records.append(M3ConcentrationAssessment(
                    candidate_id=assessment.candidate_id,
                    construct_id=construct_id,
                    status="insufficient_data",
                    data_quality="mixed",
                    formula_version=exact.formula_version,
                    effective_site_counts={"SH3": exact.n_sh3_effective, "PDZ": exact.n_pdz_effective},
                    capacity_status="conflict" if exact.status == "capacity_conflict" else "not_evaluated",
                    maximum_dense_enzyme_concentration_um=exact.maximum_dense_enzyme_concentration_um,
                    capacity_excess_um=exact.capacity_excess_um,
                    missing_inputs=[] if exact.status == "capacity_conflict" else list(exact.warnings),
                    recommended_next_action=[
                        "resolve M2 joint co-occupancy" if exact.status == "insufficient_data" else
                        "revise the construct or solve a capacity-constrained conservative model"
                    ],
                    notes="; ".join(exact.warnings),
                ))
                continue
            phi = exact.phi
            background = {
                enzyme: calculate_enrichment(EnrichmentInput(
                    species_id=enzyme,
                    total_concentration=selected[f"{enzyme.lower()}_total"].canonical_value,
                    partition_coefficient=selected[f"partition_{enzyme.lower()}"].canonical_value,
                    partition_source=selected[f"partition_{enzyme.lower()}"].selected_parameter.source_reference,
                    partition_uncertainty=selected[f"partition_{enzyme.lower()}"].selected_parameter.uncertainty,
                ), phi=phi)
                for enzyme in ("PTR", "PT")
            }
            enzyme_distribution = {
                **{enzyme: {"dense": item.dense_concentration, "dilute": item.dilute_concentration, "partition_coefficient": item.partition_coefficient} for enzyme, item in background.items()},
                "OC": {"dense": exact.oc.total_dense_um, "dilute": exact.oc.free_dilute_um, "partition_coefficient": selected["partition_oc"].canonical_value},
                "DMT": {"dense": exact.dmt.total_dense_um, "dilute": exact.dmt.free_dilute_um, "partition_coefficient": selected["partition_dmt"].canonical_value},
            }
            parameter_ids = sorted(
                resolution.selected_parameter.parameter_id
                for resolution in selected.values()
                if resolution.selected_parameter
            )
            bound_fractions = {
                "OC": exact.oc.bound_fraction_of_whole_cell_total,
                "DMT": exact.dmt.bound_fraction_of_whole_cell_total,
            }
            dense_fractions = {
                **{enzyme: item.fraction_in_dense for enzyme, item in background.items()},
                "OC": exact.oc.dense_phase_fraction_of_whole_cell_total,
                "DMT": exact.dmt.dense_phase_fraction_of_whole_cell_total,
            }
            site_occupancy = {"OC": exact.oc.site_occupancy, "DMT": exact.dmt.site_occupancy}
            context = M4CandidateContext(
                candidate_id=assessment.candidate_id,
                construct_id=construct_id,
                condition_id=condition_id,
                phi=phi,
                phi_source=exact.phi_source,
                nominal_site_counts={"SH3": assessment.s_sh3, "PDZ": assessment.s_pdz},
                m2_geometry_id=assessment.m2_geometry_id,
                site_count_basis=assessment.site_count_basis,
                enzyme_distribution=enzyme_distribution,
                metabolite_partition_coefficients={compound: selected[f"partition_x{compound}"].canonical_value for compound in ("8", "9", "10", "11", "12", "13", "14", "15") if f"partition_x{compound}" in selected},
                binding_recruited_fraction=bound_fractions,
                site_occupancy=site_occupancy,
                parameter_ids=parameter_ids,
                provenance_summary=_provenance_summary(selected.values()),
                assumptions=[
                    "M3 S1-S5/E1-E6 rapid-equilibrium cytosolic two-phase model",
                    "M2 confirmed independent treatment of joint site occupancy",
                    "PTR/PT use independent two-phase partition because S1-E6 only specify OC/DMT binding",
                ],
            )
            records.append(M3ConcentrationAssessment(
                candidate_id=assessment.candidate_id,
                construct_id=construct_id,
                status="valid",
                data_quality="mixed",
                concentrations={
                    **{enzyme: item.model_dump(mode="json") for enzyme, item in background.items()},
                    "OC": {"dense_concentration": exact.oc.total_dense_um, "dilute_concentration": exact.oc.free_dilute_um},
                    "DMT": {"dense_concentration": exact.dmt.total_dense_um, "dilute_concentration": exact.dmt.free_dilute_um},
                },
                dense_oc_dmt_ratio=exact.dense_oc_dmt_ratio,
                whole_cell_oc_dmt_ratio=exact.whole_cell_oc_dmt_ratio,
                fraction_in_dense=dense_fractions,
                binding_recruitment_status="valid",
                binding_recruited_fraction=bound_fractions,
                site_occupancy=site_occupancy,
                formula_version=exact.formula_version,
                free_dense_concentration={"OC": exact.oc.free_dense_um, "DMT": exact.dmt.free_dense_um},
                free_dilute_concentration={"OC": exact.oc.free_dilute_um, "DMT": exact.dmt.free_dilute_um},
                bound_dense_concentration={"OC": exact.oc.bound_dense_um, "DMT": exact.dmt.bound_dense_um},
                bound_fraction_of_whole_cell_total=bound_fractions,
                mass_balance_residual_um={"OC": exact.oc.mass_balance_residual_um, "DMT": exact.dmt.mass_balance_residual_um},
                effective_site_counts={"SH3": exact.n_sh3_effective, "PDZ": exact.n_pdz_effective},
                capacity_status="within_capacity" if exact.maximum_dense_enzyme_concentration_um is not None else "not_evaluated",
                maximum_dense_enzyme_concentration_um=exact.maximum_dense_enzyme_concentration_um,
                capacity_excess_um=exact.capacity_excess_um,
                normalized_sensitivities_e10=exact.normalized_sensitivities_e10,
                phi_source=exact.phi_source,
                phi_s4_if_available=exact.phi_s4_if_available,
                phi_measured_minus_s4=exact.phi-exact.phi_s4_if_available
                    if exact.phi_source == "measured_input" and exact.phi_s4_if_available is not None else None,
                design_decision_id=config.stages.m3_concentration.design_decision_id,
                rho_star_candidates={key: value for key, value in {
                    "E8_low_occupancy": exact.rho_star_low_occupancy_candidate,
                    "E9_saturation": exact.rho_star_saturation_candidate}.items() if value is not None},
                recommended_for_m4=True,
                parameter_ids=parameter_ids,
                provenance_summary=_provenance_summary(selected.values()),
                m4_candidate_context=context,
                notes="M3 conservative S1-S5/E1-E9; E8/E9 are regime-conditional design outputs, not global optima. " + "; ".join(exact.warnings),
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
    assessment_by_id = {item.candidate_id: item for item in assessments}
    for record in records:
        if record.m4_candidate_context is not None:
            record.m4_candidate_context.enzyme_sequence_sha256 = assessment_by_id[record.candidate_id].enzyme_sequence_sha256
    _label_scientific_results(config, records)
    write_models(stage_dir, "concentration_assessments", records)
    return records, _stage_output("m3_enrichment", stage_dir, "concentration_assessments", len(records))


def _m3_formal_source_violations(selected: dict[str, ParameterResolution], site_count_basis: str) -> list[str]:
    allowed_sources = {
        "phi": {"wetlab"},
        "ptr_total": {"wetlab"},
        "pt_total": {"wetlab"},
        "oc_total": {"wetlab"},
        "dmt_total": {"wetlab"},
        "partition_ptr": {"wetlab", "literature"},
        "partition_pt": {"wetlab", "literature"},
        "partition_oc": {"wetlab", "literature"},
        "partition_dmt": {"wetlab", "literature"},
        "c_dense_scaffold": {"wetlab", "literature"},
        "c_total_scaffold": {"wetlab", "literature"},
        "c_sat_scaffold": {"wetlab", "literature"},
        "kd_sh3": {"wetlab", "literature"},
        "kd_pdz": {"wetlab", "literature"},
    }
    allowed_sources.update({name: {"wetlab", "literature"} for name in selected if name.startswith("partition_x")})
    missing: list[str] = []
    for name, allowed in allowed_sources.items():
        if name not in selected:
            continue
        resolution = selected[name]
        record = resolution.selected_parameter
        if record is None or record.source_type not in allowed:
            missing.append(f"formal M3 source for {name}: {sorted(allowed)}")
    for name in ("c_dense_scaffold", "c_total_scaffold", "c_sat_scaffold"):
        if name not in selected:
            continue
        record = selected[name].selected_parameter
        if record is not None and record.conditions.get("entity_basis") != site_count_basis:
            missing.append(f"{name} conditions.entity_basis matching M2 site_count_basis")
        if record is not None and (not record.construct_id or not record.condition_id):
            missing.append(f"{name} explicit matching fusion construct and condition identity")
    for name in ("kd_sh3", "kd_pdz"):
        record = selected[name].selected_parameter
        if record is not None and not record.conditions.get("binding_pair"):
            missing.append(f"{name} conditions.binding_pair")
    return sorted(set(missing))


def run_m4(config: ProjectConfig, run_dir: Path, assessments: list[M3ConcentrationAssessment]) -> tuple[list[M4ReactionPrediction], StageOutput]:
    records, output = _run_m4_base(config, run_dir, assessments)
    settings = config.stages.m4_reaction
    for record in records:
        record.experimental_contract = {
            "assay_mode":settings.assay_mode,"expression_mode":settings.expression_mode,
            "measurement_compartment":settings.measurement_compartment,
            "assay_conditions":config.experimental_context.model_dump(mode="json"),
            "input_boundary":{"feed_mode":settings.feed_mode,"feed_compound_id":settings.feed_compound_id,
                              "feeding_time_h":settings.feeding_time_h},
            "confirmed_absent_enzymes":settings.confirmed_absent_enzymes,
            "steady_state_observation_reference":settings.steady_state_observation_reference,
            "claim_scope":record.claim_scope,
            "approximation_scope":"rapid_phase_partition_and_independent_site_binding_not_experimental_validation"}
        contract = record.simulation_inputs.get("prediction_contract")
        if contract:
            contract["experiment_context"] = record.experimental_contract
        if record.trajectory_artifact and record.trajectory_artifact.is_file():
            artifact = json.loads(record.trajectory_artifact.read_text(encoding="utf-8"))
            if "prediction_contract" in artifact:
                artifact["prediction_contract"]["experiment_context"] = record.experimental_contract
                artifact.update(experimental_contract=record.experimental_contract,
                                construct_id=record.construct_id,condition_id=record.condition_id)
                record.trajectory_artifact.write_text(json.dumps(artifact),encoding="utf-8")
    if config.stages.m4_reaction.analysis is not None:
        from igem_drylab.design_analysis import analyze_prediction
        for record in records:
            if record.status != "valid":
                continue
            try:
                for evidence in config.stages.m4_reaction.analysis.ranges:
                    sources = [r for r in config.parameters if r.parameter_id in evidence.parameter_ids]
                    if len(sources)!=len(evidence.parameter_ids) or any(r.name!=evidence.parameter_name or r.review_status!="approved"
                            or r.parameter_id not in record.parameter_ids for r in sources):
                        raise ValueError("analysis_range_requires_matching_approved_candidate_parameter_sources")
                record.analysis_result = analyze_prediction(record.simulation_inputs["prediction_contract"], config.stages.m4_reaction.analysis)
                record.robustness = record.analysis_result["robustness"]
                record.sensitivity = record.analysis_result["sensitivity"]
            except (ValueError, RuntimeError, KeyError) as error:
                record.analysis_result = {"status":"insufficient_data","error":str(error)}
        write_models(run_dir / "m4_analysis", "reaction_predictions_with_analysis", records)
    write_models(output.directory, output.json_file.stem, records)
    return records, output


def _run_m4_base(config: ProjectConfig, run_dir: Path, assessments: list[M3ConcentrationAssessment]) -> tuple[list[M4ReactionPrediction], StageOutput]:
    formal_missing = _formal_analysis_missing(config)
    if config.stages.m4_reaction.confirmed_absent_enzymes:
        formal_missing.append("declared genetic absence requires an explicit active-subnetwork version; missing kinetics cannot be set to zero")
    if _is_formal(config) and config.stages.m4_reaction.activity_mode == "unity_assumption":
        formal_missing.append("formal M4 requires reviewed phase activity; unity is sensitivity-only")
    if formal_missing:
        directory = run_dir / "m4_evidence_gate"
        records = [_m4_insufficient(item.candidate_id, config, formal_missing, construct_id=item.construct_id) for item in assessments]
        write_models(directory, "reaction_predictions", records)
        return records, _stage_output("m4_evidence_gate", directory, "reaction_predictions", len(records))
    if config.stages.m4_reaction.network_mode == "markdown_steady_state":
        return _run_markdown_steady_m4(config, run_dir, assessments)
    if config.stages.m4_reaction.network_mode == "published_reference":
        return _run_published_reference_m4(config, run_dir)
    if config.stages.m4_reaction.network_mode == "galatea_full_competitive":
        return _run_full_network_m4(config, run_dir, assessments)
    stage_dir = run_dir / "m4_glabridin_kinetics"
    gates = config.stages.m4_reaction
    gate_missing = [name for name in ("pt_gate", "oc_gate", "dmt_gate") if getattr(gates, name) is None]
    records: list[M4ReactionPrediction] = []
    for item in assessments:
        if not _m3_ready_for_m4(config, item):
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
            trajectory = stage_dir / f"{sha256(item.candidate_id.encode()).hexdigest()[:20]}_{condition_fingerprint}_trajectory.json"
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
    _label_scientific_results(config, records)
    write_models(stage_dir, "reaction_predictions", records)
    return records, _stage_output("m4_glabridin_kinetics", stage_dir, "reaction_predictions", len(records))


def _run_markdown_steady_m4(
    config: ProjectConfig,
    run_dir: Path,
    assessments: list[M3ConcentrationAssessment],
) -> tuple[list[M4ReactionPrediction], StageOutput]:
    stage_dir = run_dir / "m4_markdown_steady_state"
    settings = config.stages.m4_reaction
    requirements = requirements_for_stage(config, "m4")
    records: list[M4ReactionPrediction] = []
    for item in assessments:
        context = item.m4_candidate_context
        if not _m3_ready_for_m4(config, item):
            records.append(_m4_insufficient(item.candidate_id, config, ["valid conservative M3 context"], construct_id=item.construct_id))
            continue
        selected, missing = validate_parameters(
            config.parameters,
            requirements=_candidate_requirements(requirements, context),
            allow_assumptions=config.execution.allow_assumptions,
            host=config.experimental_context.host,
            strain=config.experimental_context.strain,
            assay_system=config.experimental_context.assay_system,
            pH=config.experimental_context.pH,
            temperature_c=config.experimental_context.temperature_c,
            construct_id=context.construct_id,
            condition_id=context.condition_id,
            require_provenance=config.execution.mode == "real" and config.execution.require_provenance,
        )
        required_files = []
        if settings.reaction_network_file is None:
            required_files.append("reaction_network_file")
        if settings.steady_state_initial_guess_um is None:
            required_files.append("steady_state_initial_guess_um")
        if set(context.enzyme_distribution) != {"PTR", "PT", "OC", "DMT"}:
            required_files.append("M3 PTR/PT/OC/DMT phase concentrations")
        if set(context.metabolite_partition_coefficients) != {str(index) for index in range(8, 16)}:
            required_files.append("M3 Kp8-Kp15")
        if missing or required_files:
            records.append(_m4_insufficient(item.candidate_id, config, [*missing, *required_files], construct_id=item.construct_id))
            continue
        if config.execution.mode == "real":
            bad_sources = [
                name for name, resolution in selected.items()
                if resolution.selected_parameter is None or resolution.selected_parameter.source_type not in {"wetlab", "literature"}
            ]
            if bad_sources:
                records.append(_m4_insufficient(item.candidate_id, config, [f"formal measured/verified M4 source: {name}" for name in bad_sources], construct_id=item.construct_id))
                continue
        reaction_identities = load_m4_reaction_identities(settings.reaction_network_file)
        reaction_inputs = [
            M4ReactionInput(
                reaction_id=reaction_id,
                enzyme=enzyme,
                substrate=substrate,
                product=product,
                kcat_per_h=selected[f"kcat_{reaction_id.lower()}"].canonical_value,
                km_um=selected[f"km_{reaction_id.lower()}"].canonical_value,
                parameter_ids=[
                    selected[f"kcat_{reaction_id.lower()}"].selected_parameter.parameter_id,
                    selected[f"km_{reaction_id.lower()}"].selected_parameter.parameter_id,
                ],
            )
            for reaction_id, enzyme, substrate, product in reaction_identities
        ]
        parameter_ids = sorted(
            resolution.selected_parameter.parameter_id
            for resolution in selected.values()
            if resolution.selected_parameter
        )
        steady_inputs = M4SteadyStateInput(
            candidate_id=item.candidate_id,
            construct_id=context.construct_id,
            condition_id=context.condition_id,
            phi=context.phi,
            enzymes={name: M4PhaseEnzymeInput(dense_um=value["dense"], dilute_um=value["dilute"], m3_source_id=item.candidate_id,
                activity_dense_ratio=selected[f"activity_dense_{name.lower()}"].canonical_value if settings.activity_mode == "sensitivity_parameters" else 1.0,
                activity_dilute_ratio=selected[f"activity_dilute_{name.lower()}"].canonical_value if settings.activity_mode == "sensitivity_parameters" else 1.0) for name, value in context.enzyme_distribution.items()},
            metabolite_kp=context.metabolite_partition_coefficients,
            reactions=reaction_inputs,
            input_flux_um_per_h=selected["input_flux_8"].canonical_value,
            secretion_rate_per_h={compound: selected[f"ksec_{compound}"].canonical_value for compound in ("8", "9", "10", "11", "12", "13", "14", "15")},
            secretion_normalization="original_unweighted_dilute_concentration",
            initial_guess_um=settings.steady_state_initial_guess_um,
            input_parameter_ids=sorted({*context.parameter_ids, *parameter_ids}),
        )
        result = solve_m4_steady_state(steady_inputs)
        if result.status != "valid":
            records.append(M4ReactionPrediction(
                candidate_id=item.candidate_id,
                construct_id=context.construct_id,
                condition_id=context.condition_id,
                target_product=settings.target_product,
                status="insufficient_data" if result.status == "blocked" else "failed",
                data_quality="mixed",
                missing_inputs=result.warnings,
                recommendation=None,
                candidate_context=context,
                parameter_ids=result.input_parameter_ids,
                notes="M4 steady-state solution was not released.",
            ))
            continue
        contract = steady_contract(steady_inputs, result)
        trajectory = stage_dir / f"{sha256((item.candidate_id + '|' + context.condition_id).encode()).hexdigest()[:24]}_steady_prediction.json"
        trajectory.parent.mkdir(parents=True, exist_ok=True)
        trajectory.write_text(json.dumps({"prediction_contract": contract}), encoding="utf-8")
        records.append(M4ReactionPrediction(
            candidate_id=item.candidate_id,
            construct_id=context.construct_id,
            condition_id=context.condition_id,
            target_product=settings.target_product,
            status="valid",
            data_quality="mixed",
            final_15=result.concentrations_cell_average_um["15"],
            final_13=result.concentrations_cell_average_um["13"],
            yield_abs=result.yield_abs,
            secretion_loss=result.secretion_loss_8_to_14,
            recommendation=None,
            candidate_context=context,
            simulation_inputs={"prediction_contract": contract, "parameters": {name: resolution.canonical_value for name, resolution in selected.items()}},
            trajectory_artifact=trajectory,
            steady_state_fluxes=result.reaction_flux_um_per_h,
            steady_state_residuals=result.steady_state_residual_um_per_h,
            mechanistic_diagnostics={"mass_invariant_residual": result.mass_invariant_residual,
                "q_10_to_11": result.reaction_flux_um_per_h["R3"]/(result.reaction_flux_um_per_h["R3"]+result.reaction_flux_um_per_h["R6"])
                    if result.reaction_flux_um_per_h["R3"]+result.reaction_flux_um_per_h["R6"]>0 else None,
                "q_9_to_13": result.reaction_flux_um_per_h["R5"]/(result.reaction_flux_um_per_h["R2"]+result.reaction_flux_um_per_h["R5"])
                    if result.reaction_flux_um_per_h["R2"]+result.reaction_flux_um_per_h["R5"]>0 else None},
            transport_report={"secretion_flux_um_per_h":result.secretion_flux_um_per_h,
                "product_recovery_15_um_per_h":result.secretion_flux_um_per_h["15"],
                "intermediate_outflow_8_to_14_um_per_h":sum(result.secretion_flux_um_per_h[str(i)] for i in range(8,15)),
                "13_role":"reactive_intermediate_not_dead_end","branch_scope":"steady_flux_fraction_not_single_molecule_channeling"},
            parameter_ids=result.input_parameter_ids,
            provenance_summary=_merge_provenance(context.provenance_summary, _provenance_summary(selected.values())),
            assumptions=result.warnings,
            notes="Original M4 Step 0-8 steady-state output; no ranking, robustness, sensitivity, or scaffold scan was invented.",
        ))
    _label_scientific_results(config, records)
    write_models(stage_dir, "reaction_predictions", records)
    return records, _stage_output("m4_markdown_steady_state", stage_dir, "reaction_predictions", len(records))


def _run_full_network_m4(config: ProjectConfig, run_dir: Path, assessments: list[M3ConcentrationAssessment]) -> tuple[list[M4ReactionPrediction], StageOutput]:
    """Production Galatea M4: full 8-compound / 10-reaction competitive network."""
    stage_dir = run_dir / "m4_glabridin_full_network"
    settings = config.stages.m4_reaction
    author_native = settings.unit_mode == "author_native_sensitivity"
    requirements = requirements_for_stage(config, "m4")
    records: list[M4ReactionPrediction] = []
    for item in assessments:
        context = item.m4_candidate_context
        if not _m3_ready_for_m4(config, item):
            records.append(_m4_insufficient(item.candidate_id, config, ["valid effective-ratio or finite-site M3 context"], construct_id=item.construct_id))
            continue
        selected, missing = validate_parameters(
            config.parameters, requirements=_candidate_requirements(requirements, context), allow_assumptions=config.execution.allow_assumptions,
            host=config.experimental_context.host, strain=config.experimental_context.strain,
            assay_system=config.experimental_context.assay_system, pH=config.experimental_context.pH,
            temperature_c=config.experimental_context.temperature_c, construct_id=context.construct_id,
            condition_id=context.condition_id, require_provenance=config.execution.mode == "real" and config.execution.require_provenance,
        )
        if missing or settings.full_network_initial_state is None or settings.reaction_network_file is None:
            records.append(_m4_insufficient(item.candidate_id, config, missing + (["full_network_initial_state"] if settings.full_network_initial_state is None else []) + (["reaction_network_file"] if settings.reaction_network_file is None else []), construct_id=context.construct_id))
            continue
        if _is_formal(config):
            state_missing = _formal_initial_state_missing(config, context)
            if state_missing:
                records.append(_m4_insufficient(item.candidate_id, config, state_missing, construct_id=context.construct_id))
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
        def configured_gate(value):
            return TemporalGate(mode="configured_induction", induction=InductionGate(**value.model_dump(exclude={"time_unit"}))) if value else TemporalGate()
        gate = configured_gate(settings.dmt_gate)
        transport = TransportParameters(
            enabled=settings.transport_enabled, access=settings.transport_access,
            rate=selected[settings.transport_rate_parameter or "transport_rate"].canonical_value if settings.transport_enabled else 0.0,
            outside_over_inside=settings.transport_outside_over_inside,
            intracellular_volume_l=settings.intracellular_volume_l,
            extracellular_volume_l=settings.extracellular_volume_l,
        )
        params = FullNetworkParameters(
            enzyme_distributions=distributions, phi=context.phi, metabolite_kp=kp,
            reactions=reactions,
            scenario=settings.scenario_mode, transport=transport, dmt_gate=gate,
            pt_gate=configured_gate(settings.pt_gate), oc_gate=configured_gate(settings.oc_gate),
            activity_dense=activity_dense, activity_dilute=activity_dilute,
            unit_mode=settings.unit_mode,
        )
        result = simulate_full_network(params, initial_intracellular=settings.full_network_initial_state.intracellular,
            initial_extracellular=settings.full_network_initial_state.extracellular, t_end=settings.t_end, points=settings.solver_points)
        contract = dynamic_contract(params, result, settings.full_network_initial_state.intracellular,
            settings.full_network_initial_state.extracellular, settings.t_end, settings.solver_points)
        fingerprint = sha256(context.condition_id.encode("utf-8")).hexdigest()[:10]
        trajectory = stage_dir / f"{sha256(item.candidate_id.encode()).hexdigest()[:20]}_{fingerprint}_full_trajectory.json"
        trajectory.parent.mkdir(parents=True, exist_ok=True)
        trajectory.write_text(json.dumps({
            "prediction_contract": contract,
            "candidate_id": item.candidate_id, "construct_id": context.construct_id, "condition_id": context.condition_id,
            "time": result.time.tolist(), "intracellular_cell_average": {str(index + 8): result.intracellular[index].tolist() for index in range(8)},
            "extracellular": {str(index + 8): result.extracellular[index].tolist() for index in range(8)},
            "reaction_fluxes": {f"R{index + 1}": result.fluxes[index].tolist() for index in range(10)},
            "flux_integrals": result.flux_integrals, "diagnostics": result.diagnostics,
            "raw_intracellular_cell_average": {str(index+8):result.raw_intracellular[index].tolist() for index in range(8)},
            "raw_extracellular": {str(index+8):result.raw_extracellular[index].tolist() for index in range(8)},
            "transport_integrals": result.transport_integrals,
            "solver_settings": result.solver_settings,
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
            side_product_fraction_13=result.diagnostics["side_product_fraction_13"],
            leakage_fraction=None, productivity=None if author_native else max(0.0, result.diagnostics["net_15_generated_cell_volume_equivalent"]) / settings.t_end,
            recommendation="iterate", recommendation_evidence=["comparative_negative_screen_requires_control_comparison"],
            candidate_context=context, simulation_inputs={"prediction_contract": contract, "parameters": {name: resolution.canonical_value for name, resolution in selected.items()}, "executed_config": settings.model_dump(mode="json")},
            bottleneck="full_network_comparative_screen", trajectory_artifact=trajectory,
            flux_integrals=({f"relative_{key}": value for key, value in result.flux_integrals.items()} if author_native else result.flux_integrals),
            transport_report={"integrals":result.transport_integrals,"units":_full_network_units(settings),
                "product_recovery_species":"15","intermediate_outflow_species":[str(i) for i in range(8,15)],
                "13_role":"reactive_intermediate_not_dead_end",
                "branch_scope":"processed_substrate_interval_fraction_not_single_molecule_channeling"},
            mechanistic_diagnostics=({key: result.diagnostics[key] for key in (
                "target_yield_fraction", "branch_9_to_13_fraction", "dmt_late_selectivity",
                "early_dmt_fraction", "oc_before_dmt_route_fraction", "side_product_fraction_13",
                "mass_balance_error",
            )} if author_native else result.diagnostics), parameter_ids=sorted({*context.parameter_ids, *(entry.selected_parameter.parameter_id for entry in selected.values() if entry.selected_parameter)}),
            provenance_summary=provenance, assumptions=["M1/M2 structural and docking scores are not kinetic inputs", "M4 is a mechanistic sensitivity model", activity_assumption],
            notes=("Full 8-compound / 10-reaction phase-specific competitive model. Values are not enzyme activity or yield predictions."
                   if result.unit_mode == "physical" else "Results are normalized mechanistic sensitivity outputs and must not be interpreted as absolute concentration, enzyme abundance, kinetic rate, productivity, or titer."),
        ))
    _label_scientific_results(config, records)
    write_models(stage_dir, "reaction_predictions", records)
    return records, _stage_output("m4_glabridin_full_network", stage_dir, "reaction_predictions", len(records))


def _full_network_reactions(settings: object, selected: dict[str, object]) -> tuple[object, ...]:
    """Keep physical and author-native kinetic acquisition paths disjoint."""
    if settings.unit_mode == "author_native_sensitivity":  # type: ignore[attr-defined]
        return load_author_native_reactions(settings.reaction_network_file)
    return tuple(
        ReactionKinetics(
            reaction_id, enzyme, substrate, product,
            selected[f"kcat_{reaction_id.lower()}"].canonical_value,
            selected[f"km_{reaction_id.lower()}"].canonical_value,
        )
        for reaction_id, enzyme, substrate, product in load_m4_reaction_identities(settings.reaction_network_file)
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
    record.numerically_solved = True
    record.claim_scope = "author_code_reproduction"
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
            group_key = _fit_group_key(result)
            if group_key not in fitted_by_group:
                aggregate = fit_groups.get(group_key)
                aggregate_prediction = prediction_by_context.get((result.construct_id, result.condition_id))
                try:
                    aggregate_comparisons = compare_prediction(aggregate_prediction.trajectory_artifact, aggregate) if aggregate and aggregate_prediction and aggregate_prediction.trajectory_artifact else {}
                except ValueError as error:
                    aggregate_comparisons = {}
                    report.flags.append(f"comparison_contract_error:{error}")
                fitted_by_group[group_key] = _fit_plan_candidate(config, aggregate_prediction, aggregate, aggregate_comparisons) if aggregate else None
            fitted = fitted_by_group[group_key]
            if fitted and fitted.get("warning"):
                report.flags.append(f"fit_contract_warning:{fitted['warning']}")
            records.append(M5FeedbackAssessment(experiment_id=result.experiment_id, construct_id=result.construct_id, condition_id=result.condition_id, replicate_id=result.replicate_id, status="valid" if report.passed and usable else "insufficient_data", data_quality="measured", qc_passed=report.passed, qc_flags=report.flags, diagnosis=joint_diagnosis, prediction_residual=residual, trend_agreement=trend, replicate_variation=variation, fit=fitted.get("fit") if fitted else None, metabolite_comparisons={key: value.model_dump() for key, value in comparisons.items()}, diagnosis_evidence=evidence, fitted_parameter_candidate=fitted.get("candidate") if fitted else None, next_measurement="measure OC/DMT abundance and metabolite time course" if joint_diagnosis not in {"INSUFFICIENT_INFORMATION", "NO_SIGNIFICANT_DISCREPANCY"} else None, notes=f"Raw outliers retained; comparison={comparison_status}; diagnosis_metabolites={','.join(item.metabolite_id for item in usable)}."))
    for record in records:
        record.fit_warnings = [flag.removeprefix("fit_contract_warning:") for flag in record.qc_flags if flag.startswith("fit_contract_warning:")]
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


def _is_formal(config: ProjectConfig) -> bool:
    return (config.execution.mode == "real" and config.execution.analysis_grade == "formal_measured"
            and config.stages.m4_reaction.unit_mode == "physical"
            and config.stages.m4_reaction.network_mode != "published_reference")


def _candidate_requirements(requirements, context):
    return [item.model_copy(update={"enzyme_sequence_sha256": context.enzyme_sequence_sha256.get(item.enzyme_id)}) for item in requirements]


def _m3_ready_for_m4(config, assessment):
    context = assessment.m4_candidate_context
    return (assessment.status == "valid" and context is not None and
            (not _is_formal(config) or (assessment.recommended_for_m4 and context.evidence_ready)))


def _formal_initial_state_missing(config, context):
    from igem_drylab.parameters import ParameterRegistry
    from igem_drylab.parameters.requirements import ParameterRequirement
    registry = ParameterRegistry(config.parameters)
    initial = config.stages.m4_reaction.full_network_initial_state
    missing = []
    for compartment, states in (("intracellular", initial.intracellular), ("extracellular", initial.extracellular)):
        if compartment == "extracellular" and not config.stages.m4_reaction.transport_enabled and not any(states.values()):
            continue
        for compound, value in states.items():
            key = f"{compartment}:{compound}"
            record = registry.get(initial.parameter_ids.get(key, ""))
            if record is None:
                missing.append(f"reviewed initial state parameter: {key}")
                continue
            requirement = ParameterRequirement(name=record.name, parameter_type="abundance", dimension="concentration", canonical_unit="uM", species_id=compound, minimum=0)
            resolved = registry.resolve(requirement, host=config.experimental_context.host,
                strain=config.experimental_context.strain, assay_system=config.experimental_context.assay_system,
                temperature_c=config.experimental_context.temperature_c, pH=config.experimental_context.pH,
                construct_id=context.construct_id, condition_id=context.condition_id, require_provenance=True)
            if resolved.status != "resolved" or resolved.selected_parameter.parameter_id != record.parameter_id or resolved.canonical_value != value or record.conditions.get("compartment") != compartment or record.conditions.get("measurement_time_h") != 0:
                missing.append(f"initial state value/compartment/time applicability: {key}")
    return missing


def _formal_analysis_missing(config: ProjectConfig) -> list[str]:
    if not _is_formal(config):
        return []
    missing = [f"formal experimental_context.{name}" for name in ("host", "temperature_c", "pH", "assay_system")
               if getattr(config.experimental_context, name) is None]
    if not config.stages.m4_reaction.condition_id:
        missing.append("formal explicit condition_id")
    settings = config.stages.m4_reaction
    if settings.assay_mode is None or settings.expression_mode is None:
        missing.append("formal explicit assay_mode and expression_mode")
    if settings.feed_mode == "batch_initial_state" and settings.feeding_time_h is None:
        missing.append("formal explicit feeding_time_h")
    if settings.network_mode == "markdown_steady_state" and not settings.steady_state_observation_reference:
        missing.append("formal steady_state_observation_reference for steady prediction applicability")
    if config.stages.m4_reaction.feed_mode is None or config.stages.m4_reaction.feed_compound_id is None:
        missing.append("formal explicit feed identity and boundary condition")
    if not config.execution.require_provenance or config.execution.allow_assumptions:
        missing.append("formal requires provenance and prohibits assumptions")
    if config.stages.m4_reaction.transport_enabled:
        missing.append("formal transport compartment-volume/equilibrium applicability adapter not connected; sensitivity-only")
    return missing


def _label_scientific_results(config: ProjectConfig, records: list[object]) -> None:
    for record in records:
        record.numerically_solved = record.status == "valid"
        record.evidence_ready = record.numerically_solved and _is_formal(config)
        record.claim_scope = ("author_native_sensitivity" if config.stages.m4_reaction.unit_mode == "author_native_sensitivity" else
                              "software_fixture_only" if config.execution.mode == "demo" else "conditional_mechanism") if record.numerically_solved else "not_established"
        context = getattr(record, "m4_candidate_context", None)
        if context is not None:
            context.evidence_ready = record.evidence_ready
            context.claim_scope = record.claim_scope


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
    values = dict(prediction.simulation_inputs.get("parameters", {}))
    kernel_key = requirement_name_to_kernel_key(plan.parameter_name)
    fixed_kernel_keys = {requirement_name_to_kernel_key(name) for name in plan.fixed_parameter_names}
    if kernel_key not in values or kernel_key in fixed_kernel_keys:
        return {"fit": None, "candidate": None, "warning": "FitPlan parameter absent_or_declared_fixed"}
    inputs = prediction.simulation_inputs
    contract = inputs.get("prediction_contract")
    if contract and contract["concentration_unit"] != "uM":
        return {"fit": None, "candidate": None, "warning": "author_native_model_cannot_fit_absolute_measurements"}
    if not contract and not all(name in inputs for name in ("pt_gate", "oc_gate", "dmt_gate", "initial", "t_end")):
        return {"fit": None, "candidate": None, "warning": "insufficient_data:missing_model_fit_adapter"}
    def predictor(value: float) -> np.ndarray:
        if contract:
            changed_contract = replay_prediction(contract, plan.parameter_name, value)
            time, series = observe_prediction(changed_contract, result)
            return np.asarray([np.interp(time_h, time, series[observable]) for observable, time_h in fit_points])
        changed = dict(values); changed[kernel_key] = value
        simulation = simulate_glabridin(GlabridinKineticParameters(**changed), pt_gate=InductionGate(**{k: v for k, v in inputs["pt_gate"].items() if k != "time_unit"}), oc_gate=InductionGate(**{k: v for k, v in inputs["oc_gate"].items() if k != "time_unit"}), dmt_gate=InductionGate(**{k: v for k, v in inputs["dmt_gate"].items() if k != "time_unit"}), initial=tuple(inputs["initial"][f"x{key}"] for key in ("9", "10", "11", "13", "15")), t_end=inputs["t_end"])
        return np.asarray([np.interp(time_h, simulation.time, getattr(simulation, f"x{observable}")) for observable, time_h in fit_points])
    try:
        # The input is an aggregate trajectory. Time points are correlated, so they
        # are not valid IID bootstrap units. A replicate-block bootstrap requires
        # retained individual replicate trajectories and is intentionally withheld.
        fit = fit_mechanistic_parameter(parameter_name=plan.parameter_name, initial_value=values[kernel_key], bounds=plan.bounds, observed=observed, predictor=predictor, bootstrap_samples=0)
        if fit.status != "estimated" or fit.best_fit is None:
            return {"fit": fit.model_dump(), "candidate": None, "warning": fit.identifiability_warning}
        fit = fit.model_copy(update={"confidence_interval": None, "identifiability_warning": "replicate_block_bootstrap_not_run_on_aggregated_trajectory"})
    except ValueError as error:
        return {"fit": None, "candidate": None, "warning": str(error)}
    requirement = next((item for item in [*requirements_for_stage(config, "m4"), *m4_kinetic_requirements(include_degradation=True)] if item.name == plan.parameter_name), None)
    if requirement is None:
        return {"fit": None, "candidate": None, "warning": "FitPlan parameter is not an approved M4 requirement"}
    source_lineage = result.notes or result.experiment_id
    fingerprint_input = {"construct": prediction.construct_id, "condition": prediction.condition_id, "requirement": requirement.name,
        "source_lineage": source_lineage, "fit_points": fit_points, "observed_uM": observed,
        "canonical_observations": {species: canonicalize_metabolite(result, species).model_dump(mode="json") for species in sorted(result.metabolites)},
        "source_replicate_data": result.source_replicate_data,
        "compartment": result.measurement_compartment, "basis": result.concentration_basis,
        "assay_conditions": result.conditions_for("metabolites").model_dump(mode="json") if result.conditions_for("metabolites") else None,
        "extraction_volume_l": result.extraction_volume_l, "observation_kind": result.observation_kind,
        "parameter_ids": sorted(prediction.parameter_ids), "bounds": plan.bounds, "observables": plan.observables,
        "model_inputs": contract or inputs, "contract": "m4-fit-observation-v2"}
    dataset_hash = sha256(json.dumps(fingerprint_input, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    assay = result.conditions_for("metabolites")
    candidate = ParameterRecord(parameter_id=f"fit:{dataset_hash}", name=requirement.name, value=fit.best_fit, unit=requirement.canonical_unit, parameter_type=requirement.parameter_type, enzyme_id=requirement.enzyme_id, substrate_id=requirement.substrate_id, product_id=requirement.product_id, species_id=requirement.species_id, source_type="wetlab", derivation_type="model_fit", source_reference=source_lineage, review_status="validated", construct_id=result.construct_id, condition_id=assay.condition_id if assay else result.condition_id, conditions=assay.parameter_conditions() if assay else {}, derived_from=[*prediction.parameter_ids, *([result.raw_data_sha256] if result.raw_data_sha256 else [])], notes=f"model_fit dataset_hash={dataset_hash}; target_requirement={requirement.name}; fit_bounds={plan.bounds}; observables={plan.observables}; source_lineage={source_lineage}; human approval is required before registry use.")
    if result.raw_data_sha256:
        candidate.notes += f"; raw_data_sha256={result.raw_data_sha256}"
    return {"fit": fit.model_dump(), "candidate": candidate.model_dump(mode="json")}


def _aggregate_fit_groups(results: list[object]) -> dict[tuple[str, str], object]:
    """Create a canonical fit dataset only from aligned, fully quantified replicates.

    Censored values are intentionally not replaced by a LOD/2 heuristic.  A
    metabolite lacking a complete quantified biological-replicate series is
    withheld from fitting rather than silently averaged as though quantified.
    """
    groups: dict[tuple[str, str], list[object]] = {}
    for result in results:
        groups.setdefault(_fit_group_key(result), []).append(result)
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
            aggregated[key].source_replicate_data = sorted([
                {"experiment_id": record.experiment_id, "replicate_id": record.replicate_id,
                 "batch_id": record.batch_id, "biological_replicate_count": record.biological_replicate_count,
                 "series": {species: canonicalize_metabolite(record, species).model_dump(mode="json") for species in sorted(record.metabolites)}}
                for record in records], key=lambda row: (row["experiment_id"], row["replicate_id"]))
    return aggregated


def _fit_group_key(result):
    base = (result.construct_id, result.condition_id)
    assay = result.conditions_for("metabolites")
    if assay:
        base = (*base, json.dumps(assay.parameter_conditions(), sort_keys=True))
    if result.measurement_compartment is None:
        return base
    return (*base, result.measurement_compartment, result.concentration_basis, result.observation_kind, result.extraction_volume_l)


def _fit_eligible(result: object) -> bool:
    """FitPlan only receives QC-valid records with a declared usable unit."""
    if getattr(result, "metabolite_concentration_unit", None) is None:
        return False
    try:
        return any("quantified" in canonicalize_metabolite(result, species).censor_mask for species in result.metabolites)
    except ValueError:
        return False
