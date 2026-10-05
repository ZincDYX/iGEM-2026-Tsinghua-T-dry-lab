"""Versioned M4 observation and replay adapters; no cross-model fitting."""
from dataclasses import asdict
from copy import deepcopy
from typing import Literal

import numpy as np
import scipy
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .full_network import COMPOUNDS, FULL_NETWORK_FORMULA_VERSION, ACTIVE_NETWORK_FORMULA_VERSION, FullNetworkParameters, PhaseDistribution, ReactionKinetics, TemporalGate, TransportParameters, simulate_full_network
from .kinetics import InductionGate
from .m4_steady_state import M4_ACTIVITY_FORMULA_VERSION, M4_FORMULA_VERSION, M4SteadyStateInput, solve_m4_steady_state


class DynamicSolverSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    t_end: float = Field(gt=0)
    points: int = Field(ge=2)
    method: Literal["LSODA", "BDF", "Radau"]
    rtol: float = Field(gt=0, lt=1)
    atol: float = Field(gt=0)
    integration_version: Literal["adaptive-cumulative-v1"]
    scipy_version: str


class SteadySolverSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    method: Literal["least_squares"]
    residual_tolerance_um_per_h: float = Field(gt=0)
    relative_residual_tolerance: float = Field(gt=0, lt=1)
    integration_version: Literal["scaled-residual-v1"]
    scipy_version: str


class PredictionContract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    schema_version: Literal["m4-prediction-v2"] = "m4-prediction-v2"
    model_kind: Literal["full_network_dynamic", "markdown_steady_state"]
    formula_version: str
    time_unit: Literal["h", "author_native_day_axis"]
    concentration_unit: Literal["uM", "author_native"]
    time: list[float] = Field(default_factory=list)
    concentrations: dict[str, dict[str, list[float]]]
    normalization: dict[str, str]
    intracellular_volume_l: float | None = Field(default=None, gt=0)
    extracellular_volume_l: float | None = Field(default=None, gt=0)
    kernel_inputs: dict
    solver_settings: dict
    experiment_context: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_series(self):
        if (self.model_kind, self.formula_version) not in _REPLAY_ADAPTERS:
            raise ValueError("unsupported_formula_version_explicit_migration_required")
        if (self.time_unit, self.concentration_unit) not in {("h", "uM"), ("author_native_day_axis", "author_native")}:
            raise ValueError("prediction_unit_pair_mismatch")
        dynamic = self.model_kind == "full_network_dynamic"
        expected = {"intracellular", "extracellular"} if dynamic else {"intracellular"}
        if set(self.concentrations) != expected or any(set(species) != set(COMPOUNDS) for species in self.concentrations.values()):
            raise ValueError("prediction_requires_complete_compartments_and_species")
        if self.normalization != {key: "cell_volume" if key == "intracellular" else "medium_volume" for key in expected}:
            raise ValueError("prediction_compartment_normalization_mismatch")
        settings_type = DynamicSolverSettings if dynamic else SteadySolverSettings
        self.solver_settings = settings_type.model_validate(self.solver_settings).model_dump()
        if dynamic:
            variant = self.kernel_inputs.get("parameters",{}).get("network_variant","full_ten")
            expected_version = ACTIVE_NETWORK_FORMULA_VERSION if variant == "oc_dmt_verified_absence" else FULL_NETWORK_FORMULA_VERSION
            if self.formula_version != expected_version:
                raise ValueError("prediction_kernel_network_variant_formula_mismatch")
            mode = self.kernel_inputs.get("parameters", {}).get("unit_mode")
            if (mode == "physical") != (self.concentration_unit == "uM") or mode not in {"physical", "author_native_sensitivity"}:
                raise ValueError("prediction_kernel_unit_mode_mismatch")
            transport = self.kernel_inputs["parameters"]["transport"]
            if (self.intracellular_volume_l != transport["intracellular_volume_l"] or
                    self.extracellular_volume_l != transport["extracellular_volume_l"]):
                raise ValueError("prediction_kernel_volume_mismatch")
            if not self.time or self.time[0] != 0 or self.time[-1] != self.solver_settings["t_end"]:
                raise ValueError("prediction_time_solver_interval_mismatch")
        else:
            if self.time or self.time_unit != "h":
                raise ValueError("steady_prediction_requires_physical_units_and_no_time_curve")
            if self.kernel_inputs.get("formula_version") != self.formula_version:
                raise ValueError("prediction_kernel_formula_version_mismatch")
            parsed = M4SteadyStateInput.model_validate(self.kernel_inputs)
            if parsed.formula_version != self.formula_version:
                raise ValueError("prediction_formula_upgrade_requires_explicit_migration")
            for key in ("residual_tolerance_um_per_h", "relative_residual_tolerance"):
                if getattr(parsed, key) != self.solver_settings[key]:
                    raise ValueError("prediction_kernel_solver_settings_mismatch")
        count = len(self.time) if self.model_kind == "full_network_dynamic" else 1
        if self.model_kind == "full_network_dynamic" and (count < 2 or any(right <= left for left, right in zip(self.time, self.time[1:]))):
            raise ValueError("prediction_time_must_be_strictly_increasing")
        if any(len(values) != count or any(value < 0 for value in values)
               for species in self.concentrations.values() for values in species.values()):
            raise ValueError("prediction_series_must_be_nonnegative_and_aligned")
        return self


