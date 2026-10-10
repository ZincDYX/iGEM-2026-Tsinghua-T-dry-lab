"""Recorded scientific state projection, not a scientific pipeline execution."""
from fastapi.testclient import TestClient
from igem_drylab.software.dashboard import create_app
from igem_drylab.workflow.models import Project, Workflow, WorkflowNode, NodeStatus


def test_job_success_never_promotes_missing_scientific_evidence(tmp_path):
    app = create_app(data_dir=tmp_path, deployment_mode="development", discover_tools=False)
    store = app.state.platform_store
    project = store.save_project(Project(id="p", name="software fixture"))
    workflow = Workflow(id="w",name="fixture",nodes=[WorkflowNode(id="m4",label="M4",tool_id="project.m4")])
    run_id = store.create_run({"project":project.model_dump(mode="json"),"workflow":workflow.model_dump(mode="json"),"tools":{}})
    records = [{"status":"insufficient_data","numerically_solved":False,"evidence_ready":False,"missing_inputs":["real_kinetics"], "claim_scope":"NOT_A_PREDICTION"} for _ in range(1000)]
    store.set_node(run_id,"m4",NodeStatus.succeeded,output={"schema_version":"scientific-stage-v2","module":"m4","records":records,"claim_scope":"NOT_A_PREDICTION", "trajectories":["NEVER_EXPORT"]*1000})
    with TestClient(app) as client:
        result = client.get(f"/api/platform/runs/{run_id}/summary")
        assert result.status_code == 200, result.text
        state = result.json()["nodes"][0]
        assert state["status"] == "succeeded"
        assert result.json()['scientific_assessment']=={'numerical_state':'partial_or_blocked','evidence_state':'partial_or_blocked','experimental_validation':'not_established'}
        assert state["scientific_summary"] == {"module":"m4", "record_count":1000, "status_counts":{"insufficient_data":1000}, "numerically_solved_count":0, "evidence_ready_count":0, "missing_input_count":1000, "claim_scope":"NOT_A_PREDICTION"}
        assert len(result.content) < 4000 and "NEVER_EXPORT" not in result.text and '"records"' not in result.text
        # The dimensions stay independent, including explicit geometry rejection.
        records[0].update(status="rejected", numerically_solved=True)
        records[1].update(status="partial_statistics", evidence_ready=True)
        store.set_node(run_id,"m4",NodeStatus.succeeded,output={"schema_version":"scientific-stage-v2","module":"m4","records":records})
        summary = client.get(f"/api/platform/runs/{run_id}/summary").json()["nodes"][0]["scientific_summary"]
        assert summary["status_counts"] == {"insufficient_data":998,"rejected":1,"partial_statistics":1}
        assert summary["numerically_solved_count"] == 1 and summary["evidence_ready_count"] == 1


def test_recorded_synthetic_cases_do_not_hide_missing_E3(tmp_path):
    app=create_app(data_dir=tmp_path, deployment_mode='development',discover_tools=False)
    store=app.state.platform_store
    project=store.save_project(Project(id='p',name='Recorded software fixture'))
    workflow=Workflow(id='w',name='PS fixture',nodes=[WorkflowNode(id='demo',label='Synthetic',tool_id='synthetic.ps_v3')])
    run_id=store.create_run({'project':project.model_dump(mode='json'),'workflow':workflow.model_dump(mode='json'),'tools':{}})
    case={'m4':{'result':{'status':'numerically_solved','numerical_admission':{'conservation_valid':True}}}}
    store.set_node(run_id,'demo',NodeStatus.succeeded,output={'schema_version':'synthetic-ps-v3-run-v1',
        'cases':{key:case for key in ('C1','C2','E1','E2')},'E3':{'status':'blocked','missing_inputs':['actual_geometry']}})
    with TestClient(app) as client:
        result=client.get(f'/api/platform/runs/{run_id}/summary').json()
    assert result['nodes'][0]['scientific_summary']['numerically_solved_count']==4
    assert result['nodes'][0]['scientific_summary']['record_count']==5
    assert result['scientific_assessment']=={'numerical_state':'partial_or_blocked','evidence_state':'partial_or_blocked','experimental_validation':'not_established'}
