"""Standalone Python 3.8 adapter for the published CALVADOS3 IDR functions.

Run this file in the separately installed original author environment. Forces,
particle masses, protonation and initial spiral come from unmodified upstream
functions, not the newer CALVADOS package. Isolated-chain results do not prove
fusion LLPS. The original free peptide termini are retained explicitly.
"""
import argparse
import csv
from dataclasses import asdict, dataclass
from hashlib import sha256
from importlib.metadata import version
import json
import math
from pathlib import Path
import sys


@dataclass
class AuthorIDRRequest:
    candidate_id: str
    sequence: str
    author_source: str
    author_commit: str
    output_dir: str
    temperature_kelvin: float
    pH: float
    ionic_strength_molar: float
    box_edge_nm: float
    timestep_ps: float
    friction_per_ps: float
    ah_cutoff_nm: float
    dh_cutoff_nm: float
    eps_factor: float
    seed: int
    equilibration_steps: int
    production_steps: int
    save_interval_steps: int
    checkpoint_interval_steps: int
    gpu_id: int
    expected_openmm_version: str
    terminal_state: str
    protocol_reference: str

    def validate(self):
        if len(self.sequence) < 2 or set(self.sequence) - set('ACDEFGHIKLMNPQRSTVWY'):
            raise ValueError('author_IDR_route_requires_complete_standard_sequence')
        if self.author_commit != '51564e0edd126c44d6a7299fbe4414c579394ef4':
            raise ValueError('published_author_source_commit_required')
        if self.terminal_state != 'original_isolated_peptide_free_termini':
            raise ValueError('original_author_termini_are_not_internal_fusion_fragment_termini')
        if self.dh_cutoff_nm != 4.0 or self.eps_factor != 0.2:
            raise ValueError('unsupported_change_to_published_native_force_parameters')
        if not all(math.isfinite(x) and x > 0 for x in (
            self.temperature_kelvin, self.ionic_strength_molar, self.box_edge_nm,
            self.timestep_ps, self.friction_per_ps, self.ah_cutoff_nm)) or not math.isfinite(self.pH):
            raise ValueError('native_physical_parameters_require_finite_values')
        if self.box_edge_nm <= 2 * max(self.ah_cutoff_nm, self.dh_cutoff_nm):
            raise ValueError('periodic_box_too_small_for_declared_native_cutoffs')
        counts = (self.seed, self.production_steps, self.save_interval_steps, self.checkpoint_interval_steps)
        if any(type(x) is not int or x <= 0 for x in counts) or type(self.equilibration_steps) is not int or self.equilibration_steps < 0:
            raise ValueError('steps_and_seed_require_explicit_integers')
        if not self.protocol_reference or type(self.gpu_id) is not int or self.gpu_id < 0:
            raise ValueError('protocol_and_explicit_GPU_required')
        return self


def build_native_system(request):
    """Reuse author CA/IDR forces, excluding all domain/slab approximations."""
    request.validate()
    if version('OpenMM') != request.expected_openmm_version:
        raise ValueError('original_OpenMM_environment_version_mismatch')
    source = Path(request.author_source).resolve()
    sys.path.insert(0, str(source))
    import utils as native
    import pandas as pd
    import numpy as np
    from openmm import unit, app

    residues = pd.read_csv(source / 'residues_pub.csv').set_index('one', drop=False)
    residues['lambdas'] = residues['CALVADOS3']
    prot = pd.Series(dict(fasta=list(request.sequence), pH=request.pH,
                          ionic=request.ionic_strength_molar, temp=request.temperature_kelvin,
                          eps_factor=request.eps_factor), name=request.candidate_id)
    lj_eps, _, _, _ = native.genParamsLJ(residues, request.candidate_id, prot)
    dh_eps, kappa = native.genParamsDH(residues, request.candidate_id, prot, request.temperature_kelvin)
    system = native.openmm.System()
    system.setDefaultPeriodicBoxVectors(*native.build_box(*([request.box_edge_nm] * 3)))
    native.add_particles(system, residues, prot)
    forces = native.set_interactions(system, residues, prot, lj_eps, request.ah_cutoff_nm,
                                    kappa, dh_eps, len(request.sequence), CoarseGrained='CA', isIDP=True)
    for force in forces:
        system.addForce(force)
    topology = native.build_topology(list(request.sequence))
    positions = native.xy_spiral_array(len(request.sequence)) + np.array([request.box_edge_nm / 2] * 3)
    metadata = dict(parameter_column='CALVADOS3', author_commit=request.author_commit,
                    original_peptide_termini=True, kappa_inverse_nm=float(kappa),
                    native_masses_dalton=[system.getParticleMass(i).value_in_unit(unit.dalton) for i in range(system.getNumParticles())],
                    source_hashes={name: sha256((source / name).read_bytes()).hexdigest()
                                   for name in ('utils.py', 'misc_tools.py', 'residues_pub.csv')})
    return native, app, unit, system, topology, positions, metadata


