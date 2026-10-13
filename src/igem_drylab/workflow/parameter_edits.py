"""Admission for unresolved value overrides, not a new resolution policy."""
from igem_drylab.parameters import ParameterRegistry
from igem_drylab.parameters.requirements import requirements_for_stage


def pending_replacements(config,stage):
    names={item.name for item in requirements_for_stage(config,stage)}
    registry=ParameterRegistry(config.parameters)
    replaced={record.supersedes for record in config.parameters if record.review_status!='rejected'}
    return [record for record in config.parameters if record.name in names
        and record.parameter_id not in replaced and record.review_status in {'extracted','validated'}
        and any(parent.review_status=='approved' for parent in registry.provenance(record.parameter_id)[1:])]


def validate_er_candidate(config,candidate,stage,name,reviewer):
    """Review only an actually bound canonical quantity, using the stage gate.

    This does not approve a whole request, invent missing context or interpret
    plain reaction-rate references as typed quantities.
    """
    from igem_drylab.pipeline.er_stages import quantities,registry_gaps
    requests=config.stages.m3_concentration.er_requests if stage=='m3' else config.stages.m4_reaction.compartment_requests
    matched=[request for request in requests.values() if any(quantity.parameter_id==candidate.parameter_id for quantity in quantities(request))]
    if not matched:return False
    if candidate.name!=name or candidate.review_status!='validated' or not reviewer.strip():
        raise ValueError('candidate_requirement_mismatch')
    from igem_drylab.parameters.models import validate_provenance_combination
    validate_provenance_combination(candidate.source_type,candidate.derivation_type)
    ParameterRegistry([*config.parameters,candidate])
    approved=candidate.model_copy(update={'review_status':'approved','approved_by':reviewer})
    proposed=config.model_copy(update={'parameters':[*config.parameters,approved]})
    gaps=sorted({gap for request in matched for gap in registry_gaps(proposed,request,only_ids={candidate.parameter_id})})
    if gaps:raise ValueError('ER_candidate_not_applicable:'+','.join(gaps))
    return True
