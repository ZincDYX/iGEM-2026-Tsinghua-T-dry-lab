"""Server-only synthetic closure probes, never project biological evidence."""
from copy import deepcopy
import pytest

from igem_drylab.pipeline.config import ProjectConfig
from igem_drylab.pipeline.models import M1Candidate,M2FusionAssessment
from igem_drylab.pipeline.er_stages import attach_membrane_geometry,quantities
from igem_drylab.pipeline.stages import run_m3,run_m4
from igem_drylab.membrane_geometry import MembraneGeometryInput
from igem_drylab.m3_er import ERRecruitmentInput,BindingGraph,BindingSite
from igem_drylab.compartments import ScientificQuantity
from igem_drylab.parameters import ParameterRecord
from test_r19_membrane_geometry import membrane
from test_r19_er_equations import recruitment,network


def register_quantities(project,request,skip=()):
    # Distinct source identities for distinct fixture quantities/versions.
    for q in quantities(request):
        if q.parameter_id in skip: continue
        q.parameter_id = "synthetic-"+str(len(project.parameters))
        q.source_reference = "SYNTHETIC MATHEMATICAL TEST ONLY; NOT MEASURED DATA"
        project.parameters.append(ParameterRecord(parameter_id=q.parameter_id,name=q.parameter_id,value=q.value,unit=q.unit,
            source_type="assumption",review_status="approved",approved_by="test fixture only",
            construct_id=request.construct_id,condition_id=request.condition_id,source_reference=q.source_reference,
            model_version=request.formula_version,conditions={"entity_basis":q.entity_basis}))


def prepared(tmp_path):
    raw = membrane(tmp_path)
    # The general geometry fixture deliberately places its pocket in the slab.
    # This closure fixture uses a separate accessible pose, not a relaxed gate.
    pdb = raw['conformers'][0]['structure']['path']
    pdb.write_text(pdb.read_text().replace('   8.000   0.000   0.000','   8.000   0.000  12.000'))
    raw['conformers'][0]['site_identities'] = {'enzyme':dict(species='OC',enzyme_construct_id='fixture',
        enzyme_fusion_sequence_sha256=raw['topology']['input_sequence_sha256'],ligand_id='synthetic-ligand',
        binding_domain='SH3',binding_pair_ref='synthetic-pair',source_reference='SYNTHETIC TEST ONLY')}
    request = MembraneGeometryInput.model_validate(raw)
    source = tmp_path/"synthetic.fasta";source.write_text(">fixture\nAAAAAAAA\n")
    project = ProjectConfig.model_validate(dict(run={"id":"synthetic-binding"},execution={"analysis_grade":"mechanistic_sensitivity","allow_assumptions":True},
        inputs=dict(protein_fasta=source,enzymes=[dict(id='OC',protein_id='fixture',reaction_role='synthetic')],scaffolds=[],linkers=[],
            constructs=[dict(id="fixture",components=["fixture"],localization_context="er_anchored",enzyme_ids=['OC'],recruitment_tags=['synthetic-ligand'])]),
        stages={"m2_fusion":{"membrane_requests":{"fixture":request.model_dump()}}}))
    candidate = M1Candidate(candidate_id="fixture",construct_id="fixture",construct_definition={},compartment_scenario="er_anchored",
        full_sequence_sha256=request.topology.input_sequence_sha256,sequence_qc={"full_protein_sequence":"AAAAAAAA"})
    m2 = M2FusionAssessment(candidate_id="fixture",construct_id="fixture",construct_definition={},compartment_scenario="er_anchored",recommended_for_m3=True)
    attach_membrane_geometry(project,[candidate],[m2],tmp_path/"m2")
    assert m2.recommended_for_m3 and m2.membrane_geometry_report
    m3 = recruitment().model_copy(deep=True)
    m3.construct_id=m3.condition_id="fixture"
    m3.geometry_ref=m2.membrane_geometry_sha256
    m3.topology_evidence_ref=request.topology.evidence_id
    m3.composition_source=request.assembly_applicability_source
    kd = m3.binding_graph.sites[0].kd.model_copy(deep=True)
    m3.binding_graph=BindingGraph(sites=[BindingSite(site_id="enzyme",species="OC",kd=kd,geometry_ref=m3.geometry_ref,binding_pair_ref="synthetic-pair")],
        conflict_edges=[],entity_basis="complete_assembly",geometry_ref=m3.geometry_ref,
        method_assumption="hard_exclusion_no_additional_cooperativity",applicability_reference="synthetic")
    register_quantities(project,m3)
    next(r for r in project.parameters if r.parameter_id==kd.parameter_id).conditions["binding_pair"]="synthetic-pair"
    project.stages.m3_concentration.er_requests["fixture"]=m3
    return project,m2


