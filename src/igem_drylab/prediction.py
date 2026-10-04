"""Versioned M4 observation and replay adapters; no cross-model fitting."""
from dataclasses import asdict
from copy import deepcopy
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .full_network import COMPOUNDS, FullNetworkParameters, PhaseDistribution, ReactionKinetics, TemporalGate, TransportParameters, simulate_full_network
from .kinetics import InductionGate
from .m4_steady_state import M4SteadyStateInput, solve_m4_steady_state


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

    @model_validator(mode="after")
    def validate_series(self):
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
    return PredictionContract(model_kind="full_network_dynamic", formula_version=FULL_NETWORK_FORMULA_VERSION,
        time_unit="author_native_day_axis" if author else "h", concentration_unit="author_native" if author else "uM",
        time=result.time.tolist(), concentrations={
            "intracellular": {name: result.intracellular[index].tolist() for index, name in enumerate(COMPOUNDS)},
            "extracellular": {name: result.extracellular[index].tolist() for index, name in enumerate(COMPOUNDS)}},
        normalization={"intracellular": "cell_volume", "extracellular": "medium_volume"},
        intracellular_volume_l=params.transport.intracellular_volume_l, extracellular_volume_l=params.transport.extracellular_volume_l,
        kernel_inputs={"parameters": asdict(params), "initial_intracellular": initial_intracellular, "initial_extracellular": initial_extracellular},
        solver_settings={"t_end": t_end, "points": points, "method": "LSODA", "rtol": 1e-8, "atol": 1e-12}).model_dump(mode="json")


def steady_contract(payload, result):
    return PredictionContract(model_kind="markdown_steady_state", formula_version=result.formula_version,
        time_unit="h", concentration_unit="uM", concentrations={
            "intracellular": {name: [value] for name, value in result.concentrations_cell_average_um.items()}},
        normalization={"intracellular": "cell_volume"}, kernel_inputs=payload.model_dump(mode="json"),
        solver_settings={"method": "least_squares", "residual_tolerance_um_per_h": payload.residual_tolerance_um_per_h}).model_dump(mode="json")


def replay_prediction(payload, parameter_name, value):
    """Perturb one declared parameter, then call the original model's solver."""
    contract = PredictionContract.model_validate(payload)
    if contract.concentration_unit != "uM":
        raise ValueError("author_native_prediction_cannot_fit_absolute_measurements")
    if contract.model_kind == "markdown_steady_state":
        inputs = deepcopy(contract.kernel_inputs)
        if parameter_name.startswith(("kcat_r", "km_r")):
            prefix, reaction_id = parameter_name.split("_", 1)
            reaction = next((row for row in inputs["reactions"] if row["reaction_id"].lower() == reaction_id), None)
            if reaction is None:
                raise ValueError("fit_parameter_not_in_selected_model")
            reaction["kcat_per_h" if prefix == "kcat" else "km_um"] = value
        elif parameter_name == "input_flux_8":
            inputs["input_flux_um_per_h"] = value
        elif parameter_name.startswith("ksec_") and parameter_name[5:] in COMPOUNDS:
            inputs["secretion_rate_per_h"][parameter_name[5:]] = value
        elif parameter_name.startswith("activity_"):
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
        initial_extracellular=inputs["initial_extracellular"], t_end=contract.solver_settings["t_end"], points=contract.solver_settings["points"])
    return dynamic_contract(params, result, inputs["initial_intracellular"], inputs["initial_extracellular"], contract.solver_settings["t_end"], contract.solver_settings["points"])
