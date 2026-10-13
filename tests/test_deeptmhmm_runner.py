"""CLI plumbing checks only; these fixtures are not scientific predictions."""

from pathlib import Path
import subprocess
import sys

import pytest

from igem_drylab import deeptmhmm_runner


@pytest.mark.parametrize("interpreter_symlink", [False, True])
def test_native_directory_contract_and_unmodified_output(tmp_path: Path, monkeypatch, interpreter_symlink) -> None:
    program = tmp_path / "original"
    program.mkdir()
    source = program / "predict.py"
    source.write_text("original source fixture; not executed\n")
    fasta = tmp_path / "input.fasta"
    fasta.write_text("software plumbing fixture; not a biological prediction\n")
    output = tmp_path / "workflow-output"
    output.mkdir()
    python = Path(sys.executable)
    if interpreter_symlink:
        python = tmp_path / "venv/bin/python"
        python.parent.mkdir(parents=True)
        try:
            python.symlink_to(sys.executable)
        except OSError as error:
            if getattr(error, "winerror", None) == 1314:
                pytest.skip("Windows symlink privilege unavailable; POSIX CI exercises this case.")
            raise
    monkeypatch.setattr(sys, "argv", ["runner", "--python", str(python),
        "--program-dir", str(program), "--fasta", str(fasta), "--output-dir", str(output)])

    def original_cli_fixture(argv, *, cwd, env, check):
        assert argv == [str(python.absolute()), str(source.resolve()),
            "--fasta", str(fasta.resolve()), "--output-dir", str(output / "native")]
        assert cwd == program.resolve() and check
        assert env["CUDA_VISIBLE_DEVICES"] == ""
        native = Path(argv[-1])
        assert not native.exists()
        native.mkdir()
        for name in ("predicted_topologies.3line", "TMRs.gff3", "deeptmhmm_results.md"):
            (native / name).write_bytes(b"unchanged CLI plumbing fixture\n")
        (native / "embeddings").mkdir()
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(deeptmhmm_runner.subprocess, "run", original_cli_fixture)
    deeptmhmm_runner.main()
    assert source.read_text() == "original source fixture; not executed\n"
    assert (output / "predicted_topologies.3line").read_bytes() == (output / "native/predicted_topologies.3line").read_bytes()
    assert not (output / "embeddings").exists()


def test_existing_native_job_is_preserved(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "native").mkdir()
    sentinel = tmp_path / "native/original-result"
    sentinel.write_bytes(b"keep")
    monkeypatch.setattr(sys, "argv", ["runner", "--python", sys.executable,
        "--program-dir", str(tmp_path), "--fasta", str(tmp_path / "input.fasta"),
        "--output-dir", str(tmp_path)])
    monkeypatch.setattr(deeptmhmm_runner.subprocess, "run", lambda *a, **kw: pytest.fail("must not resubmit"))
    with pytest.raises(FileExistsError, match="preserve the original job"):
        deeptmhmm_runner.main()
    assert sentinel.read_bytes() == b"keep"
