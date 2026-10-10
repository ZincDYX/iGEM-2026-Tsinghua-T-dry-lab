"""Software protocol fixtures, not remote scientific execution evidence."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
from threading import Event
from time import monotonic, sleep

import pytest

from igem_drylab import jpred_runner
from igem_drylab.workflow.models import Project
from igem_drylab.workflow.tools import ToolDeferred
from test_workbench_execution import engine, graph


def runner_args(tmp_path, monkeypatch, number=1):
    fasta = tmp_path / "input.fasta"
    fasta.write_text(">input\nGSTSSGGGGGSGGSGGSGGS\n")
    state = tmp_path / "job.json"
    monkeypatch.setattr(sys, "argv", ["jpred_runner", "--client", "PROTOCOL_ONLY", "--fasta", str(fasta),
        "--record", "input", "--output-dir", str(tmp_path / f"attempt-{number}"), "--state-file", str(state)])
    return state


@pytest.mark.parametrize("failure", ["timeout", "no_unique_ack"])
def test_intent_precedes_submission_and_unknown_ack_never_resubmits(tmp_path, monkeypatch, failure):
    state = runner_args(tmp_path,monkeypatch)
    submits = []
    def protocol(argv, **kwargs):
        if argv[1] == "--version":
            return subprocess.CompletedProcess(argv,0,"PROTOCOL_ONLY","")
        assert json.loads(state.read_text())["status"] == "submitting"
        submits.append(argv)
        if failure == "timeout":
            raise subprocess.TimeoutExpired(argv,1)
        return subprocess.CompletedProcess(argv,0,"response lost, not an acknowledgement","")
    monkeypatch.setattr(jpred_runner.subprocess,"run",protocol)
    with pytest.raises((subprocess.TimeoutExpired,ValueError)):
        jpred_runner.main()
    assert json.loads(state.read_text())["status"] == "submission_unknown"
    runner_args(tmp_path,monkeypatch,2)
    with pytest.raises(ValueError,match="acknowledgement unknown"):
        jpred_runner.main()
    assert len(submits) == 1


def test_original_ack_log_reconciles_crash_before_ack_commit_without_new_post(tmp_path,monkeypatch):
    state = runner_args(tmp_path,monkeypatch)
    submits = []
    accepted = jpred_runner._accepted_job
    def crash(raw):
        raise KeyboardInterrupt("simulated process death")
    monkeypatch.setattr(jpred_runner,"_accepted_job",crash)
    def protocol(argv,**kwargs):
        if argv[1] == "--version":return subprocess.CompletedProcess(argv,0,"PROTOCOL_ONLY","")
        if argv[1] == "submit":
            submits.append(argv)
            return subprocess.CompletedProcess(argv,0,"Accepted jp_ProtocolOnly","")
        raise subprocess.CalledProcessError(1,argv)  # Retrieval interruption, not a prediction.
    monkeypatch.setattr(jpred_runner.subprocess,"run",protocol)
    with pytest.raises(KeyboardInterrupt):jpred_runner.main()
    assert json.loads(state.read_text())["status"] == "submitting"
    monkeypatch.setattr(jpred_runner,"_accepted_job",accepted)
    runner_args(tmp_path,monkeypatch,2)
    with pytest.raises(subprocess.CalledProcessError):jpred_runner.main()
    assert json.loads(state.read_text())["job_id"] == "jp_ProtocolOnly"
    assert len(submits) == 1


def test_one_poll_returns_waiting_with_original_identity_not_a_prediction(tmp_path,monkeypatch,capsys):
    state = runner_args(tmp_path,monkeypatch)
    monkeypatch.setattr(sys,"argv",sys.argv+["--poll-once"])
    def protocol(argv,**kwargs):
        assert kwargs["timeout"] == 60
        if argv[1]=="--version":return subprocess.CompletedProcess(argv,0,"PROTOCOL_ONLY","")
        if argv[1]=="submit":return subprocess.CompletedProcess(argv,0,"Accepted jp_ProtocolOnly","")
        assert "--attempts=1" in argv
        return subprocess.CompletedProcess(argv,0,"still running","")
    from urllib.error import HTTPError
    def unavailable(url,**kwargs):raise HTTPError(url,404,"not ready",{},None)
    monkeypatch.setattr(jpred_runner.subprocess,"run",protocol)
    monkeypatch.setattr(jpred_runner,"urlopen",unavailable)
    jpred_runner.main()
    assert json.loads(capsys.readouterr().out)["status"] == "waiting_for_result"
    assert json.loads(state.read_text())["job_id"] == "jp_ProtocolOnly"
    assert not (tmp_path/"attempt-1/secondary.json").exists()


def test_submit_only_configuration_is_rejected_before_any_external_call(tmp_path,monkeypatch):
    from types import SimpleNamespace
    import igem_drylab.workflow.sequence_predictions as prediction
    from igem_drylab.workflow.tools import NodeContext,ToolFailure
    payload=prediction.SequencePredictionInput(item={"id":"fixture","sequence":"GSTSSGGGGGSGGSGGSGGS","role":"idr"})
    class SubmitOnly:
        def is_available(self):return True
        def build_command(self,**kwargs):return SimpleNamespace(argv=["PROTOCOL_ONLY","submit"])
        def run(self,**kwargs):pytest.fail("Submit-only route must never be executed")
    monkeypatch.setattr(prediction,"create_tool_adapter",lambda *args:SubmitOnly())
    with pytest.raises(ToolFailure,match="submit-only"):
        prediction.predict_sequence("jpred",payload,NodeContext("run","node",tmp_path))


def test_native_waiting_state_is_deferred_not_published_as_success(tmp_path,monkeypatch):
    from types import SimpleNamespace
    import igem_drylab.workflow.sequence_predictions as prediction
    from igem_drylab.workflow.tools import NodeContext
    payload=prediction.SequencePredictionInput(item={"id":"fixture","sequence":"GSTSSGGGGGSGGSGGSGGS","role":"idr"})
    work=tmp_path/"attempt-1"
    work.mkdir()
    class Native:
        def __init__(self,config):self.config=config
        def is_available(self):return True
        def build_command(self,**kwargs):return SimpleNamespace(argv=["PROTOCOL_ONLY","-m","igem_drylab.jpred_runner"])
        def run(self,**kwargs):
            assert self.config.command.endswith(" --poll-once")
            (tmp_path/"remote-job.json").write_text(json.dumps({"status":"waiting_for_result","job_id":"PROTOCOL_ONLY"}))
            return SimpleNamespace(status="succeeded")
    monkeypatch.setattr(prediction,"create_tool_adapter",lambda name,config:Native(config))
    context=NodeContext("run","node",work,runtime_tools={"jpred":{"command":"PROTOCOL_ONLY -m igem_drylab.jpred_runner"}})
    with pytest.raises(ToolDeferred) as deferred:prediction.predict_sequence("jpred",payload,context)
    assert deferred.value.job_id=="PROTOCOL_ONLY"


def wait_for_status(runtime,run_id,status):
    deadline=monotonic()+3
    while monotonic()<deadline:
        if runtime.store.execution_state(run_id)["nodes"][0]["status"] == status:return
        sleep(.01)
    pytest.fail("software fixture status not reached")


def test_remote_wait_releases_worker_and_cancel_does_not_claim_remote_cancellation(tmp_path):
    calls=[]
    def handler(payload,context):
        calls.append(context.project_id)
        if context.project_id=="remote":raise ToolDeferred("PROTOCOL_ONLY",poll_after_seconds=60)
        return {"kind":"independent_software_fixture"}
    runtime=engine(tmp_path,handler,max_workers=1,idempotent=False)
    remote=runtime.create(Project(id="remote",name="fixture"),graph(1))
    local=runtime.create(Project(id="local",name="fixture"),graph(1))
    with ThreadPoolExecutor(max_workers=2) as controllers:
        waiting=controllers.submit(runtime.run,remote)
        wait_for_status(runtime,remote,"waiting")
        assert runtime.budget.state()["active_tasks"]==0
        assert controllers.submit(runtime.run,local).result(timeout=3)["status"]=="succeeded"
        runtime.store.control(remote,"cancel")
        result=waiting.result(timeout=3)
    assert result["status"]=="cancelled"
    assert result["nodes"][0]["remote_job"]["remote_cancellation_confirmed"] is False
    assert result["artifacts"]==[] and calls.count("remote")==1


def test_paused_remote_job_survives_engine_restart_with_same_attempt_and_job_identity(tmp_path):
    ready=Event()
    calls=[]
    def handler(payload,context):
        calls.append(context.work_dir)
        if not ready.is_set():raise ToolDeferred("PROTOCOL_ONLY",poll_after_seconds=.05)
        return {"kind":"retrieved_software_fixture"}
    runtime=engine(tmp_path,handler,max_workers=1,idempotent=False)
    run_id=runtime.create(Project(id="p",name="fixture"),graph(1,max_tool_calls=1))
    with ThreadPoolExecutor(max_workers=1) as controllers:
        future=controllers.submit(runtime.run,run_id)
        wait_for_status(runtime,run_id,"waiting")
        runtime.store.control(run_id,"pause")
        assert future.result(timeout=3)["status"]=="paused"
    restarted=engine(tmp_path,handler,max_workers=1,idempotent=False)
    restarted.store.clear_control(run_id)
    ready.set()
    result=restarted.run(run_id)
    assert result["status"]=="succeeded" and result["nodes"][0]["attempts"]==1
    assert len(set(calls))==1
    assert result["nodes"][0]["remote_job"]["status"]=="published"
    assert len(result["artifacts"])==1
