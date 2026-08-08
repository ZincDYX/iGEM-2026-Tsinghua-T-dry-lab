from __future__ import annotations

from pydantic import BaseModel, Field


class NextExperimentRecommendation(BaseModel):
    target_parameter_or_hypothesis: str
    proposed_measurement: str
    rationale: str
    expected_information_gain_proxy: float = Field(ge=0)
    cost_class: str
    priority: int = Field(ge=1)


def recommend_measurements(candidates: list[dict[str, object]]) -> list[NextExperimentRecommendation]:
    """Rank transparent sensitivity×uncertainty/cost proxies, not Bayesian design."""
    costs = {"low": 1.0, "medium": 2.0, "high": 4.0}
    records = []
    for item in candidates:
        sensitivity, uncertainty, cost = float(item.get("sensitivity", 0)), float(item.get("uncertainty", 0)), str(item.get("cost_class", "high"))
        score = sensitivity * uncertainty / costs.get(cost, 4.0)
        records.append((score, item, cost))
    records.sort(key=lambda value: value[0], reverse=True)
    return [NextExperimentRecommendation(target_parameter_or_hypothesis=str(item["target"]), proposed_measurement=str(item["measurement"]), rationale="ranked by local sensitivity × uncertainty / stated cost", expected_information_gain_proxy=score, cost_class=cost, priority=index + 1) for index, (score, item, cost) in enumerate(records)]
