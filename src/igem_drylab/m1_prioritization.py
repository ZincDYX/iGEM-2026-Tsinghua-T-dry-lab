"""M1 soft risk and IDR prioritization with caller-reviewed rules only."""
from typing import Literal
from pathlib import Path

from pydantic import Field, model_validator

from .design_analysis import ScientificAnalysisInput
from .constructs.linker_features import M1ScreenResult
from .constructs.tool_evidence import ToolEvidenceProvenance, verify_artifact


class RiskPredicate(ScientificAnalysisInput):
    rule_id: str
    feature: str
    transform: Literal["identity","absolute"]
    operator: Literal["lt","le","gt","ge","inside","outside"]
    lower: float
    upper: float | None = None

    @model_validator(mode="after")
    def bounds(self):
        if self.operator in {"inside","outside"} and (self.upper is None or self.upper < self.lower):
            raise ValueError("risk_interval_requires_ordered_bounds")
        return self


class PredictorRule(ScientificAnalysisInput):
    tool: Literal["FuzDrop","catGRANULE_2016","PSPredictor","PScore","Mpipi_original"]
    normalization_minimum: float
    normalization_maximum: float
    high_direction: Literal["greater_equal","less_equal"]
    normalized_high_cutoff: float = Field(ge=0,le=1)
    weight: float = Field(ge=0)

    @model_validator(mode="after")
    def span(self):
        if self.normalization_maximum <= self.normalization_minimum:
            raise ValueError("normalization_requires_strict_positive_reviewed_span")
        return self


class PrioritizationPolicy(ScientificAnalysisInput):
    policy_version: str
    source_reference: str = Field(min_length=1)
    reviewer: str = Field(min_length=1)
    risk_rules: dict[str,list[RiskPredicate]]
    predictor_rules: list[PredictorRule] = Field(default_factory=list)
    # Original proposal does not specify the three key definitions/order.
    sort_keys: list[Literal["risk","consensus","rank_score"]] = Field(default_factory=list)
    ranking_formula_reference: str | None = None

    @model_validator(mode="after")
    def original_ranking(self):
        if self.predictor_rules:
            names = [r.tool for r in self.predictor_rules]
            if len(set(names)) != len(names) or set(names)-{"PSPredictor","PScore"} != {"FuzDrop","catGRANULE_2016","Mpipi_original"} or len(set(names)&{"PSPredictor","PScore"}) != 1:
                raise ValueError("original_ranking_requires_FuzDrop_catGRANULE2016_one_PSPredictor_or_PScore_and_original_Mpipi")
            if sum(r.weight for r in self.predictor_rules) <= 0 or set(self.sort_keys) != {"risk","consensus","rank_score"} or len(self.sort_keys)!=3 or not self.ranking_formula_reference:
                raise ValueError("ranking_requires_reviewed_positive_weights_and_three_explicit_sort_keys")
        return self


class PredictorScore(ScientificAnalysisInput):
    tool: Literal["FuzDrop","catGRANULE_2016","PSPredictor","PScore","Mpipi_original"]
    tool_version: str
    input_sequence_sha256: str
    source_file: Path
    raw_score: float
    provenance: ToolEvidenceProvenance


class PrioritizationCandidate(ScientificAnalysisInput):
    candidate_id: str
    screen: M1ScreenResult
    predictors: list[PredictorScore] = Field(default_factory=list)
    linker_design_checklist: dict[str,str] = Field(default_factory=dict)
    linker_rubric_reference: str | None = None


class M1PrioritizationInput(ScientificAnalysisInput):
    candidates: list[PrioritizationCandidate] = Field(min_length=1)
    policy: PrioritizationPolicy


