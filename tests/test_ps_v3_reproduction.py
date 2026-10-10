"""Real kernels on an explicitly provided corrected package; compute-server only.

No substitute fixture is made if the package is absent. Endpoint oracles are
the independently generated values printed in the 20261011 review section 12.
This tests synthetic software reproducibility, never experimental validity.
"""
from copy import deepcopy
import os
from pathlib import Path
import pytest
from igem_drylab.workflow.synthetic_ps import read_ps_archive,build_case
from igem_drylab.m4_compartments import solve_compartment_network


@pytest.fixture(scope='module')
def corrected_package():
    name=os.environ.get('FUSIONLAB_PS_V3_PACKAGE')
    if not name:
        pytest.skip('Corrected external PS-v3 package not provided; real reproduction not verified.')
    return read_ps_archive(Path(name).read_bytes())


def test_actual_kernel_endpoints_match_independent_corrected_package(corrected_package):
    canonical,templates=corrected_package
    expected={'C1':2380.938864,'C2':2937.500000,'E1':2838.277623,'E2':2937.500000}
    for case,template in templates.items():
        _,m3,payload=build_case(canonical,template,case)
        result=solve_compartment_network(payload)
        assert result['status']=='numerically_solved'
        assert sum(p['amounts_umol']['15'][-1] for p in result['pools'].values())==pytest.approx(expected[case],abs=2e-6,rel=0)
        if m3:
            for enzyme in ('oc','dmt'):
                record=m3[enzyme]
                recovered=canonical['phi_LLPS']*record['total_dense_um']+(1-canonical['phi_LLPS'])*record['free_dilute_um']
                assert recovered==pytest.approx(payload.pools[0].enzyme_amounts[enzyme.upper()].value+payload.pools[1].enzyme_amounts[enzyme.upper()].value,abs=1e-10)


def test_only_canonical_changes_regenerate_inputs_and_real_trajectory(corrected_package):
    canonical,templates=corrected_package
    changed=deepcopy(canonical)
    changed['kinetics']['R3']['kcat_per_h']*=.5
    _,_,first=build_case(canonical,templates['C1'],'C1')
    _,_,second=build_case(changed,templates['C1'],'C1')
    assert second.reactions[0].kcat_per_h==first.reactions[0].kcat_per_h
    r3_first=next(r for r in first.reactions if r.reaction_id=='R3')
    r3_second=next(r for r in second.reactions if r.reaction_id=='R3')
    assert r3_second.kcat_per_h==.5*r3_first.kcat_per_h
    original=solve_compartment_network(first)
    regenerated=solve_compartment_network(second)
    assert regenerated['status']=='numerically_solved'
    assert regenerated['pools']['dilute']['amounts_umol']['15'][-1]<original['pools']['dilute']['amounts_umol']['15'][-1]
    assert templates['C1']['m4']['reactions'][2]['kcat_per_h']==r3_first.kcat_per_h
