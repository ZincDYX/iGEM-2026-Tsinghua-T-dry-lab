"""Analytic input/topology format contracts, not biological validation."""
from pathlib import Path
import pytest
from igem_drylab.reference_membrane_builder import read_crd,native_molecule,source_initial_geometry,em_diagnostic


@pytest.mark.data_contract
def test_original_CRD_units_and_identity_are_retained(tmp_path):
    path=tmp_path/'original.crd'
    path.write_text('* original fixture\n2 EXT\n1 1 LIP P 10 20 30 S 1 0\n2 1 LIP C 0 -10 -20 S 1 0\n')
    names,xyz=read_crd(path)
    assert names==['P','C'] and xyz.tolist()==[[1.,2.,3.],[0.,-1.,-2.]]
    path.write_text('* fixture\n2 EXT\n1 1 LIP P 10 20 30 S 1 0\n')
    with pytest.raises(ValueError,match='complete_unique'):read_crd(path)


@pytest.mark.scientific_algorithm
def test_native_topology_renames_only_molecule_identity_and_retains_charge():
    original='[ moleculetype ]\nOther 3\n[ atoms ]\n1 PL 1 LIP P 1 1.5 30.974\n2 O2L 1 LIP OP 1 -2.5 15.9994\n[ bonds ]\n1 2 1\n[ system ]\nfixture\n[ molecules ]\nOther 1\n'
    body,names,charge=native_molecule(original,'LIP')
    assert '[ moleculetype ]\nLIP 3' in body and names==['P','OP'] and charge==-1
    assert '[ bonds ]\n1 2 1' in body and '30.974' in body and '15.9994' in body
    assert '[ system ]' not in body


@pytest.mark.scientific_algorithm
def test_initial_geometry_uses_source_coordinates_not_claimed_thickness(tmp_path):
    path=tmp_path/'reference.gro';rows=[]
    for i,z in enumerate([1.,1.,5.,5.],1):rows.append(f'{i:5d}{"LIP":<5}{"P":>5}{i:5d}{0.:8.3f}{0.:8.3f}{z:8.3f}')
    path.write_text('fixture\n4\n'+'\n'.join(rows)+'\n10 10 8\n')
    area,planes=source_initial_geometry(path,100)
    assert area==1 and planes.tolist()==[-2.,2.]


@pytest.mark.data_contract
@pytest.mark.parametrize('force',['inf','nan','1.2e24'])
def test_native_successful_exit_is_not_a_minimization_pass(force):
    result=em_diagnostic('Maximum force = '+force+' on atom 1','emtol = 1000\n')
    assert result['native_EM_target_met'] is False
    assert result['EM_max_force_finite']==(force=='1.2e24')


@pytest.mark.data_contract
def test_finite_native_EM_target_is_checked():
    result=em_diagnostic('Maximum force = 999.0 on atom 1','emtol = 1000\n')
    assert result['native_EM_target_met'] and result['max_force_kJ_mol_nm']==999
