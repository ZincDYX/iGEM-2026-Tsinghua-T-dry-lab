"""Server-only numerical workflow checks; fixtures are not measured biology."""
import asyncio
from pathlib import Path
import sys

import pytest
from mcp import Client
from mcp.client.stdio import StdioServerParameters

from igem_drylab.design_analysis import M4AnalysisConfig, RangeEvidence
from igem_drylab.m4_workflow import M4ReportInput, run_m4_report
from test_m4_markdown_contract import _input


def test_no_droplet_three_scenarios_are_identical_and_have_matched_baseline():
    result = run_m4_report(M4ReportInput(steady_input=_input(phi=0)))
    assert result["status"] == "valid"
    assert result["yield_rel"] == pytest.approx(dict(H0=1, recruit_only=1, directional=1), abs=1e-10)
    for scenario in result["scenarios"].values():
        assert scenario["mass_invariant_residual"] == pytest.approx(0, abs=1e-8)
    assert result["expression_cost"] is None
    assert not {"rank", "verdict", "hard_constraints", "composite_score"} & result.keys()


def test_joint_lhs_envelopes_use_paired_H0_not_fixed_base_denominator():
    settings = M4AnalysisConfig(ranges=[RangeEvidence(parameter_name="kcat_r3", distribution="uniform",
        lower=2, upper=8, source_reference="synthetic_protocol", parameter_ids=["kcat-R3"], reviewed_by="test_fixture")],
        samples=8, random_seed=123, standard_deviation_ddof=1, independence_evidence_reference="fixture_single_variable")
    result = run_m4_report(M4ReportInput(steady_input=_input(phi=0), analysis=settings))
    assert result["uncertainty"]["complete"]
    for row in result["uncertainty"]["intervals"].values():
        assert row["yield_rel"]["lo"] == pytest.approx(1, abs=1e-10)
        assert row["yield_rel"]["hi"] == pytest.approx(1, abs=1e-10)
    assert result["analysis"]["robustness"]["valid_samples"] == 8


def test_no_product_outlet_blocks_whole_report_not_fake_three_yields():
    case = _input()
    case.secretion_rate_per_h["15"] = 0
    result = run_m4_report(M4ReportInput(steady_input=case))
    assert result["status"] == "blocked"
    assert all(v is None for v in result["yield_abs"].values())


def test_actual_stdio_report_is_available_and_executes():
    async def exercise():
        parameters = StdioServerParameters(command=sys.executable, args=["-m", "igem_drylab.mcp.server"],
            cwd=Path(__file__).resolve().parents[1], env={"PYTHONPATH": str(Path(__file__).resolve().parents[1]/"src")})
        async with Client(parameters, read_timeout_seconds=60) as client:
            response = await client.call_tool("igem.m4.report", {"payload": M4ReportInput(steady_input=_input(phi=0)).model_dump(mode="json")})
            assert not response.is_error
            assert response.structured_content["result"]["yield_rel"]["directional"] == pytest.approx(1)
    asyncio.run(exercise())