def observe_prediction(payload, result):
    """Return canonical observation-space series; volumes never inferred."""
    contract = PredictionContract.model_validate(payload)
    for key in ("assay_mode", "expression_mode", "input_boundary"):
        declared = getattr(result, key)
        if declared and declared != contract.experiment_context.get(key):
            raise ValueError("observation_experimental_mode_or_boundary_mismatch:" + key)
    if contract.concentration_unit != "uM" or contract.time_unit != "h":
        raise ValueError("author_native_prediction_cannot_compare_absolute_measurements")
    if contract.model_kind == "markdown_steady_state" and result.observation_kind != "steady_state":
        raise ValueError("steady_state_prediction_requires_confirmed_steady_state_observations")
    compartment = result.measurement_compartment
    expected_basis = {"intracellular": "cell_volume", "extracellular": "medium_volume", "total_extract": "extraction_volume"}
    if compartment is None:
        raise ValueError("missing_measurement_compartment")
    if result.concentration_basis != expected_basis[compartment]:
        raise ValueError("measurement_concentration_basis_mismatch")
    if compartment == "total_extract":
        if contract.intracellular_volume_l is None or contract.extracellular_volume_l is None or result.extraction_volume_l is None:
            raise ValueError("total_extract_requires_model_and_extraction_volumes")
        inside, outside = contract.concentrations.get("intracellular", {}), contract.concentrations.get("extracellular", {})
        if not inside or not outside:
            raise ValueError("selected_model_does_not_predict_both_extraction_compartments")
        species = {name: (contract.intracellular_volume_l * np.asarray(inside[name]) + contract.extracellular_volume_l * np.asarray(outside[name])) / result.extraction_volume_l
                   for name in inside if name in outside}
    else:
        species = contract.concentrations.get(compartment)
        if species is None:
            raise ValueError("selected_model_does_not_predict_requested_compartment")
        if contract.normalization.get(compartment) != expected_basis[compartment]:
            raise ValueError("prediction_compartment_normalization_mismatch")
    if contract.model_kind == "markdown_steady_state":
        time = np.asarray(result.time_hours(), dtype=float)
        return time, {name: np.full(time.size, values[0]) for name, values in species.items()}
    return np.asarray(contract.time), {name: np.asarray(values) for name, values in species.items()}


def dynamic_contract(params, result, initial_intracellular, initial_extracellular, t_end, points):
    from .full_network import FULL_NETWORK_FORMULA_VERSION
    author = params.unit_mode == "author_native_sensitivity"
    return PredictionContract(model_kind="full_network_dynamic", formula_version=ACTIVE_NETWORK_FORMULA_VERSION if params.network_variant == "oc_dmt_verified_absence" else FULL_NETWORK_FORMULA_VERSION,
        time_unit="author_native_day_axis" if author else "h", concentration_unit="author_native" if author else "uM",
        time=result.time.tolist(), concentrations={
            "intracellular": {name: result.intracellular[index].tolist() for index, name in enumerate(COMPOUNDS)},
            "extracellular": {name: result.extracellular[index].tolist() for index, name in enumerate(COMPOUNDS)}},
        normalization={"intracellular": "cell_volume", "extracellular": "medium_volume"},
        intracellular_volume_l=params.transport.intracellular_volume_l, extracellular_volume_l=params.transport.extracellular_volume_l,
        kernel_inputs={"parameters": asdict(params), "initial_intracellular": initial_intracellular, "initial_extracellular": initial_extracellular},
        solver_settings={**result.solver_settings, "t_end": t_end, "points": points, "scipy_version": scipy.__version__}).model_dump(mode="json")


def steady_contract(payload, result):
    return PredictionContract(model_kind="markdown_steady_state", formula_version=result.formula_version,
        time_unit="h", concentration_unit="uM", concentrations={
            "intracellular": {name: [value] for name, value in result.concentrations_cell_average_um.items()}},
        normalization={"intracellular": "cell_volume"}, kernel_inputs=payload.model_dump(mode="json"),
        solver_settings={"method": "least_squares", "residual_tolerance_um_per_h": payload.residual_tolerance_um_per_h,
                         "relative_residual_tolerance": payload.relative_residual_tolerance,
                         "integration_version": "scaled-residual-v1", "scipy_version": scipy.__version__}).model_dump(mode="json")


