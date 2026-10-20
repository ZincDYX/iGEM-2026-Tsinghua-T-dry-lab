"""Native project CG jobs, not shortened author benchmarks or ranking scores.

CALVADOS owns its forces and integrator. Mpipi uses the unchanged 2021 author
force file. Project conditions and initial geometry must be reviewed inputs.
No scheduler, force-field reimplementation or implicit phase classifier lives
here. Use the existing external-process runtime for long jobs.
"""
import argparse
from hashlib import sha256
from importlib.metadata import version
import json
import math
from pathlib import Path
import re
import subprocess
import zipfile

from pydantic import Field, model_validator
import yaml

from .design_analysis import ScientificAnalysisInput
from .mpipi import AUTHOR_MD5, AUTHOR_URL


class CalvadosProjectInput(ScientificAnalysisInput):
    candidate_id: str = Field(pattern=r"^[A-Za-z0-9_.-]+$")
    sequence: str = Field(min_length=1, pattern=r"^[ACDEFGHIKLMNPQRSTVWY]+$")
    output_dir: Path
    config: dict
    component: dict
    expected_native_version: str
    protocol_reference: str = Field(min_length=1)
    force_field_reference: str = Field(min_length=1)
    native_defaults_review_reference: str = Field(min_length=1)

    @model_validator(mode="after")
    def explicit_protocol(self):
        required={'box','temp','ionic','pH','topol','eps_lj','cutoff_lj','cutoff_yu',
                  'friction_coeff','wfreq','random_number_seed','platform','restart'}
        if not required <= self.config.keys():
            raise ValueError('CALVADOS_project_requires_explicit_physical_and_runtime_conditions')
        if (self.config.get('steps') is None)==(self.config.get('runtime') is None):
            raise ValueError('CALVADOS_project_requires_one_explicit_duration_no_100M_step_default')
        if not {'nmol','charge_termini','restraint','molecule_type','fresidues'} <= self.component.keys():
            raise ValueError('CALVADOS_project_requires_explicit_component_and_force_field')
        if self.component['molecule_type']!='protein':
            raise ValueError('project_sequence_route_requires_protein')
        return self


def prepare_calvados_project(payload: CalvadosProjectInput):
    """Run in the separately installed native CALVADOS environment."""
    from calvados.inputmodels import SimulationInput, ComponentInput
    if version('calvados')!=payload.expected_native_version:
        raise ValueError('CALVADOS_installed_native_version_differs_from_reviewed_protocol')
    config=SimulationInput.model_validate({**payload.config,'sysname':payload.candidate_id})
    output=payload.output_dir.resolve()
    output.mkdir(parents=True,exist_ok=True)
    manifest=output/'project-input.json'
    if manifest.exists():
        if json.loads(manifest.read_text())!=payload.model_dump(mode='json'):
            raise ValueError('existing_CG_job_has_different_protocol_do_not_overwrite')
        return json.loads((output/'prepared.json').read_text())
    if any(output.iterdir()):
        raise ValueError('CALVADOS_new_job_requires_empty_output_directory')
    fasta=output/'input.fasta'
    # Native restraint mode obtains sequence from the supplied structure; verify
    # that sequence below using the author's component, never quietly use it.
    component=ComponentInput.model_validate({**payload.component,'name':payload.candidate_id,'ffasta':str(fasta)})
    residues=Path(component.fresidues).resolve()
    if not residues.is_file():raise ValueError('CALVADOS_reviewed_native_residue_table_missing')
    component=component.model_copy(update={'fresidues':str(residues)})
    fasta.write_text('>'+payload.candidate_id+'\n'+payload.sequence+'\n')
    native_components={'defaults':{},'system':{payload.candidate_id:component.model_dump(mode='json',exclude={'name'})}}
    from calvados.sim import Sim
    simulator=Sim(output,config.model_dump(),native_components)
    simulator.make_components()
    if len(simulator.components)!=1 or ''.join(simulator.components[0].seq)!=payload.sequence:
        raise ValueError('CALVADOS_native_component_does_not_match_complete_project_sequence')
    (output/'config.yaml').write_text(yaml.safe_dump(config.model_dump(mode='json')))
    (output/'components.yaml').write_text(yaml.safe_dump(native_components))
    result=dict(method='native_CALVADOS_project',candidate_id=payload.candidate_id,
        sequence_length=len(payload.sequence),native_version=version('calvados'),
        config=config.model_dump(mode='json'),components=native_components,
        force_field_reference=payload.force_field_reference,protocol_reference=payload.protocol_reference,
        native_defaults_review_reference=payload.native_defaults_review_reference,
        residue_table_sha256=sha256(residues.read_bytes()).hexdigest(),
        native_bead_masses_dalton=list(map(float,simulator.components[0].mws)),
        nmol=component.nmol,
        requested_steps=config.steps,requested_runtime_hours=config.runtime,
        scope='prepared_exact_project_input_not_executed_or_validated_LLPS')
    (output/'prepared.json').write_text(json.dumps(result,indent=2))
    manifest.write_text(payload.model_dump_json(indent=2))
    return result


