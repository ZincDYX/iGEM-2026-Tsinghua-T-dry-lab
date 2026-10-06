"""Explicit test-only HTTP handlers. No biological file parsing or solver.

Only the test launcher imports this factory; production never selects it.
"""
from hashlib import sha256
from pathlib import Path

from igem_drylab.agent.hybrid_planner import HybridLLMPlanningBackend
from igem_drylab.pipeline.config import ProjectConfig
from igem_drylab.software.dashboard import create_app
from igem_drylab.workflow.models import Project
from igem_drylab.workflow.scientific_project import ScientificProject, EvidenceFile, StageInput, bound_predecessor
from igem_drylab.workflow.tools import WorkflowTools, ToolDefinition


class SemanticFixtureClient:
    calls = 0
    def complete_json(self,prompt,**kwargs):
        self.calls += 1
        return {"change_types":["new_design_request"],"requested_outcome":"design","artifact_action":"recompute","evidence_action":"none",
            "requires_human_review":True,"requires_new_compute":True,"rationale":"SOFTWARE_FIXTURE：只验证编排，不是实际模型 API 或科学证据。"}


def fixture_app(data_dir:Path,session_token:str|None=None):
    if (data_dir / "platform.sqlite3").exists(): raise ValueError("fixture_requires_fresh_workspace")
    client = SemanticFixtureClient()
    calls = []
    tools = WorkflowTools()
    for stage in ("m1","m2","m3","m4","m5"):
        def handler(payload,context,stage=stage):
            bound_predecessor(payload,context,stage)
            calls.append(stage)
            return {"schema_version":"scientific-stage-v2","module":stage,"execution_mode":"software_fixture",
                "records":[{"candidate_id":"SOFTWARE_FIXTURE","status":"software_fixture_not_prediction","evidence_ready":False,
                    "numerically_solved":False,"missing_inputs":["software_only_no_biological_calculation"],"claim_scope":"software_fixture_only"}],
                "resource_artifacts":[],"trajectory_refs":{}}
        tools.register(ToolDefinition("project."+stage,stage.upper()+" 软件测试夹具","不是生物模型","software-fixture-v1",StageInput,handler,"scientific_project"))
    app = create_app(data_dir=data_dir,session_token=session_token,deployment_mode="authenticated" if session_token else "development",discover_tools=False,
        planning_backend=HybridLLMPlanningBackend(client),workflow_tools=tools)
    source = data_dir / "imports" / "software-fixture.txt"
    source.parent.mkdir(parents=True,exist_ok=True)
    source.write_text("SOFTWARE_FIXTURE_NOT_BIOLOGICAL_INPUT",encoding="utf-8")
    config = ProjectConfig.model_validate({"run":{"id":"SOFTWARE_FIXTURE"},"inputs":{"protein_fasta":str(source),"enzymes":[],"scaffolds":[],"linkers":[]},
        "stages":{"m1_llps":{"feature_definitions_file":str(source),"rules_file":str(source)}}})
    science = ScientificProject(config=config,evidence_files=[EvidenceFile(path=source,sha256=sha256(source.read_bytes()).hexdigest())])
    science.verify()
    app.state.platform_store.save_project(Project(id="software-fixture",name="SOFTWARE_FIXTURE · 非科学计算",scientific_project=science.model_dump(mode="json")))
    app.state.fixture_calls,app.state.fixture_client = calls,client
    return app
