"""Resolve optional M3 avidity using the same reviewed parameter registry."""
from typing import Literal
from pydantic import BaseModel,ConfigDict
from .parameters.requirements import ParameterRequirement
from .parameters import validate_parameters
from .m3_equilibrium import AvidityCorrection


class AvidityBinding(BaseModel):
    model_config=ConfigDict(extra="forbid")
    method: Literal["statistical_factor","alpha","free_energy"]
    parameter_name: str


def resolve_avidity(binding,config,construct_id,condition_id,binding_pair):
    if binding is None:
        return None,[]
    energy=binding.method=="free_energy"
    requirement=ParameterRequirement(name=binding.parameter_name,parameter_type="other",
        dimension="molar_energy" if energy else "dimensionless",canonical_unit="J/mol" if energy else "1",
        minimum=None if energy else 0,minimum_inclusive=False,maximum=0 if energy else None)
    resolved,missing=validate_parameters(config.parameters,requirements=[requirement],allow_assumptions=config.execution.allow_assumptions,
        host=config.experimental_context.host,strain=config.experimental_context.strain,assay_system=config.experimental_context.assay_system,
        pH=config.experimental_context.pH,temperature_c=config.experimental_context.temperature_c,construct_id=construct_id,condition_id=condition_id,
        require_provenance=config.execution.mode=="real" and config.execution.require_provenance)
    if missing:
        return None,missing
    resolution=resolved[binding.parameter_name]
    record=resolution.selected_parameter
    if not binding_pair or record.conditions.get("binding_pair")!=binding_pair or not record.approved_by or not record.source_reference:
        return None,["avidity_requires_reviewed_same_exact_binding_pair_and_source"]
    arguments=dict(method=binding.method,source_reference=record.source_reference,reviewed_by=record.approved_by,parameter_ids=[record.parameter_id])
    if energy:
        if config.experimental_context.temperature_c is None:
            return None,["avidity_free_energy_requires_actual_temperature"]
        arguments.update(delta_delta_g_j_per_mol=resolution.canonical_value,temperature_k=config.experimental_context.temperature_c+273.15)
    else:
        arguments["value"]=resolution.canonical_value
    return AvidityCorrection.model_validate(arguments),[]
