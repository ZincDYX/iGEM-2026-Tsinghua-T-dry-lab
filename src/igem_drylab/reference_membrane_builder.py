"""Declared bare reference bilayers from native C36 topologies and lipid library.

Construction geometry is an initial condition, not measured membrane thickness
or protein insertion. No original topology, lipid identity or force is edited.
"""
import argparse
from dataclasses import dataclass, asdict
import json
from pathlib import Path
import re
import shutil
import subprocess

import numpy as np


@dataclass
class ReferenceMembraneInput:
    recipe_id: str
    molecule_counts: dict[str, int]
    expected_lipid_charge_e: float
    native_template_root: str
    conformer_library: str
    source_geometry_gro: str
    source_geometry_lipids_per_leaflet: int
    initial_box_z_nm: float
    water_molecules_before_ions: int
    added_NaCl_molar: float
    seed: int
    gmx_executable: str
    em_mdp: str
    output_directory: str
    cpu_threads: int
    gpu_id: int
    protocol_reference: str
    packmol_executable: str
    packing_tolerance_angstrom: float
    initial_head_band_halfwidth_angstrom: float
    # Construction controls only; neither modifies the native force field.
    conformers_per_species_per_leaflet: int | None = None
    packing_timeout_seconds: int | None = None


def read_crd(path):
    lines=[line for line in Path(path).read_text().splitlines() if line.strip() and not line.lstrip().startswith('*')]
    count=int(lines[0].split()[0]);names=[];xyz=[]
    for line in lines[1:]:
        fields=line.split();names.append(fields[3]);xyz.append([float(x)/10 for x in fields[4:7]])
    if len(names)!=count or len(set(names))!=count:
        raise ValueError('lipid_library_conformer_requires_complete_unique_atom_names')
    return names,np.asarray(xyz)


def native_molecule(topology_text, species):
    """Retain native generated bonded/charge data; rename only molecule identity."""
    body=topology_text.split('[ moleculetype ]',1)[1].split('[ system ]',1)[0]
    body=re.sub(r'^Other\s+3\s*$',species+' 3',body,count=1,flags=re.M)
    if re.search(r'^Other\s+3\s*$',body,re.M):
        raise ValueError('native_lipid_molecule_identity_not_resolved')
    names=[];charge=0.;section=''
    for line in body.splitlines():
        text=line.split(';',1)[0].strip()
        if text.startswith('['):section=text.strip('[] ').strip()
        elif section=='atoms' and text and not text.startswith('#'):
            fields=text.split();names.append(fields[4]);charge+=float(fields[6])
    if not names:raise ValueError('native_lipid_topology_has_no_atoms')
    return '[ moleculetype ]'+body,names,charge


def source_initial_geometry(path, lipids_per_leaflet):
    lines=Path(path).read_text().splitlines();box=np.asarray([float(x) for x in lines[-1].split()])
    if len(box)!=3 or np.any(box<=0) or lipids_per_leaflet<=0:
        raise ValueError('reference_geometry_requires_declared_orthorhombic_box_and_leaflet_count')
    phosphate=np.asarray([float(line[36:44]) for line in lines[2:-1] if line[10:15].strip()=='P'])
    if not len(phosphate):raise ValueError('reference_geometry_has_no_phosphate_coordinates')
    # The original planar reference has one band of phosphates per leaflet.
    center=float(np.median(phosphate))
    lower=phosphate[phosphate<center];upper=phosphate[phosphate>center]
    if not len(lower) or not len(upper):raise ValueError('reference_phosphate_leaflets_not_resolved')
    planes=np.asarray([np.median(lower),np.median(upper)])
    return float(box[0]*box[1]/lipids_per_leaflet),planes-float(np.mean(planes))


