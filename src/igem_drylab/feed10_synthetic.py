"""Run the reviewed PS-v3 feed-10 synthetic package without executing uploads.

This adapter is deliberately separate from the ten-reaction steady-state model.
It reads only named CSV members, recomputes M3 with the conservative scaffold
coexistence concentrations, and integrates the package's four-reaction dynamic
reference branch.  The result remains synthetic pipeline evidence.
"""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any
from zipfile import BadZipFile, ZipFile

import numpy as np
from scipy.integrate import solve_ivp

from .m3_equilibrium import M3EquilibriumInput, solve_m3_equilibrium


MODEL_VERSION = "ps-v3-feed10-four-reaction-independent-mm-v1"
SCENARIOS = ("C1", "C2", "E1", "E2", "E3")
REQUIRED = {
    "m3_phase_recruitment.csv",
    "m4_dynamic_initial.csv",
    "m4_kinetics.csv",
    "m4_effective_in_vivo_activity.csv",
    "scenarios/enzyme_abundance_recruitment.csv",
    "scenarios/projected_titer_ILLUSTRATIVE_band.csv",
    "scenarios/terminal_state_master.csv",
    *(f"scenarios/timecourse_{scenario}.csv" for scenario in SCENARIOS),
}
REACTIONS = {
    "R3": ("OC", "x10", "x11"),
    "R6": ("DMT", "x10", "x14"),
    "R7": ("DMT", "x11", "x15"),
    "R10": ("OC", "x14", "x15"),
}
SPECIES = ("x10", "x11", "x14", "x15")


def _archive_rows(archive: ZipFile, name: str) -> list[dict[str, str]]:
    try:
        text = archive.read(name).decode("utf-8-sig")
    except (KeyError, UnicodeError) as error:
        raise ValueError(f"ps_v3_required_member_invalid:{name}") from error
    rows = list(csv.DictReader(StringIO(text)))
    if not rows:
        raise ValueError(f"ps_v3_required_table_empty:{name}")
    return rows


def read_package(path: Path) -> dict[str, list[dict[str, str]]]:
    """Read a bounded ZIP as data; never extract it or execute bundled code."""
    if path.stat().st_size > 20_000_000:
        raise ValueError("ps_v3_package_exceeds_20_MB")
    try:
        with ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > 200 or sum(item.file_size for item in infos) > 50_000_000:
                raise ValueError("ps_v3_archive_budget_exceeded")
            for item in infos:
                posix = PurePosixPath(item.filename)
                if (posix.is_absolute() or ".." in posix.parts or
                        PureWindowsPath(item.filename).drive or "\\" in item.filename):
                    raise ValueError("ps_v3_archive_path_invalid")
            names = {item.filename for item in infos if not item.is_dir()}
            missing = sorted(REQUIRED - names)
            if missing:
                raise ValueError("ps_v3_required_members_missing:" + ",".join(missing))
            return {name: _archive_rows(archive, name) for name in REQUIRED}
    except BadZipFile as error:
        raise ValueError("ps_v3_invalid_zip") from error


def _number(row: dict[str, str], field: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"ps_v3_numeric_field_invalid:{field}") from error
    if not np.isfinite(value):
        raise ValueError(f"ps_v3_numeric_field_nonfinite:{field}")
    return value


