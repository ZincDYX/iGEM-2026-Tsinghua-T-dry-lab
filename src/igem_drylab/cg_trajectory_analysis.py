"""Native CALVADOS DCD -> mass-weighted Rg and raw mass-density bins.

This exports observations only: no slab centering, equilibrium detection, phase
boundaries, fit, partition coefficient or M1 rank is guessed. CALVADOS's native
component supplies masses including its terminal patches. Orthorhombic chains
are made whole by successive bond minimum images for the Rg observation only.
"""
import csv
import json
from pathlib import Path
import numpy as np
from pydantic import Field,model_validator
from .design_analysis import ScientificAnalysisInput


class CalvadosTrajectoryInput(ScientificAnalysisInput):
    output_dir: Path
    first_saved_step: int = Field(ge=0)
    saved_step_interval: int = Field(gt=0)
    z_bin_edges_nm: list[float] = Field(min_length=2)
    coordinate_frame_reference: str = Field(min_length=1)
    observation_output_dir: Path

    @model_validator(mode='after')
    def bins(self):
        if any(a>=b for a,b in zip(self.z_bin_edges_nm,self.z_bin_edges_nm[1:])):
            raise ValueError('CG_density_bin_edges_must_be_strictly_increasing')
        return self


def export_calvados_trajectory(payload: CalvadosTrajectoryInput):
    import mdtraj as md
    from openmm import unit
    root=payload.output_dir.resolve()
    state=json.loads((root/'execution.json').read_text())
    prepared=json.loads((root/'prepared.json').read_text())
    if state['status']!='completed_native_call':raise ValueError('CG_job_not_completed_no_full_trajectory_claim')
    if payload.saved_step_interval!=prepared['config']['wfreq']:
        raise ValueError('CG_saved_step_interval_differs_from_native_reporter')
    masses=np.array(prepared['native_bead_masses_dalton'],dtype=float)
    nmol=prepared['nmol'];length=len(masses)
    if np.any(masses<=0) or not np.all(np.isfinite(masses)):
        raise ValueError('CG_native_bead_masses_invalid')
    output=payload.observation_output_dir.resolve();output.mkdir(parents=True,exist_ok=True)
    density_file=output/'density.csv';rg_file=output/'chain_rg.csv'
    if density_file.exists() or rg_file.exists():raise ValueError('CG_observation_export_exists_do_not_overwrite')
    # Dimension conversion uses the original engine's unit system.
    gram_per_dalton=(1*unit.dalton/unit.AVOGADRO_CONSTANT_NA).value_in_unit(unit.gram)
    edges=np.asarray(payload.z_bin_edges_nm,dtype=float)
    frame_index=0
    with density_file.open('w',newline='') as density_stream,rg_file.open('w',newline='') as rg_stream:
        density=csv.writer(density_stream);density.writerow(('step','lower','upper','density'))
        rg=csv.writer(rg_stream);rg.writerow(('step','chain_index','mass_weighted_Rg_nm'))
        for chunk in md.iterload(str(root/(prepared['candidate_id']+'.dcd')),top=str(root/'top.pdb'),chunk=20):
            if chunk.n_atoms!=length*nmol or any(len(list(chain.atoms))!=length for chain in chunk.topology.chains) or chunk.topology.n_chains!=nmol:
                raise ValueError('CG_native_trajectory_chain_identity_does_not_match_prepared_full_chains')
            for xyz,box in zip(chunk.xyz,chunk.unitcell_vectors):
                if not np.allclose(box,np.diag(np.diag(box)),atol=1e-7) or np.any(np.diag(box)<=0):
                    raise ValueError('CG_observation_route_requires_orthorhombic_positive_box')
                lengths=np.diag(box)
                if not np.isclose(edges[0],0) or not np.isclose(edges[-1],lengths[2]):
                    raise ValueError('CG_density_bins_must_cover_complete_declared_native_z_box')
                step=payload.first_saved_step+frame_index*payload.saved_step_interval
                weights=np.tile(masses,nmol)
                counts=np.histogram(np.mod(xyz[:,2],lengths[2]),bins=edges,weights=weights)[0]
                volume_nm3=lengths[0]*lengths[1]*np.diff(edges)
                rho=counts*gram_per_dalton/(volume_nm3*1e-21)
                for lo,hi,value in zip(edges,edges[1:],rho):density.writerow((step,float(lo),float(hi),float(value)))
                for chain_index in range(nmol):
                    coords=xyz[chain_index*length:(chain_index+1)*length].astype(float)
                    bonds=np.diff(coords,axis=0);bonds-=np.rint(bonds/lengths)*lengths
                    whole=np.vstack((coords[0],coords[0]+np.cumsum(bonds,axis=0)))
                    center=np.average(whole,axis=0,weights=masses)
                    radius=float(np.sqrt(np.average(np.sum((whole-center)**2,axis=1),weights=masses)))
                    rg.writerow((step,chain_index,radius))
                frame_index+=1
    if not frame_index:raise ValueError('CG_native_trajectory_has_no_saved_frames')
    result=dict(method='native_CALVADOS_trajectory_observations',frames=frame_index,chains=nmol,
        density_unit='g/cm3',coordinate_unit='nm',density_profile=str(density_file),chain_rg=str(rg_file),
        first_saved_step=payload.first_saved_step,saved_step_interval=payload.saved_step_interval,
        coordinate_frame_reference=payload.coordinate_frame_reference,
        rg_unwrapping='successive backbone minimum image; requires each bond shorter than half box',
        scope='raw_declared_frame_observations_not_equilibrium_LLPS_validation_or_M1_ranking')
    (output/'observations.json').write_text(json.dumps(result,indent=2))
    return result