def pack_original_conformers(root, molecules, edge, planes, request):
    """Rigid original conformers; periodic packing is not a force-field change."""
    directory=root/'packing-inputs';directory.mkdir()
    box=np.array([edge,edge,request.initial_box_z_nm])*10
    lines=[f'tolerance {request.packing_tolerance_angstrom}', 'filetype xyz',
        'output packed.xyz',f'seed {request.seed}',f'pbc {box[0]} {box[1]} {box[2]}']
    # PACKMOL optimizes molecule *types*. A unique type per individual lipid
    # made the previous native construction impractically slow. Repeated
    # original conformers can share a type without changing counts or atoms.
    groups={}
    for molecule in molecules:
        species,leaflet,names,xyz,heads=molecule
        groups.setdefault((species,leaflet,xyz.tobytes()),[]).append(molecule)
    ordered=[m for group in groups.values() for m in group]
    for index,group in enumerate(groups.values()):
        species,leaflet,names,xyz,heads=group[0]
        name=f'packing-inputs/molecule-{index}.xyz'
        with (root/name).open('w') as stream:
            stream.write(str(len(names))+'\noriginal native atom order\n')
            for atom,coordinate in zip(names,xyz*10):
                stream.write(atom[0]+' '+' '.join(f'{value:.8f}' for value in coordinate)+'\n')
        z=(request.initial_box_z_nm/2+planes[leaflet])*10
        width=request.initial_head_band_halfwidth_angstrom
        # Atomic leaflet direction avoids Euler-angle singularities. An original
        # distal carbon must lie inward from its sourced head plane. PACKMOL's
        # geometric constraints apply only to construction, never MD restraints.
        carbons=[i for i,atom in enumerate(names) if atom.startswith('C')]
        tail=max(carbons,key=lambda i:xyz[i,2]) if leaflet==0 else min(carbons,key=lambda i:xyz[i,2])
        side='above' if leaflet==0 else 'below'
        lines += [f'structure {name}',f'number {len(group)}','atoms '+' '.join(str(i+1) for i in heads),
            f'inside box 0. 0. {z-width} {box[0]} {box[1]} {z+width}','end atoms',
            f'atoms {tail+1}',f'{side} plane 0. 0. 1. {z}','end atoms','end structure']
    (root/'packmol.inp').write_text('\n'.join(lines)+'\n')
    with (root/'packmol.inp').open() as input_stream,(root/'00-native-PACKMOL.log').open('w') as log:
        subprocess.run([request.packmol_executable],cwd=root,stdin=input_stream,stdout=log,stderr=subprocess.STDOUT,check=True,
            timeout=request.packing_timeout_seconds)
    if 'Success!' not in (root/'00-native-PACKMOL.log').read_text():
        raise ValueError('native_periodic_packing_not_converged_no_EM_or_MD')
    packed=(root/'packed.xyz').read_text().splitlines()
    if int(packed[0])!=sum(len(m[2]) for m in molecules) or len(packed[2:])!=int(packed[0]):
        raise ValueError('native_packing_did_not_preserve_complete_atom_count')
    coordinates=np.array([[float(v)/10 for v in line.split()[1:4]] for line in packed[2:]])
    expected=[atom[0] for m in ordered for atom in m[2]]
    if [line.split()[0] for line in packed[2:]]!=expected or not np.all(np.isfinite(coordinates)):
        raise ValueError('native_packing_changed_original_atom_order_or_identity')
    positions={species:[] for species in request.molecule_counts};offset=0
    for species,leaflet,names,xyz,heads in ordered:
        positions[species].append(coordinates[offset:offset+len(names)]);offset+=len(names)
    return positions


def em_diagnostic(log, resolved_mdp):
    force=re.search(r'Maximum force\s*=\s*(\S+)',log)
    target=re.search(r'^\s*emtol\s*=\s*([0-9.eE+-]+)',resolved_mdp,re.M)
    value=float(force[1]) if force else None;threshold=float(target[1]) if target else None
    finite=value is not None and np.isfinite(value)
    return dict(max_force_kJ_mol_nm=value if finite else None,EM_target_kJ_mol_nm=threshold,
        EM_max_force_finite=bool(finite),native_EM_target_met=bool(finite and threshold is not None and value<threshold))


