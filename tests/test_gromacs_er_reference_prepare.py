"""Preparation contracts; original GROMACS/source acceptance is separate."""
import pytest
from igem_drylab.gromacs_er_reference_prepare import ERReferencePreparation, prepare_reference


@pytest.mark.data_contract
@pytest.mark.parametrize('box,salt', [([0.,1.,1.],.15), ([1.,1.],.15), ([1.,1.,float('nan')],.15), ([1.,1.,1.],-.1)])
def test_invalid_reference_conditions_fail_before_creating_derived_files(tmp_path, box, salt):
    destination=tmp_path/'new-reference'
    request=ERReferencePreparation(source_directory=str(tmp_path/'absent'),charmm_archive=str(tmp_path/'absent.tar'),
        em_mdp=str(tmp_path/'absent.mdp'),gmx_executable='NEVER_EXECUTE',output_directory=str(destination),
        initial_box_nm=box,target_water_molecules=12000,original_counterions=62,added_NaCl_molar=salt,
        ion_placement_seed=42,cpu_threads=1,protocol_reference='Synthetic contract only')
    with pytest.raises(ValueError):prepare_reference(request)
    assert not destination.exists()
