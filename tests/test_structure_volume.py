"""Independent sphere/union oracle; synthetic geometry, not biology."""
import math
import numpy as np
import pytest
from igem_drylab.structure_volume import sphere_union_lattice_volume


@pytest.mark.scientific_algorithm
def test_sphere_union_refinement_tracks_analytic_volume_without_double_counting():
    xyz=np.zeros((1,3));r=np.array([2.]);origin=np.array([.017,.021,.033])
    expected=4*math.pi*2**3/3
    value=sphere_union_lattice_volume(xyz,r,.125,origin)
    assert value==pytest.approx(expected,rel=.005)
    duplicate=sphere_union_lattice_volume(np.repeat(xyz,2,axis=0),np.repeat(r,2),.125,origin)
    assert duplicate==value


@pytest.mark.scientific_algorithm
def test_disjoint_and_overlapping_sphere_union_match_independent_dense_grid():
    coordinates=np.array([[0.,0.,0.],[1.,.5,.25]]);radii=np.array([1.,1.5]);spacing=.25;origin=np.zeros(3)
    grid=np.stack(np.meshgrid(np.arange(-2,3,spacing),np.arange(-2,3,spacing),np.arange(-2,3,spacing),indexing='ij'),axis=-1).reshape(-1,3)
    inside=np.any(np.sum((grid[:,None,:]-coordinates[None,:,:])**2,axis=-1)<=radii**2,axis=1)
    expected=int(inside.sum())*spacing**3
    assert sphere_union_lattice_volume(coordinates,radii,spacing,origin)==expected
