from __future__ import annotations

import asyncio
from pathlib import Path
import sys
import pytest
from pydantic import ValidationError

from igem_drylab.m3_equilibrium import M3EquilibriumInput, solve_m3_equilibrium
from igem_drylab.parameters import ParameterRecord, m3_requirements
from igem_drylab.pipeline import load_config
from igem_drylab.pipeline.models import M2FusionAssessment
from igem_drylab.pipeline.stages import run_m3


ROOT = Path(__file__).resolve().parents[1]


def _input(**updates: object) -> M3EquilibriumInput:
    payload: dict[str, object] = {
        "candidate_id": "candidate",
        "construct_id": "construct",
        "s_sh3": 3,
        "s_pdz": 1,
        "eta_acc_sh3": 0.8,
        "eta_acc_pdz": 0.9,
        "eta_bind_sh3": 0.75,
        "eta_bind_pdz": 0.5,
        "site_count_basis": "complete_assembly",
        "c_dense_basis": "complete_assembly",
        "joint_occupancy_independent": True,
        "m2_geometry_id": "m2-geometry-1",
        "phi": 0.1,
        "c_dense_um": 20.0,
        "kd_sh3_um": 2.0,
        "kd_pdz_um": 4.0,
        "k_oc": 5.0,
        "k_dmt": 2.0,
        "c_oc_total_um": 3.0,
        "c_dmt_total_um": 2.0,
        "input_parameter_ids": ["phi", "oc-total", "dmt-total"],
    }
    payload.update(updates)
    return M3EquilibriumInput.model_validate(payload)


def test_s1_and_e1_to_e6_follow_declared_equations_and_conserve_mass() -> None:
    result = solve_m3_equilibrium(_input())

    assert result.status == "valid"
    assert result.n_sh3_effective == pytest.approx(3 * 0.8 * 0.75)
    assert result.n_pdz_effective == pytest.approx(1 * 0.9 * 0.5)
    assert result.recruitment_preference_b == pytest.approx(0.5)
    assert result.oc is not None and result.dmt is not None
    assert result.oc.site_occupancy == pytest.approx(
        result.oc.free_dense_um / (2.0 + result.oc.free_dense_um)
    )
    assert abs(result.oc.mass_balance_residual_um) < 1e-10
    assert abs(result.dmt.mass_balance_residual_um) < 1e-10
    assert result.oc.bound_fraction_of_whole_cell_total == pytest.approx(
        0.1 * result.oc.bound_dense_um / 3.0
    )
    assert result.oc.dense_phase_fraction_of_whole_cell_total == pytest.approx(
        0.1 * result.oc.total_dense_um / 3.0
    )
    assert result.oc.dense_phase_fraction_of_whole_cell_total > result.oc.bound_fraction_of_whole_cell_total


def test_zero_effective_sites_reduce_to_two_phase_partition_mass_balance() -> None:
    payload = _input(
        s_sh3=0,
        s_pdz=0,
        eta_acc_sh3=0.0,
        eta_acc_pdz=0.0,
        eta_bind_sh3=0.0,
        eta_bind_pdz=0.0,
    )
    result = solve_m3_equilibrium(payload)
    expected_oc_dense = 3.0 / (0.1 + 0.9 / 5.0)

    assert result.oc is not None
    assert result.oc.free_dense_um == pytest.approx(expected_oc_dense)
    assert result.oc.bound_dense_um == 0.0


def test_s4_lever_rule_is_used_only_when_phi_is_not_supplied() -> None:
    result = solve_m3_equilibrium(
        _input(phi=None, c_scaffold_total_um=4.0, c_sat_um=1.0, c_dense_um=11.0)
    )

    assert result.phi == pytest.approx((4.0 - 1.0) / (11.0 - 1.0))
    assert result.phi_source == "S4_lever_rule"


def test_unconfirmed_independent_joint_occupancy_blocks_equilibrium_solution() -> None:
    result = solve_m3_equilibrium(_input(joint_occupancy_independent=False))

    assert result.status == "insufficient_data"
    assert result.m4_ready is False
    assert result.oc is None and result.dmt is None


def test_site_and_scaffold_concentration_entity_basis_must_match() -> None:
    with pytest.raises(ValidationError, match="site_count_basis_must_match_c_dense_basis"):
        _input(c_dense_basis="scaffold_monomer")


def test_s2_s3_capacity_conflict_does_not_rescale_e2_e3_outputs() -> None:
    baseline = solve_m3_equilibrium(_input(c_dense_um=1000.0))
    constrained = solve_m3_equilibrium(
        _input(
            c_dense_um=1000.0,
            v_scaffold_nm3=100.0,
            v_enzyme_nm3=100_000.0,
            volume_method="reviewed_3V_model",
        )
    )

    assert constrained.status == "capacity_conflict"
    assert constrained.m4_ready is False
    assert constrained.capacity_excess_um is not None and constrained.capacity_excess_um > 0
    assert constrained.oc is not None and baseline.oc is not None
    assert constrained.oc.total_dense_um == pytest.approx(baseline.oc.total_dense_um)
    assert constrained.excluded_volume_fraction == pytest.approx(6.02214076e23 * 1e-30 * 1000.0 * 100.0)
    assert "S3_capacity_exceeded_no_nonconserving_proportional_rescaling_applied" in constrained.warnings


