"""Explicit model-compound QM targets, not an automatically approved force field.

Run in an isolated PySCF environment. Native logs, SCF checkpoint, atom mapping,
optimized geometry, gradient and (when requested) Cartesian Hessian are retained.
No QM population charges are silently promoted to CHARMM partial charges.
"""
import argparse
import json
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .design_analysis import ScientificAnalysisInput


class QuantumAtom(ScientificAnalysisInput):
    source_atom_id: str = Field(min_length=1)
    element: str = Field(min_length=1)
    xyz_angstrom: tuple[float,float,float]


class CcdFragment(ScientificAnalysisInput):
    """Retained CCD heavy atoms with explicit cap/protonation edits."""
    id: str = Field(min_length=1)
    ccd_file: Path
    coordinates: list[QuantumAtom] = Field(min_length=1)
    hydrogen_counts: dict[str,int] = Field(default_factory=dict)
    formal_charges: dict[str,int] = Field(default_factory=dict)
    bond_orders: list[tuple[str,str,Literal['SING','DOUB','TRIP']]] = Field(default_factory=list)
    boundary_and_state_reference: str = Field(min_length=1)


class ModelCompoundInput(ScientificAnalysisInput):
    fragments: list[CcdFragment] = Field(min_length=1)
    covalent_connections: list[tuple[str,str]] = Field(default_factory=list)
    state_and_boundary_reference: str = Field(min_length=1)


def prepare_model_compound(payload: ModelCompoundInput) -> dict:
    """Rebuild hydrogens, not partial charges, from a declared chemical graph.

    A cut does not silently add a cap: the caller must provide its new hydrogen
    count explicitly. Hydrogens are initial coordinates only, not QM results.
    Metal coordination is not inferred from proximity or made into a covalent bond.
    """
    from Bio.PDB.MMCIF2Dict import MMCIF2Dict
    from rdkit import Chem, __version__ as rdkit_version
    from hashlib import sha256
    molecule=Chem.RWMol();indices={};positions=[];source=[]
    orders={'SING':Chem.BondType.SINGLE,'DOUB':Chem.BondType.DOUBLE,'TRIP':Chem.BondType.TRIPLE}
    for fragment in payload.fragments:
        ccd=MMCIF2Dict(str(fragment.ccd_file))
        records={name:(element,int(charge)) for name,element,charge in zip(ccd['_chem_comp_atom.atom_id'],
            ccd['_chem_comp_atom.type_symbol'],ccd['_chem_comp_atom.charge'],strict=True)}
        bonds=list(zip(ccd.get('_chem_comp_bond.atom_id_1',[]),ccd.get('_chem_comp_bond.atom_id_2',[]),
            ccd.get('_chem_comp_bond.value_order',[]),strict=True))
        coords={a.source_atom_id:a for a in fragment.coordinates}
        if len(coords)!=len(fragment.coordinates) or any(name not in records or records[name][0] in {'H','D'} for name in coords):
            raise ValueError('QM_fragment_requires_unique_CCD_heavy_atom_identifiers')
        edits=set(fragment.hydrogen_counts)|set(fragment.formal_charges)
        if not edits<=coords.keys():raise ValueError('QM_chemical_edits_must_target_retained_atoms')
        for name,coordinate in coords.items():
            element,charge=records[name]
            if element.upper()!=coordinate.element.upper():raise ValueError('QM_CCD_coordinate_element_mismatch')
            cut=[other for first,second,_ in bonds for own,other in [(first,second),(second,first)]
                if own==name and other not in coords and records[other][0] not in {'H','D'}]
            if cut and name not in fragment.hydrogen_counts:
                raise ValueError('QM_cut_atom_requires_explicit_cap_hydrogen_count:'+fragment.id+'/'+name)
            hydrogens=sum(records[other][0] in {'H','D'} for first,second,_ in bonds
                for own,other in [(first,second),(second,first)] if own==name)
            hydrogens=fragment.hydrogen_counts.get(name,hydrogens)
            if hydrogens<0:raise ValueError('QM_hydrogen_count_cannot_be_negative')
            atom=Chem.Atom(element.capitalize());atom.SetFormalCharge(fragment.formal_charges.get(name,charge))
            atom.SetNoImplicit(True);atom.SetNumExplicitHs(hydrogens)
            identity=fragment.id+'/'+name
            if identity in indices:raise ValueError('QM_fragment_atom_identity_must_be_unique')
            indices[identity]=molecule.AddAtom(atom);positions.append(coordinate.xyz_angstrom)
        overrides={frozenset((a,b)):order for a,b,order in fragment.bond_orders}
        retained={frozenset((a,b)) for a,b,_ in bonds if a in coords and b in coords}
        if len(overrides)!=len(fragment.bond_orders) or not overrides.keys()<=retained:
            raise ValueError('QM_bond_order_edits_must_identify_unique_retained_CCD_bonds')
        for first,second,order in bonds:
            if first in coords and second in coords:
                molecule.AddBond(indices[fragment.id+'/'+first],indices[fragment.id+'/'+second],
                    orders[overrides.get(frozenset((first,second)),order)])
        source.append(dict(fragment_id=fragment.id,CCD_sha256=sha256(fragment.ccd_file.read_bytes()).hexdigest(),
            boundary_and_state_reference=fragment.boundary_and_state_reference))
    for first,second in payload.covalent_connections:
        if first not in indices or second not in indices:raise ValueError('QM_connection_atom_not_retained')
        molecule.AddBond(indices[first],indices[second],Chem.BondType.SINGLE)
    molecule=molecule.GetMol();Chem.SanitizeMol(molecule)
    conformer=Chem.Conformer(molecule.GetNumAtoms())
    for index,xyz in enumerate(positions):conformer.SetAtomPosition(index,xyz)
    molecule.AddConformer(conformer);molecule=Chem.AddHs(molecule,addCoords=True)
    names={index:identity for identity,index in indices.items()};counts={}
    for index in range(len(indices),molecule.GetNumAtoms()):
        atom=molecule.GetAtomWithIdx(index)
        if atom.GetAtomicNum()!=1 or len(atom.GetNeighbors())!=1:raise ValueError('invalid_QM_generated_hydrogen_graph')
        parent=names[atom.GetNeighbors()[0].GetIdx()];counts[parent]=counts.get(parent,0)+1
        names[index]=parent+'.H'+str(counts[parent])
    prepared=[QuantumAtom(source_atom_id=names[i],element=a.GetSymbol(),
        xyz_angstrom=tuple(molecule.GetConformer().GetAtomPosition(i))).model_dump(mode='json')
        for i,a in enumerate(molecule.GetAtoms())]
    return dict(atoms=prepared,formal_charge=Chem.GetFormalCharge(molecule),RDKit_version=rdkit_version,
        mapped_bonds=[dict(first=names[b.GetBeginAtomIdx()],second=names[b.GetEndAtomIdx()],order=str(b.GetBondType()))
            for b in molecule.GetBonds()],canonical_SMILES=Chem.MolToSmiles(Chem.RemoveHs(molecule)),sources=source,
        state_and_boundary_reference=payload.state_and_boundary_reference,production_MD_ready=False,
        scope='explicit_model_compound_initial_chemical_graph_not_QM_or_force_field_validation')


