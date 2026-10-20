"""Original M4 F1--F3 reporting over the existing conservative kernels.

Sampling bounds and design evidence belong to callers. No source example
numbers, channeling multipliers, fitted constants or decision scores are added.
"""
from __future__ import annotations

from copy import deepcopy
import csv
from math import isclose
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .design_analysis import M4AnalysisConfig, ScientificAnalysisInput, analyze_response
from .m3_equilibrium import M3EquilibriumInput, solve_m3_equilibrium
from .m4_steady_state import M4SteadyStateInput, solve_m4_steady_state
from .compartments import ArtifactReference


M3_SAMPLE_PARAMETERS = {"phi":"1", "c_dense_um":"uM", "c_scaffold_total_um":"uM", "c_sat_um":"uM",
    "kd_sh3_um":"uM", "kd_pdz_um":"uM", "k_oc":"1", "k_dmt":"1", "c_oc_total_um":"uM", "c_dmt_total_um":"uM"}


class JointSampleColumn(ScientificAnalysisInput):
    column: str = Field(min_length=1)
    stage: Literal["m3", "m4"]
    parameter_name: str
    parameter_id: str = Field(min_length=1)
    unit: Literal["1", "uM", "1/h"]

    @model_validator(mode="after")
    def supported_quantity(self):
        m4_units = {**{f"partition_x{i}":"1" for i in range(8,16)},
                    **{f"kcat_r{i}":"1/h" for i in range(1,11)}, **{f"km_r{i}":"uM" for i in range(1,11)}}
        if (M3_SAMPLE_PARAMETERS if self.stage=="m3" else m4_units).get(self.parameter_name) != self.unit:
            raise ValueError("joint_sample_unsupported_parameter_or_noncanonical_unit")
        return self


class M3M4JointSamples(ScientificAnalysisInput):
    construct_id: str
    condition_id: str
    source: ArtifactReference
    source_reference: str = Field(min_length=1)
    reviewed_by: str = Field(min_length=1)
    columns: list[JointSampleColumn] = Field(min_length=1)
    sample_basis: Literal["paired_observations", "supplied_joint_model_draws"]
    sampling_method_reference: str = Field(min_length=1)

    @model_validator(mode="after")
    def unique_mapping(self):
        names=[c.column for c in self.columns]
        targets=[(c.stage,c.parameter_name) for c in self.columns]
        if "sample_id" in names or len(names)!=len(set(names)) or len(targets)!=len(set(targets)):
            raise ValueError("joint_sample_columns_and_targets_must_be_unique")
        return self


