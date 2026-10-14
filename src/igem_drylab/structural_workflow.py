"""M2 Q1/Q2 complete reference comparison from explicit reviewed selections."""
import json
from pathlib import Path
from pydantic import BaseModel

import numpy as np
from pydantic import Field

from .design_analysis import ScientificAnalysisInput
from .template_geometry import (StructureInput, CAMapping, ResidueSelection, atom_sasa,
                                selected_sasa, selected_atoms, clashes, _hashes)
from .structure_metrics import aligned_ca_rmsds


class M2EnzymeComparisonInput(ScientificAnalysisInput):
    candidate_id: str
    reference: StructureInput
    fusion: StructureInput
    core_mapping: CAMapping
    pocket_mapping: list[tuple[int | str, int | str]] = Field(min_length=1)
    pocket_definition_reference: str = Field(min_length=1)
    introduced_tail: ResidueSelection | None = None
    recruitment_ligand: ResidueSelection | None = None
    clash_cutoff_angstrom: float = Field(gt=0)
    clash_rule_reference: str = Field(min_length=1)
    burial_retention_cutoff: float | None = Field(default=None, ge=0, le=1)
    burial_rule_reference: str | None = None


class M2CoreComparisonInput(ScientificAnalysisInput):
    """Apo folded-core observation; absent holo pocket cannot become Q1 pass."""
    candidate_id: str
    reference: StructureInput
    fusion: StructureInput
    core_mapping: CAMapping
    core_definition_reference: str = Field(min_length=1)


def compare_fusion_core(payload: M2CoreComparisonInput):
    reference,ref_confidence=payload.reference.read();fusion,confidence=payload.fusion.read()
    ref_selection=ResidueSelection(chain=payload.core_mapping.reference_chain,residues=[a for a,_ in payload.core_mapping.residue_pairs])
    selection=ResidueSelection(chain=payload.core_mapping.mobile_chain,residues=[b for _,b in payload.core_mapping.residue_pairs])
    selected_atoms(reference,ref_selection);selected_atoms(fusion,selection)
    means=[float(np.mean([scores[k] for k in keys])) for scores,keys in ((ref_confidence,ref_selection.keys()),(confidence,selection.keys())) if scores is not None]
    gate='high' if not means or min(means)>70 else 'medium' if min(means)>=50 else 'low'
    rmsd=payload.core_mapping.fit(reference,fusion)[2] if gate!='low' else None
    return dict(schema_version='m2-core-only-comparison-v1',candidate_id=payload.candidate_id,core_ca_rmsd_angstrom=rmsd,
        core_residue_count=len(payload.core_mapping.residue_pairs),core_mean_confidence=means,confidence_gate=gate,
        core_definition_reference=payload.core_definition_reference,source_hashes=_hashes(payload.reference,payload.fusion),
        formal_verdict='blocked',missing=['complete sourced holo pocket and chemistry','full Q1-Q4/ER prerequisites'],
        scope='apo_frozen_core_observation_not_complete_pocket_assessment_or_enzyme_activity')


