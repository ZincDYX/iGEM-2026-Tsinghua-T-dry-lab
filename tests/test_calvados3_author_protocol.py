"""Protocol contracts only; native CUDA/force acceptance runs separately."""
from dataclasses import asdict
import pytest
from igem_drylab.calvados3_author_runner import AuthorIDRRequest


def declared_request(**changes):
    values = dict(candidate_id='declared_fixture', sequence='GG', author_source='/private/author',
                  author_commit='51564e0edd126c44d6a7299fbe4414c579394ef4', output_dir='/private/new-job',
                  temperature_kelvin=303.15, pH=7.2, ionic_strength_molar=.15, box_edge_nm=10,
                  timestep_ps=.01, friction_per_ps=.01, ah_cutoff_nm=2, dh_cutoff_nm=4, eps_factor=.2,
                  seed=42, equilibration_steps=15000000, production_steps=100000000,
                  save_interval_steps=12500, checkpoint_interval_steps=1000000, gpu_id=0,
                  expected_openmm_version='7.6.0', terminal_state='original_isolated_peptide_free_termini',
                  protocol_reference='Explicit adopted reference protocol; not project measurement')
    values.update(changes)
    return AuthorIDRRequest(**values)


@pytest.mark.data_contract
def test_full_declared_budget_and_original_free_termini_are_not_silent_defaults():
    request = declared_request().validate()
    assert request.equilibration_steps * request.timestep_ps / 1000 == 150
    assert request.production_steps * request.timestep_ps / 1000 == 1000
    assert request.save_interval_steps * request.timestep_ps / 1000 == .125
    assert AuthorIDRRequest(**asdict(request)) == request
    with pytest.raises(ValueError, match='not_internal_fusion'):
        declared_request(terminal_state='internal_fragment').validate()


@pytest.mark.data_contract
@pytest.mark.parametrize('changes', [dict(sequence='G'), dict(sequence='GX'), dict(seed=True),
                                   dict(production_steps=0), dict(equilibration_steps=-1),
                                   dict(ionic_strength_molar=float('nan')), dict(box_edge_nm=8),
                                   dict(dh_cutoff_nm=3), dict(author_commit='different')])
def test_invalid_or_unsupported_native_inputs_are_not_repaired(changes):
    with pytest.raises(ValueError):
        declared_request(**changes).validate()
