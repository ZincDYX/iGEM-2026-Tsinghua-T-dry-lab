from __future__ import annotations

import json
from pathlib import Path

from igem_drylab.mcp import create_default_registry


def test_registry_lists_mcp_style_tool_definitions():
    tools = create_default_registry().list_tools()
    names = {tool["name"] for tool in tools}

    assert "igem.pipeline.validate" in names
    assert "igem.pipeline.run" in names
    assert "igem.literature.build_prompt" in names
    assert "igem.literature.qa" in names
    assert all("inputSchema" in tool for tool in tools)


def test_pipeline_validate_tool_returns_structured_content():
    result = create_default_registry().call(
        "igem.pipeline.validate",
        {"config_path": "configs/m1_m4_example.yaml"},
    )

    payload = result.as_protocol_dict()
    assert result.is_error is False
    assert payload["structuredContent"]["ok"] is True
    assert payload["structuredContent"]["run_id"] == "m1-m4-demo"
    assert json.loads(payload["content"][0]["text"]) == payload["structuredContent"]


def test_pipeline_run_tool_writes_outputs(tmp_path):
    result = create_default_registry().call(
        "igem.pipeline.run",
        {"config_path": "configs/m1_m4_example.yaml", "output_dir": str(tmp_path)},
    )

    structured = result.as_protocol_dict()["structuredContent"]
    assert structured["ok"] is True
    assert Path(structured["run_dir"]).exists()
    assert len(structured["stages"]) == 5


def test_literature_build_prompt_tool_can_write_prompt(tmp_path):
    output_path = tmp_path / "prompt.txt"
    result = create_default_registry().call(
        "igem.literature.build_prompt",
        {
            "text_file": "examples/literature/glabridin_excerpt.txt",
            "schema_path": "data/schemas/glabridin_enzyme_catalysis.schema.json",
            "icl_bank": "data/icl/glabridin_examples.minimal.jsonl",
            "output_path": str(output_path),
        },
    )

    structured = result.as_protocol_dict()["structuredContent"]
    assert result.is_error is False
    assert structured["ok"] is True
    assert structured["prompt"] is None
    assert "Return JSON only" in output_path.read_text(encoding="utf-8")


def test_literature_build_database_tool_writes_database(tmp_path):
    result = create_default_registry().call(
        "igem.literature.build_database",
        {
            "manifest_path": "examples/literature_database/manifest.csv",
            "schema_path": "data/schemas/glabridin_enzyme_catalysis.schema.json",
            "output_dir": str(tmp_path / "database"),
            "max_per_paper": 8,
            "max_contexts_per_paper": 40,
        },
    )
    structured = result.as_protocol_dict()["structuredContent"]

    assert result.is_error is False
    assert structured["ok"] is True
    assert structured["summary"]["clean_records"] >= 1


def test_literature_qa_tool_returns_provenance(tmp_path):
    evidence = tmp_path / "evidence.jsonl"
    evidence.write_text(json.dumps({"record_id": "r1", "title": "OC study", "doi": "10.1/oc", "evidence": "OC activity in LLPS converts compound 11.", "fields": {"enzyme": "OC", "substrate": "11", "parameter_type": "activity", "irrelevant_legacy_field": "not agent context", "primary_result_value": "4.2", "primary_result_unit": "uM"}}) + "\n", encoding="utf-8")
    result = create_default_registry().call(
        "igem.literature.qa", {"question": "Which enzyme converts compound 11?", "evidence_path": str(evidence)},
    )
    structured = result.as_protocol_dict()["structuredContent"]
    assert structured["ok"] is True
    assert structured["sources"][0]["doi"] == "10.1/oc"
    assert "fields" not in structured["sources"][0]
    assert structured["sources"][0]["tier"] == "direct"
    assert structured["sources"][0]["relevant_fields"]["enzyme"] == "OC"
    assert structured["sources"][0]["relevant_fields"]["value"] == "4.2"
    assert "irrelevant_legacy_field" not in structured["sources"][0]["relevant_fields"]
    assert "parameter_candidate" not in structured
    assert "approved_parameter" not in structured
    assert structured["mode"] == "retrieve_only"
    assert structured["retrieval"]["lexical"] == "bm25"


def test_literature_qa_tool_exposes_opt_in_semantic_flag(tmp_path):
    evidence = tmp_path / "evidence.jsonl"
    evidence.write_text(json.dumps({"record_id": "r1", "title": "OC study", "doi": "10.1/oc", "evidence": "OC converts compound 11."}) + "\n", encoding="utf-8")
    registry = create_default_registry()
    schema = next(tool["inputSchema"] for tool in registry.list_tools() if tool["name"] == "igem.literature.qa")
    assert schema["properties"]["semantic_enabled"] == {"type": "boolean", "default": False}
    result = registry.call(
        "igem.literature.qa", {"question": "OC activity", "evidence_path": str(evidence), "semantic_enabled": True},
    )
    structured = result.as_protocol_dict()["structuredContent"]
    assert structured["ok"] is True
    assert structured["retrieval"]["semantic"] == "unavailable"


