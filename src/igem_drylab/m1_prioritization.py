"""Reviewed M1 risk, original weighted ranking or adopted descriptive comparison."""
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
    operator: Literal["lt","le","gt","ge","inside","outside","half_open_inside"]
    lower: float
    upper: float | None = None

    @model_validator(mode="after")
    def bounds(self):
        if self.operator in {"inside","outside","half_open_inside"} and (self.upper is None or self.upper < self.lower):
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
    comparison_mode: Literal['original_weighted','descriptive_pareto'] = 'original_weighted'
    undefined_risk_features: list[str] = Field(default_factory=list)
    comparison_group_reference: str | None = None
    fuzdrop_threshold: Literal[0.60,0.61] = 0.60
    predictor_rules: list[PredictorRule] = Field(default_factory=list)
    # Original proposal does not specify the three key definitions/order.
    sort_keys: list[Literal["risk","consensus","rank_score"]] = Field(default_factory=list)
    ranking_formula_reference: str | None = None

    @model_validator(mode="after")
    def original_ranking(self):
        if self.comparison_mode=='descriptive_pareto':
            if self.predictor_rules or self.sort_keys or not self.comparison_group_reference:
                raise ValueError('descriptive_comparison_requires_named_cohort_no_weights_or_legacy_sort_keys')
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

    @model_validator(mode="after")
    def distinct_candidates(self):
        if len({row.candidate_id for row in self.candidates}) != len(self.candidates):
            raise ValueError("M1_ranking_requires_distinct_candidate_identities")
        return self


