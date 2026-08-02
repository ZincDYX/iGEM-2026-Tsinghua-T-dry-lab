from __future__ import annotations

from igem_drylab.kinetics import CompetitiveCascadeParameters, InductionGate, simulate_piecewise_induction
from igem_drylab.scoring.m4_reaction import score_m4_piecewise_ode


def test_oc_first_dmt_later_reduces_leakage_in_competitive_model():
    params = CompetitiveCascadeParameters(
        kcat_oc=1.2,
        km_oc=1.0,
        kcat_dmt_product=1.1,
        km_dmt_product=0.7,
        kcat_dmt_leak=0.4,
        km_dmt_leak=1.0,
        partition_a=3.0,
        partition_b=6.0,
    )
    oc_gate = InductionGate(on_time=0.0, basal=0.0, induced=1.0)
    dmt_delayed = InductionGate(on_time=4.0, basal=0.0, induced=1.0)
    dmt_immediate = InductionGate(on_time=0.0, basal=0.0, induced=1.0)

    delayed = simulate_piecewise_induction(params, oc_gate=oc_gate, dmt_gate=dmt_delayed)
    immediate = simulate_piecewise_induction(params, oc_gate=oc_gate, dmt_gate=dmt_immediate)

    assert delayed.product[-1] > 0
    assert delayed.byproduct[-1] < immediate.byproduct[-1]


def test_piecewise_m4_score_reports_leakage_reduction():
    score = score_m4_piecewise_ode(
        candidate_id="demo",
        params=CompetitiveCascadeParameters(kcat_dmt_leak=0.4, partition_b=6.0),
        oc_gate=InductionGate(on_time=0.0, basal=0.0, induced=1.0),
        dmt_gate=InductionGate(on_time=4.0, basal=0.0, induced=1.0),
    )

    assert score.product_final >= 0
    assert score.byproduct_final >= 0
    assert score.observable_13_reduction >= 1.0
    assert score.recommendation in {"drop", "iterate", "test"}