def test_er_m2_m3_m4_chain_uses_actual_upstream_amounts_and_never_original_concentration_fields(tmp_path):
    project,m2=prepared(tmp_path)
    m3rows,_=run_m3(project,tmp_path,[m2]);m3=m3rows[0]
    assert m3.status=="valid" and m3.numerically_solved
    assert m3.concentrations=={} and m3.m4_candidate_context is None and not m3.evidence_ready
    assert m3.compartment_result["enzymes"]["DMT"]["bound_droplet_amount_umol"]==0
    request=network().model_copy(deep=True)
    request.construct_id=request.condition_id="fixture";request.scenario="ER_anchored_LLPS"
    request.topology_evidence_ref=m3.compartment_result["topology_evidence_ref"]
    derived=[]
    for pool in request.pools:
        pool.geometry_ref=m3.compartment_result["geometry_ref"]
        for enzyme in ("OC","DMT"):
            result=m3.compartment_result["enzymes"][enzyme]
            amount=result["free_cytosol_amount_umol"] if pool.role=="cytosol" else result["free_droplet_amount_umol"]+result["bound_droplet_amount_umol"]
            identity="m3:"+m3.compartment_result_sha256+":"+enzyme+":"+pool.role
            pool.enzyme_amounts[enzyme]=ScientificQuantity(value=amount,unit="umol",entity_basis=enzyme+"_total_in_pool",parameter_id=identity,source_reference="synthetic registered M3 result")
            derived.append(identity)
    register_quantities(project,request,derived)
    for reaction in request.reactions:
        reaction.parameter_ids=[]
        for kind,value,unit in (("kcat",reaction.kcat_per_h,"1/h"),("km",reaction.km_um,"uM")):
            identity="synthetic-"+reaction.reaction_id+"-"+kind
            project.parameters.append(ParameterRecord(parameter_id=identity,name=identity,value=value,unit=unit,parameter_type=kind,
                source_type="assumption",review_status="approved",approved_by="synthetic fixture",source_reference="SYNTHETIC KINETIC ORACLE, NOT PROJECT DATA",
                construct_id="fixture",condition_id="fixture",enzyme_id=reaction.enzyme,substrate_id=reaction.substrate,product_id=reaction.product,model_version=request.formula_version))
            reaction.parameter_ids.append(identity)
    project.stages.m4_reaction.compartment_requests["fixture"]=request
    rows,_=run_m4(project,tmp_path,[m3])
    assert rows[0].status=="valid" and rows[0].numerically_solved and not rows[0].evidence_ready
    assert rows[0].compartment_result["max_mass_conservation_residual_umol"] < 1e-8
    assert rows[0].candidate_context is None and rows[0].final_15 is None
    assert set(m3.parameter_ids) <= set(rows[0].parameter_ids)
    assert {identifier for reaction in request.reactions for identifier in reaction.parameter_ids} <= set(rows[0].parameter_ids)
    # A changed abundance must not pass merely because it carries the same source ID.
    request.pools[0].enzyme_amounts["OC"].value += .1
    rows,_=run_m4(project,tmp_path,[m3])
    assert rows[0].status=="insufficient_data"
    assert "ER_M4_enzyme_amount_not_bound_to_M3:OC:cytosol" in rows[0].missing_inputs


@pytest.mark.parametrize("mutation,expected",[
    ("condition","fusion_construct_or_condition_mismatch"),
    ("unit","canonical_value_or_unit_mismatch"),
    ("basis","entity_basis_mismatch"),
    ("method","method_applicability_not_bound"),
    ("approval","human_parameter_approval_required"),
    ("graph","ER_binding_graph_requires_complete_matching_M2_conformer_site_set_and_edges"),
    ("geometry","ER_M3_requires_exact_registered_M2_membrane_result"),
])
def test_er_parameter_scope_and_geometry_changes_cannot_be_promoted(tmp_path,mutation,expected):
    project,m2=prepared(tmp_path)
    parameter=project.parameters[0]
    if mutation=="condition":parameter.condition_id="other-condition"
    elif mutation=="unit":parameter.unit="uM"
    elif mutation=="basis":parameter.conditions["entity_basis"]="native enzyme rather than fusion"
    elif mutation=="method":parameter.model_version="old-cytosolic"
    elif mutation=="approval":parameter.review_status="extracted"
    elif mutation=="graph":project.stages.m3_concentration.er_requests["fixture"].binding_graph.sites=[]
    elif mutation=="geometry":m2.membrane_geometry_report["anchor_count"]=24
    rows,_=run_m3(project,tmp_path,[m2])
    assert rows[0].status=="insufficient_data" and not rows[0].numerically_solved
    assert any(expected in gap for gap in rows[0].missing_inputs)


def test_unreviewed_topology_label_does_not_unlock_formal_er(tmp_path):
    project,m2=prepared(tmp_path)
    project.execution.analysis_grade="formal_measured"
    request=project.stages.m2_fusion.membrane_requests["fixture"]
    request.topology.evidence_level="experimentally_supported"
    candidate=M1Candidate(candidate_id="fixture",construct_id="fixture",construct_definition={},full_sequence_sha256=request.topology.input_sequence_sha256,sequence_qc={"full_protein_sequence":"AAAAAAAA"})
    attach_membrane_geometry(project,[candidate],[m2],tmp_path/"formal-m2")
    assert not m2.recommended_for_m3
    assert "ER_topology_review_binding:body_side" in m2.missing_inputs
