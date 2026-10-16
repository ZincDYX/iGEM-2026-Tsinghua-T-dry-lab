"""QM contracts and an optional native-engine mathematical fixture, not holo validation."""
import json
import os
import numpy as np
import pytest

from igem_drylab.quantum_calculations import QuantumCalculationInput,run_quantum_calculation


def hydrogen_request(tmp_path):
    return dict(atoms=[dict(source_atom_id='a',element='H',xyz_angstrom=[0,0,0]),
        dict(source_atom_id='b',element='H',xyz_angstrom=[0,0,1])],formal_charge=0,spin_2s=0,
        method='HF',basis='sto-3g',method_reference='native RHF numerical test, not project method',
        chemical_state_reference='neutral singlet H2',model_boundary_description='complete H2, no caps',
        output_dir=tmp_path/'qm',threads=1,max_geometry_steps=30)


@pytest.mark.data_contract
@pytest.mark.parametrize('change',['atom_id','nonfinite','freeze_duplicate','freeze_outside'])
def test_qm_atom_map_and_boundaries_are_explicit(tmp_path,change):
    data=hydrogen_request(tmp_path)
    if change=='atom_id':data['atoms'][1]['source_atom_id']='a'
    if change=='nonfinite':data['atoms'][1]['xyz_angstrom'][0]=float('nan')
    if change=='freeze_duplicate':data['frozen_atoms_1based']=[1,1]
    if change=='freeze_outside':data['frozen_atoms_1based']=[3]
    with pytest.raises(ValueError):QuantumCalculationInput.model_validate(data)


@pytest.mark.data_contract
def test_model_compound_requires_explicit_cap_and_rebuilds_the_chemical_graph(tmp_path):
    pytest.importorskip('rdkit')
    from igem_drylab.quantum_calculations import ModelCompoundInput,prepare_model_compound
    ccd=tmp_path/'synthetic.cif'
    ccd.write_text('data_synthetic\nloop_\n_chem_comp_atom.atom_id\n_chem_comp_atom.type_symbol\n_chem_comp_atom.charge\nC1 C 0\nC2 C 0\nloop_\n_chem_comp_bond.atom_id_1\n_chem_comp_bond.atom_id_2\n_chem_comp_bond.value_order\nC1 C2 SING\n')
    payload=ModelCompoundInput(fragments=[dict(id='cap',ccd_file=ccd,
        coordinates=[dict(source_atom_id='C1',element='C',xyz_angstrom=[0,0,0])],
        boundary_and_state_reference='synthetic carbon graph, cap not yet specified')],
        state_and_boundary_reference='synthetic, not a biological model')
    with pytest.raises(ValueError,match='explicit_cap'):prepare_model_compound(payload)
    payload.fragments[0].hydrogen_counts={'C1':4}
    result=prepare_model_compound(payload)
    assert len(result['atoms'])==5 and result['formal_charge']==0
    assert result['canonical_SMILES']=='C' and not result['production_MD_ready']
    assert len(result['mapped_bonds'])==4
    payload.fragments[0].formal_charges={'missing':1}
    with pytest.raises(ValueError,match='chemical_edits'):prepare_model_compound(payload)


@pytest.mark.data_contract
def test_CCD_uppercase_metal_identity_is_not_an_oxidation_state_assignment(tmp_path):
    pytest.importorskip('rdkit')
    from igem_drylab.quantum_calculations import ModelCompoundInput,prepare_model_compound
    ccd=tmp_path/'synthetic-Fe.cif'
    ccd.write_text('data_synthetic\nloop_\n_chem_comp_atom.atom_id\n_chem_comp_atom.type_symbol\n_chem_comp_atom.charge\nFE FE 3\n')
    payload=ModelCompoundInput(fragments=[dict(id='metal',ccd_file=ccd,
        coordinates=[dict(source_atom_id='FE',element='Fe',xyz_angstrom=[0,0,0])],formal_charges={'FE':2},
        boundary_and_state_reference='explicit synthetic FeII override, not inferred from CCD')],
        state_and_boundary_reference='synthetic test')
    result=prepare_model_compound(payload)
    assert result['formal_charge']==2 and result['atoms'][0]['element']=='Fe'
    assert result['canonical_SMILES']=='[Fe+2]'


