from __future__ import annotations

import asyncio
from pathlib import Path
import sys

import pytest
from pydantic import ValidationError

from igem_drylab.full_network import COMPOUNDS, ENZYME_SUBSTRATES, REACTIONS
from igem_drylab.m4_steady_state import M4SteadyStateInput, solve_m4_steady_state
from igem_drylab.parameters import ParameterRecord, m4_markdown_steady_requirements
from igem_drylab.pipeline import load_config
from igem_drylab.pipeline.config import M4Config
from igem_drylab.pipeline.models import M3ConcentrationAssessment, M4CandidateContext
from igem_drylab.pipeline.stages import run_m4


ROOT = Path(__file__).resolve().parents[1]


def _input(**updates: object) -> M4SteadyStateInput:
    payload: dict[str, object] = {
        "candidate_id": "candidate",
        "construct_id": "construct",
        "condition_id": "condition",
        "phi": 0.1,
        "enzymes": {
            enzyme: {"dense_um": 1.0, "dilute_um": 1.0, "m3_source_id": "m3-result"}
            for enzyme in ENZYME_SUBSTRATES
        },
        "metabolite_kp": {compound: 1.0 for compound in COMPOUNDS},
        "reactions": [
            {
                "reaction_id": reaction_id,
                "enzyme": enzyme,
                "substrate": substrate,
                "product": product,
                "kcat_per_h": 10.0,
                "km_um": 1.0,
                "parameter_ids": [f"kcat-{reaction_id}", f"km-{reaction_id}"],
            }
            for reaction_id, enzyme, substrate, product in REACTIONS
        ],
        "input_flux_um_per_h": 0.5,
        "secretion_rate_per_h": {compound: 0.2 for compound in COMPOUNDS},
        "secretion_normalization": "original_unweighted_dilute_concentration",
        "initial_guess_um": {compound: 0.5 for compound in COMPOUNDS},
        "input_parameter_ids": ["vin", "ksec", "kp", "m3-result"],
    }
    payload.update(updates)
    return M4SteadyStateInput.model_validate(payload)


def test_step0_network_requires_r10_m14_to_m15_correction() -> None:
    payload = _input().model_dump(mode="json")
    payload["reactions"][-1]["substrate"] = "11"

    with pytest.raises(ValidationError, match="R10_is_14_to_15"):
        M4SteadyStateInput.model_validate(payload)


def test_nonzero_m15_steady_state_is_blocked_without_m15_outlet() -> None:
    result = solve_m4_steady_state(
        _input(secretion_rate_per_h={compound: (0.0 if compound == "15" else 0.2) for compound in COMPOUNDS})
    )

    assert result.status == "blocked"
    assert "requires_ksec_15" in result.warnings[0]


def test_step2_to_step6_steady_state_fluxes_and_invariant() -> None:
    result = solve_m4_steady_state(_input())

    assert result.status == "valid"
    assert set(result.reaction_flux_um_per_h) == {f"R{index}" for index in range(1, 11)}
    assert max(abs(value) for value in result.steady_state_residual_um_per_h.values()) < 1e-8
    assert result.yield_abs is not None and 0 <= result.yield_abs <= 1
    assert result.secretion_loss_8_to_14 is not None
    assert result.mass_invariant_residual == pytest.approx(0.0, abs=1e-7)
    assert result.robustness is None and result.sensitivity is None and result.scaffold_scan is None
    # Independent per-species stoichiometry from the original reaction table.
    v=result.reaction_flux_um_per_h; s=result.secretion_flux_um_per_h
    balance={'8':.5-v['R1']-v['R4']-s['8'], '9':v['R1']-v['R2']-v['R5']-s['9'],
        '10':v['R2']-v['R3']-v['R6']-s['10'], '11':v['R3']-v['R7']-s['11'],
        '12':v['R4']-v['R8']-s['12'], '13':v['R5']+v['R8']-v['R9']-s['13'],
        '14':v['R6']+v['R9']-v['R10']-s['14'], '15':v['R7']+v['R10']-s['15']}
    assert max(abs(x) for x in balance.values())<1e-8  # uM/h solver residual budget
    assert sum(s.values()) == pytest.approx(.5,rel=0.,abs=1e-8)


