from igem_drylab.parameters import ParameterRecord, validate_parameters


def test_parameter_registry_requires_review_and_provenance():
    record = ParameterRecord(
        parameter_id="km-oc", name="km_oc", value=1.2, unit="uM", source_type="literature",
        source_reference="Table 1", doi="10.1000/example", review_status="reviewed",
    )
    selected, missing = validate_parameters([record], required_names={"km_oc", "kcat_oc"})
    assert selected["km_oc"].doi == "10.1000/example"
    assert missing == ["kcat_oc"]
