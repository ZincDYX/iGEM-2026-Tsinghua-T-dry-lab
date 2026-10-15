"""Original M1 cheap -> predictor -> decision path on the durable DAG.

Only previously specified hard rules are applied. Fusion observations, soft
risk directions and ranking evidence are never synthesized by this path.
"""
from hashlib import sha256
from pathlib import Path
from typing import Literal

from pydantic import Field

from igem_drylab.constructs.linker_features import (M1FeatureDefinitions, M1V3Rules,
    DisorderEvidence, SegEvidence, SecondaryStructureEvidence, compute_sequence_features, compute_protparam_evidence,
    screen_sequence_v3, FusionToolEvidence)
from .models import Contract, SequenceRecord, Workflow, WorkflowNode, ProjectInput, NodeInput, MapSpec, LiteralInput
from .tools import NodeContext, ToolDefinition
from igem_drylab.resources import default_config_path
from igem_drylab.m1_prioritization import (PrioritizationPolicy, PrioritizationCandidate,
    M1PrioritizationInput, PredictorScore, ComparisonContext, prioritize_m1)
from igem_drylab.pipeline.config import ConstructDefinition
from igem_drylab.constructs.sequence_qc import assemble_and_validate_construct
from igem_drylab.constructs.linker_features import normalize_amino_acid_sequence


KINDS = {"idr", "enzyme_ligand_linker", "scaffold_linker", "rigid_linker", "full_fusion"}


class M1PrecheckInput(Contract):
    item: SequenceRecord
    feature_definitions: M1FeatureDefinitions
    rules: M1V3Rules


class M1DecisionInput(M1PrecheckInput):
    prioritization_policy: PrioritizationPolicy | None = None
    comparison_contexts: dict[str,ComparisonContext] = Field(default_factory=dict)
    prechecks: list[dict] = Field(default_factory=list)
    disorder_results: list[dict] = Field(default_factory=list)
    seg_results: list[dict] = Field(default_factory=list)
    secondary_results: list[dict] = Field(default_factory=list)
    signalp_results: list[dict] = Field(default_factory=list)
    topology_results: list[dict] = Field(default_factory=list)
    aggregation_results: list[dict] = Field(default_factory=list)
    pscore_results: list[dict] = Field(default_factory=list)
    catgranule_results: list[dict] = Field(default_factory=list)
    fuzdrop_results: list[dict] = Field(default_factory=list)
    llps_import_results: list[dict] = Field(default_factory=list)
    construct_context_results: list[dict] = Field(default_factory=list)


class M1ConstructContextInput(Contract):
    """Bind sourced ordered constructs to exact native full-fusion observations."""
    constructs: list[ConstructDefinition]
    sequences: list[SequenceRecord]
    feature_definitions: M1FeatureDefinitions
    rules: M1V3Rules
    signalp_results: list[dict] = Field(default_factory=list)
    topology_results: list[dict] = Field(default_factory=list)
    aggregation_results: list[dict] = Field(default_factory=list)


class IDRSubstitutionInput(Contract):
    """Explicitly authorized computational substitutions, not wet-lab records."""
    templates: list[ConstructDefinition] = Field(min_length=1)
    replacements: list[SequenceRecord] = Field(min_length=1)
    approval_reference: str = Field(min_length=1)


