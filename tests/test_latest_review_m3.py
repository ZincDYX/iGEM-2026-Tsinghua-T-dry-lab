"""Synthetic pipeline wiring checks, no real phase-diagram claims."""
from pathlib import Path

import pytest

from igem_drylab.parameters import ParameterRecord
from igem_drylab.parameters.requirements import requirements_for_stage
from igem_drylab.pipeline import load_config
from igem_drylab.pipeline.config import M3Config
from igem_drylab.pipeline.models import M2FusionAssessment
from igem_drylab.pipeline.stages import run_m3


@pytest.mark.parametrize('mode', ['measured', 'lever_rule', 'compare'])
def test_pipeline_s4_sources_and_target_are_passed(mode, tmp_path):
    config = load_config(Path('configs/m1_m4_example.yaml'))
    config.execution.allow_assumptions = True
    config.stages.m3_concentration = M3Config(phi_source=mode, target_enzyme_ratio_parameter='design_target',
                                            design_decision_id='software-fixture-finite-decision')
    values = dict(phi=.2, ptr_total=1., pt_total=1., oc_total=3., dmt_total=2.,
        partition_ptr=1., partition_pt=1., partition_oc=5., partition_dmt=2.,
        c_dense_scaffold=20., c_total_scaffold=3.8, c_sat_scaffold=2.,
        kd_sh3=2., kd_pdz=4., design_target=2.)
    values.update({f'partition_x{i}': 1. for i in range(8,16)})
    requirements = requirements_for_stage(config, 'm3')
    config.parameters = [ParameterRecord(parameter_id=item.name, name=item.name, value=values[item.name],
        unit=item.canonical_unit, parameter_type=item.parameter_type, enzyme_id=item.enzyme_id,
        species_id=item.species_id, source_type='assumption', source_reference='software fixture only',
        review_status='approved', conditions={'entity_basis':'complete_assembly'}) for item in requirements]
    assessment = M2FusionAssessment(candidate_id='fixture', construct_id='fixture', construct_definition={},
        status='valid', recommended_for_m3=True, s_sh3=3, s_pdz=1, eta_acc_sh3=.8, eta_acc_pdz=.9,
        eta_bind_sh3=.75, eta_bind_pdz=.5, site_count_basis='complete_assembly',
        joint_occupancy_independent=True, m2_geometry_id='fixture-geometry')
    result = run_m3(config, tmp_path, [assessment])[0][0]
    assert result.status == 'valid'
    assert result.phi_source == ('S4_lever_rule' if mode == 'lever_rule' else 'measured_input')
    assert result.m4_candidate_context.phi == pytest.approx(.1 if mode == 'lever_rule' else .2)
    assert result.rho_star_candidates['E8_low_occupancy'] == pytest.approx(2/1.5*2/4)
    if mode == 'compare':
        assert result.phi_measured_minus_s4 == pytest.approx(.1)
    if mode != 'measured':
        assert result.phi_s4_if_available == pytest.approx(.1)
    # Required real inputs are not silently supplied by the config.
    config.parameters = [row for row in config.parameters if row.name !=
                         ('phi' if mode == 'measured' else 'c_sat_scaffold')]
    blocked = run_m3(config, tmp_path/'missing', [assessment])[0][0]
    assert blocked.status == 'insufficient_data'


def test_target_requires_declared_design_decision():
    with pytest.raises(ValueError, match='design_decision'):
        M3Config(target_enzyme_ratio_parameter='target')


def test_formal_phase_diagram_does_not_accept_global_unfused_scaffold_evidence():
    from igem_drylab.parameters import ParameterResolution
    from igem_drylab.pipeline.stages import _m3_formal_source_violations
    requirements = {r.name:r for r in requirements_for_stage(load_config(Path('configs/m1_m4_example.yaml')),'m3')}
    selected = {}
    for name,item in requirements.items():
        record = ParameterRecord(parameter_id=name,name=name,value=.1 if name=='phi' else 1.,
            unit=item.canonical_unit,parameter_type=item.parameter_type,enzyme_id=item.enzyme_id,
            species_id=item.species_id,source_type='wetlab',source_reference='software-fixture',
            construct_id='fusion',condition_id='condition',review_status='approved',
            conditions={'entity_basis':'complete_assembly','binding_pair':'fixture'})
        selected[name] = ParameterResolution(name=name,status='resolved',selected_parameter=record,canonical_value=record.value)
    assert not _m3_formal_source_violations(selected,'complete_assembly')
    selected['c_dense_scaffold'].selected_parameter.construct_id=None
    assert any('fusion construct and condition' in item for item in _m3_formal_source_violations(selected,'complete_assembly'))