def compare_fusion_to_reference(payload: M2EnzymeComparisonInput) -> dict:
    reference, reference_confidence = payload.reference.read()
    fusion, confidence = payload.fusion.read()
    core_selection = ResidueSelection(chain=payload.core_mapping.mobile_chain,
                                      residues=[b for _, b in payload.core_mapping.residue_pairs])
    ref_core = ResidueSelection(chain=payload.core_mapping.reference_chain,
                               residues=[a for a, _ in payload.core_mapping.residue_pairs])
    ref_pocket = ResidueSelection(chain=payload.core_mapping.reference_chain, residues=[a for a, _ in payload.pocket_mapping])
    pocket = ResidueSelection(chain=payload.core_mapping.mobile_chain, residues=[b for _, b in payload.pocket_mapping])
    core_atoms = selected_atoms(fusion, core_selection)
    pocket_atoms = selected_atoms(fusion, pocket)
    selected_atoms(reference, ref_pocket)
    if (payload.burial_retention_cutoff is None) != (payload.burial_rule_reference is None):
        raise ValueError("burial_cutoff_requires_reviewed_rule")
    scores = {}
    if confidence is not None:
        for name, selection in (("core", core_selection), ("pocket", pocket)):
            scores[name] = float(np.mean([confidence[key] for key in selection.keys()]))
    reference_scores = {}
    if reference_confidence is not None:
        for name, selection in (("core", ref_core), ("pocket", ref_pocket)):
            reference_scores[name] = float(np.mean([reference_confidence[key] for key in selection.keys()]))
    folded_scores = [*scores.values(), *reference_scores.values()]
    gate = "high" if not folded_scores or min(folded_scores) > 70 else "medium" if min(folded_scores) >= 50 else "low"
    result = {"schema_version": "m2-enzyme-comparison-v1", "candidate_id": payload.candidate_id,
        "confidence_gate": gate, "region_mean_plddt": scores, "reference_region_mean_plddt": reference_scores,
        "q1_verdict": "blocked", "q2_verdict": "blocked",
        "core_ca_rmsd_angstrom": None, "pocket_ca_rmsd_angstrom": None, "pocket_sasa_retention": None,
        "tail_pocket_min_distance_angstrom": None, "tail_core_clashes": None, "ligand_accessibility": None,
        "source_hashes": _hashes(payload.reference, payload.fusion),
        "definition_sources": {"core_mapping": payload.core_mapping.reviewed_reference,
                               "pocket": payload.pocket_definition_reference, "clash": payload.clash_rule_reference},
        "formal_verdict": "blocked", "missing": ["Q3 actual fusion assembly and Q4 recruitment scenario evidence"],
        "scope": "predicted_reference_comparison_not_catalytic_activity"}
    if gate == "low":
        result["missing"].append("low_confidence_folded_core_or_pocket_geometry_not_interpretable")
        return result
    rmsd = aligned_ca_rmsds(payload.reference.path, payload.fusion.path,
        reference_chain=payload.core_mapping.reference_chain, model_chain=payload.core_mapping.mobile_chain,
        core_residues=[a for a, _ in payload.core_mapping.residue_pairs], pocket_residues=[a for a, _ in payload.pocket_mapping],
        core_residue_mapping=payload.core_mapping.residue_pairs, pocket_residue_mapping=payload.pocket_mapping,
        reference_model_id=payload.reference.model_id, model_id=payload.fusion.model_id,
        reference_altloc=payload.reference.altloc, model_altloc=payload.fusion.altloc)
    import freesasa
    parameters = freesasa.Parameters()
    ref_areas = atom_sasa({"reference": reference}, parameters)
    fusion_areas = atom_sasa({"fusion": fusion}, parameters)
    ref_area = selected_sasa(ref_areas, "reference", ref_pocket)
    if ref_area <= 0:
        raise ValueError("reference_pocket_has_no_positive_SASA_no_retention_defined")
    result.update(core_ca_rmsd_angstrom=rmsd["core_ca_rmsd_angstrom"], pocket_ca_rmsd_angstrom=rmsd["pocket_ca_rmsd_angstrom"],
                  pocket_sasa_retention=selected_sasa(fusion_areas, "fusion", pocket)/ref_area)
    failures = []
    if result["core_ca_rmsd_angstrom"] > 4:
        failures.append("original_core_RMSD_gt_4_angstrom")
    if result["pocket_sasa_retention"] < .7:
        failures.append("original_pocket_SASA_retention_lt_0.7")
    result["q1_verdict"] = "reject" if gate == "high" and failures else "review" if gate != "high" else "pass"
    result["q1_rule_hits"] = failures
    if payload.introduced_tail:
        tail = selected_atoms(fusion, payload.introduced_tail)
        if payload.introduced_tail.keys() & (pocket.keys() | core_selection.keys()):
            raise ValueError("tail_selection_must_not_overlap_pocket_or_core")
        result["tail_pocket_min_distance_angstrom"] = clashes(tail, pocket_atoms, payload.clash_cutoff_angstrom)["minimum_distance_angstrom"]
        result["tail_core_clashes"] = clashes(tail, core_atoms, payload.clash_cutoff_angstrom)
        result["tail_geometry_scope"] = "flexible_tail_reference_only_not_a_rejection"
    if payload.recruitment_ligand:
        ligand = selected_atoms(fusion, payload.recruitment_ligand)
        isolated_areas = atom_sasa({"ligand": ligand}, parameters)
        isolated = selected_sasa(isolated_areas, "ligand", payload.recruitment_ligand)
        retention = selected_sasa(fusion_areas, "fusion", payload.recruitment_ligand)/isolated if isolated > 0 else None
        ligand_score = float(np.mean([confidence[k] for k in payload.recruitment_ligand.keys()])) if confidence is not None else None
        credible = ligand_score is None or ligand_score > 70
        buried = retention < payload.burial_retention_cutoff if retention is not None and payload.burial_retention_cutoff is not None and credible else None
        result["ligand_accessibility"] = {"sasa_retention": retention, "mean_plddt": ligand_score,
            "buried": buried, "reference": "same_conformation_isolated_ligand_not_a_free_equilibrium_structure"}
        result["q2_verdict"] = "reject" if buried is True else "pass" if buried is False else "review"
    if result["q1_verdict"] == "reject" or result["q2_verdict"] == "reject":
        result["formal_verdict"] = "reject"
    return result