def run(request):
    native, app, unit, system, topology, positions, metadata = build_native_system(request)
    import mdtraj as md
    output = Path(request.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest = output / 'request.json'
    identity = asdict(request)
    if manifest.exists():
        if json.loads(manifest.read_text()) != identity:
            raise ValueError('existing_author_job_has_different_input_do_not_overwrite')
    elif any(output.iterdir()):
        raise ValueError('new_author_job_requires_empty_output_directory')
    else:
        manifest.write_text(json.dumps(identity, indent=2))
        (output / 'native-system.json').write_text(json.dumps(metadata, indent=2))
        md.Trajectory(positions, topology, 0, [request.box_edge_nm] * 3, [90] * 3).save_pdb(str(output / 'top.pdb'))
        (output / 'system.xml').write_text(native.openmm.XmlSerializer.serialize(system))
    state_path = output / 'execution.json'
    previous = json.loads(state_path.read_text()) if state_path.exists() else None
    if previous and previous['status'] == 'completed':
        return previous
    integrator = native.openmm.LangevinIntegrator(request.temperature_kelvin * unit.kelvin,
                                                 request.friction_per_ps / unit.picosecond,
                                                 request.timestep_ps * unit.picosecond)
    integrator.setRandomNumberSeed(request.seed)
    pdb = app.PDBFile(str(output / 'top.pdb'))
    simulation = app.Simulation(pdb.topology, system, integrator,
                                native.openmm.Platform.getPlatformByName('CUDA'),
                                {'DeviceIndex': str(request.gpu_id)})
    checkpoint = output / 'checkpoint.chk'
    if previous:
        if not checkpoint.exists():
            raise ValueError('interrupted_author_job_has_no_checkpoint')
        simulation.loadCheckpoint(str(checkpoint))
        # Checkpoint stores the actual integrator step, never repeat full budget.
        # OpenMM 7.6 checkpoints expose time, not State.getStepCount (newer API).
        completed = int(round(simulation.context.getState().getTime().value_in_unit(unit.picosecond)
                              / request.timestep_ps))
        simulation.currentStep = completed
    else:
        simulation.context.setPositions(pdb.positions)
        simulation.minimizeEnergy()
        simulation.context.setVelocitiesToTemperature(request.temperature_kelvin * unit.kelvin, request.seed)
        completed = 0
    total = request.equilibration_steps + request.production_steps
    if completed > total:
        raise ValueError('native_checkpoint_exceeds_declared_total_budget')
    trajectory = output / 'trajectory.dcd'
    if previous and trajectory.exists():
        with md.formats.DCDTrajectoryFile(str(trajectory), 'r') as saved:
            if len(saved) != completed // request.save_interval_steps:
                raise ValueError('trajectory_checkpoint_step_mismatch_requires_explicit_reconciliation')
    simulation.reporters.append(app.DCDReporter(str(trajectory), request.save_interval_steps,
                                               enforcePeriodicBox=False, append=trajectory.exists()))
    log_stream = (output / 'state.log').open('a' if previous else 'w')
    simulation.reporters.append(app.StateDataReporter(log_stream, request.save_interval_steps,
                                step=True, potentialEnergy=True, kineticEnergy=True, temperature=True,
                                speed=True, elapsedTime=True))
    state = dict(status='running',completed_steps=completed,total_steps=total,
                 equilibration_steps=request.equilibration_steps,production_steps=request.production_steps,
                 seed=request.seed,scientific_convergence=None,
                 scope='original_CALVADOS3_isolated_IDR_not_fusion_LLPS_or_project_measurement')
    while completed < total:
        state['status'] = 'equilibrating' if completed < request.equilibration_steps else 'production'
        state_path.write_text(json.dumps(state, indent=2))
        boundary = request.equilibration_steps if completed < request.equilibration_steps else total
        simulation.step(min(request.checkpoint_interval_steps, boundary - completed))
        log_stream.flush()
        completed = simulation.currentStep
        temporary = output / 'checkpoint.next'
        simulation.saveCheckpoint(str(temporary))
        temporary.replace(checkpoint)
        state['completed_steps'] = completed
        state_path.write_text(json.dumps(state, indent=2))
    state['status'] = 'completed'
    state_path.write_text(json.dumps(state, indent=2))
    log_stream.close()
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(AuthorIDRRequest(**json.loads(args.request.read_text())))), flush=True)