def test_e8_e9_outputs_are_labeled_regime_conditional_candidates() -> None:
    result = solve_m3_equilibrium(_input(r_target=2.0))

    assert result.rho_star_low_occupancy_candidate == pytest.approx((2.0 / 1.5) * (2.0 / 4.0))
    assert result.rho_star_saturation_candidate == 2.0
    assert any("regime_conditional" in warning for warning in result.warnings)


def test_e7_is_reported_only_as_the_documented_regime_conditional_candidate() -> None:
    result = solve_m3_equilibrium(_input())
    rho = (3 * 0.8 * 0.75) / (1 * 0.9 * 0.5)
    e_ratio = 3.0 / 2.0

    assert result.e7_low_occupancy_dense_ratio_candidate == pytest.approx(rho * e_ratio * (4.0 / 2.0))
    assert result.e7_free_ratio_candidate == pytest.approx(
        e_ratio * (0.1 + 0.9 / 2.0) / (0.1 + 0.9 / 5.0)
    )
    assert any("E7_values_are_low_occupancy" in warning for warning in result.warnings)


def test_e10_analytic_normalized_sensitivity_matches_conservative_resolve() -> None:
    baseline_input = _input()
    baseline = solve_m3_equilibrium(baseline_input)
    step = baseline_input.kd_sh3_um * 1e-5
    lower = solve_m3_equilibrium(_input(kd_sh3_um=baseline_input.kd_sh3_um - step))
    upper = solve_m3_equilibrium(_input(kd_sh3_um=baseline_input.kd_sh3_um + step))
    assert baseline.dense_oc_dmt_ratio is not None
    assert lower.dense_oc_dmt_ratio is not None and upper.dense_oc_dmt_ratio is not None
    numerical = (
        baseline_input.kd_sh3_um
        / baseline.dense_oc_dmt_ratio
        * (upper.dense_oc_dmt_ratio - lower.dense_oc_dmt_ratio)
        / (2 * step)
    )

    assert baseline.normalized_sensitivities_e10["kd_sh3"] == pytest.approx(numerical, rel=1e-7)


def test_official_mcp_server_calls_m3_solver() -> None:
    from mcp import Client
    from igem_drylab.mcp.server import server

    async def exercise() -> None:
        async with Client(server) as client:
            tools = await client.list_tools()
            assert "igem.m3.solve_equilibrium" in {item.name for item in tools.tools}
            response = await client.call_tool(
                "igem.m3.solve_equilibrium",
                {"inputs": _input().model_dump(mode="json")},
            )
            assert response.is_error is not True
            assert response.structured_content["result"]["status"] == "valid"
            assert abs(response.structured_content["result"]["oc"]["mass_balance_residual_um"]) < 1e-10

    asyncio.run(exercise())


def test_pipeline_finite_site_mode_consumes_m2_geometry_and_s1_e6_parameters(tmp_path: Path) -> None:
    config = load_config(Path("configs/m1_m4_example.yaml"))
    config.execution.allow_assumptions = True
    values = {
        "phi": 0.1,
        "pt_total": 1.0,
        "oc_total": 3.0,
        "dmt_total": 2.0,
        "partition_pt": 1.0,
        "partition_oc": 5.0,
        "partition_dmt": 2.0,
        "c_dense_scaffold": 20.0,
        "kd_sh3": 2.0,
        "kd_pdz": 4.0,
    }
    requirements = {item.name: item for item in m3_requirements()}
    config.parameters = [
        ParameterRecord(
            parameter_id=name,
            name=name,
            value=value,
            unit=requirements[name].canonical_unit,
            parameter_type=requirements[name].parameter_type,
            enzyme_id=requirements[name].enzyme_id,
            species_id=requirements[name].species_id,
            source_type="assumption",
            source_reference="M3 contract test",
            review_status="approved",
        )
        for name, value in values.items()
    ]
    assessment = M2FusionAssessment(
        candidate_id="candidate",
        construct_id="construct",
        construct_definition={"id": "construct"},
        status="valid",
        data_quality="predicted",
        screen_verdict="pass",
        confidence_gate="high",
        recommended_for_m3=True,
        s_sh3=3,
        s_pdz=1,
        eta_acc_sh3=0.8,
        eta_acc_pdz=0.9,
        eta_bind_sh3=0.75,
        eta_bind_pdz=0.5,
        site_count_basis="complete_assembly",
        joint_occupancy_independent=True,
        m2_geometry_id="m2-geometry-1",
    )

    records, _ = run_m3(config, tmp_path, [assessment])

    assert records[0].status == "valid"
    assert records[0].formula_version == "m3-s1-e10-2026-09-27"
    assert abs(records[0].mass_balance_residual_um["OC"]) < 1e-10
    assert records[0].binding_recruited_fraction["OC"] < records[0].fraction_in_dense["OC"]
    assert records[0].m4_candidate_context is not None


def test_stdio_mcp_server_calls_m3_solver() -> None:
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters

    async def exercise() -> None:
        params = StdioServerParameters(command=sys.executable, args=["-m", "igem_drylab.mcp.server"], cwd=ROOT)
        async with Client(params, read_timeout_seconds=20) as client:
            response = await client.call_tool(
                "igem.m3.solve_equilibrium",
                {"inputs": _input().model_dump(mode="json")},
            )
            assert response.is_error is not True
            assert response.structured_content["result"]["formula_version"] == "m3-s1-e10-2026-09-27"
            assert response.structured_content["result"]["m4_ready"] is True

    asyncio.run(exercise())
