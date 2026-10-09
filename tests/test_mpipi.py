"""Native-format software fixtures, not author simulations; run on the server."""
import json
from hashlib import sha256
import math
import os
from pathlib import Path
import re
import subprocess
import zipfile

import pytest

from igem_drylab.mpipi import MpipiAnalysisInput, parse_mpipi, prepare_author_case


def make_output(tmp_path, case="rg", steps=500000000):
    (tmp_path / "lammps_log.out").write_text(
        f"LAMMPS (10 Mar 2021)\nLoop time of 1 on 1 procs for {steps} steps with 2 atoms\nTotal wall time: 0:00:01\n")
    (tmp_path / "Rg.out").write_text("# native-format fixture, not real MD\n0 10\n100000 20\n200000 30\n")
    return MpipiAnalysisInput(output_dir=tmp_path, case=case, origin="author_reference")


def test_gyration_keeps_units_and_requires_explicit_window_source(tmp_path):
    payload = make_output(tmp_path)
    result = parse_mpipi(payload)
    assert not result["completed_requested_runs"]  # Deliberately partial format fixture.
    assert result["observations"][-1] == {"step": 200000, "radius_gyration_angstrom": 30}
    assert "window" not in result and "score" not in result
    with pytest.raises(ValueError, match="explicit_analysis_source"):
        parse_mpipi(payload.model_copy(update={"discard_before_step": 100000}))
    result = parse_mpipi(payload.model_copy(update={"discard_before_step": 100000, "analysis_source": "software fixture policy"}))
    assert result["window"]["mean_radius_gyration_angstrom"] == 25
    assert "not_estimated" in result["window"]["uncertainty"]


def test_timer_exit_does_not_establish_complete_original_run(tmp_path):
    payload = make_output(tmp_path, steps=100000)
    assert not parse_mpipi(payload)["completed_requested_runs"]


@pytest.mark.parametrize("content", ["0 nan\n", "0 -1\n", "0 1\n0 2\n", "0 1 extra\n", ""])
def test_gyration_rejects_invalid_or_empty_rows(tmp_path, content):
    payload = make_output(tmp_path)
    (tmp_path / "Rg.out").write_text(content)
    with pytest.raises(ValueError):
        parse_mpipi(payload)


def test_native_density_profiles_not_phase_concentration_or_m1_ranking(tmp_path):
    (tmp_path / "log.lammps").write_text("LAMMPS (10 Mar 2021)\nLoop time of 1 on 1 procs for 500000 steps with 2 atoms\nLoop time of 1 on 1 procs for 4000000 steps with 2 atoms\nTotal wall time: 0:00:01\n")
    (tmp_path / "densities_chunked2.dat").write_text("# software fixture\n100000 2 2\n1 0.25 1 0.6\n2 0.75 1 0.1\n")
    payload = MpipiAnalysisInput(output_dir=tmp_path, case="coexistence", origin="author_reference")
    result = parse_mpipi(payload)
    assert not result["completed_requested_runs"] and result["phase_concentrations"] is None
    assert result["profiles"][0]["bins"][0]["mass_density_g_cm3"] == 0.6
    assert "score" not in result
    (tmp_path / "densities_chunked2.dat").write_text("100000 2 2\n1 0.25 1 0.6\n")
    with pytest.raises(ValueError, match="truncated"):
        parse_mpipi(payload)


def test_actual_job_requires_matching_execution_record_and_unchanged_inputs(tmp_path):
    payload = make_output(tmp_path)
    (tmp_path / "log.lammps").write_bytes((tmp_path / "lammps_log.out").read_bytes())
    payload = payload.model_copy(update={"origin": "executed_job"})
    with pytest.raises(FileNotFoundError):
        parse_mpipi(payload)
    source = tmp_path / "input.dat"
    source.write_bytes(b"software fixture")
    from igem_drylab.mpipi import AUTHOR_MD5
    record = {"author_archive_md5": AUTHOR_MD5, "case": "rg", "returncode": 0,
        "input_sha256": {"input.dat": sha256(source.read_bytes()).hexdigest()}}
    (tmp_path / "mpipi_original_run.json").write_text(json.dumps(record))
    assert parse_mpipi(payload)["origin"] == "executed_job"
    source.write_bytes(b"altered fixture")
    with pytest.raises(ValueError, match="input_changed"):
        parse_mpipi(payload)


def test_unverified_author_archive_cannot_execute(tmp_path):
    archive = tmp_path / "wrong.zip"
    archive.write_bytes(b"not the author archive")
    with pytest.raises(ValueError, match="archive_mismatch"):
        prepare_author_case(archive, "rg", tmp_path / "output")