def execute_calvados_project(payload: CalvadosProjectInput):
    prepared=prepare_calvados_project(payload)
    output=payload.output_dir.resolve();state_file=output/'execution.json'
    if state_file.exists():
        state=json.loads(state_file.read_text())
        if state['status']=='completed_native_call':return state
        # Native checkpoint resumes append trajectories; arbitrary reruns could
        # reset positions or repeat a full step budget. Require explicit recovery.
        raise ValueError('CALVADOS_interrupted_job_needs_reviewed_checkpoint_continuation_not_blind_rerun')
    state=dict(status='running',method=prepared['method'],requested_steps=prepared['requested_steps'],
        requested_runtime_hours=prepared['requested_runtime_hours'])
    state_file.write_text(json.dumps(state,indent=2))
    from calvados import sim
    try:
        sim.run(path=str(output),fconfig='config.yaml',fcomponents='components.yaml')
    except Exception as error:
        state.update(status='failed_native_call',error_type=type(error).__name__)
        state_file.write_text(json.dumps(state,indent=2))
        raise
    if not (output/'top.pdb').is_file() or not (output/(payload.candidate_id+'.dcd')).is_file():
        raise ValueError('CALVADOS_native_call_missing_topology_or_trajectory')
    state['status']='completed_native_call';state['scientific_acceptance']=None
    state_file.write_text(json.dumps(state,indent=2))
    return state


class MpipiProjectInput(ScientificAnalysisInput):
    """Original force file plus explicitly reviewed full-chain starting geometry."""
    candidate_id: str
    sequence: str = Field(min_length=1, pattern=r"^[ACDEFGHIKLMNPQRSTVWY]+$")
    output_dir: Path
    author_archive: Path
    executable: Path
    initial_coordinates_angstrom: list[list[list[float]]] = Field(min_length=1)
    residue_parameters: dict[str, dict[str, float | int]]
    box_bounds_angstrom: list[tuple[float,float]] = Field(min_length=3,max_length=3)
    temperature_kelvin: float = Field(gt=0)
    random_seed: int = Field(ge=1)
    timestep_femtoseconds: float = Field(gt=0)
    damping_femtoseconds: float = Field(gt=0)
    dielectric: float = Field(gt=0)
    neighbor_skin_angstrom: float = Field(gt=0)
    neighbor_every_steps: int = Field(gt=0)
    neighbor_delay_steps: int = Field(ge=0)
    special_bonds_lj_coul: tuple[float,float,float,float,float,float]
    minimization_stages: list[dict]
    equilibration_steps: int = Field(ge=0)
    production_steps: int = Field(gt=0)
    trajectory_interval_steps: int = Field(gt=0)
    thermo_interval_steps: int = Field(gt=0)
    protocol_reference: str = Field(min_length=1)
    residue_mapping_reference: str = Field(min_length=1)
    initial_geometry_reference: str = Field(min_length=1)

    @model_validator(mode='after')
    def complete_geometry(self):
        if any(not math.isfinite(v) or not 0<=v<=1 for v in self.special_bonds_lj_coul):
            raise ValueError('Mpipi_special_bond_factors_require_finite_values_in_zero_to_one')
        if any(len(chain)!=len(self.sequence) for chain in self.initial_coordinates_angstrom):
            raise ValueError('Mpipi_initial_geometry_must_cover_each_complete_chain')
        if any(not math.isfinite(v) for pair in self.box_bounds_angstrom for v in pair) or any(lo>=hi for lo,hi in self.box_bounds_angstrom):
            raise ValueError('Mpipi_box_requires_ordered_finite_bounds')
        for chain in self.initial_coordinates_angstrom:
            for point in chain:
                if len(point)!=3 or any(not math.isfinite(v) or not lo<=v<=hi for v,(lo,hi) in zip(point,self.box_bounds_angstrom)):
                    raise ValueError('Mpipi_initial_coordinates_must_be_finite_and_inside_declared_box')
        if set(self.sequence)-self.residue_parameters.keys():raise ValueError('Mpipi_reviewed_residue_mapping_incomplete')
        for row in self.residue_parameters.values():
            if set(row)!={'type','mass','charge'} or not isinstance(row['type'],int) or not 1<=row['type']<=20 or row['mass']<=0 or not all(math.isfinite(v) for v in row.values()):
                raise ValueError('Mpipi_requires_original_20_type_mass_charge_mapping')
        if len({row['type'] for row in self.residue_parameters.values()})!=len(self.residue_parameters):
            raise ValueError('Mpipi_residue_type_mapping_must_be_one_to_one')
        return self


