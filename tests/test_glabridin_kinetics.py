from dataclasses import replace

import pytest

import numpy as np

from igem_drylab.kinetics import GlabridinKineticParameters, InductionGate, glabridin_rates, simulate_glabridin


def _params() -> GlabridinKineticParameters:
    return GlabridinKineticParameters(
        phi=0.1, pt_total=1, oc_total=1, dmt_total=1, kcat_pt=1.2, km_pt=1, kcat_oc=1.2, km_oc=1,
        kcat_dmt_9=0.5, km_dmt_9=1, kcat_dmt_11=1.1, km_dmt_11=0.7,
        partition_pt=1, partition_oc=5, partition_dmt=3, partition_9=1, partition_10=1, partition_11=2, partition_13=1, partition_15=1,
        activity_dense_pt=1, activity_dilute_pt=1, activity_dense_oc=1, activity_dilute_oc=1, activity_dense_dmt=1, activity_dilute_dmt=1,
    )


def test_glabridin_mass_balance_without_degradation():
    result = simulate_glabridin(_params(), t_end=10)
    assert result.mass_balance_error < 1e-6
    assert result.x15[-1] > 0


def test_dmt_competes_between_9_and_11():
    no_intermediate = glabridin_rates(np.array([5.0, 0.0, 0.0, 0.0, 0.0]), _params(), pt_gate_level=1, oc_gate_level=1, dmt_gate_level=1)
    with_intermediate = glabridin_rates(np.array([5.0, 0.0, 5.0, 0.0, 0.0]), _params(), pt_gate_level=1, oc_gate_level=1, dmt_gate_level=1)
    assert with_intermediate[2] < no_intermediate[2]


def test_delaying_dmt_reduces_13_in_synthetic_case():
    delayed = simulate_glabridin(_params(), dmt_gate=InductionGate(on_time=3, basal=0, induced=1), t_end=12)
    immediate = simulate_glabridin(_params(), dmt_gate=InductionGate(on_time=0, basal=0, induced=1), t_end=12)
    assert delayed.x13[-1] < immediate.x13[-1]


def test_pt_oc_dmt_and_partition_values_are_independent():
    result = simulate_glabridin(replace(_params(), pt_total=0), t_end=5)
    assert result.x10[-1] == pytest.approx(0)
    assert result.x11[-1] == pytest.approx(0)
