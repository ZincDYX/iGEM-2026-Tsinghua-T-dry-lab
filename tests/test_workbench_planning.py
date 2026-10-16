from pathlib import Path
from time import monotonic, sleep

from fastapi.testclient import TestClient
import jsonschema
import pytest

from workbench_fixture import fixture_app
from igem_drylab.software.public_contracts import public_schemas
from igem_drylab.workflow.models import Workflow


@pytest.mark.parametrize(
    ("decision", "requested", "executed", "missing"),
    [
        (
            {"change_types": ["parameter_update"]},
            ["m3", "m4"],
            ["m1", "m2", "m3", "m4"],
            [],
        ),
        (
            {
                "change_types": ["parameter_update"],
                "scientific_constraints": ["do_not_rerun_unaffected_structural_stages"],
            },
            ["m3", "m4"],
            [],
            ["verified_reusable_prerequisites"],
        ),
        (
            {"missing_inputs": ["measured_enzyme_concentration"]},
            [],
            [],
            ["measured_enzyme_concentration"],
        ),
        (
            {"change_types": ["timecourse_update"]},
            ["m5"],
            [],
            ["stage_configuration_not_prepared:m5"],
        ),
    ],
)
def test_hybrid_dependency_and_missing_input_contracts(
    tmp_path, decision, requested, executed, missing
):
    """Characterize planning only: no equations, actual tool jobs or provider."""
    app = fixture_app(tmp_path)
    project = app.state.platform_store.project("software-fixture")
    project.scientific_project["config"]["prepared_through"] = "m4"
    app.state.platform_store.save_project(project, expected_revision=project.revision)
    original = app.state.fixture_client.complete_json
    app.state.fixture_client.complete_json = (
        lambda prompt, **kwargs: original(prompt, **kwargs) | decision
    )
    with TestClient(app) as client:
        policy = {
            "max_completed_stages": 1,
            "allowed_tools": ["project.m1", "project.m2", "project.m3", "project.m4"],
        }
        response = client.post(
            "/api/platform/proposals",
            json={
                "project_id": "software-fixture",
                "goal": "scientific_pipeline",
                "mode": "hybrid",
                "objective": "SOFTWARE_FIXTURE dependency and evidence boundary",
                "external_planning_approved": True,
                "policy": policy,
            },
        )
        assert response.status_code == 200, response.text
        proposal = response.json()
        assert proposal["requested_stages"] == requested
        assert proposal["execution_stages"] == executed
        assert proposal["missing_inputs"] == missing
        assert proposal["status"] == ("proposed" if executed else "blocked")
        assert bool(proposal["confirmation"]) == bool(executed)
        if executed:
            assert proposal["workflow"]["execution_policy"]["max_completed_stages"] == 1
            assert (
                proposal["workflow"]["execution_policy"]["allowed_tools"]
                == policy["allowed_tools"]
            )
        history = client.get(
            "/api/platform/projects/software-fixture/assistant"
        ).json()["messages"]
        assert [message["role"] for message in history] == ["user", "assistant"]
        assert history[-1]["text"] == proposal["rationale"]
        assert app.state.fixture_calls == [] and app.state.platform_store.runs() == []


def wait_status(client, run_id, status):
    deadline = monotonic() + 5
    while monotonic() < deadline:
        result = client.get(f"/api/platform/runs/{run_id}/summary").json()
        if result["status"] == status:
            return result
        sleep(0.02)
    raise AssertionError(result)


