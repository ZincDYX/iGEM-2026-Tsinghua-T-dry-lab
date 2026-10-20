"""Original 2021 Mpipi author examples, not a substitute project LLPS score.

The author inputs are copied byte-for-byte. No temperature, salt, chain count,
time step, run length, region boundary or scoring policy is supplied by us.
"""
import argparse
from hashlib import md5, sha256
import json
import math
from pathlib import Path
import re
import subprocess
from typing import Literal
import zipfile

from pydantic import BaseModel, ConfigDict, Field


AUTHOR_URL = "https://ndownloader.figshare.com/files/31037434"
AUTHOR_MD5 = "a18b0f5e30f15f8b5daf7b66210b663e"
CASES = {
    "rg": {
        "inputs": ("fig4-Rg/lammps_Mpipi.in", "fig4-Rg/all_lammps_config_files/K25.dat"),
        "script": "lammps_Mpipi.in", "prefix": "fig4-Rg/",
        "output": "Rg.out", "steps": [500000000],
    },
    "coexistence": {
        "inputs": tuple("fig5-phase-diagrams/example-simulation/" + name for name in
            ("input-script.dat", "input-structure.dat", "set_pair_param-Mpipi.dat")),
        "script": "input-script.dat", "prefix": "fig5-phase-diagrams/example-simulation/",
        "output": "densities_chunked2.dat", "steps": [500000, 4000000],
    },
}


def prepare_author_case(archive: Path, case: str, destination: Path) -> dict[str, str]:
    if md5(archive.read_bytes()).hexdigest() != AUTHOR_MD5:
        raise ValueError("original_Mpipi_author_archive_mismatch")
    spec = CASES[case]
    hashes = {}
    with zipfile.ZipFile(archive) as packed:
        for name in spec["inputs"]:
            relative = name.removeprefix(spec["prefix"])
            target = destination / relative
            if target.exists():
                raise ValueError("author_example_output_directory_already_contains_inputs")
            target.parent.mkdir(parents=True, exist_ok=True)
            raw = packed.read(name)
            target.write_bytes(raw)
            hashes[relative] = sha256(raw).hexdigest()
    return hashes


class MpipiAnalysisInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    output_dir: Path
    case: Literal["rg", "coexistence"]
    origin: Literal["author_reference", "executed_job"]
    discard_before_step: int | None = Field(default=None, ge=0)
    analysis_source: str | None = None


