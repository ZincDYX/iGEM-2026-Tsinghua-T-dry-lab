import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from CatalystOptimizationSystem.core.schema_config import load_schema, schema_metric_names


def _norm_scalar(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    text = str(value).strip()
    if text.lower() in ("", "nan", "none", "null"):
        return None
    return text


def load_gold(path: str | Path) -> List[Dict[str, Any]]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def score_predictions(gold_rows: List[Dict[str, Any]], pred_df: pd.DataFrame, metrics: List[str]) -> Dict[str, Any]:
    n = min(len(gold_rows), len(pred_df))
    if n == 0:
        return {"n": 0, "error": "no comparable rows"}

    total_fields = 0
    value_matches = 0
    unit_matches = 0
    presence_matches = 0
    evidence_present = 0
    per_metric: Dict[str, Dict[str, int]] = {}

    for i in range(n):
        gold = gold_rows[i].get("expected", {})
        pred = pred_df.iloc[i]
        for metric in metrics:
            g_obj = gold.get(metric, {}) if isinstance(gold, dict) else {}
            g_value = _norm_scalar(g_obj.get("value") if isinstance(g_obj, dict) else None)
            g_unit = _norm_scalar(g_obj.get("unit") if isinstance(g_obj, dict) else None)
            p_value = _norm_scalar(pred.get(f"{metric}_value"))
            p_unit = _norm_scalar(pred.get(f"{metric}_unit"))
            p_evidence = _norm_scalar(pred.get(f"{metric}_evidence"))

            per_metric.setdefault(metric, {"fields": 0, "value": 0, "unit": 0, "presence": 0, "evidence": 0})
            total_fields += 1
            per_metric[metric]["fields"] += 1

            if (g_value is None) == (p_value is None):
                presence_matches += 1
                per_metric[metric]["presence"] += 1
            if g_value == p_value:
                value_matches += 1
                per_metric[metric]["value"] += 1
            if g_unit == p_unit:
                unit_matches += 1
                per_metric[metric]["unit"] += 1
            if p_value is not None and p_evidence:
                evidence_present += 1
                per_metric[metric]["evidence"] += 1

    def ratio(num: int, den: int) -> float:
        return float(num / den) if den else 0.0

    per_metric_rates = {
        metric: {
            "presence_accuracy": ratio(vals["presence"], vals["fields"]),
            "value_accuracy": ratio(vals["value"], vals["fields"]),
            "unit_accuracy": ratio(vals["unit"], vals["fields"]),
            "evidence_rate": ratio(vals["evidence"], vals["fields"]),
        }
        for metric, vals in per_metric.items()
    }
    return {
        "n": n,
        "field_count": total_fields,
        "presence_accuracy": ratio(presence_matches, total_fields),
        "value_accuracy": ratio(value_matches, total_fields),
        "unit_accuracy": ratio(unit_matches, total_fields),
        "evidence_rate": ratio(evidence_present, total_fields),
        "per_metric": per_metric_rates,
    }


def main():
    parser = argparse.ArgumentParser(description="Score extraction CSV against gold JSONL.")
    parser.add_argument("--gold", required=True)
    parser.add_argument("--pred", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--out")
    args = parser.parse_args()

    schema = load_schema(args.schema)
    metrics = schema_metric_names(schema)
    result = score_predictions(load_gold(args.gold), pd.read_csv(args.pred), metrics)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
