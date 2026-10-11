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
