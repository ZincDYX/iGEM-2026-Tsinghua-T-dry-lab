"""Declared-radius sphere unions, not convex hulls mistaken for protein matter.

Count lattice centers inside any sphere once, merging integer x intervals on
each y/z row. No full bounding-box grid allocation, cavity filling or constant
per-enzyme volume. Resolution checks quantify numerical, not biological error.
"""
from collections import defaultdict
import math
import numpy as np
from pydantic import Field
from .design_analysis import ScientificAnalysisInput
from .template_geometry import StructureInput,_hashes


def sphere_union_lattice_volume(coordinates,radii,spacing,origin):
    rows=defaultdict(list)
    for center,radius in zip(coordinates,radii,strict=True):
        lo=np.ceil((center-radius-origin)/spacing).astype(int)
        hi=np.floor((center+radius-origin)/spacing).astype(int)
        for y in range(lo[1],hi[1]+1):
            for z in range(lo[2],hi[2]+1):
                remainder=radius**2-(origin[1]+y*spacing-center[1])**2-(origin[2]+z*spacing-center[2])**2
                if remainder<0:continue
                reach=math.sqrt(remainder)
                first=math.ceil((center[0]-reach-origin[0])/spacing)
                last=math.floor((center[0]+reach-origin[0])/spacing)
                if first<=last:rows[y,z].append((first,last))
    occupied=0
    for intervals in rows.values():
        first,last=sorted(intervals)[0]
        for start,end in sorted(intervals)[1:]:
            if start<=last+1:last=max(last,end)
            else:occupied+=last-first+1;first,last=start,end
        occupied+=last-first+1
    return occupied*spacing**3


class StructureVolumeInput(ScientificAnalysisInput):
    """R numerical geometry; caller supplies radii/probe and fixed grid origin."""
    candidate_id: str
    structure: StructureInput
    element_radii_angstrom: dict[str,float]
    radii_reference: str = Field(min_length=1)
    probe_radius_angstrom: float = Field(ge=0)
    probe_identity: str = Field(min_length=1)
    grid_origin_angstrom: tuple[float,float,float]
    spacings_angstrom: list[float] = Field(min_length=2)
    relative_resolution_target: float = Field(gt=0,lt=1)
    numerical_policy_reference: str = Field(min_length=1)


def calculate_structure_volume(payload: StructureVolumeInput):
    atoms,_=payload.structure.read()
    if not atoms:raise ValueError('volume_requires_actual_atoms')
    if any(a.element not in payload.element_radii_angstrom for a in atoms):raise ValueError('every_present_atom_requires_declared_radius_no_guessing')
    radii=np.array([payload.element_radii_angstrom[a.element] for a in atoms])
    spacings=payload.spacings_angstrom
    if not np.all(np.isfinite(radii)) or np.any(radii<=0) or any(not math.isfinite(s) or s<=0 for s in spacings) or any(a<=b for a,b in zip(spacings,spacings[1:])):
        raise ValueError('volume_requires_positive_radii_and_strictly_refining_grid')
    coordinates=np.array([a.coordinate for a in atoms]);origin=np.array(payload.grid_origin_angstrom)
    observations=[]
    for spacing in spacings:
        material=sphere_union_lattice_volume(coordinates,radii,spacing,origin)
        excluded=sphere_union_lattice_volume(coordinates,radii+payload.probe_radius_angstrom,spacing,origin)
        observations.append(dict(spacing_angstrom=spacing,material_angstrom3=material,probe_excluded_angstrom3=excluded))
    differences={key:abs(observations[-1][key]-observations[-2][key])/observations[-1][key] if observations[-1][key]>0 else None
        for key in ('material_angstrom3','probe_excluded_angstrom3')}
    converged=all(value is not None and value<=payload.relative_resolution_target for value in differences.values())
    from scipy.spatial import ConvexHull
    hull=float(ConvexHull(coordinates).volume) if len(coordinates)>=4 and np.linalg.matrix_rank(coordinates-coordinates.mean(axis=0))==3 else None
    return dict(schema_version='declared_sphere_union_volume_v1',candidate_id=payload.candidate_id,atom_count=len(atoms),
        V_vdw_material_nm3=observations[-1]['material_angstrom3']*1e-3,
        V_probe_excluded_nm3=observations[-1]['probe_excluded_angstrom3']*1e-3,
        atom_center_convex_hull_nm3=hull*1e-3 if hull is not None else None,
        envelope_definition='convex hull of supplied atom centers; includes cage/IDR solvent space, not excluded material',
        explicit_hydrogens_present=any(a.element in {'H','D'} for a in atoms),
        coverage='supplied atoms only; no missing atoms or hydrogen states fabricated',
        probe_identity=payload.probe_identity,probe_radius_angstrom=payload.probe_radius_angstrom,
        radii=payload.element_radii_angstrom,radii_reference=payload.radii_reference,
        grid_origin_angstrom=payload.grid_origin_angstrom,observations=observations,relative_resolution_differences=differences,
        numerical_status='target_met' if converged else 'requires_refinement',
        cavity_accessibility=None,formal_M3_excluded_volume=None,source_hashes=_hashes(payload.structure),
        numerical_policy_reference=payload.numerical_policy_reference,
        scope='declared_static_supplied_atom_geometry_not_complete_holo_volume_ensemble_or_M3_free_space')