def _joint_uncertainty(steady, recruitment, settings):
    """Preserve each supplied row and its correlations; no invented distributions."""
    if (settings.construct_id,settings.condition_id)!=(steady.construct_id,steady.condition_id):
        raise ValueError("joint_samples_construct_or_condition_mismatch")
    if (recruitment.construct_id,recruitment.candidate_id)!=(steady.construct_id,steady.candidate_id):
        raise ValueError("joint_recruitment_identity_mismatch")
    baseline=solve_m3_equilibrium(recruitment)
    if not baseline.m4_ready or baseline.oc is None or baseline.dmt is None:
        raise ValueError("joint_baseline_M3_not_ready")
    for enzyme,species in (("OC",baseline.oc),("DMT",baseline.dmt)):
        phase=steady.enzymes[enzyme]
        if not isclose(steady.phi,baseline.phi,rel_tol=1e-10,abs_tol=1e-12) or not all(
            isclose(a,b,rel_tol=1e-10,abs_tol=1e-12) for a,b in
            ((phase.dense_um,species.total_dense_um),(phase.dilute_um,species.free_dilute_um))):
            raise ValueError("joint_baseline_M4_must_match_actual_M3_distribution")
    names={c.parameter_name for c in settings.columns if c.stage=="m3"}
    if recruitment.phi is not None and names & {"c_scaffold_total_um","c_sat_um"}:
        raise ValueError("joint_lever_rule_uncertainty_cannot_be_hidden_by_fixed_phi")
    settings.source.verify()
    samples=[]
    seen=set()
    with settings.source.path.open(encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream)
        expected={"sample_id",*(c.column for c in settings.columns)}
        if reader.fieldnames is None or set(reader.fieldnames)!=expected or len(reader.fieldnames)!=len(expected):
            raise ValueError("joint_sample_CSV_header_must_match_explicit_columns")
        for row in reader:
            identifier=row["sample_id"]
            if not identifier or identifier in seen:
                raise ValueError("joint_sample_ids_must_be_nonempty_and_unique")
            seen.add(identifier)
            result={"sample_id":identifier,"source_values":dict(row),"status":"invalid_input",
                    "recruitment":None,"scenarios":None}
            try:
                values={c.column:float(row[c.column]) for c in settings.columns}
                raw=recruitment.model_dump(mode="json")
                raw.update({c.parameter_name:values[c.column] for c in settings.columns if c.stage=="m3"})
                m3=solve_m3_equilibrium(M3EquilibriumInput.model_validate(raw))
                result["recruitment"]={"status":m3.status,"phi":m3.phi,"oc":m3.oc.model_dump() if m3.oc else None,
                    "dmt":m3.dmt.model_dump() if m3.dmt else None,"m4_ready":m3.m4_ready,"warnings":m3.warnings}
                if not m3.m4_ready or m3.oc is None or m3.dmt is None:
                    result["status"]="M3_not_ready"
                else:
                    sampled=_sampled_input(steady,{c.parameter_name:values[c.column] for c in settings.columns if c.stage=="m4"})
                    case=sampled.model_dump(mode="json")
                    case["phi"]=m3.phi
                    for enzyme,species in (("OC",m3.oc),("DMT",m3.dmt)):
                        case["enzymes"][enzyme].update(dense_um=species.total_dense_um,dilute_um=species.free_dilute_um)
                    scenarios=_solve_scenarios(M4SteadyStateInput.model_validate(case))
                    result["scenarios"]={name:{key:r[key] for key in ("status","yield_abs","secretion_loss_8_to_14")} for name,r in scenarios.items()}
                    result["status"]="valid" if all(r["status"]=="valid" for r in scenarios.values()) else "M4_not_ready"
            except (ValueError, RuntimeError, TypeError) as error:
                result["error"]=str(error)
            samples.append(result)  # Invalid samples are retained, never replaced.
    if len(samples)<2:
        raise ValueError("joint_uncertainty_requires_at_least_two_supplied_rows")
    valid=[r for r in samples if r["status"]=="valid"]
    envelopes={}
    for scenario in ("H0","recruit_only","directional"):
        metrics={"yield_abs":[r["scenarios"][scenario]["yield_abs"] for r in valid],
                 "secretion_loss":[r["scenarios"][scenario]["secretion_loss_8_to_14"] for r in valid],
                 "yield_rel":[r["scenarios"][scenario]["yield_abs"]/r["scenarios"]["H0"]["yield_abs"] for r in valid
                    if r["scenarios"]["H0"]["yield_abs"] is not None and r["scenarios"]["H0"]["yield_abs"]>0]}
        envelopes[scenario]={metric:{"lo":min(values) if values else None,"hi":max(values) if values else None,"valid_samples":len(values)} for metric,values in metrics.items()}
    return {"schema_version":"m3-m4-joint-samples-v1","samples":samples,"intervals":envelopes,
        "valid_samples":len(valid),"failed_samples":len(samples)-len(valid),"complete":len(valid)==len(samples),
        "scope":"all_samples" if len(valid)==len(samples) else "conditional_on_valid_samples",
        "method":"supplied_paired_rows_M3_recomputed_before_M4_not_independent_LHS_or_confidence_interval",
        "source":settings.model_dump(mode="json"),"claim_scope":"conditional_cytosolic_model_not_project_validation"}


class ScaffoldScenario(ScientificAnalysisInput):
    site_ratio: Literal[1, 2, 3, 4, 6]
    recruitment: M3EquilibriumInput
    design_reference: str = Field(min_length=1)
    synthesized: bool

    @model_validator(mode="after")
    def actual_ratio(self):
        if not self.recruitment.s_pdz or self.recruitment.s_sh3 / self.recruitment.s_pdz != self.site_ratio:
            raise ValueError("scan_ratio_must_match_declared_M2_site_counts")
        return self