def replay_prediction(payload, parameter_name, value):
    """Perturb one declared parameter, then call the original model's solver."""
    contract = PredictionContract.model_validate(payload)
    if contract.concentration_unit != "uM":
        raise ValueError("author_native_prediction_cannot_fit_absolute_measurements")
    if not np.isfinite(value):
        raise ValueError("fit_parameter_must_be_finite")
    if contract.solver_settings["scipy_version"] != scipy.__version__:
        raise ValueError("prediction_replay_requires_recorded_scipy_environment")
    replayed = _REPLAY_ADAPTERS[(contract.model_kind, contract.formula_version)](contract, parameter_name, value)
    replayed["experiment_context"] = contract.experiment_context
    return replayed


def _replay_steady(contract, parameter_name, value):
    inputs = deepcopy(contract.kernel_inputs)
    if parameter_name.startswith(("kcat_r", "km_r")):
        prefix, reaction_id = parameter_name.split("_", 1)
        reaction = next((row for row in inputs["reactions"] if row["reaction_id"].lower() == reaction_id), None)
        if reaction is None:
            raise ValueError("fit_parameter_not_in_selected_model")
        reaction["kcat_per_h" if prefix == "kcat" else "km_um"] = value
    elif parameter_name == "input_flux_8":
        inputs["input_flux_um_per_h"] = value
    elif parameter_name in {f"partition_x{compound}" for compound in COMPOUNDS}:
        if value <= 0:
            raise ValueError("metabolite_partition_coefficient_must_be_positive")
        inputs["metabolite_kp"][parameter_name.removeprefix("partition_x")] = value
    elif parameter_name.startswith("ksec_") and parameter_name[5:] in COMPOUNDS:
        inputs["secretion_rate_per_h"][parameter_name[5:]] = value
    elif parameter_name.startswith("activity_"):
        if contract.formula_version != M4_ACTIVITY_FORMULA_VERSION:
            raise ValueError("activity_parameter_requires_explicit_formula_migration")
        _, phase, enzyme = parameter_name.split("_", 2)
        if phase not in {"dense", "dilute"} or enzyme.upper() not in inputs["enzymes"]:
            raise ValueError("fit_parameter_not_in_selected_model")
        inputs["enzymes"][enzyme.upper()][f"activity_{phase}_ratio"] = value
    else:
        raise ValueError("fit_adapter_does_not_support_parameter")
    parsed = M4SteadyStateInput.model_validate(inputs)
    result = solve_m4_steady_state(parsed)
    if result.status != "valid":
        raise ValueError("fit_steady_state_solver_not_valid")
    return steady_contract(parsed, result)


def _replay_dynamic(contract, parameter_name, value):
    inputs = deepcopy(contract.kernel_inputs)
    raw = inputs["parameters"]
    if parameter_name.startswith(("kcat_r", "km_r")):
        prefix, reaction_id = parameter_name.split("_", 1)
        reaction = next((row for row in raw["reactions"] if row["reaction_id"].lower() == reaction_id), None)
        if reaction is None:
            raise ValueError("fit_parameter_not_in_selected_model")
        reaction[prefix] = value
    elif parameter_name.startswith("activity_"):
        _, phase, enzyme = parameter_name.split("_", 2)
        key = f"activity_{phase}"
        if key not in raw or enzyme.upper() not in raw[key]:
            raise ValueError("fit_parameter_not_in_selected_model")
        raw[key][enzyme.upper()] = value
    elif parameter_name == "transport_rate":
        raw["transport"]["rate"] = value
    elif parameter_name in {f"partition_x{compound}" for compound in COMPOUNDS}:
        if value <= 0:
            raise ValueError("metabolite_partition_coefficient_must_be_positive")
        raw["metabolite_kp"][parameter_name.removeprefix("partition_x")] = value
    else:
        raise ValueError("fit_adapter_does_not_support_parameter")
    raw["enzyme_distributions"] = {name: PhaseDistribution(**row) for name, row in raw["enzyme_distributions"].items()}
    raw["reactions"] = tuple(ReactionKinetics(**row) for row in raw["reactions"])
    raw["transport"] = TransportParameters(**raw["transport"])
    for name in ("pt_gate", "oc_gate", "dmt_gate"):
        row = raw[name]
        if row["induction"] is not None:
            row["induction"] = InductionGate(**row["induction"])
        raw[name] = TemporalGate(**row)
    params = FullNetworkParameters(**raw)
    result = simulate_full_network(params, initial_intracellular=inputs["initial_intracellular"],
        initial_extracellular=inputs["initial_extracellular"],
        **{key: contract.solver_settings[key] for key in ("t_end", "points", "method", "rtol", "atol")})
    return dynamic_contract(params, result, inputs["initial_intracellular"], inputs["initial_extracellular"], contract.solver_settings["t_end"], contract.solver_settings["points"])


_REPLAY_ADAPTERS = {
    ("full_network_dynamic", FULL_NETWORK_FORMULA_VERSION): _replay_dynamic,
    ("full_network_dynamic", ACTIVE_NETWORK_FORMULA_VERSION): _replay_dynamic,
    ("markdown_steady_state", M4_FORMULA_VERSION): _replay_steady,
    ("markdown_steady_state", M4_ACTIVITY_FORMULA_VERSION): _replay_steady,
}
