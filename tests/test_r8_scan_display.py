"""Registered finite-scan parser samples; no numerical scan is executed."""
import json
from copy import deepcopy
from types import SimpleNamespace
import pytest
from test_r7_display_resources import environment
from test_r7_lineage_and_binary_api import formal_parser_record
from igem_drylab.design_analysis import _candidate_comparison
from igem_drylab.workflow.scan_display import scan_page
from igem_drylab.workflow.models import WorkflowError


def sample():
    record=formal_parser_record()
    contract=_candidate_comparison(SimpleNamespace(simulation_inputs=record["simulation_inputs"]),"yield_abs").model_dump(mode="json")
    row=dict(candidate=dict(candidate_id="a",site_ratio=1,config_path="PRIVATE_ORIGINAL_PATH"),status="valid",feasible=True,
        metrics={"yield_abs":0},dense_oc_dmt_ratio=0,context=dict(candidate_id="a",nominal_site_counts={"SH3":2,"PDZ":2}),
        comparison_contract=contract,evidence_grades=dict(evidence_ready=True,context_evidence_ready=True,data_quality="literature",
        claim_scope="conditional_mechanism",context_claim_scope="conditional_mechanism"))
    bad=deepcopy(row);bad["candidate"]["candidate_id"]="b";bad["context"]["candidate_id"]="b"
    bad["comparison_contract"]["assay_conditions"]["pH"]=6
    return dict(schema_version="finite-scaffold-scan-v2",scaffold_scan=[row,bad],design_decision=dict(decision_id="SOFTWARE_PARSER_SAMPLE",objective="yield_abs",decision_scope="formal_conditional_mechanism",comparison_contract=contract))


def test_exact_scan_points_contract_gate_pagination_and_grants(tmp_path):
    _,boundary,resources=environment(tmp_path)
    source=tmp_path/"scan.json";source.write_text(json.dumps(sample()))
    asset=boundary.asset(source,project_id="a")
    first=scan_page(resources,"a",asset["id"],0,1)
    assert first["points"][0]["metric_value"]==0 and first["has_more"]
    assert first["points"][0]["dense_oc_dmt_ratio"]==0
    assert "PRIVATE_ORIGINAL_PATH" not in json.dumps(first)
    assert first["ranking_performed"] is False
    second=scan_page(resources,"a",asset["id"],1,1)
    assert second["points"][0]["metric_value"] is None
    assert "comparison_contract_differs" in second["points"][0]["reason_codes"]
    assert second["points"][0]["ordinal"]==1
    assert any(r["kind"]=="scan" for r in resources.catalog("a")["items"])
    with pytest.raises(WorkflowError,match="file_project_mismatch"):
        scan_page(resources,"b",asset["id"],0,1)
    source.write_text("changed")
    with pytest.raises(WorkflowError,match="file_identity_changed"):
        scan_page(resources,"a",asset["id"],0,1)
