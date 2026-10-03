from __future__ import annotations

import json
from pathlib import Path

from igem_drylab.parsers.freesasa import parse_freesasa_json


def test_runner_output_shape_is_parser_compatible(tmp_path: Path) -> None:
    output = tmp_path / "freesasa.json"
    output.write_text(
        json.dumps({"totalArea": 10.0, "residueAreas": {"A": {"42": {"total": 10.0}}}}),
        encoding="utf-8",
    )

    areas = parse_freesasa_json(output)

    assert len(areas) == 1
    assert areas[0].chain == "A" and areas[0].residue == 42 and areas[0].total == 10.0