def substitute_declared_idrs(payload: IDRSubstitutionInput) -> dict:
    if len({s.id for s in payload.replacements})!=len(payload.replacements):
        raise ValueError('distinct_IDR_source_identities_required')
    constructs=[];sequences=[]
    for template in payload.templates:
        positions=[i for i,p in enumerate(template.parts) if p.kind=='idr']
        if len(positions)!=1 or template.localization_context is None:
            raise ValueError('substitution_requires_one_explicit_IDR_part_and_localization')
        position=positions[0]
        for replacement in payload.replacements:
            if replacement.role!='idr':raise ValueError('replacement_requires_explicit_IDR_role')
            amino_acids=normalize_amino_acid_sequence(replacement.sequence)
            if replacement.id in {p.id for i,p in enumerate(template.parts) if i!=position}:
                raise ValueError('replacement_identity_conflicts_with_an_unchanged_part')
            parts=[p.model_copy(deep=True) for p in template.parts]
            parts[position]=parts[position].model_copy(update={'id':replacement.id,'sequence':amino_acids})
            identifier=template.id+'__IDR_'+replacement.id
            part_ids={p.id for p in parts}
            provenance={**template.provenance,'computational_IDR_substitution':dict(
                approval_reference=payload.approval_reference,template_construct_id=template.id,
                replaced_part_id=template.parts[position].id,input_IDR_id=replacement.id,
                input_IDR_sequence_sha256=sha256(amino_acids.encode()).hexdigest(),
                modified_ordered_part_index=position,source_type='computational_design_not_wetlab_sequence')}
            data={**template.model_dump(mode='json'),'id':identifier,'parts':[p.model_dump() for p in parts],
                'idr_ids':[replacement.id],'coding_dna':None,'experimental_baseline':False,
                'm1_review':None,'membrane_topology':None,'provenance':provenance,
                'sequences':{**{k:v for k,v in template.sequences.items() if k in part_ids},replacement.id:amino_acids},
                'sequence_source_ref':'Computational substitution; '+payload.approval_reference+
                    '; template='+template.id+'; original IDR input='+replacement.id}
            construct=ConstructDefinition.model_validate(data)
            part_sequences={**construct.sequences,**{p.id:p.sequence for p in parts if p.sequence is not None}}
            qc=assemble_and_validate_construct(construct_id=identifier,ordered_part_ids=construct.ordered_part_ids(),
                part_sequences=part_sequences,coding_dna=None,forbidden_restriction_sites=None,require_sequence_evidence=False)
            if qc.errors:raise ValueError('computational_substitution_cannot_assemble:'+identifier)
            constructs.append(construct.model_dump(mode='json'))
            sequences.append(SequenceRecord(id=identifier,sequence=qc.full_protein_sequence,role='full_fusion',
                localization_context=construct.localization_context).model_dump(mode='json'))
    if len({c['id'] for c in constructs})!=len(constructs):raise ValueError('distinct_substitution_targets_required')
    return dict(constructs=constructs,sequences=sequences,count=len(constructs),
        scope='authorized_fixed_backbone_IDR_substitutions_not_experimental_baselines')


def _fusion_observations(item, collections):
    digest=sha256(item.sequence.encode()).hexdigest()
    merged=dict(input_sha256=digest,provenance={},native_formats={},native_rules={})
    for rows in collections:
        found=[row for row in rows if row.get('candidate_id')==item.id]
        if len(found)>1:raise ValueError('M1_duplicate_full_fusion_tool_result')
        if not found:continue
        if found[0].get('input_sequence_sha256')!=digest:
            raise ValueError('M1_predecessor_sequence_identity_mismatch')
        for key,value in (found[0].get('parsed') or {}).items():
            if key in {'provenance','native_formats','native_rules'}:merged[key].update(value)
            elif value is not None and value!=[]:
                if key in merged and merged[key]!=value:
                    raise ValueError('M1_conflicting_full_fusion_tool_observations')
                merged[key]=value
    return FusionToolEvidence.model_validate(merged)


