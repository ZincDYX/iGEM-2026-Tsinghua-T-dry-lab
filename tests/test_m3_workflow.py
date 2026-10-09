"""Original optional avidity and uncertainty, synthetic server-only checks."""
import math

import pytest
from pydantic import ValidationError

from igem_drylab.m3_equilibrium import AvidityCorrection, solve_m3_equilibrium
from igem_drylab.m3_workflow import M3EnsembleInput, solve_m3_ensemble
from igem_drylab.design_analysis import RangeEvidence
from test_m3_markdown_contract import _input


@pytest.mark.parametrize("method,values,factor", [
    ("statistical_factor", {"value": 4}, .25), ("alpha", {"value": .2}, .2),
    ("free_energy", {"delta_delta_g_j_per_mol": -8.31446261815324*300*math.log(2), "temperature_k": 300}, .5)])
def test_optional_avidity_uses_original_factor_and_preserves_E2_mass(method, values, factor):
    correction = AvidityCorrection(method=method, **values, source_reference="synthetic_unit_fixture",
                                  reviewed_by="test_fixture", parameter_ids=["fixture-avidity"])
    base = _input()
    corrected = solve_m3_equilibrium(base.model_copy(update={"avidity_sh3": correction}))
    explicit = solve_m3_equilibrium(_input(kd_sh3_um=base.kd_sh3_um*factor))
    assert corrected.oc.total_dense_um == pytest.approx(explicit.oc.total_dense_um, abs=1e-10)
    assert corrected.phi*corrected.oc.total_dense_um+(1-corrected.phi)*corrected.oc.free_dilute_um == pytest.approx(base.c_oc_total_um, abs=1e-10)
    assert corrected.avidity_corrections["sh3"]["effective_kd_um"] == pytest.approx(base.kd_sh3_um*factor)
    assert "fixture-avidity" in corrected.input_parameter_ids


def test_expression_window_is_sampled_without_clamping_failed_geometry():
    row = RangeEvidence(parameter_name="c_oc_total_um", distribution="uniform", lower=1, upper=4,
                        source_reference="fixture", parameter_ids=["fixture-range"], reviewed_by="test_fixture")
    result = solve_m3_ensemble(M3EnsembleInput(equilibrium=_input(), ranges=[row], samples=8, seed=19,
                                              independence_reference="single_variable_fixture"))
    assert result["complete"] and result["valid_samples"] == 8
    assert result["intervals"]["oc.total_dense_um"]["hi"] > result["intervals"]["oc.total_dense_um"]["lo"]
    assert all(abs(r["result"]["oc"]["mass_balance_residual_um"]) < 1e-10 for r in result["samples"])
    blocked = solve_m3_ensemble(M3EnsembleInput(equilibrium=_input(joint_occupancy_independent=False), ranges=[row],
        samples=2, seed=19, independence_reference="fixture"))
    assert not blocked["complete"] and blocked["failed_samples"] == 2
    assert blocked["intervals"]["R_dense"]["lo"] is None


def test_no_ambiguous_avidity_or_float_topology():
    with pytest.raises(ValidationError):
        AvidityCorrection(method="free_energy", value=2, delta_delta_g_j_per_mol=-2, temperature_k=300,
                          source_reference="fixture", reviewed_by="fixture", parameter_ids=["fixture"])
    with pytest.raises(ValidationError, match="primitive"):
        M3EnsembleInput(equilibrium=_input(), ranges=[RangeEvidence(parameter_name="s_sh3", distribution="uniform",
            lower=1, upper=3, source_reference="fixture", parameter_ids=["fixture"], reviewed_by="fixture")],
            samples=2, seed=1, independence_reference="fixture")