def build_reference(request):
    counts=request.molecule_counts
    if not counts or any(type(n) is not int or n<=0 or n%2 for n in counts.values()):
        raise ValueError('symmetric_reference_requires_positive_even_counts_for_every_declared_species')
    if request.water_molecules_before_ions<1 or request.initial_box_z_nm<=0 or request.added_NaCl_molar<0:
        raise ValueError('reference_water_box_and_salt_must_be_explicit')
    if request.packing_tolerance_angstrom<=0 or request.initial_head_band_halfwidth_angstrom<=0:
        raise ValueError('initial_packing_geometry_must_be_explicit')
    if request.conformers_per_species_per_leaflet is not None and not 1<=request.conformers_per_species_per_leaflet<=2000:
        raise ValueError('declared_conformer_pool_size_outside_original_library')
    if request.packing_timeout_seconds is not None and request.packing_timeout_seconds<=0:
        raise ValueError('packing_timeout_must_be_positive')
    root=Path(request.output_directory);root.mkdir(parents=True,exist_ok=True)
    if any(root.iterdir()):raise ValueError('reference_membrane_build_requires_new_directory')
    templates=Path(request.native_template_root);ff=templates/'charmm36-jul2022.ff'
    (root/ff.name).symlink_to(ff.resolve(),target_is_directory=True)
    area_per_lipid,planes=source_initial_geometry(request.source_geometry_gro,request.source_geometry_lipids_per_leaflet)
    per_leaflet=sum(counts.values())//2;edge=float(np.sqrt(area_per_lipid*per_leaflet))
    rng=np.random.default_rng(request.seed)
    definitions={};charge=0.;files={}
    for species,count in counts.items():
        text,names,q=native_molecule((templates/species/'topol.top').read_text(),species)
        (root/(species+'.itp')).write_text(text)
        shutil.copyfile(templates/species/'posre.itp',root/(species+'-posre.itp'))
        # Preserve the native optional restraint, inactive in the bare protocol.
        path=root/(species+'.itp');path.write_text(path.read_text().replace('"posre.itp"','"'+species+'-posre.itp"'))
        definitions[species]=names;charge+=count*q
        library=Path(request.conformer_library)/species/species.lower()
        files[species]=sorted(library.glob('conf*/*.crd'))
        if len(files[species])!=2000:raise ValueError('original_lipid_library_requires_all_2000_conformers')
    if not np.isclose(charge,request.expected_lipid_charge_e,atol=1e-7):
        raise ValueError('native_reference_charge_differs_from_declared_recipe')
    molecules=[];choices=[]
    for leaflet in range(2):
        pools={s:rng.choice(files[s],size=request.conformers_per_species_per_leaflet,replace=False).tolist()
            for s in counts} if request.conformers_per_species_per_leaflet is not None else files
        species_order=[species for species,count in counts.items() for _ in range(count//2)]
        rng.shuffle(species_order)
        for species in species_order:
            conformer=Path(pools[species][int(rng.integers(len(pools[species])))]);names,xyz=read_crd(conformer)
            lookup={name:i for i,name in enumerate(names)}
            if set(names)!=set(definitions[species]):raise ValueError('original_conformer_atoms_differ_from_native_C36_topology')
            xyz=xyz[[lookup[name] for name in definitions[species]]]
            heads=[i for i,n in enumerate(definitions[species]) if n in {'P','P1','P3'}] if species!='ERG' else [definitions[species].index('O3')]
            if not heads:raise ValueError('declared_library_headgroup_atoms_missing')
            xyz-=xyz[heads].mean(axis=0)
            # Original library phospholipid tails point toward negative z.
            if leaflet==0:xyz=xyz*np.array([1.,-1.,-1.])
            angle=float(rng.uniform(0,2*np.pi)) if request.conformers_per_species_per_leaflet is None else 0.
            c,s=np.cos(angle),np.sin(angle)
            xyz=xyz@np.array([[c,s,0],[-s,c,0],[0,0,1.]])
            molecules.append((species,leaflet,definitions[species],xyz,heads))
            choices.append(dict(species=species,leaflet=leaflet,conformer=str(conformer),initial_rotation_radian=angle))
    (root/'request.json').write_text(json.dumps(asdict(request),indent=2))
    (root/'initial-library-conformer-choices.json').write_text(json.dumps(choices,indent=2))
    positions=pack_original_conformers(root,molecules,edge,planes,request)
    natoms=sum(counts[s]*len(definitions[s]) for s in counts)
    with (root/'initial.gro').open('w') as stream:
        stream.write(request.recipe_id+' bare reference initial condition\n'+str(natoms)+'\n');serial=0;residue=0
        for species,rows in positions.items():
            for xyz in rows:
                residue+=1
                for name,(x,y,z) in zip(definitions[species],xyz):
                    serial+=1;stream.write(f'{residue%100000:5d}{species:<5s}{name:>5s}{serial%100000:5d}{x:8.3f}{y:8.3f}{z:8.3f}\n')
        stream.write(f'{edge:.8f} {edge:.8f} {request.initial_box_z_nm:.8f}\n')
    top='#include "'+ff.name+'/forcefield.itp"\n'+''.join('#include "'+s+'.itp"\n' for s in counts)
    top+='#include "'+ff.name+'/tip3p.itp"\n#include "'+ff.name+'/ions.itp"\n[ system ]\n'+request.recipe_id+' bare reference\n[ molecules ]\n'
    top+=''.join(s+' '+str(n)+'\n' for s,n in counts.items());(root/'topol.top').write_text(top)
    commands=[]
    def native(arguments,log_name,stdin=None):
        command=[request.gmx_executable,*arguments];commands.append(command)
        with (root/log_name).open('w') as log:
            subprocess.run(command,cwd=root,input=stdin,text=True,stdout=log,stderr=subprocess.STDOUT,check=True)
    native(['solvate','-cp','initial.gro','-cs','spc216.gro','-o','solvated.gro','-p','topol.top','-maxsol',str(request.water_molecules_before_ions)],'01-solvate.log')
    molecules=(root/'topol.top').read_text().split('[ molecules ]')[-1]
    waters=sum(int(n) for n in re.findall(r'^\s*SOL\s+(\d+)\s*$',molecules,re.M))
    if waters!=request.water_molecules_before_ions:raise ValueError('reference_box_did_not_fit_declared_full_hydration')
    # This temporary TPR is used only to select/replace solvent during genion.
    # It is never simulated. Actual EM/MD use the unmodified supplied PME MDP.
    ion_mdp=Path(request.em_mdp).read_text();ion_mdp=re.sub(r'^\s*coulombtype\s*=.*$','coulombtype = Cut-off',ion_mdp,flags=re.M)
    (root/'ion-selection-only.mdp').write_text(ion_mdp)
    native(['grompp','-f','ion-selection-only.mdp','-c','solvated.gro','-p','topol.top','-o','ions.tpr'],'02-grompp-ion-selection.log')
    native(['genion','-s','ions.tpr','-o','ionized.gro','-p','topol.top','-pname','SOD','-nname','CLA','-neutral','-conc',str(request.added_NaCl_molar),'-seed',str(request.seed)],'03-genion.log','SOL\n')
    native(['grompp','-f',request.em_mdp,'-c','ionized.gro','-p','topol.top','-o','em.tpr','-po','em-resolved.mdp'],'04-grompp-EM.log')
    native(['mdrun','-deffnm','em','-ntmpi','1','-ntomp',str(request.cpu_threads),'-nb','gpu','-gpu_id',str(request.gpu_id)],'05-native-EM.log')
    result=dict(recipe_id=request.recipe_id,lipid_molecules=sum(counts.values()),lipid_atoms=natoms,lipid_charge_e=charge,
        water_before_ions=waters,final_molecules=(root/'topol.top').read_text().split('[ molecules ]')[-1],
        initial_geometry=dict(source=request.source_geometry_gro,area_per_lipid_nm2=area_per_lipid,box_nm=[edge,edge,request.initial_box_z_nm],
            phosphate_planes_relative_nm=planes.tolist(),measured_or_equilibrated_thickness=False),
        **em_diagnostic((root/'05-native-EM.log').read_text(),(root/'em-resolved.mdp').read_text()),commands=commands,
        scope='authorized_reduced_bare_reference_not_complete_project_membrane_anchor_or_M2',production_executed=False)
    (root/'native-preparation.json').write_text(json.dumps(result,indent=2))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--request',type=Path,required=True);args=parser.parse_args()
    print(json.dumps(build_reference(ReferenceMembraneInput(**json.loads(args.request.read_text())))),flush=True)


if __name__=='__main__':main()
