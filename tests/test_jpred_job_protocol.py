"""Remote-job retry protocol fixture, not a real JPred prediction."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

from igem_drylab import jpred_runner


@pytest.mark.integration
def test_retry_fetches_saved_job_without_second_submission(tmp_path, monkeypatch):
    fasta = tmp_path / "input.fasta"
    sequence = "GSTSSGGGGGSGGSGGSGGS"
    fasta.write_text(">input\n" + sequence + "\n")
    state = tmp_path / "persisted-job.json"
    calls = []
    def protocol(argv, **kwargs):
        calls.append(argv)
        if argv[1] == "--version":
            return subprocess.CompletedProcess(argv, 0, "PROTOCOL_ONLY\n", "")
        if argv[1] == "submit":
            return subprocess.CompletedProcess(argv, 0, "Accepted chklog?jp_ProtocolOnly", "")
        destination = Path(next(arg.split("=", 1)[1] for arg in argv if arg.startswith("--results=")))
        if len([call for call in calls if call[1] == "get_results"]) == 1:
            return subprocess.CompletedProcess(argv, 1, "temporary protocol failure", "")
        directory = destination / "jp_ProtocolOnly"
        directory.mkdir(parents=True)
        (directory / "jp_ProtocolOnly.jnet").write_text("jnetpred:" + ",".join("-" * 20) + ",\n")
        (directory / "jp_ProtocolOnly.seq").write_text(">input\n" + sequence + "\n")
        return subprocess.CompletedProcess(argv, 0, "protocol downloaded", "")
    monkeypatch.setattr(jpred_runner.subprocess, "run", protocol)
    def attempt(number):
        monkeypatch.setattr(sys, "argv", ["jpred_runner", "--client", "PROTOCOL_ONLY", "--fasta", str(fasta),
            "--record", "input", "--output-dir", str(tmp_path / f"attempt-{number}"), "--state-file", str(state)])
        jpred_runner.main()
    with pytest.raises(subprocess.CalledProcessError):
        attempt(1)
    assert json.loads(state.read_text())["job_id"] == "jp_ProtocolOnly"
    attempt(2)
    assert len([call for call in calls if call[1] == "submit"]) == 1
    evidence = json.loads((tmp_path / "attempt-2/secondary.json").read_text())
    assert evidence["states"] == "C" * 20 and evidence["ss_fraction"] == 0
    assert evidence["provenance"]["origin"] == "automated"


@pytest.mark.integration
def test_poll_once_timeout_reads_original_files_of_the_same_known_job(tmp_path, monkeypatch):
    from io import BytesIO
    sequence = "GSTSSGGGGGSGGSGGSGGS"
    fasta = tmp_path / "input.fasta";fasta.write_text(">input\n" + sequence + "\n")
    state = tmp_path / "remote-job.json"
    state.write_text(json.dumps(dict(protocol="jpred-known-job-v2",job_id="jp_ProtocolOnly",
        input_sha256=jpred_runner.sha256(sequence.encode()).hexdigest(),client_version="PROTOCOL_ONLY")))
    calls=[];urls=[]
    def protocol(argv, **kwargs):
        calls.append(argv)
        if argv[1]=="--version":return subprocess.CompletedProcess(argv,0,"PROTOCOL_ONLY\n","")
        assert argv[1]=="get_results"
        raise subprocess.TimeoutExpired(argv,60,output=b"Your job is 40% complete...",stderr=b"timeout fixture")
    def download(url, **kwargs):
        urls.append(url)
        if url.endswith('.jnet'):return BytesIO(("jnetpred:"+",".join("-"*20)+",\n").encode())
        return BytesIO((">jp_ProtocolOnly\n"+sequence+"\n").encode())
    monkeypatch.setattr(jpred_runner.subprocess,"run",protocol)
    monkeypatch.setattr(jpred_runner,"urlopen",download)
    output=tmp_path/'retrieved'
    monkeypatch.setattr(sys,"argv",['jpred_runner','--client','PROTOCOL_ONLY','--fasta',str(fasta),
        '--record','input','--output-dir',str(output),'--state-file',str(state),'--poll-once'])
    jpred_runner.main()
    assert [call[1] for call in calls]==['--version','get_results']
    assert all('/jp_ProtocolOnly/jp_ProtocolOnly.' in url for url in urls)
    assert '40%' in (output/'retrieve.log').read_text()
    evidence=json.loads((output/'secondary.json').read_text())
    assert evidence['states']=='C'*20
    assert json.loads(state.read_text())['status']=='validated_not_published'
@pytest.mark.data_contract
def test_original_acknowledgement_preserves_complete_URL_safe_job_identifier():
    from igem_drylab.jpred_runner import _accepted_job
    raw = '<h1>Created JPred job.</h1><a href="/jpred4/cgi-bin/chklog?jp_Synthetic_89">job</a> Accepted'
    assert _accepted_job(raw)=='jp_Synthetic_89'
    assert _accepted_job('Accepted chklog?jp_Abc-12_X')=='jp_Abc-12_X'
    assert _accepted_job('file: jp_filename.fasta\n'+raw)=='jp_Synthetic_89'


@pytest.mark.data_contract
def test_noncanonical_or_ambiguous_acknowledgement_does_not_guess_a_job():
    import pytest
    from igem_drylab.jpred_runner import _accepted_job
    with pytest.raises(ValueError):
        _accepted_job('Accepted jp_in_a_filename')
    with pytest.raises(ValueError):
        _accepted_job('Accepted chklog?jp_one chklog?jp_two')


@pytest.mark.integration
@pytest.mark.parametrize("saved,accepted,conflict", [
    ("jp_Synthetic", "jp_Synthetic_89", False),
    ("jp_Synthetic", "jp_Different_89", True),
])
def test_existing_job_reconciles_only_truncated_original_ack(tmp_path, monkeypatch, saved, accepted, conflict):
    from io import BytesIO
    sequence = "GSTSSGGGGGSGGSGGSGGS"
    fasta = tmp_path / "input.fasta"
    fasta.write_text(">input\n" + sequence + "\n")
    ack = tmp_path / "original-submit.log"
    ack.write_text(f'Accepted <a href="/jpred4/cgi-bin/chklog?{accepted}">original</a>')
    state = tmp_path / "remote-job.json"
    state.write_text(json.dumps(dict(job_id=saved, acknowledgement_log=str(ack),
        input_sha256=jpred_runner.sha256(sequence.encode()).hexdigest(), client_version="PROTOCOL_ONLY")))
    calls = []
    def protocol(argv, **kwargs):
        calls.append(argv)
        if argv[1] == "--version":
            return subprocess.CompletedProcess(argv, 0, "PROTOCOL_ONLY\n", "")
        assert argv[1] == "get_results" and f"--jobid={accepted}" in argv
        return subprocess.CompletedProcess(argv, 0, "", "")
    def download(url, **kwargs):
        assert f"/{accepted}/{accepted}." in url
        return BytesIO(("jnetpred:" + ",".join("-" * 20) + ",\n" if url.endswith(".jnet") else ">input\n" + sequence + "\n").encode())
    monkeypatch.setattr(jpred_runner.subprocess, "run", protocol)
    monkeypatch.setattr(jpred_runner, "urlopen", download)
    monkeypatch.setattr(sys, "argv", ["jpred_runner", "--client", "PROTOCOL_ONLY", "--fasta", str(fasta),
        "--record", "input", "--output-dir", str(tmp_path / "result"), "--state-file", str(state), "--poll-once"])
    if conflict:
        with pytest.raises(ValueError, match="conflicts"):
            jpred_runner.main()
        assert len(calls) == 1
    else:
        jpred_runner.main()
        assert [call[1] for call in calls] == ["--version", "get_results"]
        assert json.loads(state.read_text())["previous_truncated_job_id"] == saved