def prepare_mpipi_project(payload: MpipiProjectInput):
    from hashlib import md5
    if md5(payload.author_archive.read_bytes()).hexdigest()!=AUTHOR_MD5:
        raise ValueError('original_Mpipi_author_archive_mismatch')
    if set(payload.residue_parameters)!=set('ACDEFGHIKLMNPQRSTVWY'):
        raise ValueError('Mpipi_original_force_file_requires_all_20_reviewed_types')
    output=payload.output_dir.resolve();output.mkdir(parents=True,exist_ok=True)
    if any(output.iterdir()):raise ValueError('Mpipi_new_project_requires_empty_output_directory')
    with zipfile.ZipFile(payload.author_archive) as packed:
        force=packed.read('fig5-phase-diagrams/example-simulation/set_pair_param-Mpipi.dat')
    charges={int(t):float(q) for t,q in re.findall(r'set\s+type\s+(\d+)\s+charge\s+([\d.+-]+)',force.decode())}
    for row in payload.residue_parameters.values():
        if not math.isclose(row['charge'],charges.get(row['type'],0.),abs_tol=1e-12):
            raise ValueError('Mpipi_project_charge_mapping_differs_from_unchanged_original_force_file')
    (output/'set_pair_param-Mpipi.dat').write_bytes(force)
    chains=payload.initial_coordinates_angstrom;n=len(payload.sequence)
    # The original include refers to 40 types (20 protein and 20 paired types).
    # Keep that original type capacity even when the latter have zero atoms.
    data=['LAMMPS exact project chains; explicitly reviewed coordinates', '',f'{n*len(chains)} atoms',f'{(n-1)*len(chains)} bonds','40 atom types','1 bond types','']
    data += [f'{lo:.17g} {hi:.17g} {axis}lo {axis}hi' for axis,(lo,hi) in zip('xyz',payload.box_bounds_angstrom)]
    data+=['','Masses','']+[f"{row['type']+offset} {row['mass']:.17g}" for offset in (0,20) for row in sorted(payload.residue_parameters.values(),key=lambda r:r['type'])]
    data+=['','Atoms # full','']
    for chain_id,chain in enumerate(chains,1):
        for i,(aa,xyz) in enumerate(zip(payload.sequence,chain),1):
            row=payload.residue_parameters[aa]
            data.append(f"{(chain_id-1)*n+i} {chain_id} {row['type']} {row['charge']:.17g} "+' '.join(f'{v:.17g}' for v in xyz))
    data+=['','Bonds','']
    for chain_id in range(len(chains)):
        data += [f'{chain_id*(n-1)+i} 1 {chain_id*n+i} {chain_id*n+i+1}' for i in range(1,n)]
    (output/'input-structure.dat').write_text('\n'.join(data)+'\n')
    # Force and bond coefficients come only from the unchanged author include.
    # No author minimization/phase-preparation protocol is secretly inserted.
    script=f'''units real
atom_style full
boundary p p p
bond_style harmonic
read_data input-structure.dat
include set_pair_param-Mpipi.dat
dielectric {payload.dielectric:.17g}
neighbor {payload.neighbor_skin_angstrom:.17g} multi
neigh_modify every {payload.neighbor_every_steps} delay {payload.neighbor_delay_steps}
special_bonds lj {' '.join(f'{v:.17g}' for v in payload.special_bonds_lj_coul[:3])} coul {' '.join(f'{v:.17g}' for v in payload.special_bonds_lj_coul[3:])}
timestep {payload.timestep_femtoseconds:.17g}
velocity all create {payload.temperature_kelvin:.17g} {payload.random_seed}
fix thermostat all langevin {payload.temperature_kelvin:.17g} {payload.temperature_kelvin:.17g} {payload.damping_femtoseconds:.17g} {payload.random_seed}
fix integrator all nve
thermo {payload.thermo_interval_steps}
run {payload.equilibration_steps}
dump project all custom {payload.trajectory_interval_steps} project.lammpstrj id mol type x y z ix iy iz
dump_modify project sort id
run {payload.production_steps}
write_restart final.restart
'''
    stages=[]
    for stage in payload.minimization_stages:
        if set(stage)!={'timestep_femtoseconds','energy_tolerance','force_tolerance','max_iterations','max_evaluations'}:
            raise ValueError('Mpipi_minimization_requires_explicit_native_FIRE_parameters')
        if any(not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in stage.values()):
            raise ValueError('Mpipi_minimization_parameters_must_be_finite_nonnegative_numbers')
        if not all(isinstance(stage[k],int) and stage[k]>0 for k in ('max_iterations','max_evaluations')) or stage['timestep_femtoseconds']<=0:
            raise ValueError('Mpipi_minimization_requires_positive_integer_limits_and_timestep')
        stages.append('min_style fire\ntimestep '+str(stage['timestep_femtoseconds'])+'\nminimize '+ ' '.join(str(stage[k]) for k in ('energy_tolerance','force_tolerance','max_iterations','max_evaluations')))
    if stages:
        script=script.replace('fix thermostat', '\n'.join(stages)+'\ntimestep '+str(payload.timestep_femtoseconds)+'\nfix thermostat',1)
    (output/'input-script.dat').write_text(script)
    (output/'project-input.json').write_text(payload.model_dump_json(indent=2))
    return dict(method='Mpipi_original_2021_project',candidate_id=payload.candidate_id,
        sequence_length=n,chains=len(chains),source_url=AUTHOR_URL,
        force_file_sha256=sha256(force).hexdigest(),scope='prepared_original_force_field_not_project_LLPS_acceptance')