def bind_construct_contexts(payload: M1ConstructContextInput) -> dict:
    """Use declared part boundaries, never substring matching or new designs.

    DNA/cloning QC remains independent of protein-tool negative screens. Missing
    CDS, cloning route or native evidence is retained, not inferred from an alias.
    """
    sequences={item.id:item for item in payload.sequences}
    if len(sequences)!=len(payload.sequences) or len({c.id for c in payload.constructs})!=len(payload.constructs):
        raise ValueError('M1_context_requires_distinct_input_identities')
    digest=sha256(payload.feature_definitions.model_dump_json().encode()).hexdigest()
    results=[]
    for construct in payload.constructs:
        parts={key:item.sequence for key,item in sequences.items()}
        for key,value in {**construct.sequences,**{p.id:p.sequence for p in construct.parts if p.sequence is not None}}.items():
            if key in parts and normalize_amino_acid_sequence(parts[key])!=normalize_amino_acid_sequence(value):
                raise ValueError('M1_declared_part_sequence_conflicts_with_project:'+key)
            parts[key]=value
        qc=assemble_and_validate_construct(construct_id=construct.id,ordered_part_ids=construct.ordered_part_ids(),
            part_sequences=parts,coding_dna=construct.coding_dna,
            forbidden_restriction_sites=construct.forbidden_restriction_sites,require_sequence_evidence=True)
        row=dict(construct_id=construct.id,source_reference=construct.sequence_source_ref,
            localization_context=construct.localization_context,sequence_qc=qc.model_dump(mode='json'),
            part_bindings=[],fusion_evidence=None,fusion_screen=None,missing=[])
        full=sequences.get(construct.id)
        if full is None:row['missing'].append('registered_complete_construct_sequence')
        elif full.role!='full_fusion' or qc.protein_sha256!=sha256(full.sequence.encode()).hexdigest():
            row['missing'].append('declared_parts_do_not_match_registered_complete_construct')
        if not construct.sequence_source_ref:row['missing'].append('construct_sequence_source_reference')
        if construct.localization_context is None:row['missing'].append('declared_construct_localization_context')
        elif full and construct.localization_context!=full.localization_context:
            row['missing'].append('construct_localization_context_mismatch')
        kinds={p.id:p.kind for p in construct.parts}
        kinds.update({key:'idr' for key in construct.idr_ids})
        for boundary in qc.part_boundaries:
            row['part_bindings'].append({**boundary.model_dump(),
                'sequence_sha256':sha256(normalize_amino_acid_sequence(parts[boundary.part_id]).encode()).hexdigest(),
                'kind':kinds.get(boundary.part_id)})
        if not row['missing'] and full is not None:
            fusion=_fusion_observations(full,(payload.signalp_results,payload.topology_results,payload.aggregation_results))
            features=compute_sequence_features(full.sequence,definitions=payload.feature_definitions,definitions_sha256=digest)
            screen=screen_sequence_v3(sequence=full.sequence,features=features,sequence_kind='full_fusion',
                rules=payload.rules,fusion_evidence=fusion,full_fusion_sha256=qc.protein_sha256,
                localization_context=full.localization_context)
            row.update(fusion_evidence=fusion.model_dump(mode='json'),fusion_screen=screen.model_dump(mode='json'))
        row['claim_scope']='construct_binding_and_full_fusion_screen_not_complete_M1_approval'
        results.append(row)
    return dict(items=results,count=len(results),scope='sourced_construct_context_not_automatic_M1_approval')


def _context_tool(payload: M1ConstructContextInput, context: NodeContext) -> dict:
    for rows in (payload.signalp_results,payload.topology_results,payload.aggregation_results):
        if rows and not any(parent['output'].get('items')==rows for parent in context.upstream_results):
            raise ValueError('M1_requires_registered_upstream_observations')
    return bind_construct_contexts(payload)


def screen_part_contexts(screen, sequence, rules, contexts):
    """Apply the same original screen separately to every declared context."""
    results=[]
    for bound in contexts:
        matched=[p for p in bound['part_bindings'] if p['kind']==screen.sequence_kind and p['sequence_sha256']==screen.features.sequence_sha256]
        if not matched or bound['missing'] or bound['localization_context']!=screen.localization_context:continue
        qc=bound['sequence_qc'];fusion_data=bound.get('fusion_evidence')
        if not fusion_data:continue
        contextual=screen_sequence_v3(features=screen.features,sequence=sequence,sequence_kind=screen.sequence_kind,
            rules=rules,disorder=screen.disorder,seg=screen.seg,secondary_structure=screen.secondary_structure,
            protparam=screen.protparam,fusion_evidence=FusionToolEvidence.model_validate(fusion_data),
            full_fusion_sha256=qc['protein_sha256'],full_fusion_sequence=qc['full_protein_sequence'],
            localization_context=screen.localization_context)
        results.append(dict(construct_id=bound['construct_id'],part_occurrences=matched,
            screen=contextual.model_dump(mode='json'),sequence_qc=qc,
            claim_scope='part_screen_in_declared_construct_not_complete_M1_approval'))
    return results


