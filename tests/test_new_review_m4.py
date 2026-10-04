"""N03/N04 numerical algorithm fixtures, never biological parameters."""
from dataclasses import replace

import numpy as np
import pytest

from igem_drylab.full_network import COMPOUNDS,ENZYME_SUBSTRATES,REACTIONS,FullNetworkParameters,PhaseDistribution,ReactionKinetics,TransportParameters,TemporalGate,simulate_full_network
from igem_drylab.kinetics import InductionGate
from igem_drylab.m4_steady_state import M4SteadyStateInput,solve_m4_steady_state


def single_reaction():
    return FullNetworkParameters(phi=0,enzyme_distributions={e:PhaseDistribution(0,1 if e=='DMT' else 0) for e in ENZYME_SUBSTRATES},
        metabolite_kp={c:1 for c in COMPOUNDS},reactions=tuple(ReactionKinetics(*row,kcat=1000 if row[0]=='R5' else 0,km=1) for row in REACTIONS),scenario='homogeneous_constitutive')


def test_adaptive_integral_independent_of_display_density():
    results=[simulate_full_network(single_reaction(),initial_intracellular={c:float(c=='9') for c in COMPOUNDS},t_end=1,points=n) for n in (2,501,5001)]
    for result in results:
        assert result.flux_integrals['R5']==pytest.approx(result.diagnostics['net_13_generated_cell_volume_equivalent'],abs=1e-9)
        assert result.flux_integrals['R5']==pytest.approx(1,abs=1e-7)
        assert result.diagnostics['integrated_stoichiometry_max_abs_error']<1e-9
    assert np.ptp([r.flux_integrals['R5'] for r in results])<1e-9


def test_step_boundary_has_no_trapezoid_pulse():
    gate=TemporalGate(mode='configured_induction',induction=InductionGate(mode='step',on_time=.5,off_time=.75))
    params=replace(single_reaction(),dmt_gate=gate,scenario='homogeneous_published_like_temporal')
    for points in (2,501):
        result=simulate_full_network(params,initial_intracellular={c:float(c=='9') for c in COMPOUNDS},t_end=1,points=points)
        assert result.flux_integrals['R5']==pytest.approx(1,abs=1e-7)
        assert result.flux_integrals['R5']==pytest.approx(result.intracellular[5,-1],abs=1e-9)


@pytest.mark.parametrize('method',['LSODA','BDF','Radau'])
def test_supported_solvers_agree_on_integrated_reaction(method):
    result=simulate_full_network(single_reaction(),initial_intracellular={c:float(c=='9') for c in COMPOUNDS},
                                 t_end=.01,points=2,method=method,rtol=1e-10,atol=1e-13)
    # Single MM fixture: S0=Km=1, Vmax=1000, t=.01 => S+ln(S)=-9.
    # Consumption is 1-W(exp(-9)), not a fitted/golden production output.
    from scipy.special import lambertw
    from math import exp
    assert result.flux_integrals['R5']==pytest.approx(1-float(lambertw(exp(-9)).real),rel=0.,abs=2e-9)
    assert result.solver_settings['method']==method


def test_gross_transport_is_distinct_from_net_accumulation():
    params=single_reaction()
    params=replace(params,reactions=tuple(replace(r,kcat=0) for r in params.reactions),
                   transport=TransportParameters(enabled=True,access='cell_average',rate=2,
                   outside_over_inside={c:1 for c in COMPOUNDS},intracellular_volume_l=1,extracellular_volume_l=3))
    result=simulate_full_network(params,initial_intracellular={c:float(c=='9') for c in COMPOUNDS},t_end=2,points=2)
    transport=result.transport_integrals['9']
    assert transport['total_outflow_cell_volume_equivalent']>transport['net_outflow_cell_volume_equivalent']
    assert transport['total_inflow_cell_volume_equivalent']>0
    assert transport['net_outflow_cell_volume_equivalent']==pytest.approx(3*result.extracellular[1,-1],abs=1e-9)
    assert result.diagnostics['mass_balance_error']<1e-9


def steady_fixture(scale=1.,drain_8=True):
    return M4SteadyStateInput(candidate_id='software-fixture',construct_id='fixture',condition_id='fixture',phi=0,
        enzymes={e:dict(dense_um=0,dilute_um=0,m3_source_id='software-fixture') for e in ENZYME_SUBSTRATES},
        metabolite_kp={c:1 for c in COMPOUNDS},reactions=[dict(reaction_id=a,enzyme=b,substrate=c,product=d,
          kcat_per_h=0,km_um=1,parameter_ids=['fixture-kcat','fixture-km']) for a,b,c,d in REACTIONS],
        input_flux_um_per_h=scale,secretion_rate_per_h={c:scale if c=='15' or (c=='8' and drain_8) else 0 for c in COMPOUNDS},
        secretion_normalization='original_unweighted_dilute_concentration',initial_guess_um={c:0 for c in COMPOUNDS},input_parameter_ids=['software-fixture'])


def test_no_reachable_outlet_is_blocked_even_for_tiny_positive_input():
    result=solve_m4_steady_state(steady_fixture(1e-12,drain_8=False))
    assert result.status=='blocked' and result.yield_abs is None
    assert any('no_reachable' in w for w in result.warnings)


@pytest.mark.parametrize('scale',[1e-12,1.,1e12])
def test_steady_qualification_is_flux_scale_invariant(scale):
    result=solve_m4_steady_state(steady_fixture(scale))
    assert result.status=='valid'
    assert result.concentrations_cell_average_um['8']==pytest.approx(1,abs=1e-6)
    assert abs(result.mass_invariant_residual)<1e-6
    assert abs(result.input_output_balance_relative_residual)<1e-6
    assert result.max_scaled_species_residual<1e-6
