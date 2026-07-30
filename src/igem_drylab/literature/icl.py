from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


@dataclass(frozen=True)
class IclExample:
    id: str
    domain: str | None
    covered_metrics: tuple[str, ...]
    units: tuple[str, ...]
    keywords: tuple[str, ...]
    instruction: str
    context: str
    output: dict[str, Any]


def load_icl_examples(path: Path | None) -> list[IclExample]:
    if path is None or not path.exists():
        return []
    examples: list[dict[str, Any]] = []
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8") as handle:
            examples = [json.loads(line) for line in handle if line.strip()]
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
        examples = data if isinstance(data, list) else data.get("examples", [])
    return [_coerce_example(item) for item in examples]


def select_icl_examples(
    examples: Sequence[IclExample],
    text: str,
    metrics: Sequence[str],
    *,
    domain: str | None = None,
    k: int = 3,
) -> list[IclExample]:
    scored = [
        (_score_example(example, text, metrics, domain), _keyword_hits(example, text), index, example)
        for index, example in enumerate(examples)
    ]
    pool = [item for item in scored if item[1] > 0] or scored
    pool.sort(key=lambda item: (-item[0], -item[1], item[2]))
    return [example for score, _hits, _index, example in pool[:k] if score > 0]


def _score_example(
    example: IclExample,
    text: str,
    metrics: Sequence[str],
    domain: str | None,
) -> float:
    score = 0.0
    score += min(len(set(metrics) & set(example.covered_metrics)), 8)
    lower = text.lower()
    score += 0.5 * sum(1 for unit in example.units if unit.lower() in lower)
    score += 4.0 * _keyword_hits(example, text)
    score += 0.2 * len(_tokens(text) & _tokens(example.context))
    if domain and example.domain == domain:
        score += 3.0
    return score


def _keyword_hits(example: IclExample, text: str) -> int:
    lower = text.lower()
    hits = 0
    for keyword in example.keywords:
        token = keyword.strip().lower()
        if not token or token.isdigit():
            continue
        if len(token) < 3 and not re.search(r"[a-z]\d|\d[a-z]", token):
            continue
        if token in lower:
            hits += 1
    return hits


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z0-9_/%'.-]+", (text or "").lower()))


def _coerce_example(item: dict[str, Any]) -> IclExample:
    return IclExample(
        id=str(item.get("id", "")),
        domain=item.get("domain"),
        covered_metrics=tuple(str(x) for x in item.get("covered_metrics", [])),
        units=tuple(str(x) for x in item.get("units", [])),
        keywords=tuple(str(x) for x in item.get("keywords", [])),
        instruction=str(item.get("instruction", "")),
        context=str(item.get("context", "")),
        output=item.get("output", {}) if isinstance(item.get("output"), dict) else {},
    )