def test_hybrid_compiler_proposal_acceptance_and_real_stage_boundaries_share_one_ledger(
    tmp_path,
):
    app = fixture_app(tmp_path)
    with TestClient(app) as client:
        request = {
            "project_id": "software-fixture",
            "goal": "scientific_pipeline",
            "objective": "SOFTWARE_FIXTURE design",
            "mode": "hybrid",
            "policy": {"max_completed_stages": 1},
        }
        blocked = client.post("/api/platform/proposals", json=request).json()
        assert blocked["status"] == "blocked" and app.state.fixture_client.calls == 0
        request["external_planning_approved"] = True
        proposal = client.post("/api/platform/proposals", json=request).json()
        assert proposal["source"] == "hybrid_semantic_compiler" and proposal[
            "execution_stages"
        ] == ["m1", "m2", "m3", "m4"]
        assert app.state.fixture_client.calls == 1 and app.state.fixture_calls == []
        jsonschema.validate(proposal, public_schemas()["ProposalView"])
        run_request = {
            "project_id": "software-fixture",
            "proposal_id": proposal["id"],
            "workflow": proposal["workflow"],
            "confirmation": proposal["confirmation"],
            "request_id": proposal["id"],
        }
        assert client.post("/api/platform/runs", json=run_request).status_code == 409
        accepted = client.post(
            f"/api/platform/proposals/{proposal['id']}/decision",
            json={"action": "accept"},
        ).json()
        assert accepted["status"] == "accepted" and app.state.fixture_calls == []
        response = client.post("/api/platform/runs", json=run_request)
        assert response.status_code == 202, response.text
        run_id = response.json()["id"]
        first = wait_status(client, run_id, "paused")
        assert app.state.fixture_calls == ["m1"]
        jsonschema.validate(first, public_schemas()["RunSummaryView"])
        for expected in (2, 3, 4):
            assert (
                client.post(
                    f"/api/platform/runs/{run_id}/control", json={"action": "resume"}
                ).status_code
                == 200
            )
            wait_status(client, run_id, "succeeded" if expected == 4 else "paused")
            assert app.state.fixture_calls == ["m1", "m2", "m3", "m4"][:expected]
        assert len(app.state.platform_store.runs()) == 1
        assert (
            client.post("/api/platform/runs", json=run_request).json()["id"] == run_id
        )
        assert len(app.state.fixture_calls) == 4
        actions = client.get(
            "/api/platform/plan-actions?project_id=software-fixture"
        ).json()
        assert {row["action"] for row in actions} >= {
            "proposed",
            "accept",
            "execution_requested",
        }
        page = client.get(f"/api/platform/runs/{run_id}/nodes/m4/result").json()
        assert page["node"]["output"]["records"][0]["numerically_solved"] is False
        jsonschema.validate(page, public_schemas()["NodePage"])


def test_edited_project_stales_proposal_and_iteration_keeps_original_snapshot(tmp_path):
    app = fixture_app(tmp_path)
    with TestClient(app) as client:
        proposal = client.post(
            "/api/platform/proposals",
            json={"project_id": "software-fixture", "goal": "scientific_pipeline"},
        ).json()
        store = app.state.platform_store
        old = store.project("software-fixture")
        saved = store.save_project(
            old.model_copy(update={"name": "edited fixture"}),
            expected_revision=old.revision,
        )
        assert (
            client.post(
                f"/api/platform/proposals/{proposal['id']}/decision",
                json={"action": "accept"},
            ).status_code
            == 409
        )
        engine = app.state.workflow_engine
        from igem_drylab.workflow.models import Workflow

        run_id = engine.create(saved, Workflow.model_validate(proposal["workflow"]))
        frozen = store.run(run_id)["snapshot_hash"]
        iteration = client.post(f"/api/platform/runs/{run_id}/iteration", json={})
        assert iteration.status_code == 200, iteration.text
        value = iteration.json()
        assert (
            value["project"]["id"] != saved.id
            and value["project"]["parent_snapshot_sha256"] == frozen
        )
        assert value["reuse_supported"] is False
        assert store.run(run_id)["snapshot_hash"] == frozen
        assert (
            value["project"]["scientific_project"]["evidence_files"][0]["sha256"]
            == old.scientific_project["evidence_files"][0]["sha256"]
        )
        assert str(tmp_path) not in iteration.text
        jsonschema.validate(value, public_schemas()["IterationView"])


