from pathlib import Path

from igem_drylab.literature import build_prompt, load_schema, parse_json_object, select_icl_examples
from igem_drylab.literature.icl import load_icl_examples


def test_icl_selector_prefers_keyword_matched_example():
    examples = load_icl_examples(Path("data/icl/glabridin_examples.minimal.jsonl"))
    selected = select_icl_examples(
        examples,
        "GgOC1 converted 4'-O-methylpreglabridin to glabridin.",
        ["enzyme_name", "substrate_name", "main_product_name"],
        domain="glabridin_enzyme_catalysis",
        k=1,
    )

    assert len(selected) == 1
    assert selected[0].id == "glabridin_case_01"


def test_literature_prompt_contains_schema_metrics_and_json_contract():
    schema = load_schema(Path("data/schemas/glabridin_enzyme_catalysis.schema.json"))
    examples = load_icl_examples(Path("data/icl/glabridin_examples.minimal.jsonl"))
    prompt = build_prompt(
        text=Path("examples/literature/glabridin_excerpt.txt").read_text(encoding="utf-8"),
        schema=schema,
        examples=examples,
    )

    assert "enzyme_name" in prompt
    assert "Return JSON only" in prompt
    assert '{"records": [<record>, ...]}' in prompt
    assert "GgOC1" in prompt


def test_parse_json_object_accepts_fenced_json():
    parsed = parse_json_object('```json\n{"records": []}\n```')
    assert parsed == {"records": []}
