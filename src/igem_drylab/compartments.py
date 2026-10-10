"""Scenario routing shared by stage boundaries, not a membrane solver.

The historical cytosolic method remains unchanged. An ER construct or design
cannot be made cytosolic by an old/default downstream assessment.
"""
from typing import Literal

CompartmentScenario = Literal["cytosolic_two_phase", "er_anchored"]


def scenario_for_construct(config, construct_id: str, definition: dict | None = None) -> CompartmentScenario:
    definitions = {item.id: item for item in config.inputs.constructs}
    for record in config.inputs.construct_records:
        if record.review_status == "approved":
            from igem_drylab.pipeline.config import ConstructDefinition
            item = ConstructDefinition.model_validate(record.candidate_definition())
            definitions[item.id] = item
    design = next((item for item in config.inputs.designs if item.id == construct_id), None)
    members = design.protein_construct_ids if design else [construct_id]
    if (definition or {}).get("localization_context") == "er_anchored":
        return "er_anchored"
    if any(definitions[item].localization_context == "er_anchored" for item in members if item in definitions):
        return "er_anchored"
    return "cytosolic_two_phase"
