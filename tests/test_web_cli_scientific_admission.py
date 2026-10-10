"""Independent review counterexamples; execute all numerical tests server-only."""
from copy import deepcopy
from types import SimpleNamespace
import numpy as np
import pytest

from igem_drylab.m4_compartments import CompartmentComparisonInput, solve_compartment_network
from igem_drylab.pipeline.stages import run_m3
from igem_drylab.pipeline.er_stages import attach_membrane_geometry
from igem_drylab.pipeline.models import M1Candidate
from test_r19_er_equations import network, quantity
from test_r19_er_stage_bindings import prepared


def test_species_swap_cannot_reinterpret_registered_oc_site_as_dmt(tmp_path):
    project, m2 = prepared(tmp_path)
    legal,_ = run_m3(project,tmp_path,[m2])
    assert legal[0].numerically_solved
    project.stages.m3_concentration.er_requests['fixture'].binding_graph.sites[0].species = 'DMT'
    changed,_ = run_m3(project,tmp_path,[m2])
    assert not changed[0].numerically_solved and not changed[0].recommended_for_m4
    assert 'ER_M3_site_species_or_binding_pair_not_bound_to_registered_M2_enzyme_fusion' in changed[0].missing_inputs


def test_one_conflicted_pose_does_not_reject_a_different_eligible_pose(tmp_path):
    project,m2 = prepared(tmp_path)
    request = project.stages.m2_fusion.membrane_requests['fixture']
    clash = request.conformers[0].model_copy(deep=True)
    clash.conformer_id = 'slab-conflict'
    source = tmp_path/'conflicted.pdb'
    source.write_text(clash.structure.path.read_text().replace('   8.000   0.000  12.000','   8.000   0.000   0.000'))
    clash.structure.path = source
    request.conformers.append(clash)
    candidate = M1Candidate(candidate_id='fixture',construct_id='fixture',construct_definition={},
        full_sequence_sha256=request.topology.input_sequence_sha256,sequence_qc={'full_protein_sequence':'AAAAAAAA'})
    attach_membrane_geometry(project,[candidate],[m2],tmp_path/'poses')
    assert [c['eligibility'] for c in m2.membrane_geometry_report['conformers']]==['eligible','excluded']
    er = project.stages.m3_concentration.er_requests['fixture']
    er.geometry_ref = m2.membrane_geometry_sha256
    er.binding_graph.geometry_ref = er.geometry_ref
    for site in er.binding_graph.sites: site.geometry_ref = er.geometry_ref
    rows,_ = run_m3(project,tmp_path,[m2])
    assert rows[0].numerically_solved  # The eligible concrete pose remains usable.
    m2.membrane_geometry_report['conformers'] = m2.membrane_geometry_report['conformers'][1:]
    from igem_drylab.pipeline.er_stages import result_identity
    m2.membrane_geometry_sha256 = result_identity(m2.membrane_geometry_report)
    er.geometry_ref=m2.membrane_geometry_sha256
    er.binding_graph.geometry_ref=er.geometry_ref
    for site in er.binding_graph.sites: site.geometry_ref=er.geometry_ref
    rows,_ = run_m3(project,tmp_path,[m2])
    assert not rows[0].numerically_solved
    assert 'ER_M3_requires_eligible_matching_M2_conformer_not_conflicted_or_conditional_capacity' in rows[0].missing_inputs


def test_closed_exchange_root_keeps_initial_three_umol_not_the_zero_root():
    payload = network()
    guess = {p.pool_id:{c:0. for c in payload.initial_amounts_umol[p.pool_id]} for p in payload.pools}
    payload.steady_initial_guesses_umol = [guess]
    result = solve_compartment_network(payload)
    accepted = [c for c in result['steady_state_candidates'] if c['status']=='steady_state_found']
    assert accepted, result['steady_state_candidates']
    # Independently: Va=2, Vb=1, Kb/a=4, total=3 -> amounts (1,2).
    assert accepted[0]['amounts_umol']['a']['8'] == pytest.approx(1,abs=1e-8)
    assert accepted[0]['amounts_umol']['b']['8'] == pytest.approx(2,abs=1e-8)
    assert accepted[0]['initial_compatibility_class_valid']


def test_open_feed_and_sink_are_not_falsely_constrained_to_initial_total():
    payload = network()
    payload.boundaries = []
    raw = payload.model_dump()
    raw['boundaries'] = [dict(boundary_id='feed',pool_id='a',compound='8',kind='constant_feed',
        quantity=quantity(3,'umol/h'),normalization='physical_amount'),
        dict(boundary_id='sink',pool_id='b',compound='8',kind='first_order_loss',
        quantity=quantity(1,'1/h'),normalization='physical_amount')]
    raw['steady_initial_guesses_umol'] = [{p.pool_id:{c:1. for c in raw['initial_amounts_umol'][p.pool_id]} for p in payload.pools}]
    result = solve_compartment_network(type(payload).model_validate(raw))
    root = next(c for c in result['steady_state_candidates'] if c['status']=='steady_state_found')
    # Independently: sink fixes Nb=3; exchange=3 gives Na/2-Nb/4=1 -> Na=3.5.
    assert root['amounts_umol']['a']['8'] == pytest.approx(3.5,abs=1e-7)
    assert root['amounts_umol']['b']['8'] == pytest.approx(3,abs=1e-7)


def comparison_cases():
    cases = {}
    for name in ('no_LLPS','cytosolic_LLPS','ER_anchored_LLPS'):
        case = network().model_copy(deep=True)
        case.scenario = name
        case.topology_evidence_ref = 'SYNTHETIC' if name=='ER_anchored_LLPS' else None
        cases[name] = case
    return dict(cases=cases,matched_enzyme_relative_tolerance=1e-9)


def test_matched_controls_compare_total_initial_amount_not_pool_distribution():
    raw = comparison_cases()
    CompartmentComparisonInput.model_validate(raw)
    changed = raw['cases']['ER_anchored_LLPS'].initial_amounts_umol
    changed['a']['8'].value = 1
    changed['b']['8'].value = 2
    CompartmentComparisonInput.model_validate(raw)  # Same amount, different partition allowed.
    changed['b']['8'].value = 3
    with pytest.raises(ValueError,match='same_initial_total_metabolite_amount'):
        CompartmentComparisonInput.model_validate(raw)


def test_successful_integrator_with_mass_drift_is_not_numerically_admitted(monkeypatch):
    # Inject an integrator defect, not fabricated biological evidence.
    time = np.array([0,.2,1,3])
    values = np.zeros((18,4)); values[0,:] = [3,3,3,4]
    monkeypatch.setattr('scipy.integrate.solve_ivp',lambda *a,**kw: SimpleNamespace(success=True,y=values,t=time))
    result = solve_compartment_network(network())
    assert result['status']=='numerical_admission_failed'
    assert not result['numerical_admission']['conservation_valid']
    assert result['max_mass_conservation_residual_umol']==pytest.approx(1)
    assert result['pools']['a']['amounts_umol']['8'][-1]==4  # Diagnostic not clipped away.
