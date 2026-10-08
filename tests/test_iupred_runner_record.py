import json
from hashlib import sha256

import pytest

from igem_drylab.constructs.linker_features import parse_iupred2a_output, parse_secondary_structure_output


def test_iupred_sidecar_binds_actual_output_version_and_sequence(tmp_path):
    output = tmp_path / "iupred2a.txt"
    output.write_text("1 G 0.8\n2 S 0.9\n")
    digest = sha256(b"GS").hexdigest()
    record = dict(tool_name="IUPred2A", tool_version="0.1.2", input_sha256=digest,
        output_sha256=sha256(output.read_bytes()).hexdigest(), origin="automated", returncode=0,
        command=["python", "-m", "igem_drylab.iupred_runner"])
    output.with_suffix(".run.json").write_text(json.dumps(record))
    evidence = parse_iupred2a_output(output, tool_version="0.1.2", input_sha256=digest)
    assert evidence.provenance is not None
    assert evidence.disorder_mean == pytest.approx(0.85)
    output.write_text("1 G 0.7\n2 S 0.9\n")
    with pytest.raises(ValueError, match="record_output_sha256_mismatch"):
        parse_iupred2a_output(output, tool_version="0.1.2", input_sha256=digest)


def test_real_jpred_companion_sequence_is_explicit_and_exact(tmp_path):
    output = tmp_path / "job.jnet"
    output.write_text("jnetpred:-,H,E,-,\nJNETCONF:8,9,8,7,\n")
    companion = tmp_path / "job.seq"
    companion.write_text(">job\nGSAD\n")
    digest = sha256(b"GSAD").hexdigest()
    with pytest.raises(ValueError, match="sequence_hash_mismatch"):
        parse_secondary_structure_output(output, tool_name="JPred", tool_version="JPred4", input_sha256=digest)
    evidence = parse_secondary_structure_output(output, tool_name="JPred", tool_version="JPred4", input_sha256=digest, sequence_file=companion)
    assert evidence.states == "CHEC" and evidence.ss_fraction == 0.5
    assert evidence.sequence_file == companion
    companion.write_text(">job\nGSAE\n")
    with pytest.raises(ValueError, match="sequence_hash_mismatch"):
        parse_secondary_structure_output(output, tool_name="JPred", tool_version="JPred4", input_sha256=digest, sequence_file=companion)
