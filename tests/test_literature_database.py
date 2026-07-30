from __future__ import annotations

from pathlib import Path

from igem_drylab.literature.database import build_database_from_manifest, mine_numeric_evidence, read_manifest
from igem_drylab.literature.schema import load_schema


def test_mine_numeric_evidence_from_cached_text_manifest():
    articles = read_manifest(Path("examples/literature_database/manifest.csv"))
    evidence = mine_numeric_evidence(articles, max_per_paper=8, max_contexts_per_paper=40)

    assert evidence
    assert any(item.value_text == "62" and item.unit_text == "%" for item in evidence)
    assert any(item.metric_hint == "titer" for item in evidence)


def test_build_database_from_manifest_writes_outputs(tmp_path):
    summary = build_database_from_manifest(
        manifest=Path("examples/literature_database/manifest.csv"),
        schema=load_schema(Path("data/schemas/glabridin_enzyme_catalysis.schema.json")),
        output_dir=tmp_path,
        max_per_paper=8,
        max_contexts_per_paper=40,
    )

    assert summary["numeric_evidence_rows"] >= 2
    assert summary["clean_records"] >= 1
    assert (tmp_path / "numeric_evidence.csv").exists()
    assert (tmp_path / "structured_records.csv").exists()
    assert (tmp_path / "clean_database.csv").exists()
