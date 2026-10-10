"""Evidence-bound ER adapters over the sole scientific stage execution chain.

The conditional kernels are also available through MCP. This adapter checks
project registry applicability and registered upstream results before use.
It does not reinterpret historical cytosolic concentration fields as amounts.
"""
from hashlib import sha256
import json
from pydantic import BaseModel

from igem_drylab.compartments import ScientificQuantity, evaluate_topology
from igem_drylab.membrane_geometry import calculate_membrane_geometry
from igem_drylab.m3_er import solve_er_recruitment
from igem_drylab.m4_compartments import solve_compartment_network
from .models import M3ConcentrationAssessment, M4ReactionPrediction


def result_identity(result):
    return sha256(json.dumps(result,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()


def quantities(value):
    if isinstance(value,ScientificQuantity):
        yield value
    elif isinstance(value,BaseModel):
        for name in type(value).model_fields:
            yield from quantities(getattr(value,name))
    elif isinstance(value,dict):
        for child in value.values(): yield from quantities(child)
    elif isinstance(value,(list,tuple)):
        for child in value: yield from quantities(child)


def registry_gaps(config, request, *, skip_ids=()):
    """Exact canonical bindings; no global native-assay to fusion transfer.

Entity basis and applicability live in the existing ParameterRecord conditions.
Units/values have already been canonicalized by the input producer. A different
unit is a different binding here, not permission to reinterpret a number.
"""
    records = {r.parameter_id:r for r in config.parameters}
    gaps = []
    if config.execution.analysis_grade == "formal_measured":
        gaps += ["ER_formal_experimental_context:"+key for key in ("host","temperature_c","pH","assay_system")
            if getattr(config.experimental_context,key) is None]
        if not config.execution.require_provenance or config.execution.allow_assumptions:
            gaps.append("ER_formal_requires_provenance_without_assumptions")
    for quantity in quantities(request):
        if quantity.parameter_id in skip_ids: continue
        record = records.get(quantity.parameter_id)
        reason = None
        if record is None:
            reason = "registered_parameter_missing"
        elif record.review_status != "approved" or not record.approved_by:
            reason = "human_parameter_approval_required"
        elif record.construct_id != request.construct_id or record.condition_id != request.condition_id:
            reason = "fusion_construct_or_condition_mismatch"
        elif record.unit != quantity.unit or record.value != quantity.value:
            reason = "canonical_value_or_unit_mismatch"
        elif record.conditions.get("entity_basis") != quantity.entity_basis:
            reason = "entity_basis_mismatch"
        elif not record.source_reference or record.source_reference != quantity.source_reference:
            reason = "source_reference_mismatch"
        elif record.model_version != request.formula_version:
            reason = "method_applicability_not_bound"
        elif record.source_type == "assumption" and not config.execution.allow_assumptions:
            reason = "assumed_physical_parameter_not_allowed"
        elif config.execution.analysis_grade == "formal_measured" and record.source_type in {"assumption","prediction"}:
            reason = "formal_quantification_requires_measured_or_reviewed_transfer_evidence"
        else:
            for key,value in config.experimental_context.model_dump().items():
                if value is not None and record.conditions.get(key) != value:
                    reason = "experimental_context_mismatch:"+key
                    break
        if reason: gaps.append(quantity.parameter_id+":"+reason)
    return sorted(set(gaps))


def topology_review_gaps(config,topology):
    records = {r.parameter_id:r for r in config.parameters}
    expected = {"body_side":topology.body_side,"cleavage_state":topology.cleavage_state,
                "body_retained":"yes" if topology.body_removed_by_cleavage is False else "no"}
    gaps = []
    if topology.evidence_level != "experimentally_supported":
        gaps.append("ER_topology_experimental_support_not_established")
    for key,value in expected.items():
        record = records.get(topology.review_parameter_ids.get(key))
        if (record is None or record.review_status != "approved" or not record.approved_by or
            record.construct_id != topology.construct_id or record.condition_id != topology.condition_id or
            record.value != value or record.source_type != "wetlab" or not record.source_reference or
            record.conditions.get("sequence_sha256") != topology.input_sequence_sha256 or
            record.conditions.get("construct_version") != topology.construct_version):
            gaps.append("ER_topology_review_binding:"+key)
    return gaps


def attach_membrane_geometry(config,candidates,assessments,stage_dir):
    known = {row.construct_id:row for row in candidates}
    for assessment in assessments:
        if assessment.compartment_scenario != "er_anchored": continue
        request = config.stages.m2_fusion.membrane_requests.get(assessment.construct_id)
        if request is None:
            assessment.missing_inputs.append("ER_membrane_ensemble_not_supplied")
            assessment.recommended_for_m3 = False
            assessment.evidence_ready = False
            assessment.status = "insufficient_data"
            continue
        try:
            if request.construct_id != assessment.construct_id:
                raise ValueError("ER_membrane_request_construct_mismatch")
            candidate = known.get(request.topology.construct_id)
            # A design-level membrane request refers to its actual scaffold ORF.
            if candidate is None:
                design = next((d for d in config.inputs.designs if d.id == assessment.construct_id),None)
                candidate = next((known[i] for i in design.protein_construct_ids
                    if known[i].compartment_scenario == "er_anchored"),None) if design else None
            if candidate is None or candidate.full_sequence_sha256 != request.topology.input_sequence_sha256:
                raise ValueError("ER_membrane_topology_not_registered_M1_sequence")
            sequence = (candidate.sequence_qc or {}).get("full_protein_sequence")
            if not sequence: raise ValueError("ER_registered_full_sequence_missing")
            topology = evaluate_topology(request.topology,sequence)
            for conformer in request.conformers:
                if conformer.structure.source_kind == "prediction" and sha256(conformer.structure.expected_sequence.encode()).hexdigest() != candidate.full_sequence_sha256:
                    raise ValueError("ER_membrane_prediction_not_registered_full_construct")
                for name,identity in conformer.site_identities.items():
                    definition = next((d for d in config.inputs.constructs if d.id == identity.enzyme_construct_id),None)
                    enzyme_candidate = known.get(identity.enzyme_construct_id)
                    if (name not in conformer.recruited_enzymes or identity.binding_domain not in conformer.domains
                        or definition is None or identity.species not in definition.enzyme_ids
                        or identity.ligand_id not in definition.recruitment_tags
                        or enzyme_candidate is None or enzyme_candidate.full_sequence_sha256 != identity.enzyme_fusion_sequence_sha256):
                        raise ValueError('ER_M2_site_identity_not_bound_to_registered_enzyme_fusion_and_domain:'+name)
            report = calculate_membrane_geometry(request)
            report["topology_report"] = topology
            report["subunit_composition"] = request.subunit_composition
            report["assembly_applicability_source"] = request.assembly_applicability_source
            report["input_identity"] = result_identity(request.model_dump(mode="json"))
            assessment.membrane_geometry_report = report
            assessment.membrane_geometry_sha256 = result_identity(report)
            stage_dir.mkdir(parents=True,exist_ok=True)
            (stage_dir/(assessment.construct_id+"-membrane.json")).write_text(json.dumps(report,indent=2),encoding="utf-8")
            # Static clashes/confidence are observations, not automatic rejection.
            gaps = list(topology["flags"])
            if config.execution.analysis_grade == "formal_measured":
                gaps += topology_review_gaps(config,request.topology)
            if gaps:
                assessment.missing_inputs = sorted(set(assessment.missing_inputs+gaps))
                assessment.recommended_for_m3 = False
                assessment.evidence_ready = False
                assessment.status = "insufficient_data"
        except (ValueError,OSError) as error:
            assessment.missing_inputs.append(str(error))
            assessment.recommended_for_m3 = False
            assessment.evidence_ready = False
            assessment.status = "invalid_input"


def run_er_m3(config,assessment):
    row = M3ConcentrationAssessment(candidate_id=assessment.candidate_id,construct_id=assessment.construct_id,
        compartment_scenario="er_anchored",status="insufficient_data",claim_scope="conditional_proposed_ER_model")
    request = config.stages.m3_concentration.er_requests.get(assessment.construct_id)
    if request is None:
        row.missing_inputs = ["ER_recruitment_request_not_supplied"]
        return row
    gaps = []
    if not assessment.recommended_for_m3: gaps += assessment.missing_inputs or ["M2_negative_screen_or_membrane_binding_not_ready"]
    geometry = assessment.membrane_geometry_report
    if (geometry is None or not assessment.membrane_geometry_sha256 or
        result_identity(geometry) != assessment.membrane_geometry_sha256 or request.geometry_ref != assessment.membrane_geometry_sha256):
        gaps.append("ER_M3_requires_exact_registered_M2_membrane_result")
    else:
        topology = geometry["topology_report"]
        if (request.body_side != topology["body_side"] or request.topology_evidence_ref != topology["evidence_id"] or
            request.condition_id != topology["condition_id"] or request.construct_id != assessment.construct_id):
            gaps.append("ER_M3_topology_or_condition_mismatch")
        composition = geometry["subunit_composition"]
        if (request.subunits_per_assembly != len(composition) or request.anchors_per_assembly != sum(composition.values()) or
            request.composition_source != geometry["assembly_applicability_source"]):
            gaps.append("ER_M3_assembly_composition_mismatch")
        # A graph is a concrete conformer, not an aggregate of incompatible poses.
        graphs = [{frozenset((edge["first"],edge["second"])) for edge in c["site_conflict_graph"]}
            for c in geometry["conformers"]]
        ids = {site.site_id for site in request.binding_graph.sites}
        placements = [{name for name in c["enzyme_scaffold_clashes"]} for c in geometry["conformers"]]
        supplied = {frozenset(edge) for edge in request.binding_graph.conflict_edges}
        if not any(ids == names and supplied == graph for names,graph in zip(placements,graphs)):
            gaps.append("ER_binding_graph_requires_complete_matching_M2_conformer_site_set_and_edges")
        matched = [c for c,names,graph in zip(geometry['conformers'],placements,graphs)
            if ids == names and supplied == graph and c.get('eligibility') == 'eligible']
        if not matched:
            gaps.append('ER_M3_requires_eligible_matching_M2_conformer_not_conflicted_or_conditional_capacity')
        identities_match = lambda c: all(
            (identity := c.get('site_identities',{}).get(site.site_id)) is not None
            and identity['species'] == site.species and identity['binding_pair_ref'] == site.binding_pair_ref
            for site in request.binding_graph.sites)
        if not any(identities_match(c) for c in matched):
            gaps.append('ER_M3_site_species_or_binding_pair_not_bound_to_registered_M2_enzyme_fusion')
        for site in request.binding_graph.sites:
            record = next((r for r in config.parameters if r.parameter_id == site.kd.parameter_id),None)
            if site.geometry_ref != request.geometry_ref or record is None or record.conditions.get("binding_pair") != site.binding_pair_ref:
                gaps.append("ER_site_binding_pair_or_geometry_mismatch:"+site.site_id)
    gaps += registry_gaps(config,request)
    if gaps:
        row.missing_inputs = sorted(set(gaps)); return row
    result = solve_er_recruitment(request)
    row.compartment_result = result
    row.compartment_result_sha256 = result_identity(result)
    row.formula_version = request.formula_version
    row.parameter_ids = sorted({q.parameter_id for q in quantities(request)} | set(assessment.parameter_ids))
    row.numerically_solved = result["status"] == "numerically_solved"
    row.evidence_ready = row.numerically_solved and config.execution.mode == "real" and config.execution.analysis_grade == "formal_measured"
    row.status = "valid" if row.numerically_solved else "insufficient_data"
    row.recommended_for_m4 = row.numerically_solved
    row.missing_inputs = result["missing"]
    row.data_quality = "mixed"
    row.notes = "ER amounts remain separate from original cytosolic fields; no anchor Kd, avidity or phase volume was invented."
    return row


def run_er_m4(config,assessment,stage_dir):
    request = config.stages.m4_reaction.compartment_requests.get(assessment.construct_id)
    row = M4ReactionPrediction(candidate_id=assessment.candidate_id,construct_id=assessment.construct_id,
        condition_id=request.condition_id if request else (config.stages.m4_reaction.condition_id or "unspecified"),
        target_product=config.stages.m4_reaction.target_product,compartment_scenario="er_anchored",
        status="insufficient_data",claim_scope="conditional_proposed_ER_model")
    if request is None:
        row.missing_inputs = ["ER_amount_network_request_not_supplied"]; return row
    result = assessment.compartment_result
    gaps = []
    if (result is None or not assessment.compartment_result_sha256 or
        result_identity(result) != assessment.compartment_result_sha256 or not assessment.recommended_for_m4):
        row.missing_inputs = ["ER_M4_requires_registered_amount_conserving_M3_result"]; return row
    if (request.scenario != "ER_anchored_LLPS" or request.construct_id != assessment.construct_id or
        request.condition_id != result["condition_id"] or request.topology_evidence_ref != result["topology_evidence_ref"]):
        gaps.append("ER_M4_scenario_topology_or_condition_mismatch")
    pools = {role:[p for p in request.pools if p.role == role] for role in ("cytosol","anchored_droplet")}
    derived_ids = set()
    if any(len(values) != 1 for values in pools.values()):
        gaps.append("ER_M4_requires_one_bound_cytosol_and_one_bound_droplet_pool")
    else:
        for role,values in pools.items():
            pool = values[0]
            if pool.geometry_ref != result["geometry_ref"]: gaps.append("ER_M4_pool_geometry_mismatch:"+role)
            volume = result["cytosol_volume_l"] if role == "cytosol" else result["droplet_volume_l"]
            if pool.volume.value != volume: gaps.append("ER_M4_volume_not_bound_to_M3:"+role)
            for enzyme in ("OC","DMT"):
                enzyme_result = result["enzymes"][enzyme]
                amount = (enzyme_result["free_cytosol_amount_umol"] if role == "cytosol" else
                          enzyme_result["free_droplet_amount_umol"]+enzyme_result["bound_droplet_amount_umol"])
                identity = "m3:"+assessment.compartment_result_sha256+":"+enzyme+":"+role
                quantity = pool.enzyme_amounts[enzyme]
                if quantity.parameter_id != identity or quantity.value != amount or quantity.entity_basis != enzyme+"_total_in_pool":
                    gaps.append("ER_M4_enzyme_amount_not_bound_to_M3:"+enzyme+":"+role)
                else: derived_ids.add(identity)
        for pool in request.pools:
            if pool.role not in pools and any(pool.enzyme_amounts[e].value != 0 for e in ("OC","DMT")):
                gaps.append("ER_M4_OC_DMT_amount_outside_bound_M3_pools")
    gaps += registry_gaps(config,request,skip_ids=derived_ids)
    # Reaction kinetic evidence uses the existing reviewed kcat/Km registry.
    records = {r.parameter_id:r for r in config.parameters}
    for reaction in request.reactions:
        for key,value,unit in (("kcat",reaction.kcat_per_h,"1/h"),("km",reaction.km_um,"uM")):
            selected = [records[i] for i in reaction.parameter_ids if i in records and records[i].parameter_type == key]
            record = selected[0] if len(selected) == 1 else None
            if (record is None or record.review_status != "approved" or not record.approved_by or
                record.value != value or record.unit != unit or record.construct_id != request.construct_id or
                record.condition_id != request.condition_id or record.enzyme_id != reaction.enzyme or
                record.substrate_id != reaction.substrate or record.product_id != reaction.product or
                record.model_version != request.formula_version or not record.source_reference or
                (config.execution.analysis_grade == "formal_measured" and record.source_type in {"prediction","assumption"}) or
                any(value is not None and record.conditions.get(key) != value
                    for key,value in config.experimental_context.model_dump().items())):
                gaps.append("ER_M4_kinetic_applicability:"+reaction.reaction_id+":"+key)
    if gaps:
        row.missing_inputs = sorted(set(gaps)); return row
    result = solve_compartment_network(request)
    row.compartment_result = result
    row.numerically_solved = result["status"] == "numerically_solved"
    row.evidence_ready = row.numerically_solved and assessment.evidence_ready
    row.status = "valid" if row.numerically_solved else "insufficient_data"
    row.missing_inputs = result.get("missing",[])
    row.simulation_inputs = request.model_dump(mode="json")
    row.parameter_ids = sorted({q.parameter_id for q in quantities(request)} |
        {identifier for reaction in request.reactions for identifier in reaction.parameter_ids} | set(assessment.parameter_ids))
    stage_dir.mkdir(parents=True,exist_ok=True)
    row.trajectory_artifact = stage_dir/(assessment.construct_id+"-ER-amounts.json")
    row.trajectory_artifact.write_text(json.dumps(result,indent=2),encoding="utf-8")
    row.notes = "Pool-specific amounts/concentrations and fluxes are in compartment_result; steady-state search is not a global uniqueness proof."
    return row
