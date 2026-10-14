"""Independent profile oracle and explicit project contracts, not LLPS validation."""
from pathlib import Path
import pytest
from igem_drylab.phase_profile_analysis import PhaseProfileAnalysisInput,analyse_phase_profile
from igem_drylab.coarse_grain_project import CalvadosProjectInput,MpipiProjectInput


def profile(tmp_path,rows):
    path=tmp_path/'density.csv';path.write_text('step,lower,upper,density\n'+rows)
    return PhaseProfileAnalysisInput(path=path,density_unit='g/cm3',coordinate_unit='nm',
        start_step=10,end_step=20,dense_regions=[(1,4)],dilute_regions=[(0,1)],
        analysis_reference='synthetic declared window',coordinate_frame_reference='stationary fixture',independent_replicate_id='one')


@pytest.mark.scientific_algorithm
def test_phase_unequal_bin_widths_and_saved_frames_independent_oracle(tmp_path):
    request=profile(tmp_path,'10,0,1,1\n10,1,2,3\n10,2,4,6\n20,0,1,2\n20,1,2,6\n20,2,4,12\n')
    result=analyse_phase_profile(request)
    assert result['dense_phase_concentration']==pytest.approx(7.5)
    assert result['dilute_phase_concentration']==pytest.approx(1.5)
    assert result['enrichment_factor']==pytest.approx(5)
    assert result['llps_score'] is None and result['uncertainty'] is None


@pytest.mark.data_contract
def test_partial_bin_window_does_not_interpolate_a_phase(tmp_path):
    request=profile(tmp_path,'10,0,1,1\n10,1,2,3\n10,2,4,6\n').model_copy(update={'dense_regions':[(1,3)]})
    with pytest.raises(ValueError,match='complete_native_bin_edges'):analyse_phase_profile(request)


@pytest.mark.data_contract
def test_zero_dilute_density_not_infinite_partition_score(tmp_path):
    result=analyse_phase_profile(profile(tmp_path,'10,0,1,0\n10,1,2,3\n10,2,4,6\n'))
    assert result['enrichment_factor'] is None


@pytest.mark.data_contract
def test_calvados_requires_project_duration_and_physical_protocol(tmp_path):
    data=dict(candidate_id='synthetic',sequence='GYA',output_dir=tmp_path,config={},component={},
              expected_native_version='0.9.0',protocol_reference='fixture',force_field_reference='fixture',native_defaults_review_reference='fixture')
    with pytest.raises(ValueError,match='physical_and_runtime'):CalvadosProjectInput.model_validate(data)
    data['config']=dict(box=[10,10,10],temp=298,ionic=.15,pH=7,topol='single',eps_lj=.2,
        cutoff_lj=2,cutoff_yu=4,friction_coeff=.01,wfreq=10,random_number_seed=12345,platform='CUDA',restart=None)
    with pytest.raises(ValueError,match='explicit_duration'):CalvadosProjectInput.model_validate(data)


@pytest.mark.data_contract
def test_phase_nonfinite_missing_or_overlapping_native_bins_rejected(tmp_path):
    for rows in ('10,0,1,nan\n','10,0,2,1\n10,1,3,1\n','10,0,1,1\n10,2,4,3\n'):
        with pytest.raises(ValueError):analyse_phase_profile(profile(tmp_path,rows))