def precheck(payload: M1PrecheckInput, context: NodeContext) -> dict:
    digest = sha256(payload.feature_definitions.model_dump_json().encode()).hexdigest()
    features = compute_sequence_features(payload.item.sequence, definitions=payload.feature_definitions,
                                         definitions_sha256=digest)
    result = dict(candidate_id=payload.item.id, input_sequence_sha256=features.sequence_sha256,
                  sequence_kind=payload.item.role, localization_context=payload.item.localization_context,
                  features=features.model_dump(mode="json"),
                  eligible_for_tools=False, hard_reject_reasons=[], missing=[])
    if payload.item.role not in KINDS:
        result["missing"] = ["Explicit M1 role: idr / enzyme_ligand_linker / scaffold_linker / rigid_linker / full_fusion"]
        return result
    observed = screen_sequence_v3(features=features, sequence=payload.item.sequence,
        sequence_kind=payload.item.role, rules=payload.rules,
        localization_context=payload.item.localization_context, require_external_evidence=False)
    result["hard_reject_reasons"] = observed.hard_reject_reasons
    result["eligible_for_tools"] = not observed.hard_reject_reasons and payload.item.role != "full_fusion"
    return result


def decision(payload: M1DecisionInput, context: NodeContext) -> dict:
    observed = precheck(payload, context)
    # These file-bearing observations must be actual registered predecessors,
    # not browser-supplied literal dictionaries pointing at arbitrary files.
    for rows in (payload.prechecks, payload.disorder_results, payload.seg_results, payload.secondary_results,
                 *[r for r in (payload.signalp_results,payload.topology_results,payload.aggregation_results,
                    payload.pscore_results, payload.catgranule_results, payload.fuzdrop_results,payload.llps_import_results,
                    payload.construct_context_results) if r]):
        if not any(parent["output"].get("items") == rows for parent in context.upstream_results):
            raise ValueError("M1_requires_registered_upstream_observations")
    def selected(rows):
        found = [row for row in rows if row.get("candidate_id") == payload.item.id]
        if len(found) != 1:
            raise ValueError("M1_each_candidate_requires_one_registered_predecessor_result")
        row = found[0]
        if row.get("input_sequence_sha256") != observed["input_sequence_sha256"]:
            raise ValueError("M1_predecessor_sequence_identity_mismatch")
        return row
    if selected(payload.prechecks) != observed:
        raise ValueError("M1_precheck_result_does_not_match_original_rules")
    from igem_drylab.constructs.linker_features import SequenceFeatures
    features = SequenceFeatures.model_validate(observed["features"])
    disorder = selected(payload.disorder_results)
    seg = selected(payload.seg_results)
    secondary = selected(payload.secondary_results)
    fusion = None
    if payload.item.role == "full_fusion":
        fusion=_fusion_observations(payload.item,(payload.signalp_results,payload.topology_results,payload.aggregation_results))
    if observed["missing"]:
        return dict(schema_version="m1-method-check-v1", candidate_id=payload.item.id,
                    verdict="blocked", precheck=observed, missing=observed["missing"], screen=None)
    secondary_evidence=secondary.get('parsed')
    if secondary.get('method_applicability')=='no_reported_homologs_not_a_calibrated_hard_veto':
        secondary_evidence=None  # Raw prediction stays in its native parent result.
    screen = screen_sequence_v3(features=features, sequence=payload.item.sequence,
        sequence_kind=payload.item.role, rules=payload.rules,
        disorder=DisorderEvidence.model_validate(disorder["parsed"]) if disorder.get("parsed") else None,
        seg=SegEvidence.model_validate(seg["parsed"]) if seg.get("parsed") else None,
        secondary_structure=SecondaryStructureEvidence.model_validate(secondary_evidence) if secondary_evidence else None,
        protparam=compute_protparam_evidence(payload.item.sequence, input_sha256=features.sequence_sha256),
        fusion_evidence=fusion,full_fusion_sha256=features.sequence_sha256 if fusion else None,
        localization_context=payload.item.localization_context, require_external_evidence=True)
    context_screens=screen_part_contexts(screen,payload.item.sequence,payload.rules,payload.construct_context_results)
    if payload.item.role=='full_fusion':
        fusion_missing=screen.missing_required_evidence
        fusion_status='blocked' if fusion_missing else 'completed'
    elif context_screens:
        fusion_missing=sorted({missing for row in context_screens for missing in
            [*row['screen']['missing_required_evidence'],*row['sequence_qc']['missing_inputs'],*row['sequence_qc']['errors']]})
        fusion_status='partial' if fusion_missing else 'completed'
    else:
        fusion_status='blocked'
        fusion_missing=['declared_construct_context_with_native_full_fusion_evidence']
    prioritization = None
    predictors = []
    for collection in (payload.pscore_results, payload.catgranule_results,payload.fuzdrop_results,payload.llps_import_results):
        if collection:
            row = selected(collection)
            parsed = row.get("parsed") or row
            predictors.extend(PredictorScore.model_validate(value) for value in parsed.get("predictor_scores", []))
    if payload.prioritization_policy is not None:
        prioritization = prioritize_m1(M1PrioritizationInput(policy=payload.prioritization_policy,
            candidates=[PrioritizationCandidate(candidate_id=payload.item.id, screen=screen, predictors=predictors,
                comparison_context=payload.comparison_contexts.get(payload.item.id))]))
    priority = prioritization['candidates'][0] if prioritization else None
    return dict(schema_version="m1-method-check-v1", candidate_id=payload.item.id,
        verdict=screen.verdict, precheck=observed, screen=screen.model_dump(mode="json"),
        prioritization=prioritization,
        predictor_scores=[score.model_dump(mode="json") for score in predictors],
        comparison_context=payload.comparison_contexts[payload.item.id].model_dump(mode='json') if payload.item.id in payload.comparison_contexts else None,
        construct_context_screens=context_screens,
        steps=[dict(step="1", name="Cheap sequence fields", status="reject" if observed["hard_reject_reasons"] else "completed"),
               dict(step="2", name="External fragment predictors", status="not_eligible" if not observed["eligible_for_tools"] else
                    "completed" if all(row.get("parse_status") == "succeeded" for row in (disorder, seg, secondary)) else "partial",
                    missing=[label for row, label in ((disorder, "IUPred"), (seg, "SEG"), (secondary, "exact-sequence PSIPRED/JPred secondary structure"))
                             if row.get("parse_status") != "succeeded"]),
               dict(step="3", name="Actual full fusion checks", status=fusion_status,
                    missing=fusion_missing,construct_count=len(context_screens),
                    excluded_checks=screen.excluded_checks),
               dict(step="4", name="Soft risk review", status="completed" if priority and (priority['risk'] is not None or 'soft_review_flags' in priority) else "blocked",
                    missing=[] if priority and (priority['risk'] is not None or 'soft_review_flags' in priority) else ["reviewed complete risk directions"]),
               dict(step="5", name="Original-method ranking", status="not_applicable" if payload.item.role!='idr' else
                    "completed" if priority and priority['rank_score'] is not None else "partial" if priority and priority.get('comparison_method') else "blocked",
                    missing=(priority['missing'] if priority else ["raw LLPS predictions and reviewed normalization/rubric"])
                    if payload.item.role=='idr' else [],
                    note="Linkers use the original checklist/rubric, not an invented composite score." if payload.item.role!='idr' else
                    "Three-predictor equal-weight initial score; batch comparison requires a frozen complete cohort." if priority and priority.get('comparison_method')=='initial_equal_weight_midrank_v2' else
                    "Adopted descriptive comparison; original weighted score remains undefined." if priority and priority.get('comparison_method') else None)],
        claim_scope="original_M1_available_hard_checks_not_full_candidate_acceptance")