class MpipiTrajectoryInput(ScientificAnalysisInput):
    """Read the original engine's saved image flags, no invented unwrapping."""
    output_dir: Path
    z_bin_edges_angstrom: list[float] = Field(min_length=2)
    coordinate_frame_reference: str = Field(min_length=1)
    observation_output_dir: Path

    @model_validator(mode='after')
    def bins(self):
        if any(a>=b for a,b in zip(self.z_bin_edges_angstrom,self.z_bin_edges_angstrom[1:])):
            raise ValueError('CG_density_bin_edges_must_be_strictly_increasing')
        return self


def _mpipi_frames(path):
    with path.open() as stream:
        while True:
            line=stream.readline()
            if not line:return
            if line.strip()!='ITEM: TIMESTEP':raise ValueError('invalid_native_Mpipi_dump_step_header')
            step=int(stream.readline())
            if stream.readline().strip()!='ITEM: NUMBER OF ATOMS':raise ValueError('invalid_native_Mpipi_atom_count_header')
            count=int(stream.readline())
            if stream.readline().strip()!='ITEM: BOX BOUNDS pp pp pp':raise ValueError('Mpipi_profile_requires_native_orthorhombic_periodic_box')
            box=np.array([list(map(float,stream.readline().split())) for _ in range(3)])
            if box.shape!=(3,2) or not np.all(np.isfinite(box)) or np.any(box[:,1]<=box[:,0]):raise ValueError('invalid_Mpipi_box')
            if stream.readline().strip()!='ITEM: ATOMS id mol type x y z ix iy iz':raise ValueError('Mpipi_trajectory_requires_declared_native_coordinate_and_image_columns')
            rows=np.array([list(map(float,stream.readline().split())) for _ in range(count)])
            if rows.shape!=(count,9) or not np.all(np.isfinite(rows)) or not np.array_equal(rows[:,0],np.arange(1,count+1)):
                raise ValueError('Mpipi_native_dump_truncated_or_not_complete_sorted_atom_identity')
            if not np.all(rows[:,[0,1,2,6,7,8]]==np.rint(rows[:,[0,1,2,6,7,8]])):
                raise ValueError('Mpipi_native_atom_ids_types_and_image_flags_must_be_integers')
            yield step,box,rows


