"""Bind reviewed transport measurements to the existing volume-aware equations."""
import re
import math
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .full_network import COMPOUNDS, TransportParameters
from .parameters import ParameterRegistry, resolve_requirement
from .parameters.requirements import ParameterRequirement


TRANSPORT_FORMULA_VERSION = "volume-aware-reversible-first-order-v1"
RATE_DEFINITION = "forward_plus_reverse_first_order_coefficients"
RATIO_DEFINITION = "C_outside/C_accessible_inside_at_zero_net_flux"


class TransportEvidenceBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    formula_version: str = TRANSPORT_FORMULA_VERSION
    rate_parameter_id: str = Field(min_length=1)
    intracellular_volume_parameter_id: str = Field(min_length=1)
    extracellular_volume_parameter_id: str = Field(min_length=1)
    outside_over_inside_parameter_ids: dict[str,str]

    @model_validator(mode="after")
    def _complete(self):
        if self.formula_version != TRANSPORT_FORMULA_VERSION:
            raise ValueError("transport_formula_version_not_supported")
        if set(self.outside_over_inside_parameter_ids) != set(COMPOUNDS) or any(not v.strip() for v in self.outside_over_inside_parameter_ids.values()):
            raise ValueError("transport_ratio_evidence_requires_all_compounds")
        return self


def resolve_transport_evidence(records, binding, experimental_context, *, construct_id, condition_id, access):
    """Fixed evidence IDs must pass the same formal resolver as kinetics, no fallback."""
    registry=ParameterRegistry(records)
    selected=[]
    def resolve(identifier, parameter_type, dimension, canonical_unit, *, species_id=None, minimum=0, positive=False, conditions=None):
        record=registry.get(identifier)
        if record is None:
            raise ValueError("transport_evidence_record_missing:"+identifier)
        requirement=ParameterRequirement(name=record.name,parameter_type=parameter_type,dimension=dimension,
            canonical_unit=canonical_unit,species_id=species_id,minimum=minimum,minimum_inclusive=not positive)
        resolution=resolve_requirement(registry,requirement,experimental_context,allow_assumptions=False,
            construct_id=construct_id,condition_id=condition_id,require_provenance=True)
        if resolution.status!="resolved" or resolution.selected_parameter.parameter_id!=identifier:
            raise ValueError("transport_evidence_not_formally_applicable:"+identifier+":"+",".join(resolution.reasons))
        if not re.fullmatch(r"[0-9a-f]{64}",str(record.conditions.get("raw_data_sha256",""))):
            raise ValueError("transport_raw_data_identity_missing:"+identifier)
        for key,value in (conditions or {}).items():
            if record.conditions.get(key)!=value:
                raise ValueError("transport_measurement_definition_mismatch:"+key+":"+identifier)
        selected.append(record)
        return resolution.canonical_value
    rate=resolve(binding.rate_parameter_id,"export_rate","rate","1/h",conditions={
        "rate_definition":RATE_DEFINITION,"transport_access":access,"normalization":"cell_volume_equivalent_flux"})
    vi=resolve(binding.intracellular_volume_parameter_id,"other","volume","L",positive=True,
        conditions={"compartment":"intracellular","volume_definition":"effective_intracellular_reaction_volume"})
    ve=resolve(binding.extracellular_volume_parameter_id,"other","volume","L",positive=True,
        conditions={"compartment":"extracellular","volume_definition":"extracellular_medium_volume"})
    ratios={c:resolve(binding.outside_over_inside_parameter_ids[c],"other","dimensionless","1",species_id=c,
        conditions={"ratio_definition":RATIO_DEFINITION,"transport_access":access}) for c in COMPOUNDS}
    parameters=TransportParameters(enabled=True,access=access,rate=rate,outside_over_inside=ratios,
        intracellular_volume_l=vi,extracellular_volume_l=ve)
    parameters.validate()
    return parameters,{"formula_version":binding.formula_version,"status":"formal_evidence_bound",
        "parameter_ids":[r.parameter_id for r in selected],"records":[r.model_dump(mode="json") for r in selected],
        "rate_definition":RATE_DEFINITION,"ratio_definition":RATIO_DEFINITION,
        "scope":"condition_matched_measured_or_verified_parameters_not_transport_validation"}


def match_configured_transport(parameters,settings,rate):
    pairs=[("rate",parameters.rate,rate), ("intracellular_volume_l",parameters.intracellular_volume_l,settings.intracellular_volume_l),
        ("extracellular_volume_l",parameters.extracellular_volume_l,settings.extracellular_volume_l)]
    pairs += [("outside_over_inside:"+c,parameters.outside_over_inside[c],settings.transport_outside_over_inside[c]) for c in COMPOUNDS]
    for name,actual,declared in pairs:
        if declared is None or not math.isclose(actual,declared,rel_tol=1e-12,abs_tol=0):
            raise ValueError("transport_config_disagrees_with_verified_evidence:"+name)