def export_observations(output_dir):
    """Export every saved native frame; do not assert equilibration or LLPS."""
    import mdtraj as md
    import numpy as np
    root = Path(output_dir)
    request = AuthorIDRRequest(**json.loads((root / 'request.json').read_text())).validate()
    state = json.loads((root / 'execution.json').read_text())
    total = request.equilibration_steps + request.production_steps
    if state['status'] != 'completed' or state['completed_steps'] != total:
        raise ValueError('author_CG_requires_completed_declared_budget_before_export')
    metadata = json.loads((root / 'native-system.json').read_text())
    masses = np.asarray(metadata['native_masses_dalton'], dtype=float)
    if len(masses) != len(request.sequence) or not np.all(np.isfinite(masses)) or np.any(masses <= 0):
        raise ValueError('author_CG_native_masses_do_not_match_full_sequence')
    target = root / 'observations.csv'
    if target.exists():
        raise ValueError('author_CG_observations_already_exist_do_not_overwrite')
    temporary = target.with_suffix('.next')
    frame = 0
    with temporary.open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(('candidate_id', 'seed', 'step', 'time_ns', 'phase', 'mass_weighted_Rg_nm', 'end_to_end_nm'))
        for chunk in md.iterload(str(root / 'trajectory.dcd'), top=str(root / 'top.pdb'), chunk=100):
            if chunk.n_atoms != len(masses) or chunk.topology.n_chains != 1:
                raise ValueError('author_CG_native_trajectory_is_not_one_complete_IDR')
            for xyz, box in zip(chunk.xyz, chunk.unitcell_vectors):
                lengths = np.diag(box)
                if np.any(lengths <= 0) or not np.allclose(box, np.diag(lengths), atol=1e-7):
                    raise ValueError('author_CG_observations_require_orthorhombic_native_box')
                bonds = np.diff(xyz.astype(float), axis=0)
                bonds -= np.rint(bonds / lengths) * lengths
                if np.any(np.linalg.norm(bonds, axis=1) >= min(lengths) / 2):
                    raise ValueError('author_CG_chain_unwrapping_ambiguous')
                whole = np.vstack((xyz[0], xyz[0] + np.cumsum(bonds, axis=0)))
                center = np.average(whole, axis=0, weights=masses)
                rg = float(np.sqrt(np.average(np.sum((whole - center) ** 2, axis=1), weights=masses)))
                re = float(np.linalg.norm(whole[-1] - whole[0]))
                frame += 1
                step = frame * request.save_interval_steps
                writer.writerow((request.candidate_id, request.seed, step, step * request.timestep_ps / 1000,
                    'equilibration' if step <= request.equilibration_steps else 'production', rg, re))
    if frame != total // request.save_interval_steps:
        raise ValueError('author_CG_frame_count_differs_from_full_native_budget')
    temporary.replace(target)
    result = dict(candidate_id=request.candidate_id, seed=request.seed, frames=frame,
        production_frames=frame - request.equilibration_steps // request.save_interval_steps,
        pH=request.pH, temperature_kelvin=request.temperature_kelvin,
        effective_ionic_strength_molar=request.ionic_strength_molar,
        observations_file=str(target), coordinate_unit='nm', time_unit='ns',
        scope='native_isolated_chain_Rg_Re_not_LLPS_slab_or_internal_fusion',
        scientific_convergence=None, formal_M1_pass=False)
    (root / 'observations.json').write_text(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    main()
