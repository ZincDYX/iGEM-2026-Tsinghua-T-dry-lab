from dataclasses import replace

import numpy as np

from igem_drylab.kinetics import CascadeParameters, phase_concentrations, simulate_cascade


def test_phase_partition_conserves_average_concentration():
    average, partition, phi = 7.5, 20.0, 0.08
    dense, dilute = phase_concentrations(average, partition, phi)
    assert np.isclose(phi * dense + (1 - phi) * dilute, average)
    assert np.isclose(dense / dilute, partition)


def test_cascade_respects_mass_without_degradation():
    params = CascadeParameters(phi=0.1, oc_total=1.0, dmt_total=1.0)
    result = simulate_cascade(params, initial=(10.0, 0.0, 0.0), t_end=10.0)
    assert np.allclose(result.concentrations.sum(axis=0), 10.0, atol=1e-6)
    assert result.product[-1] > 0


def test_zero_second_enzyme_accumulates_no_product():
    params = replace(CascadeParameters(), dmt_total=0.0)
    result = simulate_cascade(params, t_end=5.0)
    assert np.isclose(result.product[-1], 0.0)
    assert result.intermediate[-1] > 0
