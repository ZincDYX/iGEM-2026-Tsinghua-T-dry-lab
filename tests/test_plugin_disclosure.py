"""Actual stdlib plugin process, fake env only; not OS sandbox certification."""
import json
from pathlib import Path

import pytest

from igem_drylab.workflow.engine import WorkflowEngine
from igem_drylab.workflow.models import LiteralInput, Project, Workflow, WorkflowNode
from igem_drylab.workflow.plugins import PluginManager
from igem_drylab.workflow.store import WorkflowStore
from igem_drylab.workflow.tools import WorkflowTools


@pytest.mark.parametrize("mode,grant", [("result", False), ("result", True), ("stderr", True)])
def test_real_plugin_secret_requires_hash_grant_and_cannot_leave_public_boundary(tmp_path, monkeypatch, mode, grant):
    marker = "NOT_REAL_PLUGIN_CREDENTIAL_SOFTWARE_FIXTURE"
    monkeypatch.setenv("FUSIONLAB_FIXTURE_ENV", marker)
    source = tmp_path / "fixture-source"
    source.mkdir()
    (source / "plugin.json").write_text(json.dumps({"id":"fixture","name":"fixture","description":"fake-secret oracle",
        "version":"1","capability":"software_fixture","license":"test-only","entrypoint":"main.py",
        "input_schema":{"type":"object"},"output_schema":{"type":"object"},"secret_env":["FUSIONLAB_FIXTURE_ENV"]}),encoding="utf-8")
    (source / "main.py").write_text(
        "import argparse,json,os,sys\np=argparse.ArgumentParser();p.add_argument('--input');p.add_argument('--output');a=p.parse_args()\n"
        "mode=json.load(open(a.input))['mode']; value=os.environ['FUSIONLAB_FIXTURE_ENV']\n"
        "if mode=='stderr': print(value,file=sys.stderr); sys.exit(7)\n"
        "json.dump({'value':value},open(a.output,'w'))\n",encoding="utf-8")
    store, tools = WorkflowStore(tmp_path / "ledger.sqlite"), WorkflowTools()
    engine = WorkflowEngine(store, tools, tmp_path / "artifacts")
    manager = PluginManager(tmp_path / "plugins", store, tools, disclosure=engine.disclosure)
    inspection = manager.inspect(source)
    if grant:
        manager.authorize(inspection["hash"], ["secret_env:FUSIONLAB_FIXTURE_ENV"])
    manager.install(source, trusted=True, expected_hash=inspection["hash"])
    tool_id = tools.list()[0]["id"]
    workflow = Workflow(id="fixture",name="fixture",nodes=[WorkflowNode(id="plugin",label="plugin",tool_id=tool_id,inputs={"mode":LiteralInput(value=mode)})])
    result = engine.run(engine.create(Project(id="fixture",name="fixture"),workflow))
    assert result["status"] == "failed" and result["artifacts"] == []
    public = engine.disclosure.run(result)
    assert marker not in json.dumps(public)
    expected = "plugin_capability_not_authorized" if not grant else ("plugin_process_failed" if mode == "stderr" else "disclosure_quarantined")
    assert public["nodes"][0]["error"]["code"] == expected
    assert public["nodes"][0]["error"]["diagnostic_id"]
