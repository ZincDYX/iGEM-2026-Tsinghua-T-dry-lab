"""Prepare the declared S59/C36 standard-mass bare ER reference, not anchor MD.

This is a trusted backend CLI. Keep the original third-party inputs separately;
all edits affect a new derived directory. Do not use original HMR/pore-pulling
settings or pretend a prepared bare membrane validates ER fusion orientation.
"""
import argparse
import csv
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import tarfile


@dataclass
class ERReferencePreparation:
    source_directory: str
    charmm_archive: str
    em_mdp: str
    gmx_executable: str
    output_directory: str
    initial_box_nm: list[float]
    target_water_molecules: int
    original_counterions: int
    added_NaCl_molar: float
    ion_placement_seed: int
    cpu_threads: int
    protocol_reference: str


def prepare_reference(request: ERReferencePreparation):
    """Standard masses from fixed official atom types; no new force parameters."""
    if len(request.initial_box_nm)!=3 or any(not math.isfinite(x) or x<=0 for x in request.initial_box_nm):
        raise ValueError('ER_reference_requires_explicit_finite_positive_box')
    if not math.isfinite(request.added_NaCl_molar) or request.added_NaCl_molar<0 or request.cpu_threads<1 or request.ion_placement_seed<1:
        raise ValueError('ER_reference_salt_and_runtime_values_invalid')
    original, output = Path(request.source_directory), Path(request.output_directory)
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError('ER_reference_preparation_requires_new_directory')
    with tarfile.open(request.charmm_archive) as archive:
        archive.extractall(output, filter='data')
    ff = next(output.glob('charmm36-jul2022.ff'))
    atomtypes, section = {}, ''
    for line in (ff/'ffnonbonded.itp').read_text().splitlines():
        value = line.split(';',1)[0].strip()
        if value.startswith('['):
            section = value.strip('[] ').strip()
        elif section == 'atomtypes' and value and not value.startswith('#'):
            fields = value.split()
            atomtypes[fields[0]] = float(fields[2])
    restorations = []
    for path in original.glob('*.itp'):
        if path.name in {'forcefield_all.itp','SOD.itp','tip3p.itp'}:
            continue
        lines, section, before, after = [], '', 0., 0.
        for line in path.read_text().splitlines():
            value = line.split(';',1)[0].strip()
            if value.startswith('['):
                section = value.strip('[] ').strip()
            elif section == 'atoms' and value and not value.startswith('#'):
                fields = value.split()
                old, mass = float(fields[7]), atomtypes[fields[1]]
                before += old
                after += mass
                if old != mass:
                    restorations.append(dict(file=path.name, atom=fields[4], atom_type=fields[1],
                                             old_mass=old, official_mass=mass))
                fields[7] = str(mass)
                line = ' '.join(fields) + ((' ;'+line.split(';',1)[1]) if ';' in line else '')
            lines.append(line)
        if abs(before-after) >= .05:
            raise ValueError('restored_lipid_mass_differs_beyond_source_rounding_review_required')
        (output/path.name).write_text('\n'.join(lines)+'\n')
    top = (original/'topol.top').read_text()
    top = top.replace('#include "./forcefield_all.itp"', f'#include "{ff.name}/forcefield.itp"')
    top = top.replace('#include "./tip3p.itp"', f'#include "{ff.name}/tip3p.itp"')
    top = top.replace('#include "./SOD.itp"', f'#include "{ff.name}/ions.itp"')
    (output/'topol.top').write_text(top)
    shutil.copyfile(original/'confin.gro', output/'source.gro')
    source_molecules = top.split('[ molecules ]')[-1]
    source_water = sum(map(int, re.findall(r'^\s*SOL\s+(\d+)\s*$',source_molecules,re.M)))
    source_counterions = sum(map(int,re.findall(r'^\s*SOD\s+(\d+)\s*$',source_molecules,re.M)))
    if source_counterions != request.original_counterions:
        raise ValueError('original_counterion_count_does_not_match_source_topology')
    additional_water = request.target_water_molecules-source_water
    if additional_water < 0:
        raise ValueError('declared_target_cannot_silently_remove_original_waters')
    commands = []
    def native(arguments, log_name, input_text=None):
        command = [request.gmx_executable, *arguments]
        commands.append(command)
        with (output/log_name).open('w') as log:
            subprocess.run(command, cwd=output, input=input_text, text=True,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
    native(['editconf','-f','source.gro','-o','boxed.gro','-c','-box',*map(str,request.initial_box_nm)],'01-box.log')
    if additional_water:
        native(['solvate','-cp','boxed.gro','-cs','spc216.gro','-o','solvated.gro','-p','topol.top',
                '-maxsol',str(additional_water)],'02-solvate.log')
    else:
        shutil.copyfile(output/'boxed.gro',output/'solvated.gro')
    top = (output/'topol.top').read_text()
    molecules = top.split('[ molecules ]')[-1]
    if sum(map(int,re.findall(r'^\s*SOL\s+(\d+)\s*$',molecules,re.M))) != request.target_water_molecules:
        raise ValueError('native_solvation_did_not_reach_declared_water_count_review_box')
    gro = (output/'solvated.gro').read_text().splitlines()
    atoms = gro[2:-1]
    ordered = ([a for a in atoms if a[5:10].strip() not in {'SOL','SOD'}]
               + [a for a in atoms if a[5:10].strip()=='SOL']
               + [a for a in atoms if a[5:10].strip()=='SOD'])
    # Change only serialization order/atom serial, preserving intact molecules
    # and coordinates. Native genion requires a continuous solvent group.
    (output/'solvated.gro').write_text('\n'.join(gro[:2]+[
        line[:15]+f'{i%100000:5d}'+line[20:] for i,line in enumerate(ordered,1)]+[gro[-1]])+'\n')
    start = top.index('[ molecules ]')
    nonwater = [line for line in top[start:].splitlines()[1:] if line.strip()
                and not line.lstrip().startswith(';') and line.split()[0] not in {'SOL','SOD'}]
    (output/'topol.top').write_text(top[:start]+'[ molecules ]\n'+'\n'.join(nonwater)
        +f'\nSOL {request.target_water_molecules}\nSOD {request.original_counterions}\n')
    native(['grompp','-f',request.em_mdp,'-c','solvated.gro','-p','topol.top','-o','ions.tpr','-po','ions-resolved.mdp'],'03-grompp-ions.log')
    native(['genion','-s','ions.tpr','-o','ionized.gro','-p','topol.top','-pname','SOD','-nname','CLA',
            '-neutral','-conc',str(request.added_NaCl_molar),'-seed',str(request.ion_placement_seed)],'04-genion.log','SOL\n')
    native(['grompp','-f',request.em_mdp,'-c','ionized.gro','-p','topol.top','-o','em.tpr','-po','em-resolved.mdp'],'05-grompp-em.log')
    native(['mdrun','-deffnm','em','-ntmpi','1','-ntomp',str(request.cpu_threads),'-nb','cpu'],'06-EM-console.log')
    with (output/'mass-restoration.csv').open('w',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=['file','atom','atom_type','old_mass','official_mass'])
        writer.writeheader()
        writer.writerows(restorations)
    force = re.search(r'Maximum force\s*=\s*([0-9.eE+-]+)',(output/'06-EM-console.log').read_text())
    emtol = re.search(r'^\s*emtol\s*=\s*([0-9.eE+-]+)',(output/'em-resolved.mdp').read_text(),re.M)
    force_value, target = float(force[1]) if force else None, float(emtol[1]) if emtol else None
    result = dict(method='S59_derived_standard_mass_C36_ER_reference',mass_restorations=len(restorations),
                  max_force_kJ_mol_nm=force_value, declared_minimization_target_kJ_mol_nm=target,
                  converged_to_declared_EM_target=force_value<=target if force_value is not None and target is not None else None,
                  forcefield=ff.name,
                  protocol_reference=request.protocol_reference,commands=commands,production_executed=False,
                  water_before_genion=request.target_water_molecules,
                  initial_box_nm=request.initial_box_nm,added_NaCl_molar=request.added_NaCl_molar,
                  ion_placement_seed=request.ion_placement_seed,
                  final_molecules=(output/'topol.top').read_text().split('[ molecules ]')[-1],
                  scope='bare_reference_preparation_not_equilibrated_thickness_anchor_MD_or_complete_M2')
    (output/'preparation.json').write_text(json.dumps(result,indent=2))
    (output/'request.json').write_text(json.dumps(request.__dict__,indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(prepare_reference(ERReferencePreparation(**json.loads(args.request.read_text())))))


if __name__ == '__main__':
    main()