def test_literature_evidence_detail_requires_explicit_record_and_can_select_fields(tmp_path):
    evidence = tmp_path / "evidence.jsonl"
    evidence.write_text(json.dumps({"record_id": "r1", "title": "OC study", "doi": "10.1/oc", "evidence": "OC activity.", "fields": {"reaction_temperature": "30 C", "reaction_ph": "7.0", "hidden": "raw"}}) + "\n", encoding="utf-8")
    registry = create_default_registry()
    names = {tool["name"] for tool in registry.list_tools()}
    assert "igem.literature.evidence_detail" in names
    selected = registry.call("igem.literature.evidence_detail", {"evidence_path": str(evidence), "record_id": "r1", "fields": ["reaction_temperature", "reaction_ph"]}).as_protocol_dict()["structuredContent"]
    assert selected["detail_level"] == "selected_fields"
    assert selected["record"]["fields"] == {"reaction_temperature": "30 C", "reaction_ph": "7.0"}
    full = registry.call("igem.literature.evidence_detail", {"evidence_path": str(evidence), "record_id": "r1"}).as_protocol_dict()["structuredContent"]
    assert full["detail_level"] == "full_record"
    assert full["record"]["fields"]["hidden"] == "raw"


def test_literature_search_tool_writes_manifest(monkeypatch, tmp_path):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "results": [
                    {
                        "id": "https://openalex.org/W1",
                        "doi": "https://doi.org/10.0000/tool",
                        "title": "Tool search record",
                        "publication_year": 2024,
                    }
                ]
            }

    monkeypatch.setattr("igem_drylab.literature.sources.requests.get", lambda *args, **kwargs: FakeResponse())
    manifest = tmp_path / "manifest.csv"
    result = create_default_registry().call(
        "igem.literature.search",
        {"query": "glabridin", "providers": ["openalex"], "output_manifest": str(manifest), "max_results": 5},
    )
    structured = result.as_protocol_dict()["structuredContent"]

    assert result.is_error is False
    assert structured["ok"] is True
    assert structured["result_count"] == 1
    assert manifest.exists()


def test_scoring_mcp_tools_return_structured_results():
    registry = create_default_registry()

    sasa = registry.call(
        "igem.scoring.pocket_sasa",
        {
            "model_json": "examples/real_metrics/freesasa_model.json",
            "reference_json": "examples/real_metrics/freesasa_reference.json",
            "chain": "A",
            "residues": [10, 11, 12],
        },
    ).as_protocol_dict()["structuredContent"]
    assert sasa["ok"] is True
    assert sasa["result"]["passes"] is True

    m2 = registry.call(
        "igem.scoring.m2_structure",
        {
            "candidate_id": "demo",
            "sasa_retention": 0.9,
            "pocket_rmsd_angstrom": 0.8,
            "iptm": 0.8,
            "mean_plddt": 85.0,
            "interface_contact_count": 30,
            "clash_count": 0,
        },
    ).as_protocol_dict()["structuredContent"]
    assert m2["ok"] is True
    assert m2["result"]["recommended_for_m3"] is True

    docking = registry.call(
        "igem.scoring.docking_penalty",
        {
            "candidate_id": "demo",
            "reference_vina_output": "examples/real_metrics/vina_reference.txt",
            "fusion_vina_output": "examples/real_metrics/vina_fusion.txt",
        },
    ).as_protocol_dict()["structuredContent"]
    assert docking["ok"] is True
    assert docking["result"]["passes_negative_screen"] is True

    m4 = registry.call(
        "igem.scoring.m4_ode",
        {
            "candidate_id": "demo",
            "docking_penalty": docking["result"],
        },
    ).as_protocol_dict()["structuredContent"]
    assert m4["ok"] is True
    assert m4["result"]["recommendation"] in {"drop", "iterate", "test"}

    structure = registry.call(
        "igem.parsers.structure_prediction",
        {
            "path": "examples/real_metrics/structure_prediction/af3",
            "candidate_id": "demo_af3",
        },
    ).as_protocol_dict()["structuredContent"]
    assert structure["ok"] is True
    assert structure["result"]["iptm"] == 0.68

    calvados = registry.call(
        "igem.parsers.calvados",
        {"path": "examples/real_metrics/calvados"},
    ).as_protocol_dict()["structuredContent"]
    assert calvados["ok"] is True
    assert calvados["result"]["enrichment_factor"] == 30.0

    piecewise = registry.call(
        "igem.scoring.m4_piecewise_ode",
        {
            "candidate_id": "demo_piecewise",
            "dmt_gate": {"on_time": 4.0, "basal": 0.0, "induced": 1.0},
        },
    ).as_protocol_dict()["structuredContent"]
    assert piecewise["ok"] is True
    assert piecewise["result"]["observable_13_reduction"] >= 1.0


def test_compute_check_tool_reports_configured_command():
    result = create_default_registry().call(
        "igem.compute.check_tool",
        {"config_path": "configs/m1_m4_example.yaml", "tool_name": "colabfold"},
    )
    structured = result.as_protocol_dict()["structuredContent"]

    assert result.is_error is False
    assert structured["ok"] is True
    assert structured["tool_name"] == "colabfold"
    assert "colabfold_batch" in structured["command"]


def test_compute_run_tool_can_dry_run_command(tmp_path):
    result = create_default_registry().call(
        "igem.compute.run_tool",
        {
            "config_path": "configs/m1_m4_example.yaml",
            "tool_name": "colabfold",
            "output_dir": str(tmp_path / "colabfold"),
            "dry_run": True,
            "context": {"input_file": "examples/data/proteins.fasta"},
        },
    )
    structured = result.as_protocol_dict()["structuredContent"]

    assert result.is_error is False
    assert structured["ok"] is True
    assert structured["run"]["status"] == "dry_run"
    assert "examples/data/proteins.fasta" in structured["run"]["argv"]
    assert Path(structured["run"]["manifest_file"]).exists()


def test_unknown_tool_returns_mcp_error_result():
    result = create_default_registry().call("missing.tool", {})
    structured = result.as_protocol_dict()["structuredContent"]

    assert result.is_error is True
    assert structured["ok"] is False
    assert structured["error"]["type"] == "unknown_tool"
