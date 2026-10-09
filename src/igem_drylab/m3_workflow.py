"""M3 expression-window and uncertainty propagation using the original solver."""
from pydantic import Field, model_validator
from scipy.stats import qmc

from .design_analysis import RangeEvidence, ScientificAnalysisInput, sample_range
from .m3_equilibrium import M3EquilibriumInput, solve_m3_equilibrium


class M3EnsembleInput(ScientificAnalysisInput):
    equilibrium: M3EquilibriumInput
    ranges: list[RangeEvidence] = Field(min_length=1)
    samples: int = Field(ge=2)
    seed: int
    independence_reference: str = Field(min_length=1)

    @model_validator(mode="after")
    def varying_physical_fields(self):
        allowed = {"eta_acc_sh3", "eta_acc_pdz", "eta_bind_sh3", "eta_bind_pdz", "phi", "c_dense_um",
                   "c_scaffold_total_um", "c_sat_um", "kd_sh3_um", "kd_pdz_um", "k_oc", "k_dmt",
                   "c_oc_total_um", "c_dmt_total_um", "v_scaffold_nm3", "v_enzyme_nm3"}
        names = [r.parameter_name for r in self.ranges]
        if len(names) != len(set(names)) or not set(names) <= allowed:
            raise ValueError("M3_ranges_require_unique_primitive_physical_parameters_not_integer_topology")
        if self.equilibrium.phi is not None and {"c_scaffold_total_um", "c_sat_um"} & set(names):
            raise ValueError("lever_rule_uncertainty_cannot_be_hidden_by_fixed_measured_phi")
        return self


def solve_m3_ensemble(payload: M3EnsembleInput) -> dict:
    base = solve_m3_equilibrium(payload.equilibrium)
    samples = []
    for index, quantiles in enumerate(qmc.LatinHypercube(d=len(payload.ranges), seed=payload.seed).random(payload.samples)):
        values = {r.parameter_name: sample_range(r, q) for r, q in zip(payload.ranges, quantiles, strict=True)}
        try:
            raw = payload.equilibrium.model_dump(mode="json")
            raw.update(values)
            result = solve_m3_equilibrium(M3EquilibriumInput.model_validate(raw))
            samples.append({"sample_id": index, "parameters": values, "status": result.status,
                            "result": result.model_dump(mode="json")})
        except ValueError as error:
            samples.append({"sample_id": index, "parameters": values, "status": "invalid_input", "error": str(error)})
    valid = [row["result"] for row in samples if row["status"] == "valid"]
    def interval(path):
        def get(row):
            for key in path:
                row = row[key]
                if row is None:
                    return None
            return row
        values = [v for row in valid if (v := get(row)) is not None]
        return {"value": get(base.model_dump()), "lo": min(values) if values else None,
                "hi": max(values) if values else None, "valid_samples": len(values)}
    fields = {"R_dense": ["dense_oc_dmt_ratio"], "phi": ["phi"]}
    for species in ("oc", "dmt"):
        for field in ("total_dense_um", "free_dense_um", "free_dilute_um", "bound_dense_um", "site_occupancy",
                      "site_unoccupied_fraction", "bound_fraction_of_whole_cell_total", "dense_phase_fraction_of_whole_cell_total"):
            fields[species+"."+field] = [species, field]
    return {"schema_version": "m3-ensemble-v1", "base": base.model_dump(mode="json"), "samples": samples,
            "intervals": {name: interval(path) for name, path in fields.items()},
            "complete": len(valid) == len(samples), "valid_samples": len(valid), "failed_samples": len(samples)-len(valid),
            "method": "observed_LHS_envelope_not_confidence_interval",
            "scope": "all_samples" if len(valid) == len(samples) else "conditional_on_valid_samples",
            "range_evidence": [r.model_dump() for r in payload.ranges], "seed": payload.seed,
            "independence_reference": payload.independence_reference,
            "claim_scope": "conditional_model_uncertainty_not_measured_expression_or_LLPS"}
