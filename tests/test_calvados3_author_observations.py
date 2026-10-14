"""Synthetic analytic observations, not project simulation validation."""
from dataclasses import asdict
import csv
import json
from types import SimpleNamespace
import sys

import numpy as np
import pytest
from igem_drylab.calvados3_author_runner import export_observations
from test_calvados3_author_protocol import declared_request


@pytest.mark.scientific_algorithm
def test_native_frame_export_uses_actual_masses_and_distinguishes_equilibration(tmp_path, monkeypatch):
    request = declared_request(equilibration_steps=10, production_steps=10, save_interval_steps=10)
    (tmp_path / 'request.json').write_text(json.dumps(asdict(request)))
    (tmp_path / 'execution.json').write_text(json.dumps(dict(status='completed', completed_steps=20)))
    (tmp_path / 'native-system.json').write_text(json.dumps(dict(native_masses_dalton=[1.,3.])))
    # Two beads 2 nm apart, unequal masses: Rg=sqrt(3)/2 nm, Re=2 nm.
    # The second frame crosses the periodic boundary and must give the same result.
    chunk = SimpleNamespace(n_atoms=2, topology=SimpleNamespace(n_chains=1),
        xyz=np.array([[[1.,0.,0.],[3.,0.,0.]], [[9.,0.,0.],[1.,0.,0.]]]),
        # Actual MDTraj has nonzero float32 cos(90) terms in unitcell_vectors.
        unitcell_lengths=np.array([[10.,10.,10.]]*2,dtype=np.float32),
        unitcell_angles=np.array([[90.,90.,90.]]*2,dtype=np.float32))
    monkeypatch.setitem(sys.modules, 'mdtraj', SimpleNamespace(iterload=lambda *a,**kw: iter([chunk])))
    result = export_observations(tmp_path)
    with (tmp_path / 'observations.csv').open() as stream:
        rows = list(csv.DictReader(stream))
    assert result['frames']==2 and result['production_frames']==1
    assert [r['phase'] for r in rows]==['equilibration','production']
    assert [float(r['mass_weighted_Rg_nm']) for r in rows]==pytest.approx([np.sqrt(3)/2]*2)
    assert [float(r['end_to_end_nm']) for r in rows]==pytest.approx([2.,2.])
    assert result['scientific_convergence'] is None and not result['formal_M1_pass']
    with pytest.raises(ValueError, match='already_exist'):
        export_observations(tmp_path)


@pytest.mark.data_contract
def test_incomplete_budget_is_not_exported_as_complete(tmp_path, monkeypatch):
    (tmp_path / 'request.json').write_text(json.dumps(asdict(declared_request())))
    (tmp_path / 'execution.json').write_text(json.dumps(dict(status='production',completed_steps=100)))
    monkeypatch.setitem(sys.modules, 'mdtraj', SimpleNamespace())
    with pytest.raises(ValueError,match='completed_declared_budget'):
        export_observations(tmp_path)
    assert not (tmp_path / 'observations.csv').exists()


@pytest.mark.data_contract
@pytest.mark.parametrize('lengths,angles',[([10.,10.,10.],[90.,85.,90.]),([10.,float('nan'),10.],[90.,90.,90.])])
def test_actual_nonrectangular_or_invalid_box_is_not_rounded_into_pass(tmp_path,monkeypatch,lengths,angles):
    request=declared_request(equilibration_steps=0,production_steps=10,save_interval_steps=10)
    (tmp_path/'request.json').write_text(json.dumps(asdict(request)))
    (tmp_path/'execution.json').write_text(json.dumps(dict(status='completed',completed_steps=10)))
    (tmp_path/'native-system.json').write_text(json.dumps(dict(native_masses_dalton=[1.,3.])))
    chunk=SimpleNamespace(n_atoms=2,topology=SimpleNamespace(n_chains=1),xyz=np.array([[[1.,0.,0.],[3.,0.,0.]]]),
        unitcell_lengths=np.array([lengths]),unitcell_angles=np.array([angles]))
    monkeypatch.setitem(sys.modules,'mdtraj',SimpleNamespace(iterload=lambda *a,**kw:iter([chunk])))
    with pytest.raises(ValueError,match='orthorhombic_native_box'):export_observations(tmp_path)
    assert not (tmp_path/'observations.csv').exists()
