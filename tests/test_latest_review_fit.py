"""Analytical numerical fixtures, never scientific input records."""
import numpy as np
import pytest

from igem_drylab.wetlab.fit import fit_mechanistic_parameter, fit_scale_parameter


@pytest.mark.parametrize('scale', [1., 1e-3, 1e-6, 1e-12])
def test_common_observation_scale_preserves_optimum(scale):
    x = scale * np.arange(1., 5.)
    fit = fit_mechanistic_parameter(parameter_name='fixture', initial_value=1., bounds=(0., 4.),
        observed=(2*x).tolist(), predictor=lambda a: a*x)
    assert fit.status == 'estimated' and fit.best_fit == pytest.approx(2., abs=1e-8)
    assert fit.diagnostics['residual_scale'] > 0
    assert not fit.diagnostics['solution_inferior_to_profile']
    assert fit.diagnostics['squared_error'] == pytest.approx(sum(v*v for v in fit.residuals))


def test_nonmonotonic_predictor_restarts_from_better_profile():
    # a=0 is a stationary, poor local solution; sign is not globally identified.
    x = np.arange(1., 5.) * 1e-6
    fit = fit_mechanistic_parameter(parameter_name='fixture', initial_value=0., bounds=(-3., 3.),
        observed=(4*x).tolist(), predictor=lambda a: a*a*x)
    assert fit.status == 'estimated' and abs(fit.best_fit) == pytest.approx(2., abs=1e-7)
    assert not fit.diagnostics['solution_inferior_to_profile']


def test_scale_zero_is_unidentifiable_and_default_has_no_iid_interval():
    fit = fit_scale_parameter([0]*4, [0]*4, bootstrap_samples=20)
    assert fit.status == 'unidentifiable' and fit.best_fit is None and fit.confidence_interval is None
    regular = fit_scale_parameter([1,2,3,4], [2,4,6,8])
    assert regular.best_fit == pytest.approx(2.) and regular.confidence_interval is None
    assert regular.diagnostics['fit_kind'].startswith('descriptive')


def test_scale_bounds_and_resampling_requirements():
    fit = fit_scale_parameter([1,2,3,4], [20,40,60,80], bounds=(0,4))
    assert fit.status == 'boundary_limited' and fit.best_fit is None
    fit = fit_scale_parameter([1,2,3,4], [2,4,6,8], bootstrap_samples=10)
    assert fit.confidence_interval is None and 'declared' in fit.identifiability_warning
    fit = fit_scale_parameter([1,2,3,4], [2,4,6,8], bootstrap_samples=10, independent_samples=True)
    assert fit.confidence_interval == pytest.approx((2.,2.))
