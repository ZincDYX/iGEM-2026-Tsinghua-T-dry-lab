from igem_drylab.parameters import ParameterRecord, ParameterRegistry, m4_requirements
from igem_drylab.pipeline.config import M4Config


def _record(identifier: str, value: float, *, construct: str | None = None, condition: str | None = None) -> ParameterRecord:
    return ParameterRecord(parameter_id=identifier, name="oc_total", value=value, unit="uM", parameter_type="abundance", enzyme_id="OC", source_type="wetlab", source_reference="wetlab", review_status="approved", construct_id=construct, condition_id=condition)


def test_construct_specific_parameter_overrides_global_and_does_not_cross_use():
    requirement = next(item for item in m4_requirements() if item.name == "oc_total")
    registry = ParameterRegistry([_record("global", 1), _record("a", 5, construct="candidate-a")])
    assert registry.resolve(requirement, construct_id="candidate-a").canonical_value == 5
    assert registry.resolve(requirement, construct_id="candidate-b").canonical_value == 1
    assert ParameterRegistry([_record("a", 5, construct="candidate-a")]).resolve(requirement, construct_id="candidate-b").status == "unresolved"


def test_degradation_requirements_are_only_present_when_enabled():
    assert all(not item.name.startswith("kdeg_") for item in m4_requirements())
    assert {item.name for item in m4_requirements(include_degradation=True)} >= {"kdeg_9", "kdeg_10", "kdeg_11", "kdeg_13", "kdeg_15"}
    assert M4Config().enable_degradation is False