def calculation_kinds():
    from .template_geometry import (AssemblyExpansionInput, expand_actual_fusion,
        RecruitmentGeometryInput, calculate_recruitment_geometry, RecruitmentEnsembleInput, calculate_recruitment_ensemble,
        AssemblyAccessibilityInput,calculate_assembly_accessibility,
        RecruitmentPosePreparationInput,prepare_recruitment_poses)
    return {"enzyme_comparison": (M2EnzymeComparisonInput, compare_fusion_to_reference),
            'core_comparison':(M2CoreComparisonInput,compare_fusion_core),
            "assembly_expansion": (AssemblyExpansionInput, expand_actual_fusion),
            "recruitment_geometry": (RecruitmentGeometryInput, calculate_recruitment_geometry),
            'recruitment_pose_preparation':(RecruitmentPosePreparationInput,prepare_recruitment_poses),
            "recruitment_ensemble": (RecruitmentEnsembleInput, calculate_recruitment_ensemble),
            'assembly_accessibility':(AssemblyAccessibilityInput,calculate_assembly_accessibility)}


def enzyme_comparison_metrics(request: M2EnzymeComparisonInput, result: dict,
                              candidate_id: str, output_dir: Path):
    """Transfer computed Q1/Q2 observations; absent Q3/Q4 stay absent.

    No template-domain burial, assembly integrity, volume or recruitment
    efficiency is invented to make this partial comparison formally pass.
    """
    from importlib.metadata import version
    from hashlib import sha256
    import freesasa
    from .scoring.m2_structure import M2StructureMetrics
    output_dir.mkdir(parents=True,exist_ok=True)
    geometry=output_dir/'comparison-input.json'
    geometry.write_text(request.model_dump_json(indent=2))
    parameters=freesasa.Parameters()
    sasa=output_dir/'sasa-configuration.json'
    sasa.write_text(json.dumps(dict(tool='FreeSASA',version=version('freesasa'),
        calculator_implementation_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        algorithm=parameters.algorithm(),probe_radius=parameters.probeRadius(),
        points=parameters.nPoints(),slices=parameters.nSlices(),threads=parameters.nThreads(),
        selection='original atom_sasa nonhetero heavy atoms; default FreeSASA classifier'),indent=2))
    digest=lambda path:sha256(path.read_bytes()).hexdigest()
    if any(not isinstance(pair[1],int) for pair in [*request.core_mapping.residue_pairs,*request.pocket_mapping]):
        raise ValueError('M2_metric_transfer_requires_complete_fusion_sequence_indices')
    scores=result.get('region_mean_plddt',{})
    ligand=result.get('ligand_accessibility') or {}
    return M2StructureMetrics(candidate_id=candidate_id,source_tool='FusionLab original coordinate comparison',
        source_tool_version='Native M2 V2 (source checkout)',artifact_path=str(request.fusion.path),
        artifact_sha256=digest(request.fusion.path),
        prediction_input_sequence_sha256=sha256(request.fusion.expected_sequence.encode()).hexdigest()
            if request.fusion.expected_sequence else None,
        chain_sequence_sha256={request.core_mapping.mobile_chain:sha256(request.fusion.expected_sequence.encode()).hexdigest()}
            if request.fusion.expected_sequence else {},
        reference_structure_id=request.reference.source_reference,
        reference_artifact_path=str(request.reference.path),reference_artifact_sha256=digest(request.reference.path),
        geometry_input_path=str(geometry),geometry_input_sha256=digest(geometry),
        sasa_configuration_path=str(sasa),sasa_configuration_hash=digest(sasa),
        clash_rule_provenance=request.clash_rule_reference,
        pocket_definition_source_ref=request.pocket_definition_reference,
        residue_mapping_source_ref=request.core_mapping.reviewed_reference,
        core_residue_ids=[pair[1] for pair in request.core_mapping.residue_pairs if isinstance(pair[1],int)],
        pocket_residue_ids=[pair[1] for pair in request.pocket_mapping if isinstance(pair[1],int)],
        core_ca_rmsd_angstrom=result['core_ca_rmsd_angstrom'],
        pocket_rmsd_angstrom=result['pocket_ca_rmsd_angstrom'],sasa_retention=result['pocket_sasa_retention'],
        core_mean_plddt=scores.get('core'),
        pocket_mean_plddt=scores.get('pocket'),
        tail_pocket_min_distance_angstrom=result.get('tail_pocket_min_distance_angstrom'),
        ligand_sasa_retention=ligand.get('sasa_retention'),ligand_buried=ligand.get('buried'))