def _data_lines(path: Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            yield line.split()


def parse_mpipi(payload: MpipiAnalysisInput) -> dict:
    spec = CASES[payload.case]
    raw = payload.output_dir / spec["output"]
    log = payload.output_dir / "log.lammps"
    # The original Fig. 4 reference uses a different log filename.
    if payload.origin == "author_reference" and payload.case == "rg":
        log = payload.output_dir / "lammps_log.out"
    text = log.read_text(encoding="utf-8")
    if not text.startswith("LAMMPS (10 Mar 2021)"):
        raise ValueError("original_Mpipi_requires_author_LAMMPS_version")
    steps = [int(value) for value in re.findall(r"Loop time .*? for (\d+) steps", text)]
    complete = (steps[-len(spec["steps"]):] == spec["steps"] and "Total wall time:" in text
        and "ERROR:" not in text)
    result = dict(method="Mpipi_original_2021", origin=payload.origin, case=payload.case,
        completed_requested_runs=complete, requested_run_steps=spec["steps"], observed_loop_steps=steps,
        source_url=AUTHOR_URL, scientific_status="diagnostic_not_project_LLPS_or_M1_rank",
        raw_output_sha256=sha256(raw.read_bytes()).hexdigest(), log_sha256=sha256(log.read_bytes()).hexdigest())
    if payload.origin == "executed_job":
        record = json.loads((payload.output_dir / "mpipi_original_run.json").read_text())
        if (record["author_archive_md5"] != AUTHOR_MD5 or record["case"] != payload.case
                or record["returncode"] != 0):
            raise ValueError("original_Mpipi_execution_record_mismatch_or_failed")
        for name, expected in record["input_sha256"].items():
            if sha256((payload.output_dir / name).read_bytes()).hexdigest() != expected:
                raise ValueError("original_Mpipi_input_changed_since_execution")
        result["execution_record"] = record
    rows = list(_data_lines(raw))
    if payload.case == "rg":
        values = []
        for row in rows:
            if len(row) != 2:
                raise ValueError("invalid_LAMMPS_gyration_columns")
            step, radius = int(row[0]), float(row[1])
            if radius < 0 or not math.isfinite(radius) or (values and step <= values[-1]["step"]):
                raise ValueError("invalid_LAMMPS_gyration_observation")
            values.append(dict(step=step, radius_gyration_angstrom=radius))
        result["observations"] = values
        # A complete log does not make a truncated output export complete.
        result["completed_requested_runs"] = complete and [row["step"] for row in values] == list(range(0, 500000001, 100000))
        result["radius_definition"] = "LAMMPS mass-weighted gyration; angstrom in units real"
        if payload.discard_before_step is not None:
            if not payload.analysis_source or not payload.analysis_source.strip():
                raise ValueError("equilibration_window_requires_explicit_analysis_source")
            selected = [row["radius_gyration_angstrom"] for row in values if row["step"] >= payload.discard_before_step]
            if not selected:
                raise ValueError("empty_explicit_equilibration_window")
            result["window"] = dict(discard_before_step=payload.discard_before_step,
                analysis_source=payload.analysis_source, observations=len(selected),
                mean_radius_gyration_angstrom=math.fsum(selected)/len(selected),
                uncertainty="not_estimated; correlated MD frames are not independent replicates")
    else:
        if payload.discard_before_step is not None:
            raise ValueError("phase_region_boundaries_and_analysis_policy_required; no_implicit_phase_average")
        profiles, index = [], 0
        while index < len(rows):
            header = rows[index]
            if len(header) != 3:
                raise ValueError("invalid_LAMMPS_chunk_header")
            step, count, total = int(header[0]), int(header[1]), float(header[2])
            if count <= 0 or total < 0 or not math.isfinite(total) or (profiles and step <= profiles[-1]["step"]):
                raise ValueError("invalid_LAMMPS_chunk_header")
            bins = []
            for number in range(1, count+1):
                index += 1
                if index >= len(rows):
                    raise ValueError("truncated_LAMMPS_chunk_profile")
                row = rows[index]
                if len(row) != 4 or int(row[0]) != number:
                    raise ValueError("invalid_LAMMPS_chunk_columns_or_order")
                coordinate, atoms, density = map(float, row[1:])
                if not all(math.isfinite(value) for value in (coordinate, atoms, density)) or min(atoms, density) < 0:
                    raise ValueError("invalid_LAMMPS_chunk_observation")
                bins.append(dict(bin=number, reduced_z=coordinate, mean_atom_count=atoms, mass_density_g_cm3=density))
            profiles.append(dict(step=step, total_atom_count=total, bins=bins))
            index += 1
        result["profiles"] = profiles
        result["completed_requested_runs"] = complete and len(profiles) >= 45 and all(len(row["bins"]) == 50 for row in profiles)
        result["phase_concentrations"] = None
        result["blocker"] = "Explicit dilute/dense regions, equilibration and applicable molecular-weight conversion are required; no inferred M1 score."
    if not rows:
        raise ValueError("empty_Mpipi_output")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--case", choices=tuple(CASES), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mpi-executable", type=Path)
    parser.add_argument("--mpi-ranks", type=int)
    args = parser.parse_args()
    if ((args.mpi_executable is None) != (args.mpi_ranks is None)
            or (args.mpi_ranks is not None and args.mpi_ranks < 1)):
        parser.error("MPI requires both an explicit launcher and a positive rank count")
    executable = args.executable.resolve()
    help_text = subprocess.run([str(executable), "-h"], capture_output=True, text=True, check=True).stdout
    if "10 Mar 2021" not in help_text or "wf/cut" not in help_text:
        raise ValueError("original_Mpipi_requires_LAMMPS_10Mar2021_with_wf_cut")
    hashes = prepare_author_case(args.archive, args.case, args.output_dir)
    argv = [str(executable), "-echo", "none", "-screen", "none", "-in", CASES[args.case]["script"], "-log", "log.lammps"]
    if args.mpi_executable is not None:
        argv = [str(args.mpi_executable.resolve()), "-n", str(args.mpi_ranks), *argv]
    completed = subprocess.run(argv, cwd=args.output_dir, check=False)
    record = dict(case=args.case, author_archive_md5=AUTHOR_MD5, source_url=AUTHOR_URL,
        input_sha256=hashes, executable_sha256=sha256(executable.read_bytes()).hexdigest(),
        command=argv, returncode=completed.returncode, method="Mpipi_original_2021")
    (args.output_dir / "mpipi_original_run.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    if completed.returncode:
        raise SystemExit(completed.returncode)
    result = parse_mpipi(MpipiAnalysisInput(output_dir=args.output_dir, case=args.case, origin="executed_job"))
    (args.output_dir / "analysis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    if not result["completed_requested_runs"]:
        raise SystemExit("Original run incomplete (for example, the author's timer expired); partial files retained.")


if __name__ == "__main__":
    main()
