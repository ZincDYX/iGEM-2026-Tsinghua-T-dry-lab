from igem_drylab.constructs import ConstructRecord, ConstructRegistry
import pytest

from igem_drylab.parameters import ParameterRecord, ParameterRegistry, condition_compatibility, convert_value, identity_compatibility, parameter_from_evidence


def _literature(parameter_id: str, value: float, *, status: str = "approved", supersedes: str | None = None) -> ParameterRecord:
    return ParameterRecord(parameter_id=parameter_id, name="km_dmt_11", value=value, unit="uM", parameter_type="km", enzyme_id="DMT", substrate_id="11", source_type="literature", doi="10.1/example", source_reference="table", evidence_text="reported Km", review_status=status, supersedes=supersedes)


def test_literature_evidence_is_not_automatically_approved():
    candidate = parameter_from_evidence(parameter_id="e1", name="km_dmt_11", value=37, unit="µM", source={"doi": "10.1/e", "evidence": "Km 37"}, parameter_type="km", enzyme_id="DMT", substrate_id="11")
    assert candidate.review_status == "extracted"
    assert candidate.unit == "uM"


def test_conflicting_literature_values_are_not_silently_resolved():
    registry = ParameterRegistry([_literature("a", 20), _literature("b", 80)])
    assert registry.resolve_for_model("km_dmt_11").status == "conflict"


def test_wetlab_parameter_supersedes_literature_but_history_remains():
    old = _literature("lit", 50)
    new = ParameterRecord(parameter_id="wet", name="km_dmt_11", value=23, unit="uM", parameter_type="km", source_type="wetlab", source_reference="E17", review_status="approved", supersedes="lit")
    registry = ParameterRegistry([old, new])
    assert registry.resolve_for_model("km_dmt_11").selected_parameter.parameter_id == "wet"
    assert [item.parameter_id for item in registry.provenance("wet")] == ["wet", "lit"]


def test_construct_registry_feeds_approved_candidates():
    registry = ConstructRegistry([ConstructRecord(construct_id="c1", construct_type="fusion", proteins=["OC", "IDR"], scaffold="FTH1", linker_sequences={"gs": "GGGGS"}, source_type="literature", doi="10.1/c", evidence="construct", review_status="approved")])
    assert registry.candidates()[0]["id"] == "c1"


def test_identity_matching_rejects_other_enzyme():
    record = _literature("a", 20)
    assert identity_compatibility(record, enzyme_id="OtherDMT", substrate_id="11").level == "incompatible"


def test_unit_conversion_is_explicit_and_condition_mismatch_is_retained():
    record = _literature("a", 20)
    record.conditions = {"host": "E. coli", "temperature_c": 20}
    assert convert_value(1.0, "mM", "uM") == pytest.approx(1000.0)
    assert condition_compatibility(record, host="S. cerevisiae").level == "incompatible"
    with pytest.raises(ValueError):
        convert_value(1.0, "1/s", "uM")