def execute_mpipi_project(payload: MpipiProjectInput):
    result=prepare_mpipi_project(payload);output=payload.output_dir.resolve()
    command=[str(payload.executable.resolve()),'-in','input-script.dat']
    state_file=output/'execution.json'
    state=dict(**result,status='running',command=command)
    state_file.write_text(json.dumps(state,indent=2))
    with (output/'native-console.log').open('w') as log:
        completed=subprocess.run(command,cwd=output,stdout=log,stderr=subprocess.STDOUT,check=False)
    state.update(status='completed_native_call' if completed.returncode==0 else 'failed',returncode=completed.returncode)
    state_file.write_text(json.dumps(state,indent=2))
    if completed.returncode:raise ValueError('original_Mpipi_native_project_job_failed')
    if not (output/'final.restart').is_file() or not (output/'project.lammpstrj').is_file():
        raise ValueError('original_Mpipi_project_missing_requested_native_outputs')
    return state


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',choices=('calvados','mpipi'),required=True)
    parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--prepare-only',action='store_true')
    args=parser.parse_args()
    contract,prepare,execute=(CalvadosProjectInput,prepare_calvados_project,execute_calvados_project) if args.engine=='calvados' else (MpipiProjectInput,prepare_mpipi_project,execute_mpipi_project)
    payload=contract.model_validate_json(args.request.read_text())
    print(json.dumps((prepare if args.prepare_only else execute)(payload)))


if __name__=='__main__':main()