def test_saved_input_diff_uses_real_bindings_and_does_not_reuse_or_cross_project(
    tmp_path,
):
    app = fixture_app(tmp_path)
    with TestClient(app) as client:
        store = app.state.platform_store
        proposal = client.post(
            "/api/platform/proposals",
            json={"project_id": "software-fixture", "goal": "scientific_pipeline"},
        ).json()
        project = store.project("software-fixture")
        run_id = app.state.workflow_engine.create(
            project, Workflow.model_validate(proposal["workflow"])
        )
        route = f"/api/platform/projects/software-fixture/input-diff?run_id={run_id}"
        assert client.get(route).json()["changed_fields"] == []
        project = store.save_project(
            project.model_copy(update={"name": "metadata only"}), project.revision
        )
        metadata = client.get(route).json()
        assert (
            metadata["changed_fields"] == ["name", "revision"]
            and metadata["affected_nodes"] == []
        )
        project.scientific_project["config"]["experimental_context"][
            "temperature_c"
        ] = 31
        store.save_project(project, project.revision)
        response = client.get(route)
        assert response.status_code == 200, response.text
        changed = response.json()
        assert (
            "scientific_project.config.experimental_context.temperature_c"
            in changed["changed_fields"]
        )
        assert (
            changed["affected_nodes"] == ["m1", "m2", "m3", "m4", "m5"]
            and changed["reuse_supported"] is False
        )
        jsonschema.validate(changed, public_schemas()["InputDiffView"])
        iteration = client.post(
            f"/api/platform/runs/{run_id}/iteration", json={}
        ).json()["project"]
        derived = client.get(
            f"/api/platform/projects/{iteration['id']}/input-diff?run_id={run_id}"
        ).json()
        assert not any(
            field.startswith("scientific_project")
            for field in derived["changed_fields"]
        ), derived
        assert derived["affected_nodes"] == []
        from igem_drylab.workflow.models import Project

        store.save_project(Project(id="unrelated", name="software fixture"))
        assert (
            client.get(
                f"/api/platform/projects/unrelated/input-diff?run_id={run_id}"
            ).status_code
            == 403
        )


def test_user_workflow_requires_same_acceptance_and_blocks_literal_formal_records(
    tmp_path,
):
    app = fixture_app(tmp_path)
    with TestClient(app) as client:
        template = client.post(
            "/api/platform/proposals",
            json={"project_id": "software-fixture", "goal": "scientific_pipeline"},
        ).json()
        request = {
            "project_id": "software-fixture",
            "workflow": template["workflow"],
            "objective": "SOFTWARE_FIXTURE user DAG",
        }
        result = client.post("/api/platform/custom-proposals", json=request)
        assert result.status_code == 200, result.text
        proposal = result.json()
        assert (
            proposal["source"] == "user_reviewed_workflow"
            and proposal["status"] == "proposed"
        )
        assert app.state.fixture_calls == [] and app.state.platform_store.runs() == []
        run_request = {
            "project_id": "software-fixture",
            "workflow": proposal["workflow"],
            "confirmation": proposal["confirmation"],
            "proposal_id": proposal["id"],
            "request_id": proposal["id"],
        }
        assert client.post("/api/platform/runs", json=run_request).status_code == 409
        request["workflow"]["nodes"][1]["inputs"]["upstream"] = {
            "kind": "literal",
            "value": {"evidence_ready": True},
        }
        assert client.post(
            "/api/platform/custom-proposals", json=request
        ).status_code in (409, 422)
        assert app.state.fixture_calls == []


def test_measurement_binding_and_private_profile_cannot_be_fabricated_over_http(
    tmp_path,
):
    app = fixture_app(tmp_path)
    with TestClient(app) as client:
        store = app.state.platform_store
        original = store.project("software-fixture").model_dump(mode="json")
        binding = {
            "project_id": "software-fixture",
            "expected_revision": original["revision"] + 1,
            "file_id": "asset:missing-software-fixture",
        }
        assert (
            client.post(
                "/api/platform/scientific-projects/bind-measurement", json=binding
            ).status_code
            == 409
        )
        binding["expected_revision"] = original["revision"]
        assert (
            client.post(
                "/api/platform/scientific-projects/bind-measurement", json=binding
            ).status_code
            >= 400
        )
        public = client.get("/api/platform/projects/software-fixture").json()
        public["runtime_profile_ref"] = "fabricated-profile"
        assert (
            client.post(
                "/api/platform/projects",
                json={"project": public, "expected_revision": original["revision"]},
            ).status_code
            == 403
        )
        assert store.project("software-fixture").model_dump(mode="json") == original
        catalogue = client.get("/api/platform/tools")
        assert catalogue.status_code == 200, catalogue.text
        assert all("input_schema" not in row for row in catalogue.json())
        schemas = client.get("/api/platform/schemas")
        assert schemas.status_code == 200, schemas.text
        assert '"repo_path"' not in schemas.text and '"secret_env"' not in schemas.text


