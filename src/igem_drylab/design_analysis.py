"""Evidence-declared F2/F3; no parameter-library mutation or implicit biology."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator
from scipy.stats import qmc, spearmanr


class ScientificAnalysisInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class RangeEvidence(ScientificAnalysisInput):
    parameter_name: str
    distribution: Literal["uniform", "empirical", "interpolated_empirical"]
    interpolation_reference: str | None = None
    lower: float | None = None
    upper: float | None = None
    empirical_values: list[float] = Field(default_factory=list)
    source_reference: str = Field(min_length=1)
    parameter_ids: list[str] = Field(min_length=1)
    reviewed_by: str = Field(min_length=1)

    @model_validator(mode="after")
    def valid_distribution(self):
        if self.distribution == "uniform":
            if self.lower is None or self.upper is None or not self.lower < self.upper:
                raise ValueError("uniform_requires_evidenced_increasing_range")
        elif len(self.empirical_values) < 2 or min(self.empirical_values) == max(self.empirical_values):
            raise ValueError("empirical_requires_actual_nonconstant_samples")
        if self.distribution == "interpolated_empirical" and not self.interpolation_reference:
            raise ValueError("continuous_empirical_requires_reviewed_interpolation_reference")
        return self


def sample_range(row: RangeEvidence, quantile: float) -> float:
    if row.distribution == "uniform":
        return float(row.lower + (row.upper - row.lower) * quantile)
    return float(np.quantile(row.empirical_values, quantile,
        method="inverted_cdf" if row.distribution == "empirical" else "linear"))


class IDRMappingEvidence(ScientificAnalysisInput):
    a: float
    b: float
    c: float
    const: float
    logp: dict[str, float]
    aromatic_counts: dict[str, float]
    theta_hydro: float
    theta_aro: float
    source_reference: str = Field(min_length=1)
    applicable_domain_reference: str = Field(min_length=1)
    reviewed_by: str = Field(min_length=1)


class M4AnalysisConfig(ScientificAnalysisInput):
    local_parameter_names: list[str] = Field(default_factory=list)
    ranges: list[RangeEvidence] = Field(default_factory=list)
    samples: int = Field(default=256, ge=2)
    random_seed: int = 42
    standard_deviation_ddof: Literal[0, 1] | None = None
    independence_evidence_reference: str | None = None
    idr_mapping: IDRMappingEvidence | None = None

    @model_validator(mode="after")
    def explicit_joint_assumptions(self):
        if self.ranges and (not self.independence_evidence_reference or self.standard_deviation_ddof is None):
            raise ValueError("LHS_requires_explicit_independence_evidence_and_sigma_convention")
        names = [row.parameter_name for row in self.ranges]
        if len(names) != len(set(names)) or len(self.local_parameter_names) != len(set(self.local_parameter_names)):
            raise ValueError("analysis_parameter_names_must_be_unique")
        return self


def _steady_yield(contract):
    from .m4_steady_state import M4SteadyStateInput, solve_m4_steady_state
    if contract["model_kind"] != "markdown_steady_state":
        raise ValueError("original_F2_yield_requires_original_steady_model")
    result = solve_m4_steady_state(M4SteadyStateInput.model_validate(contract["kernel_inputs"]))
    if result.status != "valid" or result.yield_abs is None:
        raise ValueError("analysis_steady_solve_not_valid")
    return result.yield_abs


def _value(contract, name):
    inputs = contract["kernel_inputs"]
    if name.startswith("partition_x") and name.removeprefix("partition_x") in inputs["metabolite_kp"]:
        return inputs["metabolite_kp"][name.removeprefix("partition_x")]
    if name.startswith(("kcat_r", "km_r")):
        prefix, reaction = name.split("_", 1)
        row = next((r for r in inputs["reactions"] if r["reaction_id"].lower() == reaction), None)
        if row:
            return row["kcat_per_h" if prefix == "kcat" else "km_um"]
    raise ValueError("analysis_parameter_not_supported")


def analyze_prediction(contract: dict, settings: M4AnalysisConfig) -> dict:
    from copy import deepcopy
    import scipy
    from .prediction import PredictionContract
    from .m4_steady_state import M4SteadyStateInput, solve_m4_steady_state
    contract = PredictionContract.model_validate(contract).model_dump(mode="json")
    if contract["solver_settings"]["scipy_version"] != scipy.__version__:
        raise ValueError("analysis_requires_recorded_scipy_environment")
    base_yield = _steady_yield(contract)
    def evaluate(values):
        # Apply a complete joint sample before solving, not a sequence of
        # potentially invalid intermediate parameter sets.
        inputs = deepcopy(contract["kernel_inputs"])
        for name, value in values.items():
            _value(contract, name)
            if name.startswith("partition_x"):
                inputs["metabolite_kp"][name.removeprefix("partition_x")] = value
            else:
                prefix, reaction = name.split("_", 1)
                row = next(r for r in inputs["reactions"] if r["reaction_id"].lower()==reaction)
                row["kcat_per_h" if prefix=="kcat" else "km_um"] = value
        solved = solve_m4_steady_state(M4SteadyStateInput.model_validate(inputs))
        if solved.status != "valid" or solved.yield_abs is None:
            raise ValueError("analysis_joint_sample_solver_not_valid")
        return solved.yield_abs
    return analyze_response(settings, {name: _value(contract, name) for name in
        set(settings.local_parameter_names) | {r.parameter_name for r in settings.ranges}}, evaluate, base_yield)


def analyze_response(settings, base_values, evaluate, base_yield):
    """Pure analysis boundary; caller supplies the same versioned physical solver."""
    local = {}
    for name in settings.local_parameter_names:
        value = base_values[name]
        rows = []
        for fraction in (.01, .005, .0025):
            delta = value * fraction
            try:
                if delta == 0:
                    raise ValueError("relative_step_undefined_at_zero_parameter")
                perturbed_yield = evaluate({name: value + delta})
                rows.append({"fraction": fraction, "delta": delta, "derivative": (perturbed_yield-base_yield)/delta,
                             "normalized_sensitivity": (perturbed_yield-base_yield)/delta*value/base_yield if base_yield else None})
            except (ValueError, RuntimeError) as error:
                rows.append({"fraction": fraction, "delta": delta, "derivative": None, "error": str(error)})
        finite = [row["derivative"] for row in rows if row["derivative"] is not None]
        local[name] = {"formula": "[Y(Kp+delta)-Y(Kp)]/delta", "step_role": "numerical_not_measured_uncertainty",
                      "steps": rows, "successive_derivative_differences": np.diff(finite).tolist(),
                      "convergence_claim": "step_diagnostics_only_no_biological_tolerance_assumed"}
    global_result, robustness = None, None
    if settings.ranges:
        unit_samples = qmc.LatinHypercube(d=len(settings.ranges), seed=settings.random_seed).random(settings.samples)
        samples = []
        for sample_id, unit_row in enumerate(unit_samples):
            values = {row.parameter_name: sample_range(row,u) for row,u in zip(settings.ranges,unit_row,strict=True)}
            try:
                result = float(evaluate(values))
                if not np.isfinite(result):
                    raise ValueError("nonfinite_analysis_yield")
                samples.append({"sample_id": sample_id, "parameters": values, "yield_abs": result, "status":"valid"})
            except (ValueError, RuntimeError) as error:
                samples.append({"sample_id": sample_id, "parameters": values, "yield_abs": None, "status":"failed", "error":str(error)})
        valid = [row for row in samples if row["status"]=="valid"]
        yields = np.asarray([row["yield_abs"] for row in valid])
        ranks = {}
        for name in (row.parameter_name for row in settings.ranges):
            x = [row["parameters"][name] for row in valid]
            ranks[name] = float(spearmanr(x,yields).statistic) if len(valid)>1 and np.ptp(yields)>0 and np.ptp(x)>0 else None
        sigma = float(np.std(yields, ddof=settings.standard_deviation_ddof)) if len(valid)>settings.standard_deviation_ddof else None
        robustness = {"value": 1/sigma if sigma is not None and sigma>0 else None, "sigma":sigma,
            "zero_sigma_interpretation":"unbounded_reciprocal_not_finite_estimate" if sigma==0 else None,
            "ddof":settings.standard_deviation_ddof, "formula":"1/sigma_LHS(yield_abs)",
            "scope":"all_samples" if len(valid)==len(samples) else "conditional_on_valid_samples",
            "valid_samples":len(valid), "failed_samples":len(samples)-len(valid)}
        global_result = {"method":"LatinHypercube_and_Spearman_not_partial_derivatives",
            "spearman":ranks, "samples":samples, "range_evidence":[row.model_dump() for row in settings.ranges],
            "independence_evidence_reference":settings.independence_evidence_reference,
            "random_seed":settings.random_seed}
        global_result["sampling_methods"] = {row.parameter_name: (
            "uniform_inverse_cdf" if row.distribution == "uniform" else
            "discrete_inverse_ecdf_preserving_duplicate_weights" if row.distribution == "empirical" else
            "continuous_linear_quantile_interpolation") for row in settings.ranges}
    chain = None
    if settings.idr_mapping:
        mapping = settings.idr_mapping
        required = {str(i) for i in range(8,16)}
        if set(mapping.aromatic_counts)!=required or set(mapping.logp)!=required or not all(f"partition_x{i}" in local for i in required):
            raise ValueError("IDR_chain_requires_all_species_descriptors_and_local_derivatives")
        derivatives = {i:local[f"partition_x{i}"]["steps"][0]["derivative"] for i in required}
        if all(v is not None for v in derivatives.values()):
            mapped = {i:float(np.exp(mapping.a*mapping.logp[i]+mapping.b*mapping.theta_hydro+
                         mapping.c*mapping.aromatic_counts[i]*mapping.theta_aro+mapping.const)) for i in required}
            if not all(np.isfinite(v) and v>0 for v in mapped.values()):
                raise ValueError("IDR_mapping_outside_finite_numeric_domain")
            mapping_values = {f"partition_x{i}":mapped[i] for i in required}
            mapped_yield = evaluate(mapping_values)
            derivatives = {i:(evaluate({**mapping_values, f"partition_x{i}":mapped[i]*1.01})-mapped_yield)/(mapped[i]*.01) for i in required}
            chain = {"dY_dtheta_hydro":sum(derivatives[i]*mapping.b*mapped[i] for i in required),
                     "dY_dtheta_aro":sum(derivatives[i]*mapping.c*mapping.aromatic_counts[i]*mapped[i] for i in required),
                     "mapped_kp":mapped, "mapping_evidence":mapping.model_dump(),
                     "mapped_base_yield":mapped_yield, "mapped_local_derivatives":derivatives,
                     "scope":"original_forward_1pct_chain_at_declared_mapping_not_measured_Kp_spectrum"}
    return {"schema_version":"m4-analysis-v1", "base_yield_abs":base_yield,
            "sensitivity":{"local_forward_difference":local,"global":global_result,"idr_chain":chain},
            "robustness":robustness}


class ScaffoldCandidate(ScientificAnalysisInput):
    config_path: Path
    candidate_id: str
    site_ratio: Literal[1,2,3,4,6]
    design_evidence_reference: str = Field(min_length=1)
    synthesized: bool  # A design is not implicitly an experimental construct.


class DesignComparisonContract(ScientificAnalysisInput):
    """Comparable meanings and physical boundaries, not equality of condition labels."""
    model_kind: Literal["full_network_dynamic", "markdown_steady_state"]
    formula_version: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    metric_unit: Literal["1", "uM/h"]
    normalization: dict[str, str]
    measurement_compartment: Literal["intracellular", "extracellular", "total_extract"]
    assay_mode: Literal["substrate_feeding_functional", "full_pathway_production"]
    expression_mode: Literal["constitutive", "induced"]
    input_boundary: dict[str, str | float | None]
    input_definition: dict
    assay_conditions: dict[str, str | float | None]
    interval_h: float | None = Field(default=None, gt=0)
    steady_state_observation_reference: str | None = None

    @model_validator(mode="after")
    def complete_boundaries(self):
        if any(self.assay_conditions.get(k) is None for k in ('host','strain','pH','temperature_c','assay_system')):
            raise ValueError("comparison_requires_actual_assay_conditions")
        if any(self.input_boundary.get(k) is None for k in ('feed_mode','feed_compound_id')):
            raise ValueError("comparison_requires_feed_identity_and_boundary")
        if self.model_kind == 'full_network_dynamic' and (self.interval_h is None or
                self.input_boundary.get('feeding_time_h') is None):
            raise ValueError("dynamic_comparison_requires_interval_and_feeding_time")
        if self.model_kind == 'markdown_steady_state' and not self.steady_state_observation_reference:
            raise ValueError("steady_comparison_requires_observation_evidence")
        return self


def _candidate_comparison(prediction, objective):
    from .prediction import PredictionContract
    contract = PredictionContract.model_validate(prediction.simulation_inputs.get('prediction_contract',{}))
    if contract.concentration_unit != 'uM' or contract.time_unit != 'h':
        raise ValueError('comparison_requires_physical_units')
    definitions = {
        ('markdown_steady_state','yield_abs'):('product_15_secretion_flux/input_8_flux','1'),
        ('full_network_dynamic','yield_abs'):('net_15_generated/initial_convertible_backbone','1'),
        ('full_network_dynamic','productivity'):('net_15_generated_cell_volume_equivalent/interval_h','uM/h'),
    }
    if (contract.model_kind,objective) not in definitions:
        raise ValueError('objective_not_defined_for_selected_model')
    definition,unit = definitions[(contract.model_kind,objective)]
    experiment = contract.experiment_context
    inputs = contract.kernel_inputs
    boundary = ({'initial_intracellular':inputs['initial_intracellular'],
        'initial_extracellular':inputs['initial_extracellular'],
        'volumes_l':[contract.intracellular_volume_l,contract.extracellular_volume_l],
        'temporal_gates':{k:inputs['parameters'][k] for k in ('pt_gate','oc_gate','dmt_gate')},
        'transport':inputs['parameters']['transport']} if contract.model_kind == 'full_network_dynamic' else
        {'input_flux_um_per_h':inputs['input_flux_um_per_h'],
         'secretion_rate_per_h':inputs['secretion_rate_per_h'],
         'secretion_normalization':inputs['secretion_normalization']})
    return DesignComparisonContract(model_kind=contract.model_kind,formula_version=contract.formula_version,
        metric_definition=definition,metric_unit=unit,normalization=contract.normalization,
        measurement_compartment=experiment.get('measurement_compartment'),assay_mode=experiment.get('assay_mode'),
        expression_mode=experiment.get('expression_mode'),input_boundary=experiment.get('input_boundary',{}),input_definition=boundary,
        assay_conditions=experiment.get('assay_conditions',{}),
        interval_h=contract.solver_settings.get('t_end'),
        steady_state_observation_reference=experiment.get('steady_state_observation_reference'))


class FiniteDesignPlan(ScientificAnalysisInput):
    candidates: list[ScaffoldCandidate] = Field(min_length=1)
    objective: Literal["yield_abs", "productivity"]
    minimum_metrics: dict[str,float] = Field(default_factory=dict)
    maximum_metrics: dict[str,float] = Field(default_factory=dict)
    objective_reference: str = Field(min_length=1)
    decision_id: str = Field(min_length=1)
    decision_scope: Literal["formal_conditional_mechanism", "software_fixture_only", "exploratory_sensitivity"]
    comparison_contract: DesignComparisonContract | None = None
    varying_design_factors: list[Literal["idr", "linker", "site_topology", "localization"]] = Field(default_factory=list)

    @model_validator(mode="after")
    def explicit_formal_comparison(self):
        if self.decision_scope == "formal_conditional_mechanism" and self.comparison_contract is None:
            raise ValueError("formal_decision_requires_comparison_contract")
        return self


def scan_scaffold_designs(plan: FiniteDesignPlan, output_dir: Path) -> dict:
    from .pipeline import load_config, run_through_m4
    rows = []
    for index, candidate in enumerate(plan.candidates):
        try:
            raw = candidate.config_path.read_bytes()
            config = load_config(candidate.config_path)
            config.run.id = f"scan-{index}"
            config.run.output_dir = output_dir
            manifest, predictions = run_through_m4(config)
            prediction = next((p for p in predictions if p.candidate_id==candidate.candidate_id),None)
            if prediction is None or prediction.status!="valid" or prediction.candidate_context is None:
                raise ValueError("candidate_not_valid_after_fresh_M1_M2_M3_M4")
            context = prediction.candidate_context
            if (context.candidate_id,context.construct_id,context.condition_id) != (
                    prediction.candidate_id,prediction.construct_id,prediction.condition_id):
                raise ValueError('M3_M4_candidate_identity_mismatch')
            formal = plan.decision_scope == 'formal_conditional_mechanism'
            grades = {'evidence_ready':prediction.evidence_ready,'data_quality':prediction.data_quality,
                'claim_scope':prediction.claim_scope,'context_evidence_ready':context.evidence_ready,
                'context_claim_scope':context.claim_scope}
            comparison = None
            if formal and (not prediction.evidence_ready or not context.evidence_ready or
                    prediction.data_quality not in {'measured','fitted','literature','mixed'} or
                    prediction.claim_scope != 'conditional_mechanism' or context.claim_scope != 'conditional_mechanism' or
                    prediction.provenance_summary.get('assumption',0) or context.provenance_summary.get('assumption',0)):
                rows.append({'candidate':candidate.model_dump(mode='json'),'status':'rejected',
                    'error':'candidate_not_formally_eligible','evidence_grades':grades})
                continue
            if plan.comparison_contract is not None:
                comparison = _candidate_comparison(prediction,plan.objective)
                actual,expected = comparison.model_dump(),plan.comparison_contract.model_dump()
                # Independent steady references may differ; their presence is mandatory,
                # while the actual model and assay facts determine comparability.
                differences = [k for k in expected if k != 'steady_state_observation_reference' and actual[k] != expected[k]]
                if differences:
                    rows.append({'candidate':candidate.model_dump(mode='json'),'status':'rejected',
                        'error':'incompatible_comparison_contract:'+','.join(differences),
                        'comparison_contract':actual,'evidence_grades':grades})
                    continue
            counts = context.nominal_site_counts
            if not counts or counts.get("PDZ",0)==0 or counts.get("SH3")/counts["PDZ"]!=candidate.site_ratio:
                raise ValueError("declared_scan_ratio_does_not_match_candidate_M2_site_counts")
            metrics = {"yield_abs":prediction.yield_abs, "productivity":prediction.productivity}
            metrics.update(prediction.mechanistic_diagnostics)
            required_metrics = set(plan.minimum_metrics) | set(plan.maximum_metrics) | {plan.objective}
            missing = [k for k in required_metrics if k not in metrics or metrics[k] is None]
            if missing:
                raise ValueError('missing_or_unknown_decision_metrics:'+','.join(sorted(missing)))
            feasible = metrics[plan.objective] is not None and all(metrics.get(k) is not None and metrics[k]>=v for k,v in plan.minimum_metrics.items()) and all(metrics.get(k) is not None and metrics[k]<=v for k,v in plan.maximum_metrics.items())
            oc,dmt = context.enzyme_distribution["OC"]["dense"],context.enzyme_distribution["DMT"]["dense"]
            rows.append({"candidate":candidate.model_dump(mode="json"),"status":"valid","feasible":feasible,
                "metrics":metrics,"dense_oc_dmt_ratio":oc/dmt if dmt else None,"context":context.model_dump(),
                "config_sha256":sha256(raw).hexdigest(),"manifest":manifest.model_dump(mode="json"),
                "expression_cost":"not_evaluated_without_declared_cost_model"})
            rows[-1].update(evidence_grades=grades,comparison_contract=comparison.model_dump() if comparison else None)
        except (ValueError,RuntimeError,OSError) as error:
            rows.append({"candidate":candidate.model_dump(mode="json"),"status":"failed","error":str(error)})
    feasible = [row for row in rows if row.get("feasible")]
    best = max(feasible,key=lambda row:row["metrics"][plan.objective]) if feasible else None
    formal = plan.decision_scope == 'formal_conditional_mechanism'
    return {"schema_version":"finite-scaffold-scan-v2","scaffold_scan":rows,
        "design_decision":{"decision_id":plan.decision_id,"objective":plan.objective,"objective_reference":plan.objective_reference,
            "constraints":{"minimum":plan.minimum_metrics,"maximum":plan.maximum_metrics},
            "selected_candidate":best["candidate"] if best else None,"r_target":best["dense_oc_dmt_ratio"] if best and formal else None,
            "exploratory_dense_ratio":best["dense_oc_dmt_ratio"] if best and not formal else None,
            "decision_scope":plan.decision_scope,"comparison_contract":plan.comparison_contract.model_dump() if plan.comparison_contract else None,
            "varying_design_factors":plan.varying_design_factors,
            "scope":"finite_evidence_covered_candidates_not_global_optimum_or_wetlab_validation"}}