def export_mpipi_trajectory(payload: MpipiTrajectoryInput):
    from scipy.constants import Avogadro
    from .coarse_grain_project import MpipiProjectInput
    root=payload.output_dir.resolve();state=json.loads((root/'execution.json').read_text())
    request=MpipiProjectInput.model_validate_json((root/'project-input.json').read_text())
    if state['status']!='completed_native_call' or state['returncode']!=0:
        raise ValueError('Mpipi_job_not_completed_no_full_trajectory_claim')
    length=len(request.sequence);nmol=len(request.initial_coordinates_angstrom)
    expected_types=np.tile([request.residue_parameters[aa]['type'] for aa in request.sequence],nmol)
    masses=np.tile([request.residue_parameters[aa]['mass'] for aa in request.sequence],nmol)
    output=payload.observation_output_dir.resolve();output.mkdir(parents=True,exist_ok=True)
    density_file=output/'density.csv';rg_file=output/'chain_rg.csv'
    if density_file.exists() or rg_file.exists():raise ValueError('CG_observation_export_exists_do_not_overwrite')
    edges=np.array(payload.z_bin_edges_angstrom);count=0;previous=-1
    with density_file.open('w',newline='') as density_stream,rg_file.open('w',newline='') as rg_stream:
        density=csv.writer(density_stream);density.writerow(('step','lower','upper','density'))
        rg=csv.writer(rg_stream);rg.writerow(('step','chain_index','mass_weighted_Rg_angstrom','end_to_end_angstrom'))
        for step,box,rows in _mpipi_frames(root/'project.lammpstrj'):
            if step<=previous or len(rows)!=length*nmol or not np.array_equal(rows[:,2],expected_types) or not np.array_equal(rows[:,1],np.repeat(np.arange(1,nmol+1),length)):
                raise ValueError('Mpipi_frame_must_cover_complete_ordered_project_chains_and_types')
            dimensions=box[:,1]-box[:,0]
            if not np.isclose(edges[0],box[2,0]) or not np.isclose(edges[-1],box[2,1]):raise ValueError('Mpipi_density_bins_must_cover_complete_native_z_box')
            coords=rows[:,3:6]
            weights=np.histogram((coords[:,2]-box[2,0])%dimensions[2]+box[2,0],bins=edges,weights=masses)[0]
            densities=weights/Avogadro/(dimensions[0]*dimensions[1]*np.diff(edges)*1e-24)
            for lo,hi,value in zip(edges,edges[1:],densities):density.writerow((step,float(lo),float(hi),float(value)))
            whole=coords+rows[:,6:9]*dimensions
            for chain in range(nmol):
                xyz=whole[chain*length:(chain+1)*length];mass=masses[chain*length:(chain+1)*length]
                center=np.average(xyz,axis=0,weights=mass)
                radius=float(np.sqrt(np.average(np.sum((xyz-center)**2,axis=1),weights=mass)))
                rg.writerow((step,chain,radius,float(np.linalg.norm(xyz[-1]-xyz[0]))))
            previous=step;count+=1
    if not count:raise ValueError('Mpipi_native_dump_empty')
    result=dict(method='original_Mpipi_native_dump_observations',frames=count,chains=nmol,density_unit='g/cm3',coordinate_unit='angstrom',
        density_profile=str(density_file),chain_rg=str(rg_file),coordinate_frame_reference=payload.coordinate_frame_reference,
        mass_conversion='masses in g/mol divided by SI Avogadro; angstrom^3 to cm^3 factor 1e-24',
        scope='derived_raw_profile_and_native_image_flag_Rg_not_equilibrium_LLPS_M1_rank_or_phase_classification')
    (output/'observations.json').write_text(json.dumps(result,indent=2));return result


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--engine',choices=('calvados','mpipi'),required=True)
    parser.add_argument('--request',type=Path,required=True);args=parser.parse_args()
    contract,handler=(CalvadosTrajectoryInput,export_calvados_trajectory) if args.engine=='calvados' else (MpipiTrajectoryInput,export_mpipi_trajectory)
    print(json.dumps(handler(contract.model_validate_json(args.request.read_text()))))


if __name__=='__main__':main()