class QuantumCalculationInput(ScientificAnalysisInput):
    atoms: list[QuantumAtom] = Field(min_length=2)
    formal_charge: int
    spin_2s: int = Field(ge=0)
    method: Literal['HF','B3LYPG','PBE0']
    basis: str = Field(min_length=1)
    method_reference: str = Field(min_length=1)
    chemical_state_reference: str = Field(min_length=1)
    model_boundary_description: str = Field(min_length=1)
    output_dir: Path
    backend: Literal['cpu','cuda'] = 'cpu'
    density_fitting: bool = False
    calculate_hessian: bool = True
    frozen_atoms_1based: list[int] = Field(default_factory=list)
    threads: int = Field(default=8,ge=1)
    memory_MB: int = Field(default=16000,ge=1)
    max_geometry_steps: int = Field(default=200,ge=1)
    max_scf_cycles: int = Field(default=200,ge=1)
    scf_energy_tolerance_hartree: float = Field(default=1e-9,gt=0)

    @model_validator(mode='after')
    def atom_mapping(self):
        if len({a.source_atom_id for a in self.atoms})!=len(self.atoms):
            raise ValueError('QM_source_atom_mapping_must_be_unique')
        if not np.isfinite([a.xyz_angstrom for a in self.atoms]).all():
            raise ValueError('QM_coordinates_must_be_finite')
        if len(set(self.frozen_atoms_1based))!=len(self.frozen_atoms_1based) or any(
                i<1 or i>len(self.atoms) for i in self.frozen_atoms_1based):
            raise ValueError('invalid_QM_frozen_atom_indices')
        return self