class M4ReportInput(ScientificAnalysisInput):
    steady_input: M4SteadyStateInput
    recruitment_input: M3EquilibriumInput | None = None
    joint_samples: M3M4JointSamples | None = None
    analysis: M4AnalysisConfig | None = None
    scaffold_designs: list[ScaffoldScenario] = Field(default_factory=list)
    candidate_kp_spectra: dict[str, dict[str, float]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def comparable_scans(self):
        if (self.recruitment_input is None)!=(self.joint_samples is None):
            raise ValueError("joint_samples_require_actual_M3_recruitment_input")
        # A scan varies site topology, not expression, medium or affinity.
        fields = ("c_oc_total_um", "c_dmt_total_um", "k_oc", "k_dmt", "kd_sh3_um", "kd_pdz_um",
                  "c_dense_um", "phi", "c_scaffold_total_um", "c_sat_um", "site_count_basis", "c_dense_basis")
        if self.scaffold_designs:
            first = self.scaffold_designs[0].recruitment
            if any(any(getattr(row.recruitment, k) != getattr(first, k) for k in fields)
                   for row in self.scaffold_designs[1:]):
                raise ValueError("scan_requires_condition_matched_recruitment_inputs")
            phi = first.phi if first.phi is not None else (first.c_scaffold_total_um-first.c_sat_um)/(first.c_dense_um-first.c_sat_um)
            if phi != self.steady_input.phi:
                raise ValueError("scan_phi_must_match_M4_base_condition")
            for enzyme,total in (("OC",first.c_oc_total_um),("DMT",first.c_dmt_total_um)):
                phase=self.steady_input.enzymes[enzyme]
                if not isclose(phi*phase.dense_um+(1-phi)*phase.dilute_um,total,rel_tol=1e-10,abs_tol=1e-12):
                    raise ValueError("scan_requires_same_OC_DMT_total_expression_as_M4_base")
        for spectrum in self.candidate_kp_spectra.values():
            if set(spectrum) != {str(i) for i in range(8, 16)} or any(v <= 0 for v in spectrum.values()):
                raise ValueError("feasibility_requires_complete_positive_candidate_Kp8_to_Kp15")
        return self


def _scenario_inputs(base: M4SteadyStateInput) -> dict[str, M4SteadyStateInput]:
    recruit = base.model_dump(mode="json")
    recruit["metabolite_kp"] = {name: 1.0 for name in base.metabolite_kp}
    h0 = deepcopy(recruit)
    h0["phi"] = 0.0
    for enzyme, phase in h0["enzymes"].items():
        original = base.enzymes[enzyme]
        # OC/DMT are whole-cell totals; PTR/PT use the source's dilute
        # background definition. Do not silently repair that source ambiguity.
        phase["dilute_um"] = (base.phi * original.dense_um + (1-base.phi) * original.dilute_um
                              if enzyme in {"OC", "DMT"} else original.dilute_um)
        phase["dense_um"] = 0.0
    return {"H0": M4SteadyStateInput.model_validate(h0),
            "recruit_only": M4SteadyStateInput.model_validate(recruit), "directional": base}


def _sampled_input(base: M4SteadyStateInput, values: dict[str, float]) -> M4SteadyStateInput:
    raw = base.model_dump(mode="json")
    for name, value in values.items():
        if name.startswith("partition_x") and name[11:] in raw["metabolite_kp"]:
            raw["metabolite_kp"][name[11:]] = value
        elif name.startswith(("kcat_r", "km_r")):
            prefix, reaction = name.split("_", 1)
            row = next((r for r in raw["reactions"] if r["reaction_id"].lower() == reaction), None)
            if row is None:
                raise ValueError("unknown_analysis_reaction")
            row["kcat_per_h" if prefix == "kcat" else "km_um"] = value
        else:
            raise ValueError("original_report_unsupported_analysis_parameter:" + name)
    return M4SteadyStateInput.model_validate(raw)


def _base_value(base: M4SteadyStateInput, name: str) -> float:
    if name.startswith("partition_x") and name[11:] in base.metabolite_kp:
        return base.metabolite_kp[name[11:]]
    prefix, _, reaction = name.partition("_")
    row = next((r for r in base.reactions if r.reaction_id.lower() == reaction), None)
    if prefix not in {"km", "kcat"} or row is None:
        raise ValueError("original_report_unsupported_analysis_parameter:" + name)
    return row.kcat_per_h if prefix == "kcat" else row.km_um


def _solve_scenarios(base):
    return {name: solve_m4_steady_state(case).model_dump(mode="json")
            for name, case in _scenario_inputs(base).items()}


def run_m4_report(payload: M4ReportInput) -> dict:
    if any(e.activity_dense_ratio!=1 or e.activity_dilute_ratio!=1 for e in payload.steady_input.enzymes.values()):
        return {"schema_version":"m4-original-report-v1","status":"blocked","candidate_id":payload.steady_input.candidate_id,
            "missing":["matched_H0_activity_model_for_phase_specific_activity_extension"],
            "claim_scope":"original_three_scenario_controls_do_not_infer_activity_after_removing_droplet"}
    cases = _solve_scenarios(payload.steady_input)
    complete = all(row["status"] == "valid" for row in cases.values())
    output = {"schema_version": "m4-original-report-v1", "candidate_id": payload.steady_input.candidate_id,
              "status": "valid" if complete else "blocked", "scenarios": cases,
              "yield_abs": {k: v["yield_abs"] for k, v in cases.items()},
              "yield_rel": {}, "secretion_loss": {k: v["secretion_loss_8_to_14"] for k, v in cases.items()},
              "yield_baselines": {"H0": "condition_matched_uniform_OC_DMT_no_droplet",
                                  "theoretical_max": {"value": 1.0, "meaning": "stoichiometric_bound_not_a_solved_no_outlet_steady_state"}},
              "background_basis": "PTR_PT_original_dilute_background_not_reinterpreted_as_cell_average",
              "uncertainty": None, "analysis": None, "scaffold_scan": [],
              "expression_cost": None, "expression_cost_reason": "source_does_not_define_a_cost_formula",
              "kp_feasibility_raw": None, "claim_scope": "conditional_model_not_biological_validation"}
    h0 = cases["H0"]["yield_abs"]
    output["yield_rel"] = {k: v["yield_abs"]/h0 if v["yield_abs"] is not None and h0 else None
                           for k, v in cases.items()}
    if complete and payload.analysis is not None:
        evaluated = {}
        def evaluate(values):
            sampled = _solve_scenarios(_sampled_input(payload.steady_input, values))
            if any(row["status"] != "valid" for row in sampled.values()):
                raise ValueError("sample_has_no_valid_condition_matched_three_scenario_solution")
            evaluated[tuple(sorted(values.items()))] = {name:{key:row[key] for key in ("yield_abs","secretion_loss_8_to_14")}
                for name,row in sampled.items()}
            return sampled["directional"]["yield_abs"]
        names = set(payload.analysis.local_parameter_names) | {r.parameter_name for r in payload.analysis.ranges}
        analysis = analyze_response(payload.analysis, {n: _base_value(payload.steady_input, n) for n in names},
                                    evaluate, cases["directional"]["yield_abs"])
        output["analysis"] = analysis
        global_result = analysis["sensitivity"]["global"]
        if global_result:
            samples = global_result["samples"]
            valid = [evaluated[tuple(sorted(row["parameters"].items()))] for row in samples if row["status"] == "valid"]
            intervals = {}
            for scenario in cases:
                metrics = {"yield_abs": [row[scenario]["yield_abs"] for row in valid],
                           "secretion_loss": [row[scenario]["secretion_loss_8_to_14"] for row in valid],
                           "yield_rel": [row[scenario]["yield_abs"]/row["H0"]["yield_abs"]
                                         for row in valid if row["H0"]["yield_abs"] > 0]}
                intervals[scenario] = {metric: {"value": output[metric][scenario],
                    "lo": min(values) if values else None, "hi": max(values) if values else None,
                    "valid_samples": len(values)} for metric, values in metrics.items()}
            output["uncertainty"] = {"intervals": intervals, "method": "observed_LHS_envelope_not_confidence_interval",
                "complete": len(valid) == len(samples), "failed_samples": len(samples)-len(valid),
                "scope": "all_samples" if len(valid) == len(samples) else "conditional_on_valid_samples",
                "sensitivity_interval": None,
                "sensitivity_interval_reason": "one_LHS_Spearman_statistic_has_no_declared_resampling_interval"}
    if payload.joint_samples is not None:
        output["joint_uncertainty"]=_joint_uncertainty(payload.steady_input,payload.recruitment_input,payload.joint_samples)
    for design in payload.scaffold_designs:
        recruitment = solve_m3_equilibrium(design.recruitment)
        row = {"site_ratio": design.site_ratio, "design_reference": design.design_reference,
               "synthesized": design.synthesized, "recruitment": recruitment.model_dump(mode="json")}
        if not recruitment.m4_ready:
            row.update(status="blocked", yield_abs=None, yield_rel=None)
        else:
            raw = payload.steady_input.model_dump(mode="json")
            for enzyme, species in (("OC", recruitment.oc), ("DMT", recruitment.dmt)):
                raw["enzymes"][enzyme].update(dense_um=species.total_dense_um, dilute_um=species.free_dilute_um,
                                             m3_source_id=design.recruitment.candidate_id)
            solved = solve_m4_steady_state(M4SteadyStateInput.model_validate(raw))
            row.update(status=solved.status, yield_abs=solved.yield_abs,
                       yield_rel=solved.yield_abs/h0 if solved.yield_abs is not None and h0 else None,
                       result=solved.model_dump(mode="json"))
        output["scaffold_scan"].append(row)
    if payload.candidate_kp_spectra:
        ratios = {name: spectrum["14"]/spectrum["9"] for name, spectrum in payload.candidate_kp_spectra.items()}
        output["kp_feasibility_raw"] = {"achievable_Kp14_over_Kp9": max(ratios.values()), "candidate_ratios": ratios,
            "scope": "supplied_evidence_covered_candidates_not_global_chemical_bound"}
    return output