class M1BatchRankInput(Contract):
    decisions: list[dict]
    prioritization_policy: PrioritizationPolicy | None = None


def batch_rank(payload: M1BatchRankInput, context: NodeContext) -> dict:
    if not any(parent["output"].get("items") == payload.decisions for parent in context.upstream_results):
        raise ValueError("M1_ranking_requires_registered_decisions")
    if payload.prioritization_policy is None:
        return dict(status="blocked", missing=["reviewed_complete_risk_directions_and_original_ranking_policy"],
            ranked_IDR_candidate_ids=[], candidate_count=len(payload.decisions))
    from igem_drylab.constructs.linker_features import M1ScreenResult
    candidates = [PrioritizationCandidate(candidate_id=row["candidate_id"],
        screen=M1ScreenResult.model_validate(row["screen"]),
        comparison_context=row.get('comparison_context'),
        predictors=[PredictorScore.model_validate(value) for value in row.get("predictor_scores", [])])
        for row in payload.decisions if row.get("screen")]
    if not candidates:
        return dict(status="blocked", missing=["explicit_M1_roles_and_observed_screens"], ranked_IDR_candidate_ids=[])
    result = prioritize_m1(M1PrioritizationInput(candidates=candidates, policy=payload.prioritization_policy))
    result["status"] = "partial" if any(row["missing"] for row in result["candidates"]) else "completed"
    return result


