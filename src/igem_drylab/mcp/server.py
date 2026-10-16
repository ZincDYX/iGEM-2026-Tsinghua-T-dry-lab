"""Transport-level Model Context Protocol server for the dry-lab tools."""

from __future__ import annotations

from typing import Any, Literal

from mcp.server import MCPServer

from .registry import create_default_registry
from igem_drylab.m4_workflow import M4ReportInput
from igem_drylab.m3_workflow import M3EnsembleInput
from igem_drylab.structural_workflow import M2EnzymeComparisonInput
from igem_drylab.structural_workflow import M2CoreComparisonInput
from igem_drylab.nominal_sequence_descriptors import NominalDescriptorsInput
from igem_drylab.cg_sampling import SamplingInput
from igem_drylab.phase_profile_analysis import PhaseProfileAnalysisInput
from igem_drylab.structure_volume import StructureVolumeInput
from igem_drylab.pocket_preparation import PocketPreparationInput
from igem_drylab.pocket_preparation import PocketPredictionInput
from igem_drylab.pocket_preparation import CofactorTransferInput
from igem_drylab.dssp_context import DsspContextInput
from igem_drylab.dssp_context import LinkerContextReviewInput
from igem_drylab.quantum_calculations import ModelCompoundInput
from igem_drylab.quantum_calculations import RelaxedPESReferenceInput
from igem_drylab.template_geometry import AssemblyPreparationInput
from igem_drylab.template_geometry import AssemblyAccessibilityInput
from igem_drylab.template_geometry import RecruitmentPosePreparationInput
from igem_drylab.template_geometry import AssemblyExpansionInput, RecruitmentGeometryInput, RecruitmentEnsembleInput
from igem_drylab.fusion_tool_import import FusionImportInput
from igem_drylab.fusion_tool_import import FusionBatchObservationInput
from igem_drylab.m1_prioritization import M1PrioritizationInput
from igem_drylab.workflow.m1_checks import M1ConstructContextInput,IDRSubstitutionInput
from igem_drylab.llps_artifacts import LLPSImportInput
from igem_drylab.mpipi import MpipiAnalysisInput
from igem_drylab.membrane_geometry import MembraneGeometryInput
from igem_drylab.m3_er import ERRecruitmentInput
from igem_drylab.m4_compartments import CompartmentNetworkInput, CompartmentComparisonInput

server = MCPServer(
    name="igem-drylab-2026",
    title="iGEM 2026 Tsinghua-T dry-lab scientific tools",
    description="Auditable M1--M4 calculations and explicitly configured scientific tool execution.",
    version="0.1.0",
    instructions=(
        "Formal calculations require provenance-bearing real inputs. Missing scientific evidence must "
        "be returned as blocked or insufficient_data and must never be replaced by guessed values."
    ),
)


@server.tool(name='igem.m2.fit_relaxed_PES_reference',title='Local native QM PES reference with held-out points',structured_output=True)
def m2_fit_relaxed_PES_reference(payload: RelaxedPESReferenceInput) -> dict[str,Any]:
    return _call_local('igem.m2.fit_relaxed_PES_reference',{'payload':payload.model_dump(mode='json')})


@server.tool(name='igem.m1.read_native_fusion_batch',title='Native source-FASTA batch observations',structured_output=True)
def m1_read_native_fusion_batch(payload: FusionBatchObservationInput) -> dict[str,Any]:
    return _call_local('igem.m1.read_native_fusion_batch',{'payload':payload.model_dump(mode='json')})


@server.tool(name='igem.m1.bind_construct_contexts',title='Bind sourced full-fusion contexts',structured_output=True)
def m1_bind_construct_contexts(payload: M1ConstructContextInput) -> dict[str,Any]:
    return _call_local('igem.m1.bind_construct_contexts',{'payload':payload.model_dump(mode='json')})