def load_calculation_requests(path: Path):
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("M2_calculations_require_request_list")
    def resolve(model):
        if isinstance(model, BaseModel):
            for key in type(model).model_fields:
                value = getattr(model, key)
                if isinstance(value, Path) and not value.is_absolute():
                    setattr(model, key, (path.parent/value).resolve())
                else:
                    resolve(value)
        elif isinstance(model, (tuple, list)):
            for value in model:
                resolve(value)
    result = []
    for row in rows:
        if set(row) != {"kind", "candidate_id", "payload"} or row["kind"] not in calculation_kinds():
            raise ValueError("M2_calculation_requires_explicit_kind_candidate_and_payload")
        contract, handler = calculation_kinds()[row["kind"]]
        request = contract.model_validate(row["payload"])
        if getattr(request, "candidate_id", row["candidate_id"]) != row["candidate_id"]:
            raise ValueError("M2_calculation_candidate_identity_mismatch")
        resolve(request)
        result.append((row["kind"], row["candidate_id"], request, handler))
    return result


def attach_geometry_metrics(row, *, kind, request, result, candidate_id, artifact):
    """Transfer defined observations only; no Q3 verdict/eta/volume invented.

    Each conditional scenario remains a separate calculation report. Multiple
    scenarios cannot silently select the last one or average their evidence.
    """
    from hashlib import sha256
    from .scoring.m2_structure import M2StructureMetrics
    from .template_geometry import AssemblyExpansionInput
    actual = request.actual_fusion if kind == "assembly_expansion" else request.scaffold
    if isinstance(actual, AssemblyExpansionInput): actual = actual.actual_fusion
    digest = sha256(actual.path.read_bytes()).hexdigest()
    if row is not None and row.artifact_sha256 != digest:
        raise ValueError("M2_geometry_comparison_models_require_explicit_same_conformation")
    row = row or M2StructureMetrics(candidate_id=candidate_id,
        source_tool="FusionLab original template geometry", source_tool_version="Native M2 V2 (source checkout)",
        artifact_path=str(actual.path), artifact_sha256=digest,
        prediction_input_sequence_sha256=sha256(actual.expected_sequence.encode()).hexdigest()
            if actual.expected_sequence else None)
    values = row.model_dump()
    if kind == "assembly_expansion":
        values["interface_contact_count"] = len(result["interface_contacts"])
    elif kind == "recruitment_geometry":
        occupancy = result["cooccupancy"]
        # Nominal counts require the original assembly applicability gate;
        # accessibility/affinity remain distinct. No eta_bind is inferred.
        values.update(s_sh3=occupancy["nominal_sh3_sites"], s_pdz=occupancy["nominal_pdz_sites"],
            site_count_basis="complete_assembly" if result["conflict_graph"]["assembly_applicability_confirmed"] else None,
            m2_geometry_id=sha256(artifact.read_bytes()).hexdigest(),
            joint_occupancy_independent=result["joint_occupancy_independent"] if occupancy["m3_ready"] else None)
    return M2StructureMetrics.model_validate(values)