def m1_check_tools():
    implementation = (Path(__file__), Path(__file__).parents[1] / "constructs/linker_features.py",
        Path(__file__).parents[1]/"m1_prioritization.py", Path(__file__).parents[1]/"llps_artifacts.py")
    return [ToolDefinition("method.m1.precheck", "M1 Step 1 — cheap sequence veto", "Original hard boundaries; rejected parts skip expensive predictions.",
                "1", M1PrecheckInput, precheck, "scientific_project", implementation_files=implementation),
            ToolDefinition("method.m1.decision", "M1 evidence and missing-step decision", "Consume exact real IUPred/SEG outputs; missing evidence is not a pass.",
                "1", M1DecisionInput, decision, "scientific_project", implementation_files=implementation),
            ToolDefinition("method.m1.rank", "M1 batch ranking", "Original reviewed formula applied to all registered candidates; never assign default policy.",
                "1", M1BatchRankInput, batch_rank, "scientific_project", implementation_files=implementation),
            ToolDefinition('method.m1.construct_contexts','Bind declared full-fusion contexts',
                'Reuse exact native full-fusion results and original ordered-part/DNA QC, not substring guesses.',
                '1',M1ConstructContextInput,_context_tool,'scientific_project',
                implementation_files=(*implementation,Path(__file__).parents[1]/'constructs/sequence_qc.py',
                    Path(__file__).parents[1]/'pipeline/config.py'))]