@pytest.mark.scientific_algorithm
@pytest.mark.parametrize('backend',['cpu','cuda'])
def test_native_qm_optimization_gradient_hessian_and_no_MD_promotion(tmp_path,backend):
    if backend=='cuda' and os.environ.get('FUSIONLAB_QM_GPU_TEST')!='1':
        pytest.skip('GPU QM native test requires an explicitly assigned CUDA device')
    pyscf=pytest.importorskip('pyscf')
    from pyscf import gto,scf
    request=QuantumCalculationInput.model_validate(hydrogen_request(tmp_path))
    request.backend=backend
    # Independent direct energy call at the unoptimized initial coordinates.
    reference=scf.RHF(gto.M(atom='H 0 0 0; H 0 0 1',unit='Angstrom',basis='sto-3g',verbose=0)).kernel()
    result=run_quantum_calculation(request)
    assert result['engine_version']==pyscf.__version__
    assert result['final_SCF_initial_guess']=='same_attempt_geometry_optimization_checkpoint'
    assert result['energy_hartree']<reference
    mapping=json.loads((request.output_dir/'optimized-atom-mapping.json').read_text())
    direct=scf.RHF(gto.M(atom=[(a['element'],a['xyz_angstrom']) for a in mapping],unit='Angstrom',basis='sto-3g',verbose=0)).kernel()
    assert result['energy_hartree']==pytest.approx(direct,abs=1e-8,rel=0)
    assert result['maximum_absolute_gradient_hartree_per_bohr']<4.5e-4
    assert len(result['frequencies_wavenumber_cm_inverse'])==1
    assert result['frequencies_wavenumber_cm_inverse'][0]>0
    hessian=np.load(request.output_dir/'cartesian-hessian-hartree-per-bohr2.npy')
    np.testing.assert_allclose(hessian,hessian.transpose(1,0,3,2),atol=1e-8)
    assert not result['production_MD_ready'] and not result['CHARMM_partial_charges_fitted']
    assert not result['bonded_parameters_fitted']
    assert json.loads((request.output_dir/'request.json').read_text())['formal_charge']==0
    with pytest.raises(FileExistsError):run_quantum_calculation(request)


@pytest.mark.data_contract
@pytest.mark.parametrize('constraint',[
    dict(kind='distance',atoms_1based=[1,1],target=.9),
    dict(kind='distance',atoms_1based=[1,3],target=.9),
    dict(kind='distance',atoms_1based=[1,2],target=-.9),
    dict(kind='angle',atoms_1based=[1,2,3],target=181),
    dict(kind='distance',atoms_1based=[1,2],target=float('nan')),
])
def test_PES_coordinate_constraints_reject_ambiguous_or_nonphysical_inputs(tmp_path,constraint):
    data=hydrogen_request(tmp_path);data['coordinate_constraints']=[constraint]
    with pytest.raises(ValueError):QuantumCalculationInput.model_validate(data)


@pytest.mark.data_contract
def test_reversed_duplicate_coordinate_does_not_manufacture_independent_constraints(tmp_path):
    data=hydrogen_request(tmp_path);data['coordinate_constraints']=[dict(kind='distance',atoms_1based=indices,target=.9) for indices in [[1,2],[2,1]]]
    with pytest.raises(ValueError,match='duplicate_QM_coordinate_constraint'):QuantumCalculationInput.model_validate(data)


@pytest.mark.data_contract
@pytest.mark.parametrize('target',[0.,180.])
def test_linear_angle_targets_are_not_rejected_as_nonphysical(tmp_path,target):
    data=hydrogen_request(tmp_path)
    data['atoms'].append(dict(source_atom_id='c',element='O',xyz_angstrom=[1,0,1]))
    data['coordinate_constraints']=[dict(kind='angle',atoms_1based=[1,2,3],target=target)]
    assert QuantumCalculationInput.model_validate(data).coordinate_constraints[0].target==target