def prioritize_m1(payload: M1PrioritizationInput) -> dict:
    rows = []
    for candidate in payload.candidates:
        screen = candidate.screen
        values = screen.features.model_dump()
        values.update(polar_plus_charged_fraction=screen.features.polar_fraction+screen.features.charged_fraction)
        if screen.seg:
            values["seg_low_complexity_fraction"]=screen.seg.low_complexity_fraction
        rules = payload.policy.risk_rules.get(screen.sequence_kind)
        missing, hits = [], []
        if not rules:
            missing.append("reviewed_complete_risk_directions_for_sequence_kind")
        for rule in rules or []:
            value = values.get(rule.feature)
            if value is None:
                missing.append("defined_algorithm_or_observation:"+rule.feature)
                continue
            value = abs(value) if rule.transform=="absolute" else value
            condition = {"lt":lambda:value<rule.lower,"le":lambda:value<=rule.lower,
                "gt":lambda:value>rule.lower,"ge":lambda:value>=rule.lower,
                "inside":lambda:rule.lower<=value<=rule.upper,
                "outside":lambda:not rule.lower<=value<=rule.upper}[rule.operator]()
            if condition:
                hits.append(rule.rule_id)
        risk = None if missing else "low" if not hits else "medium" if len(hits)==1 else "high"
        row = dict(candidate_id=candidate.candidate_id,sequence_kind=screen.sequence_kind,risk=risk,risk_hits=hits,
            missing=missing,normalized_scores={},consensus=None,rank_score=None,sort_key=None,
            policy_version=payload.policy.policy_version,policy_source=payload.policy.source_reference,
            eligible_for_ranking=screen.verdict=="pass" and risk in {"low","medium"})
        if screen.sequence_kind != "idr":
            row.update(linker_checklist=candidate.linker_design_checklist,linker_rubric_reference=candidate.linker_rubric_reference,
                rank_score_reason="original_linker_checklist_and_rubric_no_composite_score")
        elif row["eligible_for_ranking"]:
            scores = {r.tool:r for r in candidate.predictors}
            if len(scores)!=len(candidate.predictors):
                raise ValueError("duplicate_predictor_score")
            rules = payload.policy.predictor_rules
            if not rules:
                row["missing"].append("reviewed_original_predictor_normalization_weights_and_sort_order")
            high = []
            for rule in rules:
                observation = scores.get(rule.tool)
                if observation is None:
                    row["missing"].append("original_predictor_output:"+rule.tool)
                    continue
                if observation.input_sequence_sha256 != screen.features.sequence_sha256 or not verify_artifact(
                        observation.provenance,observation.source_file,observation.tool,observation.tool_version,
                        screen.features.sequence_sha256,{"raw_score":observation.raw_score}):
                    raise ValueError("ranking_requires_exact_input_and_raw_score_review:"+rule.tool)
                if observation.tool=="PScore":
                    # The native runner records sequence identity and raw bytes;
                    # extract the global value again rather than trust a scalar.
                    import re
                    raw=observation.source_file.read_text()
                    native_scores=re.findall(r"(?:^|<br>)\s*PScore:\s*(-?\d+(?:\.\d+)?)\s*$",raw)
                    if len(native_scores)!=1 or float(native_scores[0]) != observation.raw_score:
                        raise ValueError("PScore_native_global_score_mismatch")
                elif observation.provenance.origin!="manual_review":
                    raise ValueError("predictor_requires_version_specific_parser_or_raw_value_review:"+rule.tool)
                normalized = (observation.raw_score-rule.normalization_minimum)/(rule.normalization_maximum-rule.normalization_minimum)
                if not 0<=normalized<=1:
                    row["missing"].append("score_outside_reviewed_normalization_range:"+rule.tool)
                    continue  # no clamping/repair
                row["normalized_scores"][rule.tool]=normalized
                high.append(normalized>=rule.normalized_high_cutoff if rule.high_direction=="greater_equal" else normalized<=rule.normalized_high_cutoff)
            if rules and not row["missing"]:
                row["consensus"]=sum(high)/len(high)
                row["rank_score"]=sum(row["normalized_scores"][r.tool]*r.weight for r in rules)/sum(r.weight for r in rules)
                row["rank_formula"]="sum(reviewed_weight*normalized_raw_score)/sum(reviewed_weight)"
                values = {"risk":{"low":0,"medium":1}[risk],"consensus":-row["consensus"],"rank_score":-row["rank_score"]}
                row["sort_key"]=[values[key] for key in payload.policy.sort_keys]
        rows.append(row)
    ranked = sorted((r for r in rows if r["sort_key"] is not None),key=lambda r:(r["sort_key"],r["candidate_id"]))
    return {"schema_version":"m1-reviewed-prioritization-v1","candidates":rows,
        "ranked_IDR_candidate_ids":[r["candidate_id"] for r in ranked],
        "scope":"reviewed_design_rules_not_LLPS_probability_or_functional_validation"}
