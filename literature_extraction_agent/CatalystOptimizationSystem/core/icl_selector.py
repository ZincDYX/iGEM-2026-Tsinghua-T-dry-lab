import json
import re
from pathlib import Path
from typing import Any, Dict, List, Sequence


def load_icl_bank(path: str | Path | None) -> List[Dict[str, Any]]:
    if not path:
        return []
    path = Path(path)
    if not path.exists():
        return []
    examples = []
    if path.suffix.lower() == ".jsonl":
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    examples.append(json.loads(line))
    else:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        examples = data if isinstance(data, list) else data.get("examples", [])
    return examples


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z0-9_/%.-]+", (text or "").lower()))


def _keyword_hits(example: Dict[str, Any], text: str) -> int:
    text_lower = text.lower()
    hits = 0
    for keyword in example.get("keywords", []):
        token = str(keyword).strip().lower()
        if not token or token.isdigit():
            continue
        if len(token) < 3 and not re.search(r"[a-z]\d|\d[a-z]", token):
            continue
        if token in text_lower:
            hits += 1
    return hits


def score_example(example: Dict[str, Any], text: str, metrics: Sequence[str], domain: str | None = None) -> float:
    score = 0.0
    metric_set = set(metrics)
    covered = set(example.get("covered_metrics", []))
    score += 1.0 * min(len(metric_set & covered), 8)

    text_lower = text.lower()
    for unit in example.get("units", []):
        if str(unit).lower() in text_lower:
            score += 0.5
    score += 4.0 * _keyword_hits(example, text)

    score += 0.2 * len(_tokens(text) & _tokens(example.get("context", "")))
    if domain and example.get("domain") == domain:
        score += 3.0
    return score


def select_icl_examples(
    examples: List[Dict[str, Any]],
    text: str,
    metrics: Sequence[str],
    *,
    domain: str | None = None,
    k: int = 3,
) -> List[Dict[str, Any]]:
    scored = [
        (score_example(example, text, metrics, domain), _keyword_hits(example, text), idx, example)
        for idx, example in enumerate(examples)
    ]
    keyword_matched = [item for item in scored if item[1] > 0]
    pool = keyword_matched if keyword_matched else scored
    pool.sort(key=lambda item: (-item[0], -item[1], item[2]))
    return [example for score, _, _, example in pool[:k] if score > 0]