@pytest.mark.scientific_algorithm
def test_native_constrained_PES_point_is_not_a_free_minimum_or_a_force_field(tmp_path):
    pytest.importorskip('pyscf')
    data=hydrogen_request(tmp_path);data['coordinate_constraints']=[dict(kind='distance',atoms_1based=[1,2],target=.9)]
    request=QuantumCalculationInput.model_validate(data);result=run_quantum_calculation(request)
    mapping=json.loads((request.output_dir/'optimized-atom-mapping.json').read_text())
    distance=np.linalg.norm(np.asarray(mapping[0]['xyz_angstrom'])-mapping[1]['xyz_angstrom'])
    assert distance==pytest.approx(.9,abs=1e-3)
    assert result['frequencies_wavenumber_cm_inverse'] is None
    assert result['coordinate_constraints']==data['coordinate_constraints']
    assert result['maximum_absolute_gradient_hartree_per_bohr']>4.5e-4
    assert not result['production_MD_ready'] and not result['bonded_parameters_fitted']


def synthetic_PES_reference(tmp_path):
    """Explicit analytical native-format fixture, not an actual PySCF job."""
    from igem_drylab.quantum_calculations import RelaxedPESReferenceInput
    folders=[]
    for index,distance in enumerate([.9,1.,1.1,.95,1.05]):
        folder=tmp_path/('point'+str(index));folder.mkdir();folders.append(folder)
        data=hydrogen_request(folder);data['coordinate_constraints']=[dict(kind='distance',atoms_1based=[1,2],target=distance)]
        data['method_reference']='SYNTHETIC analytical curve, not native execution'
        request=QuantumCalculationInput.model_validate(data);(folder/'request.json').write_text(request.model_dump_json())
        native={key:getattr(request,key) for key in ('formal_charge','spin_2s','method','basis','density_fitting','backend')}
        native.update(geometry_converged=True,SCF_converged=True,engine='SYNTHETIC-NOT-PySCF',engine_version='fixture',
            energy_hartree=-1+3*(distance-1)**2)
        (folder/'result.json').write_text(json.dumps(native))
        mapping=[a.model_dump(mode='json') for a in request.atoms];mapping[1]['xyz_angstrom']=[0,0,distance]
        (folder/'optimized-atom-mapping.json').write_text(json.dumps(mapping))
    return RelaxedPESReferenceInput(training_directories=folders[:3],validation_directories=folders[3:],
        source_reference='Independent analytic E=-1+3*(r-1)^2 fixture; not biological validation')


@pytest.mark.scientific_algorithm
def test_local_PES_independent_quadratic_and_holdout_units_not_force_constants(tmp_path):
    from scipy.constants import physical_constants,Avogadro
    from igem_drylab.quantum_calculations import fit_relaxed_PES_reference
    result=fit_relaxed_PES_reference(synthetic_PES_reference(tmp_path))
    assert result['local_fitted_minimum_angstrom']==pytest.approx(1.,abs=1e-12)
    assert result['coefficients']['a_hartree_per_angstrom2']==pytest.approx(3.,abs=1e-12)
    expected=6*physical_constants['Hartree energy'][0]*Avogadro/1000*100
    assert result['relaxed_QM_curvature_kJ_mol_nm2']==pytest.approx(expected,rel=1e-12)
    assert result['holdout_errors']['maximum_absolute_error_kJ_mol']<1e-9
    assert len(result['training_points'])==3 and len(result['holdout_points'])==2
    assert not result['bonded_parameters_fitted'] and not result['production_MD_ready']


@pytest.mark.data_contract
@pytest.mark.parametrize('fault',['reused_holdout','changed_spin','changed_atom','unconverged','native_theory'])
def test_local_PES_rejects_reused_or_incomparable_reference_points(tmp_path,fault):
    from igem_drylab.quantum_calculations import fit_relaxed_PES_reference
    request=synthetic_PES_reference(tmp_path);folder=request.validation_directories[0]
    if fault=='reused_holdout':request.validation_directories=[request.training_directories[0]]
    elif fault=='changed_spin':
        path=folder/'request.json';data=json.loads(path.read_text());data['spin_2s']=2;path.write_text(json.dumps(data))
    elif fault=='changed_atom':
        path=folder/'optimized-atom-mapping.json';data=json.loads(path.read_text());data[0]['source_atom_id']='other';path.write_text(json.dumps(data))
    else:
        path=folder/'result.json';data=json.loads(path.read_text())
        if fault=='unconverged':data['SCF_converged']=False
        if fault=='native_theory':data['basis']='other'
        path.write_text(json.dumps(data))
    with pytest.raises(ValueError):fit_relaxed_PES_reference(request)