@server.tool(name='igem.m1.substitute_idrs',title='Authorized fixed-backbone IDR designs',structured_output=True)
def m1_substitute_idrs(payload: IDRSubstitutionInput) -> dict[str,Any]:
    return _call_local('igem.m1.substitute_idrs',{'payload':payload.model_dump(mode='json')})


@server.tool(name='igem.m1.review_linker_context',title='Approved full-fusion linker context review',structured_output=True)
def m1_review_linker_context(payload: LinkerContextReviewInput) -> dict[str,Any]:
    return _call_local('igem.m1.review_linker_context',{'payload':payload.model_dump(mode='json')})


@server.tool(name="igem.m1.parse_mpipi", title="Original Mpipi raw simulation observations", structured_output=True)
def m1_parse_mpipi(payload: MpipiAnalysisInput) -> dict[str, Any]:
    return _call_local("igem.m1.parse_mpipi", {"payload": payload.model_dump(mode="json")})


def _call_local(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    result = create_default_registry().call(name, arguments)
    if result.is_error:
        error = result.structured_content.get("error", {})
        raise ValueError(str(error.get("message", "local tool failed")))
    return result.structured_content


def _present(arguments: dict[str, Any]) -> dict[str, Any]:
    """Omit only absent optional fields; preserve false, zero and empty inputs."""
    return {key: value for key, value in arguments.items() if value is not None}


@server.tool(name="igem.m2.membrane_geometry", title="ER membrane-constrained M2 conformations", structured_output=True)
def m2_membrane_geometry(payload: MembraneGeometryInput) -> dict[str, Any]:
    return _call_local("igem.m2.membrane_geometry", {"payload":payload.model_dump(mode="json")})


@server.tool(name="igem.m3.er_recruitment", title="Versioned ER graph recruitment and amount conservation", structured_output=True)
def m3_er_recruitment(payload: ERRecruitmentInput) -> dict[str, Any]:
    return _call_local("igem.m3.er_recruitment", {"payload":payload.model_dump(mode="json")})


@server.tool(name="igem.m4.compartment_amounts", title="Amount-based compartment network and exchange", structured_output=True)
def m4_compartment_amounts(payload: CompartmentNetworkInput) -> dict[str, Any]:
    return _call_local("igem.m4.compartment_amounts", {"payload":payload.model_dump(mode="json")})


@server.tool(name="igem.m4.compare_compartments", title="Matched physical no-LLPS / cytosolic / ER controls", structured_output=True)
def m4_compare_compartments(payload: CompartmentComparisonInput) -> dict[str, Any]:
    return _call_local("igem.m4.compare_compartments", {"payload":payload.model_dump(mode="json")})


@server.tool(name="igem.m4.report", title="Original M4 three-scenario F1/F2/F3 report", structured_output=True)
def m4_report(payload: M4ReportInput) -> dict[str, Any]:
    return _call_local("igem.m4.report", {"payload": payload.model_dump(mode="json")})


@server.tool(name="igem.m3.ensemble", title="Propagate original M3 parameter uncertainty", structured_output=True)
def m3_ensemble(payload: M3EnsembleInput) -> dict[str, Any]:
    return _call_local("igem.m3.ensemble", {"payload": payload.model_dump(mode="json")})


@server.tool(name="igem.m2.compare_enzyme", title="Original M2 Q1/Q2 reference comparisons", structured_output=True)
def m2_compare_enzyme(payload: M2EnzymeComparisonInput) -> dict[str, Any]:
    return _call_local("igem.m2.compare_enzyme", {"payload": payload.model_dump(mode="json")})


@server.tool(name="igem.m2.prepare_pocket", title="Pocket contacts from a sourced ligand pose", structured_output=True)
def m2_prepare_pocket(payload: PocketPreparationInput) -> dict[str, Any]:
    return _call_local("igem.m2.prepare_pocket", {"payload": payload.model_dump(mode="json")})


@server.tool(name='igem.m2.read_pocket_candidates',structured_output=True,
             description='Read bound original P2Rank predictions; never approve a catalytic pocket from its rank.')
def m2_read_pocket_candidates(payload: PocketPredictionInput) -> dict[str,Any]:
    return _call_local('igem.m2.read_pocket_candidates',{'payload':payload.model_dump(mode='json')})


@server.tool(name='igem.m2.transfer_cofactor', title='Observed cofactor pose transfer', structured_output=True)
def m2_transfer_cofactor(payload: CofactorTransferInput) -> dict[str,Any]:
    return _call_local('igem.m2.transfer_cofactor', {'payload':payload.model_dump(mode='json')})


@server.tool(name='igem.m2.prepare_qm_compound',title='Explicit model-compound chemical graph',structured_output=True)
def m2_prepare_qm_compound(payload: ModelCompoundInput) -> dict[str,Any]:
    return _call_local('igem.m2.prepare_qm_compound',{'payload':payload.model_dump(mode='json')})


@server.tool(name="igem.m2.secondary_context", title="Native DSSP auxiliary fusion context", structured_output=True)
def m2_secondary_context(payload: DsspContextInput) -> dict[str, Any]:
    return _call_local("igem.m2.secondary_context", {"payload": payload.model_dump(mode="json")})


@server.tool(name="igem.m2.prepare_assembly", title="Actual complete fusion template copies", structured_output=True)
def m2_prepare_assembly(payload: AssemblyPreparationInput) -> dict[str, Any]:
    return _call_local("igem.m2.prepare_assembly", {"payload": payload.model_dump(mode="json")})


@server.tool(name='igem.m2.assembly_accessibility',title='Actual full-assembly region accessibility',structured_output=True)
def m2_assembly_accessibility(payload: AssemblyAccessibilityInput) -> dict[str,Any]:
    return _call_local('igem.m2.assembly_accessibility',{'payload':payload.model_dump(mode='json')})


@server.tool(name="igem.m2.expand_fusion", title="Actual fusion core assembly template expansion", structured_output=True)
def m2_expand_fusion(payload: AssemblyExpansionInput) -> dict[str, Any]:
    return _call_local("igem.m2.expand_fusion", {"payload": payload.model_dump(mode="json")})


@server.tool(name="igem.m2.place_recruitment", title="Template recruitment placement and conflict graph", structured_output=True)
def m2_place_recruitment(payload: RecruitmentGeometryInput) -> dict[str, Any]:
    return _call_local("igem.m2.place_recruitment", {"payload": payload.model_dump(mode="json")})


@server.tool(name="igem.m2.recruitment_ensemble", title="Independent recruitment conformation observations", structured_output=True)
def m2_recruitment_ensemble(payload: RecruitmentEnsembleInput) -> dict[str, Any]:
    return _call_local("igem.m2.recruitment_ensemble", {"payload": payload.model_dump(mode="json")})


@server.tool(name="igem.m1.import_fusion_results",title="Import native full-fusion raw tool results",structured_output=True)
def m1_import_fusion_results(payload: FusionImportInput) -> dict[str,Any]:
    return _call_local("igem.m1.import_fusion_results",{"payload":payload.model_dump(mode="json")})


@server.tool(name="igem.m1.prioritize",title="Reviewed M1 risk and original/descriptive comparison",structured_output=True)
def m1_prioritize(payload: M1PrioritizationInput) -> dict[str,Any]:
    return _call_local("igem.m1.prioritize",{"payload":payload.model_dump(mode="json")})


@server.tool(name="igem.m1.import_llps_results",title="Read native LLPS global scores and profiles",structured_output=True)
def m1_import_llps_results(payload: LLPSImportInput) -> dict[str, Any]:
    return _call_local("igem.m1.import_llps_results", {"payload": payload.model_dump(mode="json")})


@server.tool(name="igem.m2.assess_regions", title="Assess actual full-length model regions", structured_output=True)
def m2_assess_regions(candidate_id: str, sequence: str, confidence_file: str,
                      regions: list[dict[str, Any]], calculate_accessibility: bool = True, tool_input_id: str | None = None) -> dict[str, Any]:
    return _call_local("igem.m2.assess_regions", locals())


@server.tool(
    name="igem.m1.compute_features",
    title="Compute audited M1 V3 sequence features",
    description=(
        "Compute the exact M1 V3 sequence feature equations with a versioned definition file. "
        "The output is not an LLPS probability or functional score."
    ),
    structured_output=True,
)
def m1_compute_features(
    sequence: str,
    feature_definitions_file: str | None = None,
    forbidden_amino_acid_motifs: list[str] | None = None,
) -> dict[str, Any]:
    forbidden_amino_acid_motifs = forbidden_amino_acid_motifs or []
    return _call_local("igem.m1.compute_features", _present(locals()))


@server.tool(
    name="igem.m1.validate_construct_sequence",
    title="Assemble and validate a sequenced construct",
    description="Compare ordered protein parts with the translated coding DNA and scan declared restriction motifs.",
    structured_output=True,
)
def m1_validate_construct_sequence(
    construct_id: str,
    ordered_part_ids: list[str],
    part_sequences: dict[str, str],
    coding_dna: str | None = None,
    forbidden_restriction_sites: dict[str, str] | None = None,
    require_sequence_evidence: bool = True,
) -> dict[str, Any]:
    return _call_local("igem.m1.validate_construct_sequence", _present(locals()))


@server.tool(
    name="igem.m1.compute_protparam",
    title="Compute local ProtParam cross-check",
    description="Calculate molecular weight, theoretical pI, and composition with versioned Biopython ProtParam.",
    structured_output=True,
)
def m1_compute_protparam(sequence: str) -> dict[str, Any]:
    return _call_local("igem.m1.compute_protparam", {"sequence": sequence})


@server.tool(
    name="igem.m1.parse_seg",
    title="Parse real SEG low-complexity output",
    description="Parse one NCBI segmasker FASTA artifact and calculate the low-complexity fraction.",
    structured_output=True,
)
def m1_parse_seg(path: str, tool_version: str, input_sha256: str, expected_length: int) -> dict[str, Any]:
    return _call_local("igem.m1.parse_seg", locals())


@server.tool(
    name="igem.m1.screen_sequence",
    title="Apply M1 V3 negative-screen rules",
    description=(
        "Apply the exact M1 V3 negative-screen policy. Formal mode blocks on missing external "
        "IUPred2A, secondary-structure, and full-fusion evidence rather than imputing it."
    ),
    structured_output=True,
)
def m1_screen_sequence(
    sequence: str,
    sequence_kind: Literal["idr", "enzyme_ligand_linker", "scaffold_linker", "rigid_linker", "full_fusion"],
    localization_context: Literal["cytosolic", "er_anchored"] = "cytosolic",
    feature_definitions_file: str | None = None,
    rules_file: str | None = None,
    forbidden_amino_acid_motifs: list[str] | None = None,
    disorder_evidence: dict[str, Any] | None = None,
    secondary_structure_evidence: dict[str, Any] | None = None,
    seg_evidence: dict[str, Any] | None = None,
    protparam_evidence: dict[str, Any] | None = None,
    fusion_evidence: dict[str, Any] | None = None,
    full_fusion_sha256: str | None = None,
    full_fusion_sequence: str | None = None,
    require_external_evidence: bool = True,
) -> dict[str, Any]:
    forbidden_amino_acid_motifs = forbidden_amino_acid_motifs or []
    return _call_local("igem.m1.screen_sequence", _present(locals()))


@server.tool(
    name="igem.m1.parse_iupred2a",
    title="Parse real IUPred2A output",
    description="Parse a versioned IUPred2A per-residue score file for the declared input sequence hash.",
    structured_output=True,
)
def m1_parse_iupred2a(
    path: str,
    tool_version: str,
    input_sha256: str,
    score_boundary: float = 0.5,
) -> dict[str, Any]:
    return _call_local("igem.m1.parse_iupred2a", locals())


@server.tool(
    name="igem.m1.parse_secondary_structure",
    title="Parse real PSIPRED/JPred output",
    description="Parse a versioned PSIPRED SS2 or JPred state file for the declared input sequence hash.",
    structured_output=True,
)
def m1_parse_secondary_structure(
    path: str,
    tool_name: Literal["PSIPRED", "JPred"],
    tool_version: str,
    input_sha256: str,
    sequence_file: str | None = None,
) -> dict[str, Any]:
    return _call_local("igem.m1.parse_secondary_structure", _present(locals()))


@server.tool(
    name="igem.m2.calculate_geometry",
    title="Calculate M2 V2 C-alpha geometry",
    description=(
        "Kabsch-align declared core C-alpha atoms and calculate core/pocket C-alpha RMSD, optional "
        "tail distance, and explicit inter-module heavy-atom clashes."
    ),
    structured_output=True,
)
def m2_calculate_geometry(
    reference_pdb: str,
    model_pdb: str,
    reference_chain: str,
    model_chain: str,
    core_residues: list[int | str],
    pocket_residues: list[int | str],
    core_residue_mapping: list[dict[str, int | str]] | None = None,
    pocket_residue_mapping: list[dict[str, int | str]] | None = None,
    tail_residues: list[int | str] | None = None,
    first_module_chain: str | None = None,
    first_module_residues: list[int | str] | None = None,
    second_module_chain: str | None = None,
    second_module_residues: list[int | str] | None = None,
    clash_cutoff_angstrom: float | None = None,
    reference_model_id: int | None = None,
    model_id: int | None = None,
    reference_altloc: str | None = None,
    model_altloc: str | None = None,
) -> dict[str, Any]:
    return _call_local("igem.m2.calculate_geometry", _present(locals()))


@server.tool(
    name="igem.m2.screen_structure",
    title="Apply M2 V2 confidence-gated negative screen",
    description=(
        "Apply the explicit 0.70 pocket-SASA and 4 A core-C-alpha-RMSD rules after pLDDT gating. "
        "No composite structure score is generated."
    ),
    structured_output=True,
)
def m2_screen_structure(metrics: dict[str, Any]) -> dict[str, Any]:
    return _call_local("igem.scoring.m2_structure", metrics)


@server.tool(
    name="igem.m2.site_cooccupancy",
    title="Solve species-specific M2 co-occupancy",
    description=(
        "Solve an explicit OC/DMT clash graph and return species-specific feasible ranges and Pareto "
        "combinations without inventing one shared eta."
    ),
    structured_output=True,
)
def m2_site_cooccupancy(graph: dict[str, Any]) -> dict[str, Any]:
    return _call_local("igem.m2.site_cooccupancy", graph)


@server.tool(
    name="igem.m2.pocket_sasa",
    title="Calculate same-residue FreeSASA retention",
    description="Compare declared pocket residues and apply the M2 V2 0.70 retention boundary.",
    structured_output=True,
)
def m2_pocket_sasa(
    chain: str,
    residues: list[int | str],
    model_json: str | None = None,
    reference_json: str | None = None,
    model_pdb: str | None = None,
    reference_pdb: str | None = None,
    threshold_loss_fraction: float = 0.30,
    model_configuration_hash: str | None = None,
    reference_configuration_hash: str | None = None,
    reference_model_id: int | None = None,
    model_id: int | None = None,
    reference_altloc: str | None = None,
    model_altloc: str | None = None,
    residue_mapping: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return _call_local("igem.scoring.pocket_sasa", _present(locals()))


@server.tool(
    name="igem.m2.parse_structure_prediction",
    title="Parse real structure-prediction artifacts",
    description="Parse version-specific ColabFold/AF3/ABCFold/Boltz/Chai confidence artifacts without inventing missing metrics.",
    structured_output=True,
)
def m2_parse_structure_prediction(path: str, candidate_id: str | None = None, model_rank: int = 1) -> dict[str, Any]:
    return _call_local("igem.parsers.structure_prediction", _present(locals()))


@server.tool(
    name="igem.m2.compare_docking",
    title="Compare same-ligand M2 docking runs",
    description=(
        "Calculate fusion minus reference Vina score only when configuration and ligand hashes match. "
        "The result is not Kd, kcat, activity, an activity multiplier, or a standalone reject rule."
    ),
    structured_output=True,
)
def m2_compare_docking(
    candidate_id: str,
    reference_vina_output: str,
    fusion_vina_output: str,
    reference_configuration_hash: str,
    fusion_configuration_hash: str,
    reference_ligand_hash: str,
    fusion_ligand_hash: str,
) -> dict[str, Any]:
    return _call_local("igem.scoring.docking_penalty", locals())


@server.tool(
    name="igem.m3.solve_equilibrium",
    title="Solve M3 S1-S5 and E1-E10 equilibrium",
    description=(
        "Solve the documented two-phase OC/DMT free-plus-bound mass balances. Capacity conflicts are "
        "reported without the non-conserving proportional rescaling from the draft."
    ),
    structured_output=True,
)
def m3_solve_equilibrium(inputs: dict[str, Any]) -> dict[str, Any]:
    return _call_local("igem.m3.solve_equilibrium", inputs)


@server.tool(
    name="igem.m4.solve_steady_state",
    title="Solve documented M4 ten-reaction steady state",
    description=(
        "Solve the original eight steady-state balances. Requires explicit V_in and k_sec for compounds "
        "8-15 and blocks nonzero M15 steady state without an M15 outlet."
    ),
    structured_output=True,
)
def m4_solve_steady_state(inputs: dict[str, Any]) -> dict[str, Any]:
    return _call_local("igem.m4.solve_steady_state", inputs)


@server.tool(
    name="igem.m4.analyze_steady_state",
    title="Analyze M4 local stability and declared multistart roots",
    description="Original-RHS analytic Jacobian/eigenvalues and finite declared initial-guess search; no global uniqueness claim.",
    structured_output=True,
)
def m4_analyze_steady_state(inputs: dict[str, Any]) -> dict[str, Any]:
    return _call_local("igem.m4.analyze_steady_state", inputs)


@server.tool(
    name="igem.compute.check_tool",
    title="Check an explicitly configured scientific executable",
    description="Resolve the configured command and report whether its real executable is available.",
    structured_output=True,
)
def check_external_tool(config_path: str, tool_name: str) -> dict[str, Any]:
    return _call_local("igem.compute.check_tool", locals())


@server.tool(
    name="igem.compute.audit_deployment",
    title="Audit external-tool disk budget",
    description="Measure unique deployment roots and report whether they fit within the declared byte budget.",
    structured_output=True,
)
def audit_external_tool_deployment(config_path: str, budget_bytes: int | None = 15_000_000_000) -> dict[str, Any]:
    return _call_local("igem.compute.audit_deployment", locals())


@server.tool(
    name="igem.compute.run_tool",
    title="Run an explicitly configured scientific executable",
    description=(
        "Execute the configured external command without a shell, persist its manifest, and return "
        "missing_executable/failed rather than substituting mock scientific output."
    ),
    structured_output=True,
)
def run_external_tool(
    config_path: str,
    tool_name: str,
    output_dir: str,
    context: dict[str, Any],
    timeout_seconds: int = 3600,
    dry_run: bool = False,
) -> dict[str, Any]:
    return _call_local("igem.compute.run_tool", locals())


@server.tool(name="igem.m4.analyze_prediction", structured_output=True,
             description="Original finite differences and evidence-declared LHS/Spearman; no invented ranges.")
def m4_analyze_prediction(prediction_contract: dict[str, Any], analysis_config: dict[str, Any]) -> dict[str, Any]:
    return _call_local("igem.m4.analyze_prediction", locals())


@server.tool(name="igem.design.scan_scaffolds", structured_output=True,
             description="Finite candidate scan reruns M1-M4 per explicit project; retains failed designs.")
def design_scan_scaffolds(design_plan: dict[str, Any], output_dir: str) -> dict[str, Any]:
    return _call_local("igem.design.scan_scaffolds", locals())


@server.tool(name="igem.research.freeze_prediction", structured_output=True,
             description="Freeze source, solver, parameter and calibration bytes; not a validation claim.")
def research_freeze_prediction(prediction_file: str, parameter_file: str, calibration_datasets: dict[str,str],
                               freeze_id: str, construct_id: str, condition_id: str, claim_scope: str) -> dict[str,Any]:
    return _call_local("igem.research.freeze_prediction", locals())


@server.tool(name="igem.research.validate_holdout", structured_output=True,
             description="Evaluate only held-out data against frozen predictions, without fitting or changing parameters.")
def research_validate_holdout(snapshot: dict[str,Any], dataset_id: str, dataset_file: str) -> dict[str,Any]:
    return _call_local("igem.research.validate_holdout", locals())


@server.tool(name='igem.m1.analyse_phase_profile', structured_output=True,
             description='Declared native bin edges, units and phase/time windows; no automatic phase guesses or LLPS score.')
def m1_analyse_phase_profile(payload: PhaseProfileAnalysisInput) -> dict[str,Any]:
    return _call_local('igem.m1.analyse_phase_profile',{'payload':payload.model_dump(mode='json')})


@server.tool(name='igem.m1.nominal_descriptors', structured_output=True,
             description='Native localCIDER 0.1.21 kappa plus explicit KR/DE SCD; FUS Tyr density is not effective recruitment valence.')
def m1_nominal_descriptors(payload: NominalDescriptorsInput) -> dict[str,Any]:
    return _call_local('igem.m1.nominal_descriptors',{'payload':payload.model_dump(mode='json')})


@server.tool(name='igem.m1.assess_cg_sampling',structured_output=True,
             description='Native-trace independent-seed autocorrelation/precision/drift diagnostics; never a formal LLPS or M1 pass.')
def m1_cg_sampling(payload: SamplingInput) -> dict[str,Any]:
    return _call_local('igem.m1.assess_cg_sampling',{'payload':payload.model_dump(mode='json')})


@server.tool(name='igem.m2.compare_core', structured_output=True,
             description='Compare explicitly frozen apo cores; no guessed pocket or formal Q1 pass.')
def m2_compare_core(payload: M2CoreComparisonInput) -> dict[str,Any]:
    return _call_local('igem.m2.compare_core',{'payload':payload.model_dump(mode='json')})


@server.tool(name='igem.m2.structure_volume',structured_output=True,
             description='Explicit radii/probe sphere unions with refinement; never hull-as-protein or automatic M3 volume.')
def m2_structure_volume(payload: StructureVolumeInput) -> dict[str,Any]:
    return _call_local('igem.m2.structure_volume',{'payload':payload.model_dump(mode='json')})


@server.tool(name='igem.m2.prepare_recruitment_poses', structured_output=True,
             description='Sourced rigid pose preparation; no anchors substituted for a complete catalytic pocket.')
def m2_prepare_recruitment_poses(payload: RecruitmentPosePreparationInput) -> dict[str,Any]:
    return _call_local('igem.m2.prepare_recruitment_poses', {'payload': payload.model_dump(mode='json')})


def main() -> None:
    """Run the production MCP server over stdio."""

    server.run(transport="stdio")


if __name__ == "__main__":
    main()