def run_quantum_calculation(payload: QuantumCalculationInput) -> dict:
    import pyscf
    from pyscf import gto,scf,dft,lib
    from pyscf.hessian import thermo
    root=payload.output_dir
    root.mkdir(parents=True,exist_ok=False)  # A retry is a new immutable attempt.
    (root/'request.json').write_text(payload.model_dump_json(indent=2))
    lib.num_threads(payload.threads)
    molecule=gto.M(atom=[(a.element,a.xyz_angstrom) for a in payload.atoms],unit='Angstrom',
        basis=payload.basis,charge=payload.formal_charge,spin=payload.spin_2s,
        max_memory=payload.memory_MB,verbose=4,output=str(root/'native-pyscf.log'))
    if payload.method=='HF':
        mean_field=scf.RHF(molecule) if not payload.spin_2s else scf.UHF(molecule)
    else:
        mean_field=dft.RKS(molecule) if not payload.spin_2s else dft.UKS(molecule)
        mean_field.xc=payload.method
        mean_field.grids.level=4
    if payload.density_fitting:mean_field=mean_field.density_fit()
    if payload.backend=='cuda':
        import gpu4pyscf
        import cupy
        mean_field=mean_field.to_gpu()
    mean_field.chkfile=str(root/'wavefunction.chk')
    mean_field.conv_tol=payload.scf_energy_tolerance_hartree
    mean_field.max_cycle=payload.max_scf_cycles
    optimizer=mean_field.Gradients().optimizer(solver='geomeTRIC')
    optimizer.max_cycle=payload.max_geometry_steps
    parameters=dict(convergence_energy=1e-6,
        convergence_grms=3e-4,convergence_gmax=4.5e-4,convergence_drms=1.2e-3,convergence_dmax=1.8e-3)
    if payload.frozen_atoms_1based:
        constraints=root/'constraints.txt'
        constraints.write_text('$freeze\n'+'\n'.join(f'xyz {i}' for i in payload.frozen_atoms_1based)+'\n$end\n')
        parameters['constraints']=str(constraints)
    optimized=optimizer.kernel(params=parameters)
    if not optimizer.converged:
        raise RuntimeError('QM_geometry_did_not_converge_native_outputs_preserved')
    mean_field=mean_field.reset(optimized)
    energy=float(mean_field.kernel())
    if not mean_field.converged:raise RuntimeError('final_QM_SCF_did_not_converge')
    coordinates=optimized.atom_coords(unit='Angstrom')
    (root/'optimized.xyz').write_text(str(len(payload.atoms))+'\nQM model compound, not a production-ready topology\n'+
        '\n'.join(f'{a.element} {x:.10f} {y:.10f} {z:.10f}' for a,(x,y,z) in zip(payload.atoms,coordinates,strict=True))+'\n')
    mapping=[dict(source_atom_id=a.source_atom_id,element=a.element,xyz_angstrom=xyz.tolist())
        for a,xyz in zip(payload.atoms,coordinates,strict=True)]
    (root/'optimized-atom-mapping.json').write_text(json.dumps(mapping,indent=2))
    gradient=mean_field.nuc_grad_method().kernel()
    if payload.backend=='cuda':gradient=cupy.asnumpy(gradient)
    np.save(root/'gradient-hartree-per-bohr.npy',gradient)
    frequencies=None
    if payload.calculate_hessian:
        hessian=mean_field.Hessian().kernel()
        if payload.backend=='cuda':hessian=cupy.asnumpy(hessian)
        np.save(root/'cartesian-hessian-hartree-per-bohr2.npy',hessian)
        if not payload.frozen_atoms_1based:
            # Signed negative wavenumbers retain imaginary modes, without an
            # invented tolerance that would classify a saddle as validated.
            frequencies=thermo.harmonic_analysis(optimized,hessian,imaginary_freq=False)['freq_wavenumber'].tolist()
    result=dict(schema_version='QM-model-compound-targets-v1',engine='PySCF',engine_version=pyscf.__version__,
        method=payload.method,basis=payload.basis,density_fitting=payload.density_fitting,backend=payload.backend,
        formal_charge=payload.formal_charge,spin_2s=payload.spin_2s,multiplicity=payload.spin_2s+1,
        electrons=optimized.nelectron,atom_count=optimized.natm,geometry_converged=True,SCF_converged=True,
        energy_hartree=energy,maximum_absolute_gradient_hartree_per_bohr=float(np.abs(gradient).max()),
        frequencies_wavenumber_cm_inverse=frequencies,frozen_atoms_1based=payload.frozen_atoms_1based,
        frozen_atom_displacement_angstrom={payload.atoms[i-1].source_atom_id:float(np.linalg.norm(
            coordinates[i-1]-np.asarray(payload.atoms[i-1].xyz_angstrom))) for i in payload.frozen_atoms_1based},
        Hessian_calculated=payload.calculate_hessian,geometry_convergence=parameters,
        production_MD_ready=False,CHARMM_partial_charges_fitted=False,bonded_parameters_fitted=False,
        scope='QM_reference_targets_only_not_CHARMM_parameter_validation_or_MD_approval')
    if payload.spin_2s:result['spin_square_and_effective_multiplicity']=[float(v) for v in mean_field.spin_square()]
    if payload.backend=='cuda':result['gpu4pyscf_version']=gpu4pyscf.__version__
    (root/'result.json').write_text(json.dumps(result,indent=2));return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',type=Path,required=True)
    args=parser.parse_args()
    payload=QuantumCalculationInput.model_validate_json(args.request.read_text())
    print(json.dumps(run_quantum_calculation(payload),indent=2))


if __name__=='__main__':main()