@pytest.mark.scientific_algorithm
@pytest.mark.parametrize('types', [(1, 2), (3, 7), (3, 3), (10, 20), (20, 20)])
@pytest.mark.parametrize('distance_kind', ['repulsive', 'attractive', 'outside_wf_cutoff'])
def test_actual_original_lammps_energy_and_force_against_analytic_potential(tmp_path, types, distance_kind):
    """Actual native run-0 oracle, not a shortened author/project simulation.

    Analytic Wang-Frenkel energy/derivative plus the original Debye term,
    non-default exponents and both charge signs; unmodified author parameters.
    """
    executable = os.environ.get('FUSIONLAB_ORIGINAL_LAMMPS')
    archive = os.environ.get('FUSIONLAB_MPIPI_ARCHIVE')
    if not executable or not archive:
        pytest.skip('Original LAMMPS and author archive are optional external scientific dependencies; not installed in CI')
    from igem_drylab.mpipi import AUTHOR_MD5
    from hashlib import md5
    assert md5(Path(archive).read_bytes()).hexdigest() == AUTHOR_MD5
    with zipfile.ZipFile(archive) as packed:
        parameters = packed.read('all-model-parameters/set_pair_param-Mpipi.dat').decode()
        k25 = packed.read('fig4-Rg/all_lammps_config_files/K25.dat').decode()
    left, right = types
    line = [line.split() for line in parameters.splitlines()
        if line.startswith(f'pair_coeff {left} {right} wf/cut ')][-1]
    epsilon, sigma = map(float, line[4:6])
    nu, mu = map(int, line[6:8])  # LAMMPS argument order is nu, mu, not mu, nu.
    cutoff = float(line[8])
    radius = {'repulsive': sigma*.9, 'attractive': sigma*1.2, 'outside_wf_cutoff': cutoff*1.01}[distance_kind]
    charges = {int(row[2]): float(row[4]) for row in map(str.split, parameters.splitlines()) if row[:2] == ['set', 'type']}
    alpha = 2*nu*(cutoff/sigma)**(2*mu)*((1+2*nu)/(2*nu*((cutoff/sigma)**(2*mu)-1)))**(2*nu+1)
    energy = derivative = 0.0
    if radius < cutoff:
        a, b = (sigma/radius)**(2*mu)-1, (cutoff/radius)**(2*mu)-1
        energy = epsilon*alpha*a*b**(2*nu)
        derivative = epsilon*alpha*((-2*mu*(a+1)/radius)*b**(2*nu)
            + a*2*nu*b**(2*nu-1)*(-2*mu*(b+1)/radius))
    # LAMMPS 10Mar2021 real-units Coulomb factor; original dielectric and kappa.
    q1, q2 = charges.get(left, 0), charges.get(right, 0)
    style = next(row.split() for row in parameters.splitlines() if row.startswith('pair_style'))
    kappa = float(style[style.index('coul/debye')+1])
    coulomb = 332.06371*q1*q2*math.exp(-kappa*radius)/(80*radius) if radius < 35 else 0.0
    energy += coulomb
    derivative -= coulomb*(kappa+1/radius)
    (tmp_path/'parameters.dat').write_text(parameters)
    masses = k25.split('Masses', 1)[1].split('Atoms', 1)[0].strip()
    (tmp_path/'pair.dat').write_text('Independent two-bead potential oracle\n\n2 atoms\n40 atom types\n0 bonds\n1 bond types\n\n0 200 xlo xhi\n0 200 ylo yhi\n0 200 zlo zhi\n\nMasses\n\n'+masses+
        f'\n\nAtoms\n\n1 1 {left} 0 50 50 50\n2 2 {right} 0 {50+radius:.17g} 50 50\n')
    (tmp_path/'oracle.in').write_text('units real\nboundary p p p\natom_style full\nbond_style harmonic\ndielectric 80\nread_data pair.dat\ninclude parameters.dat\n'
        'thermo_style custom step pe ecoul\nthermo_modify norm no format float %.17g\n'
        'dump d all custom 1 forces.dat id fx fy fz\ndump_modify d sort id format float %.17g\nrun 0\n')
    completed = subprocess.run([executable, '-in', 'oracle.in', '-echo', 'none'], cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert completed.returncode == 0, completed.stdout+completed.stderr
    match = re.search(r'^\s*0\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s*$', completed.stdout, re.M)
    assert match, completed.stdout
    actual_energy, actual_coulomb = map(float, match.groups())
    force_rows = (tmp_path/'forces.dat').read_text().split('ITEM: ATOMS id fx fy fz\n')[1].splitlines()
    actual_fx = float(force_rows[0].split()[1])
    assert actual_energy == pytest.approx(energy, rel=2e-10, abs=2e-12)
    assert actual_coulomb == pytest.approx(coulomb, rel=2e-10, abs=2e-12)
    assert actual_fx == pytest.approx(derivative, rel=2e-10, abs=2e-12)