def prioritize_m1(payload: M1PrioritizationInput) -> dict:
    rows = []
    for candidate in payload.candidates:
        screen = candidate.screen
        values = screen.features.model_dump()
        values.update(polar_plus_charged_fraction=screen.features.polar_fraction+screen.features.charged_fraction)
        if screen.seg:
            values["seg_low_complexity_fraction"]=screen.seg.low_complexity_fraction
        rules = payload.policy.risk_rules.get(screen.sequence_kind)
        missing, hits = ['undefined_risk_direction:'+f for f in payload.policy.undefined_risk_features], []
        if not rules:
            missing.append("reviewed_complete_risk_directions_for_sequence_kind")
        for rule in rules or []:
            value = values.get(rule.feature)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                missing.append("defined_algorithm_or_observation:"+rule.feature)
                continue
            value = abs(value) if rule.transform=="absolute" else value
            condition = {"lt":lambda:value<rule.lower,"le":lambda:value<=rule.lower,
                "gt":lambda:value>rule.lower,"ge":lambda:value>=rule.lower,
                "inside":lambda:rule.lower<=value<=rule.upper,
                'half_open_inside':lambda:rule.lower<=value<rule.upper,
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
        elif row["eligible_for_ranking"] and payload.policy.comparison_mode=='original_weighted':
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
                _verify_predictor(observation,screen.features.sequence_sha256)
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
    if payload.policy.comparison_mode=='descriptive_pareto':
        _describe_comparison(payload,rows)
    ranked = sorted((r for r in rows if r["sort_key"] is not None),key=lambda r:(r["sort_key"],r["candidate_id"]))
    return {"schema_version":"m1-reviewed-prioritization-v1","candidates":rows,
        "ranked_IDR_candidate_ids":[r["candidate_id"] for r in ranked],
        "scope":"reviewed_design_rules_not_LLPS_probability_or_functional_validation"}


def _verify_predictor(observation: PredictorScore, digest: str):
    if observation.input_sequence_sha256!=digest or not verify_artifact(observation.provenance,
            observation.source_file,observation.tool,observation.tool_version,digest,{'raw_score':observation.raw_score}):
        raise ValueError('ranking_requires_exact_input_and_raw_score_review:'+observation.tool)
    if observation.tool=='PScore':
        import re
        values=re.findall(r'(?:^|<br>)\s*PScore:\s*(-?\d+(?:\.\d+)?)\s*$',observation.source_file.read_text())
        if len(values)!=1 or float(values[0])!=observation.raw_score:raise ValueError('PScore_native_global_score_mismatch')
    elif observation.tool in {'FuzDrop','catGRANULE_2016'}:
        import json
        from .llps_artifacts import verify_native_predictor_score
        record=json.loads(observation.provenance.record_file.read_text())
        if record.get('native_format') or observation.provenance.origin!='manual_review':verify_native_predictor_score(observation)
    elif observation.provenance.origin!='manual_review':
        raise ValueError('predictor_requires_version_specific_parser_or_raw_value_review:'+observation.tool)


def _describe_comparison(payload,rows):
    """Adopted 2026-10-14 alternative, not the original weighted formula.

    Group by exact length and observed tools. Deduplicate identical sequence
    aliases; compare raw vector dominance, with no missing-value imputation.
    Incomplete screens/risk remain incomplete even when a table is available.
    """
    required={'FuzDrop','catGRANULE_2016','PScore'}
    groups={};deduplicated={}
    for candidate,row in zip(payload.candidates,rows):
        row.update(comparison_method='descriptive_midrank_and_Pareto_v1',raw_scores={},
            library_percentiles={},pareto_layer=None,risk_complete=row['risk'] is not None,
            rank_score=None,sort_key=None,eligible_for_ranking=False,hard_screen=candidate.screen.verdict,
            comparison_group_reference=payload.policy.comparison_group_reference)
        if candidate.screen.sequence_kind!='idr':continue
        for observation in candidate.predictors:
            if observation.tool not in required:continue  # Simulations remain a distinct physical branch.
            if observation.tool in row['raw_scores']:raise ValueError('duplicate_predictor_score')
            _verify_predictor(observation,candidate.screen.features.sequence_sha256)
            row['raw_scores'][observation.tool]=observation.raw_score
        scores=row['raw_scores'];observed=set(scores)
        positive=[];high=[]
        for tool,value in scores.items():
            if tool=='catGRANULE_2016':positive.append(value>0);high.append(value>1)
            else:
                cutoff=payload.policy.fuzdrop_threshold if tool=='FuzDrop' else 4.
                positive.append(value>=cutoff);high.append(value>=cutoff)
        row.update(positive_votes=sum(positive),high_reference_votes=sum(high),observed_predictors=len(scores),
            coverage=len(scores)/3,consensus=None if not scores else sum(high)/len(scores),
            original_reference_thresholds={'FuzDrop':payload.policy.fuzdrop_threshold,'catGRANULE_positive':'>0',
                'catGRANULE_high':'>1','PScore':'>=4'},
            fuzdrop_threshold_sensitivity={str(c):scores['FuzDrop']>=c for c in (.60,.61)} if 'FuzDrop' in scores else {},
            extrapolation='artificial_or_excised_FUS_IDRs_not_independently_validated')
        row['missing'].extend('original_predictor_output:'+name for name in sorted(required-observed))
        digest=candidate.screen.features.sequence_sha256
        if digest in deduplicated:
            first=deduplicated[digest]
            if first['raw_scores']!=scores or first['hard_screen']!=row['hard_screen'] or first['risk_hits']!=row['risk_hits']:
                raise ValueError('identical_sequence_aliases_have_conflicting_evidence_or_screens')
            first.setdefault('aliases',[]).append(row['candidate_id']);row['alias_of']=first['candidate_id']
        else:
            deduplicated[digest]=row
            key=(candidate.screen.features.length,tuple(sorted(observed)))
            groups.setdefault(key,[]).append(row)
    for (length,tools),cohort in groups.items():
        for tool in tools:
            values=[r['raw_scores'][tool] for r in cohort]
            for row,value in zip(cohort,values):
                rank=1+sum(v<value for v in values)+(sum(v==value for v in values)-1)/2
                row['library_percentiles'][tool]=(rank-1)/(len(values)-1) if len(values)>1 else None
        remaining=list(cohort);layer=1
        while remaining and tools:
            front=[r for r in remaining if not any(all(p['raw_scores'][t]>=r['raw_scores'][t] for t in tools)
                and any(p['raw_scores'][t]>r['raw_scores'][t] for t in tools) for p in remaining)]
            for row in front:row['pareto_layer']=layer
            remaining=[r for r in remaining if r not in front];layer+=1
        for row in cohort:
            row['comparison_group']=dict(length=length,observed_tools=list(tools),unique_sequences=len(cohort))
    for row in rows:
        if row.get('alias_of'):
            first=next(r for r in rows if r['candidate_id']==row['alias_of'])
            for key in ('pareto_layer','library_percentiles','comparison_group'):row[key]=first.get(key)
