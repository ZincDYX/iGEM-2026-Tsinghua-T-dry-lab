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
    assert not em_diagnostic('Maximum force = 1000','emtol = 1000\n')['native_EM_target_met']


@pytest.mark.data_contract
def test_grouped_original_conformers_preserve_all_atoms_and_species_counts(tmp_path,monkeypatch):
    import numpy as np
    from types import SimpleNamespace
    from igem_drylab.reference_membrane_builder import pack_original_conformers
    xyz=np.array([[0.,0.,0.],[0.,0.,1.]])
    molecules=[('A',0,['P','C'],xyz,[0]),('B',1,['P','C'],xyz,[0]),('A',0,['P','C'],xyz,[0])]
    request=SimpleNamespace(initial_box_z_nm=8.,packing_tolerance_angstrom=2.,seed=1,
        initial_head_band_halfwidth_angstrom=2.,packmol_executable='synthetic-fixture-not-native-job',
        packing_timeout_seconds=5,molecule_counts={'A':2,'B':1},align_head_tail_for_initial_packing=True)
    def synthetic(command,**kwargs):
        assert kwargs['timeout']==5
        # Output order follows the grouped native input: A, A, B.
        (tmp_path/'packed.xyz').write_text('6\nsynthetic-format-fixture\nP 0 0 10\nC 0 0 20\nP 10 0 10\nC 10 0 20\nP 20 0 10\nC 20 0 20\n')
        kwargs['stdout'].write('Success!\n');kwargs['stdout'].flush()
    monkeypatch.setattr('igem_drylab.reference_membrane_builder.subprocess.run',synthetic)
    result=pack_original_conformers(tmp_path,molecules,10.,np.array([-2.,2.]),request)
    assert len(result['A'])==2 and len(result['B'])==1
    assert result['B'][0][0].tolist()==[2.,0.,1.]
    text=(tmp_path/'packmol.inp').read_text()
    assert text.count('\nstructure ')==2 and '\nnumber 2\n' in text
    assert 'restart_from initial.pack' in text
    for axis in ('x','y','z'):assert text.count(f'constrain_rotation {axis} 0. 0.')==2


@pytest.mark.scientific_algorithm
@pytest.mark.parametrize('heads',[[0],[0,1]])
def test_rigid_initial_orientation_preserves_geometry_and_chirality(heads):
    import numpy as np
    from igem_drylab.reference_membrane_builder import orient_initial_conformer
    names=['P1','P3','C1','C2','O1']
    xyz=np.array([[1.,2.,3.],[2.,2.,4.],[3.,1.,-1.],[1.,0.,-2.],[4.,3.,1.]])
    oriented=orient_initial_conformer(names,xyz,heads)
    assert np.allclose(np.linalg.norm(xyz[:,None]-xyz[None,:],axis=2),
        np.linalg.norm(oriented[:,None]-oriented[None,:],axis=2))
    assert np.allclose(oriented[heads].mean(axis=0),0.)
    assert oriented[[2,3],2].mean()<0
    if len(heads)==2:assert np.allclose(oriented[heads,2],0.)
    # A reflection would preserve distances but invert this signed volume.
    assert np.linalg.det(xyz[1:4]-xyz[0])==pytest.approx(np.linalg.det(oriented[1:4]-oriented[0]))


@pytest.mark.scientific_algorithm
def test_native_restart_places_heads_not_atomic_centroids_on_declared_planes(tmp_path):
    import numpy as np
    from igem_drylab.reference_membrane_builder import write_initial_packing_grid
    xyz=np.array([[1.,2.,3.],[2.,1.,1.]])
    molecules=[('A',leaflet,['P','C'],xyz,[0]) for leaflet in (0,0,1,1)]
    path=tmp_path/'initial.pack';box=np.array([100.,100.,80.]);planes=np.array([-2.,2.])
    write_initial_packing_grid(path,molecules,box,planes,7)
    native=np.loadtxt(path)
    assert native.shape==(4,6) and np.all(native[:,3:]==0)
    heads=native[:,:3]-xyz.mean(axis=0)*10+xyz[0]*10
    assert np.allclose(heads[:,2],[20.,20.,60.,60.])
    assert np.all((heads[:,:2]>0)&(heads[:,:2]<100))
    assert len({tuple(row) for row in heads})==4
    other=tmp_path/'repeated.pack';write_initial_packing_grid(other,molecules,box,planes,7)
    assert path.read_bytes()==other.read_bytes()