def m1_workflow(policy: PrioritizationPolicy | None = None, *, sequence_count: int | None = None,
                comparison_contexts: dict[str,ComparisonContext] | None = None,
                secondary_tool: Literal['jpred','psipred'] = 'jpred',
                aggregation_exclusion_reference: str | None = None,
                constructs: list[ConstructDefinition] | None = None) -> Workflow:
    import yaml
    definitions, _ = M1FeatureDefinitions.from_yaml(default_config_path("m1_feature_definitions.yaml"))
    rules = M1V3Rules.model_validate({**yaml.safe_load(default_config_path("m1_rules_v3.yaml").read_text()),
        "aggregation_exclusion_reference":aggregation_exclusion_reference})
    inputs = dict(feature_definitions=LiteralInput(value=definitions.model_dump(mode="json")),
                  rules=LiteralInput(value=rules.model_dump(mode="json")))
    batch = MapSpec(items=ProjectInput(path=["sequences"]))
    checks = NodeInput(node_id="m1_fields", path=["items"])
    nodes = [WorkflowNode(id="m1_fields", label="M1 Step 1 — cheap sequence veto", tool_id="method.m1.precheck", inputs=inputs, map=batch)]
    for tool in ("iupred2a", "seg", secondary_tool):
        nodes.append(WorkflowNode(id="m1_"+tool, label="M1 Step 2 — real "+tool,
            tool_id="prediction."+tool, inputs={"prechecks": checks}, map=batch))
    for tool in ("signalp","deeptmhmm")+(() if rules.aggregation_exclusion_reference else ("tango",)):
        nodes.append(WorkflowNode(id="m1_"+tool,label="M1 Step 3 — full-fusion "+tool,
            tool_id="prediction."+tool,map=batch))
    for tool in ("pscore", "catgranule",'fuzdrop'):
        nodes.append(WorkflowNode(id="m1_"+tool, label="M1 original LLPS — "+tool,
            tool_id="prediction."+tool, inputs={"prechecks": checks}, map=batch))
    if constructs:
        nodes.append(WorkflowNode(id='m1_construct_contexts',label='Bind sourced construct contexts and DNA QC',
            tool_id='method.m1.construct_contexts',inputs={**inputs,
                'constructs':LiteralInput(value=[c.model_dump(mode='json') for c in constructs]),
                'sequences':ProjectInput(path=['sequences']),
                'signalp_results':NodeInput(node_id='m1_signalp',path=['items']),
                'topology_results':NodeInput(node_id='m1_deeptmhmm',path=['items']),
                'aggregation_results':LiteralInput(value=[]) if rules.aggregation_exclusion_reference else NodeInput(node_id='m1_tango',path=['items'])}))
    nodes.append(WorkflowNode(id="m1_decisions", label="M1 decisions and explicit unfinished steps", tool_id="method.m1.decision",
        inputs={**inputs, "prioritization_policy": LiteralInput(value=policy.model_dump(mode='json') if policy else None),
                "comparison_contexts": LiteralInput(value={key:value.model_dump(mode='json') for key,value in (comparison_contexts or {}).items()}),
                'construct_context_results':NodeInput(node_id='m1_construct_contexts',path=['items']) if constructs else LiteralInput(value=[]),
                "prechecks": checks, "disorder_results": NodeInput(node_id="m1_iupred2a", path=["items"]),
                "seg_results": NodeInput(node_id="m1_seg", path=["items"]),
                "secondary_results": NodeInput(node_id="m1_"+secondary_tool, path=["items"]),
                "signalp_results":NodeInput(node_id="m1_signalp",path=["items"]),
                "topology_results":NodeInput(node_id="m1_deeptmhmm",path=["items"]),
                "aggregation_results":LiteralInput(value=[]) if rules.aggregation_exclusion_reference else NodeInput(node_id="m1_tango",path=["items"]),
                "pscore_results":NodeInput(node_id="m1_pscore",path=["items"]),
                "catgranule_results":NodeInput(node_id="m1_catgranule",path=["items"]),
                'fuzdrop_results':NodeInput(node_id='m1_fuzdrop',path=['items'])}, map=batch))
    nodes.append(WorkflowNode(id="m1_ranking", label="M1 reviewed batch ranking", tool_id="method.m1.rank",
        inputs={"decisions": NodeInput(node_id="m1_decisions",path=["items"]),
            "prioritization_policy": LiteralInput(value=policy.model_dump(mode="json") if policy else None)}))
    from .models import ExecutionPolicy
    return Workflow(id="m1-sequence-checks", name="M1 original hard checks", nodes=nodes,
        execution_policy=ExecutionPolicy(max_tool_calls=max(1000, (sequence_count or 0)*(len(nodes)-1)+1)),
        description="Real durable sequence checks, not a full fusion/ranking approval. Assign explicit M1 roles before running.")
