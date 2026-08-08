import pytest

from igem_drylab.parameters import ParameterRecord, ParameterRegistry, m4_requirements
from igem_drylab.project_state import ProjectState


def _requirement(name: str):
    return next(item for item in m4_requirements() if item.name == name)


def test_resolver_normalizes_concentration_and_rate_units():
    km = ParameterRecord(parameter_id="km", name="km_pt", value=1, unit="mM", parameter_type="km", enzyme_id="PT", substrate_id="9", source_type="wetlab", source_reference="E", review_status="approved")
    rate = ParameterRecord(parameter_id="rate", name="kcat_pt", value=3600, unit="h^-1", parameter_type="kcat", enzyme_id="PT", substrate_id="9", product_id="10", source_type="wetlab", source_reference="E", review_status="approved")
    registry = ParameterRegistry([km, rate])
    assert registry.resolve(_requirement("km_pt")).canonical_value == pytest.approx(1000)
    assert registry.resolve(_requirement("kcat_pt")).canonical_value == pytest.approx(1)


def test_dimension_and_identity_mismatches_are_unresolved():
    record = ParameterRecord(parameter_id="bad", name="km_pt", value=1, unit="1/s", parameter_type="km", enzyme_id="OTHER", source_type="wetlab", source_reference="E", review_status="approved")
    result = ParameterRegistry([record]).resolve(_requirement("km_pt"))
    assert result.status == "unresolved"


def test_validated_candidate_cannot_enter_project_state_until_approved():
    candidate = ParameterRecord(parameter_id="c", name="phi", value=0.1, unit="1", parameter_type="phi", source_type="wetlab", source_reference="E", review_status="validated")
    state = ProjectState(project_id="p")
    assert "phi" in state.missing_inputs("m3")
    approved = state.approve_parameter(candidate, reviewer="reviewer")
    assert "phi" not in approved.missing_inputs("m3")