def test_generated_wire_schema_matches_python_and_validators_have_no_runtime_eval():
    import json

    root = Path(__file__).resolve().parents[1]
    contracts = root / "software/dashboard/src/contracts"
    assert (
        json.loads((contracts / "public.schemas.json").read_text(encoding="utf-8"))
        == public_schemas()
    )
    validator = (contracts / "public.validators.generated.js").read_text(
        encoding="utf-8"
    )
    assert "new Function(" not in validator and "eval(" not in validator
    from igem_drylab.workflow.mcp_bridge import server_parameters

    parameters = server_parameters(root / "src/igem_drylab")
    assert parameters.args == ["-B", "-m", "igem_drylab.mcp.server"]
    assert "FUSIONLAB_SESSION_TOKEN" not in parameters.env


def test_registered_m5_binding_is_preview_only_and_keeps_empty_measurements_empty(
    tmp_path,
):
    import json

    app = fixture_app(tmp_path)
    with TestClient(app) as client:
        store = app.state.platform_store
        # Typed software record with no biological values or verification facts.
        record = {
            "experiment_id": "SOFTWARE_FIXTURE_NOT_EXPERIMENT",
            "construct_id": "SOFTWARE_FIXTURE",
            "condition_id": "SOFTWARE_FIXTURE",
            "replicate_id": "SOFTWARE_FIXTURE",
            "notes": "SOFTWARE_FIXTURE_ONLY; no biological measurement",
        }
        preview = client.post(
            "/api/platform/imports/preview",
            json={
                "filename": "software-fixture-wetlab.json",
                "content": json.dumps([record]),
                "input_kind": "wetlab",
            },
        )
        assert preview.status_code == 200, preview.text
        imported = preview.json()
        project = client.get("/api/platform/projects/software-fixture").json()
        project["files"].append(imported["file"])
        project["datasets"].extend(imported["patch"]["datasets"])
        response = client.post(
            "/api/platform/projects",
            json={"project": project, "expected_revision": project["revision"]},
        )
        assert response.status_code == 200, response.text
        saved = response.json()
        frozen = store.project(saved["id"]).model_dump(mode="json")
        bound = client.post(
            "/api/platform/scientific-projects/bind-measurement",
            json={
                "project_id": saved["id"],
                "expected_revision": saved["revision"],
                "file_id": imported["file"]["file_id"],
            },
        )
        assert bound.status_code == 200, bound.text
        result = bound.json()
        jsonschema.validate(result, public_schemas()["BindingPreviewView"])
        assert (
            result["requires_confirmation"] is True
            and result["status"] == "binding_preview_not_parameter_approval"
        )
        assert (
            result["project"]["scientific_project"]["config"]["stages"]["m5_feedback"][
                "wetlab_results_file"
            ]
            == imported["file"]["path"]
        )
        assert result["project"]["datasets"][0]["records"][0]["metabolites"] == {}
        assert store.project(saved["id"]).model_dump(mode="json") == frozen
        assert app.state.fixture_calls == []


def test_base_api_does_not_eagerly_import_deprecated_scientific_registry(tmp_path):
    import os, subprocess, sys

    source = Path(__file__).resolve().parents[1] / "src"
    code = "from pathlib import Path; import sys,igem_drylab; assert Path(igem_drylab.__file__).resolve().is_relative_to(Path(sys.argv[2])); from igem_drylab.software.dashboard import create_app; app=create_app(data_dir=Path(sys.argv[1]),session_token='SOFTWARE_FIXTURE_SESSION',discover_tools=False); assert 'igem_drylab.mcp.registry' not in sys.modules; print('basic-api-without-legacy-registry')"
    result = subprocess.run(
        [sys.executable, "-B", "-c", code, str(tmp_path / "cold-import"), str(source)],
        capture_output=True,
        text=True,
        timeout=30,
        env={
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "PYTHONPATH": str(source),
            "OPENBLAS_NUM_THREADS": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "basic-api-without-legacy-registry"
