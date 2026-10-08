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
