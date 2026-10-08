"""Protocol fixture only; actual author predictions are separate server evidence."""
from hashlib import sha256
import json

import pytest

from igem_drylab.pscore_runner import parse_pscore_output


def test_original_global_score_is_read_without_repairing_raw_table(tmp_path):
    sequence = "G" * 140
    output = tmp_path / "pscore.txt"
    raw = "seq_N aa PScore<br>137 G 1.100<br>137 G 1.100<br><br> PScore: 2.75 "
    output.write_text(raw)
    record = dict(input_sha256=sha256(sequence.encode()).hexdigest(), input_length=140,
                  output_sha256=sha256(output.read_bytes()).hexdigest(), tool_version="PROTOCOL_ONLY",
                  source="author-source", interpretation="not experiment")
    output.with_suffix(".run.json").write_text(json.dumps(record))
    parsed = parse_pscore_output(output, sequence=sequence)
    assert parsed["pscore"] == 2.75 and parsed["formal_ranking"] is None
    assert output.read_text() == raw
    with pytest.raises(ValueError, match="input identity"):
        parse_pscore_output(output, sequence="A" * 140)
    output.write_text(raw + "changed")
    with pytest.raises(ValueError, match="raw output changed"):
        parse_pscore_output(output, sequence=sequence)