def _parameters(tables: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    parameters = {row["code_field"]: row for row in tables["m3_phase_recruitment.csv"]}
    kinetics: dict[str, dict[str, float]] = {}
    for row in tables["m4_kinetics.csv"]:
        reaction = row.get("reaction")
        if reaction not in REACTIONS:
            continue
        if row.get("parameter_set_id") != "PS-v3" or row.get("source_type") != "synthetic":
            raise ValueError("ps_v3_active_kinetics_scope_invalid")
        kind = row["parameter"].split("_", 1)[0]
        if kind not in {"kcat", "km"}:
            raise ValueError("ps_v3_kinetic_parameter_invalid")
        kinetics.setdefault(reaction, {})[kind] = _number(row, "value")
    if any(set(kinetics.get(reaction, {})) != {"kcat", "km"} for reaction in REACTIONS):
        raise ValueError("ps_v3_feed10_kinetics_incomplete")
    effective = {(row["scenario_id"], row["reaction"]): _number(row, "total_activity_multiplier")
                 for row in tables["m4_effective_in_vivo_activity.csv"]}
    if any((scenario, reaction) not in effective for scenario in SCENARIOS for reaction in REACTIONS):
        raise ValueError("ps_v3_effective_activity_incomplete")
    abundance = {row["condition_id"]: row for row in tables["scenarios/enzyme_abundance_recruitment.csv"]}
    export = {row["scenario_id"]: _number(row, "x15_extracellular_fraction_of_total")
              for row in tables["scenarios/projected_titer_ILLUSTRATIVE_band.csv"]}
    reference = {row["scenario_id"]: row for row in tables["scenarios/terminal_state_master.csv"]}
    if set(abundance) != set(SCENARIOS) or set(export) != set(SCENARIOS) or set(reference) != set(SCENARIOS):
        raise ValueError("ps_v3_scenario_identity_incomplete")
    dynamic_rows = tables["m4_dynamic_initial.csv"]
    initial: dict[str, float] = {}
    end_h: float | None = None
    for row in dynamic_rows:
        if row.get("branch") == "closed_intracellular_reference" and row.get("at") == "t=0" and row.get("species") in SPECIES:
            initial[row["species"]] = _number(row, "initial_uM")
        if row.get("species") == "run_end":
            end_h = _number(row, "initial_uM")
    if set(initial) != set(SPECIES) or end_h is None or end_h <= 0:
        raise ValueError("ps_v3_dynamic_initial_incomplete")
    return {"rows": parameters, "kinetics": kinetics, "effective": effective,
            "abundance": abundance, "export": export, "reference": reference,
            "initial_uM": initial, "end_h": end_h}


def solve_m3_cases(parameters: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Use 22.55/18.05 uM as the reviewed dense scaffold basis."""
    rows = parameters["rows"]
    kd_sh3 = _number(rows["kd_sh3"], "value")
    kd_pdz = _number(rows["kd_pdz"], "value")
    k_oc = _number(rows["partition_oc"], "value")
    k_dmt = _number(rows["partition_dmt"], "value")
    results: dict[str, dict[str, Any]] = {}
    for scenario in SCENARIOS:
        source = parameters["abundance"][scenario]
        phi = _number(source, "phi")
        total = _number(source, "total_enzyme_uM")
        dense = 18.05 if scenario == "E3" else 22.55
        payload = M3EquilibriumInput(
            candidate_id=scenario,
            construct_id="PS-v3-SYNTHETIC-" + scenario,
            s_sh3=3,
            s_pdz=1,
            eta_acc_sh3=1.0,
            eta_acc_pdz=1.0,
            eta_bind_sh3=1.0,
            eta_bind_pdz=1.0,
            site_count_basis="scaffold_monomer",
            c_dense_basis="scaffold_monomer",
            joint_occupancy_independent=True,
            m2_geometry_id="SYNTHETIC_PIPELINE_TEST",
            phi=phi,
            c_scaffold_total_um=_number(rows["s_tot"], "value") if phi else None,
            c_sat_um=_number(rows["s_dilute"], "value") if phi else None,
            c_dense_um=dense,
            kd_sh3_um=kd_sh3,
            kd_pdz_um=kd_pdz,
            k_oc=k_oc,
            k_dmt=k_dmt,
            c_oc_total_um=total,
            c_dmt_total_um=total,
            input_parameter_ids=["PS-v3"],
        )
        solved = solve_m3_equilibrium(payload)
        if solved.status != "valid" or solved.oc is None or solved.dmt is None:
            raise ValueError(f"ps_v3_m3_not_solved:{scenario}")
        results[scenario] = {
            "input": payload.model_dump(mode="json"),
            "result": solved.model_dump(mode="json"),
            "scope": "synthetic_conservative_dense_scaffold_basis_not_formal_prediction",
        }
    return results


def _time_grid(tables: dict[str, list[dict[str, str]]], end_h: float) -> list[float]:
    grids = {
        scenario: sorted({_number(row, "time_h") for row in tables[f"scenarios/timecourse_{scenario}.csv"]})
        for scenario in SCENARIOS
    }
    values = grids[SCENARIOS[0]]
    if (not values or values[0] != 0 or values[-1] != end_h
            or any(b <= a for a, b in zip(values, values[1:]))
            or any(grid != values for grid in grids.values())):
        raise ValueError("ps_v3_time_grid_invalid_or_inconsistent")
    return values


def solve_m4_cases(tables: dict[str, list[dict[str, str]]], parameters: dict[str, Any],
                   m3: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    time_grid = _time_grid(tables, parameters["end_h"])
    initial = np.array([parameters["initial_uM"][species] for species in SPECIES], dtype=float)
    initial_total = float(initial.sum())
    kp = {species: _number(parameters["rows"]["partition_" + species], "value") for species in SPECIES}
    output: dict[str, dict[str, Any]] = {}
    for scenario in SCENARIOS:
        phi = parameters["abundance"][scenario]
        phi = _number(phi, "phi")
        recruitment = m3[scenario]["result"]
        enzymes = {
            "OC": (recruitment["oc"]["free_dilute_um"], recruitment["oc"]["total_dense_um"] if phi else 0.0),
            "DMT": (recruitment["dmt"]["free_dilute_um"], recruitment["dmt"]["total_dense_um"] if phi else 0.0),
        }

        def phase(global_concentration: float, species: str) -> tuple[float, float]:
            dilute = global_concentration / (1.0 - phi + phi * kp[species])
            return dilute, kp[species] * dilute

        def rhs(_time: float, state: np.ndarray) -> list[float]:
            concentrations = {species: phase(float(state[index]), species)
                              for index, species in enumerate(SPECIES)}
            rates: dict[str, float] = {}
            for phase_index, weight in ((0, 1.0 - phi), (1, phi)):
                for reaction, (enzyme, substrate, _product) in REACTIONS.items():
                    substrate_concentration = concentrations[substrate][phase_index]
                    kinetic = parameters["kinetics"][reaction]
                    rate = (kinetic["kcat"] * parameters["effective"][scenario, reaction]
                            * enzymes[enzyme][phase_index] * substrate_concentration
                            / (kinetic["km"] + substrate_concentration))
                    rates[reaction] = rates.get(reaction, 0.0) + weight * rate
            production = rates["R7"] + rates["R10"]
            return [-(rates["R3"] + rates["R6"]), rates["R3"] - rates["R7"],
                    rates["R6"] - rates["R10"], production]

        solved = solve_ivp(rhs, (time_grid[0], time_grid[-1]), initial,
                           t_eval=time_grid, method="LSODA", rtol=1e-9, atol=1e-11)
        if not solved.success or solved.y.shape != (4, len(time_grid)) or float(solved.y.min()) < -1e-8:
            raise ValueError(f"ps_v3_m4_not_solved:{scenario}")
        export_fraction = parameters["export"][scenario]
        retained = solved.y[3] * (1.0 - export_fraction)
        extracellular = solved.y[3] * export_fraction
        closure = solved.y[0] + solved.y[1] + solved.y[2] + retained + extracellular
        if float(np.max(np.abs(closure - initial_total))) > 1e-6:
            raise ValueError(f"ps_v3_m4_mass_balance_failed:{scenario}")
        reference = parameters["reference"][scenario]
        reference_terminal = np.array([_number(reference, field) for field in (
            "x10_global", "x11_global", "x14_global", "x15_retained_global", "x15_extracellular_global")])
        terminal = np.array([solved.y[0, -1], solved.y[1, -1], solved.y[2, -1], retained[-1], extracellular[-1]])
        output[scenario] = {
            "status": "numerically_solved",
            "model_version": MODEL_VERSION,
            "parameter_set_id": "PS-v3",
            "source_type": "synthetic",
            "formal_prediction_allowed": False,
            "time_h": time_grid,
            "series_uM": {"x10": solved.y[0].tolist(), "x11": solved.y[1].tolist(),
                          "x14": solved.y[2].tolist(), "x15_retained": retained.tolist(),
                          "x15_extracellular": extracellular.tolist()},
            "terminal_uM": dict(zip(("x10", "x11", "x14", "x15_retained", "x15_extracellular"), terminal.tolist())),
            "reference_terminal_delta_uM": dict(zip(("x10", "x11", "x14", "x15_retained", "x15_extracellular"), (terminal - reference_terminal).tolist())),
            "max_mass_balance_residual_uM": float(np.max(np.abs(closure - initial_total))),
            "numerics": {"method": "LSODA", "rtol": 1e-9, "atol_uM": 1e-11},
            "scope": "synthetic_closed_intracellular_reference_with_package_product_export_fraction",
        }
    return output


def run_package(path: Path) -> dict[str, Any]:
    tables = read_package(path)
    parameters = _parameters(tables)
    m3 = solve_m3_cases(parameters)
    m4 = solve_m4_cases(tables, parameters, m3)
    return {
        "schema_version": "ps-v3-feed10-reproduction-v1",
        "parameter_set_id": "PS-v3",
        "source_type": "synthetic",
        "formal_prediction_allowed": False,
        "m3_dense_scaffold_basis_uM": {"E1": 22.55, "E2": 22.55, "E3": 18.05},
        "m3": m3,
        "m4": m4,
    }