def test_phi_zero_uses_explicit_single_phase_path_without_division_by_phi() -> None:
    result = solve_m4_steady_state(_input(phi=0.0))

    assert result.status == "valid"
    assert all(value == 0.0 for value in result.concentrations_dense_um.values())


def test_official_mcp_server_calls_m4_steady_state() -> None:
    from mcp import Client
    from igem_drylab.mcp.server import server

    async def exercise() -> None:
        async with Client(server) as client:
            tools = await client.list_tools()
            assert "igem.m4.solve_steady_state" in {item.name for item in tools.tools}
            response = await client.call_tool(
                "igem.m4.solve_steady_state",
                {"inputs": _input().model_dump(mode="json")},
            )
            assert response.is_error is not True
            assert response.structured_content["result"]["status"] == "valid"

    asyncio.run(exercise())


def test_pipeline_routes_markdown_steady_state_without_decision_fields(tmp_path: Path) -> None:
    network = tmp_path / "reactions.csv"
    network.write_text(
        "reaction_id,enzyme,substrate,product\n"
        + "".join(f"{rid},{enzyme},{substrate},{product}\n" for rid, enzyme, substrate, product in REACTIONS),
        encoding="utf-8",
    )
    config = load_config(Path("configs/m1_m4_example.yaml"))
    config.execution.allow_assumptions = True
    config.stages.m4_reaction = M4Config(
        network_mode="markdown_steady_state",
        reaction_network_file=network,
        condition_id="steady-condition",
        steady_state_initial_guess_um={compound: 0.5 for compound in COMPOUNDS},
    )
    requirements = {item.name: item for item in m4_markdown_steady_requirements()}
    values = {
        **{f"kcat_r{index}": 10.0 for index in range(1, 11)},
        **{f"km_r{index}": 1.0 for index in range(1, 11)},
        "input_flux_8": 0.5,
        **{f"ksec_{compound}": 0.2 for compound in COMPOUNDS},
    }
    config.parameters = [
        ParameterRecord(
            parameter_id=name,
            name=name,
            value=value,
            unit=requirements[name].canonical_unit,
            parameter_type=requirements[name].parameter_type,
            enzyme_id=requirements[name].enzyme_id,
            substrate_id=requirements[name].substrate_id,
            product_id=requirements[name].product_id,
            species_id=requirements[name].species_id,
            source_type="assumption",
            source_reference="steady pipeline test",
            review_status="approved",
        )
        for name, value in values.items()
    ]
    context = M4CandidateContext(
        candidate_id="candidate",
        construct_id="construct",
        condition_id="steady-condition",
        phi=0.1,
        enzyme_distribution={enzyme: {"dense": 1.0, "dilute": 1.0, "partition_coefficient": 1.0} for enzyme in ENZYME_SUBSTRATES},
        metabolite_partition_coefficients={compound: 1.0 for compound in COMPOUNDS},
    )
    m3 = M3ConcentrationAssessment(
        candidate_id="candidate",
        construct_id="construct",
        status="valid",
        recommended_for_m4=True,
        m4_candidate_context=context,
    )

    records, output = run_m4(config, tmp_path, [m3])

    assert output.stage == "m4_markdown_steady_state"
    assert records[0].status == "valid"
    assert records[0].recommendation is None
    assert records[0].yield_abs is not None
    assert max(abs(value) for value in records[0].steady_state_residuals.values()) < 1e-8


def test_stdio_mcp_server_calls_m4_steady_state() -> None:
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters

    async def exercise() -> None:
        params = StdioServerParameters(command=sys.executable, args=["-m", "igem_drylab.mcp.server"], cwd=ROOT)
        async with Client(params, read_timeout_seconds=20) as client:
            response = await client.call_tool(
                "igem.m4.solve_steady_state",
                {"inputs": _input().model_dump(mode="json")},
            )
            assert response.is_error is not True
            assert response.structured_content["result"]["formula_version"] == "m4-step0-step8-2026-09-27"
            assert response.structured_content["result"]["status"] == "valid"

    asyncio.run(exercise())
