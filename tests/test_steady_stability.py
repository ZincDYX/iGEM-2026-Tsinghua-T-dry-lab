"""Original equation derivatives with independent analytic/finite-difference oracles."""
import asyncio
from pathlib import Path
import sys
import numpy as np
import pytest

from igem_drylab.full_network import COMPOUNDS, REACTIONS, ENZYME_SUBSTRATES
from igem_drylab.m4_steady_state import (M4SteadyStateInput, M4SteadyStateAnalysisInput,
    solve_m4_steady_state, steady_state_jacobian, steady_state_evaluator,
    classify_local_stability, analyze_m4_steady_state)


def software_input(*, active=False, phi=.2):
    return M4SteadyStateInput(candidate_id="software", construct_id="software", condition_id="software",
        phi=phi, enzymes={e:dict(dense_um=2 if active else 0, dilute_um=.5 if active else 0,
            m3_source_id="software") for e in ENZYME_SUBSTRATES},
        metabolite_kp={c:2+i for i,c in enumerate(COMPOUNDS)},
        reactions=[dict(reaction_id=r, enzyme=e, substrate=s, product=p, kcat_per_h=2+i,
            km_um=1+i/4, parameter_ids=[r+"-kcat",r+"-km"]) for i,(r,e,s,p) in enumerate(REACTIONS)],
        input_flux_um_per_h=.5, secretion_rate_per_h={c:.2+i/10 for i,c in enumerate(COMPOUNDS)},
        secretion_normalization="original_unweighted_dilute_concentration",
        initial_guess_um={c:1 if c=="8" else 0 for c in COMPOUNDS}, input_parameter_ids=["software_fixture_only"])


@pytest.mark.parametrize("phi", [0.,.2])
def test_exact_competitive_jacobian_matches_independent_central_differences(phi):
    payload=software_input(active=True,phi=phi)
    x=np.arange(1,9,dtype=float)/3
    evaluate=steady_state_evaluator(payload)
    numerical=np.column_stack([(evaluate(x+np.eye(8)[j]*1e-5)[0]-evaluate(x-np.eye(8)[j]*1e-5)[0])/2e-5 for j in range(8)])
    # uM/h per uM = 1/h; truncation budget for central differences, all pools active.
    np.testing.assert_allclose(steady_state_jacobian(payload,x), numerical,rtol=0,atol=1e-8)


def test_secretion_only_root_eigenvalues_match_original_unweighted_definition():
    payload=software_input()
    result=solve_m4_steady_state(payload)
    assert result.status=="valid"
    factors=np.asarray([1/(.8+.2*payload.metabolite_kp[c]) for c in COMPOUNDS])
    expected=-np.asarray([payload.secretion_rate_per_h[c] for c in COMPOUNDS])*factors
    np.testing.assert_allclose(result.local_stability["jacobian_per_h"],np.diag(expected),rtol=0,atol=1e-14)
    np.testing.assert_allclose(sorted(v["real"] for v in result.local_stability["eigenvalues_per_h"]),sorted(expected),rtol=0,atol=1e-14)
    assert result.local_stability["status"]=="locally_asymptotically_stable"
    assert result.concentrations_cell_average_um["8"]==pytest.approx(.5/(.2*factors[0]),abs=1e-8)


@pytest.mark.parametrize("eigenvalue,status", [(-2,"locally_asymptotically_stable"),(0,"inconclusive_nonhyperbolic_or_numerically_neutral"),(2,"unstable")])
def test_linearization_classifier_does_not_claim_neutral_is_stable(eigenvalue,status):
    report=classify_local_stability(np.diag([eigenvalue,-3]),1e-10)
    assert report["status"]==status  # independent diagonal spectra, 1/h


def search_input(payload,guesses):
    return M4SteadyStateAnalysisInput(steady_state_input=payload, initial_guesses_um=guesses,
        root_merge_atol_um=1e-6,root_merge_rtol=1e-6,eigenvalue_tolerance_per_h=1e-10)


def test_multistart_records_neutral_root_family_and_blocked_attempts():
    payload=software_input()
    payload.secretion_rate_per_h["9"]=0  # unfed, no reaction: actual free pool, not a unique root
    guesses=[{c:float(v) if c in {"8","9"} else 0 for c in COMPOUNDS} for v in (1,3)]
    report=analyze_m4_steady_state(search_input(payload,guesses))
    assert report["distinct_roots_found"]==2
    assert all(r["local_stability"]["status"]=="inconclusive_nonhyperbolic_or_numerically_neutral" for r in report["roots"])
    assert [a["root_index"] for a in report["attempts"]]==[0,1]
    assert [r["concentrations_cell_average_um"]["9"] for r in report["roots"]]==pytest.approx([1,3],abs=1e-12)
    payload.secretion_rate_per_h["15"]=0
    blocked=analyze_m4_steady_state(search_input(payload,guesses))
    assert blocked["distinct_roots_found"]==0
    assert len(blocked["attempts"])==2
    assert all(a["result"]["status"]=="blocked" for a in blocked["attempts"])
    assert "not_global" in blocked["scope"]


def test_official_stdio_mcp_executes_declared_multistart_analysis():
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters
    payload=search_input(software_input(),[{c:v if c=="8" else 0 for c in COMPOUNDS} for v in (1.,3.)])
    async def exercise():
        params=StdioServerParameters(command=sys.executable,args=["-m","igem_drylab.mcp.server"],
            cwd=Path(__file__).resolve().parents[1],env={"PYTHONPATH":str(Path(__file__).resolve().parents[1]/"src")})
        async with Client(params,read_timeout_seconds=30) as client:
            response=await client.call_tool("igem.m4.analyze_steady_state",{"inputs":payload.model_dump(mode="json")})
            assert not response.is_error
            result=response.structured_content["result"]
            assert result["distinct_roots_found"]==1
            assert len(result["attempts"])==2
            assert result["roots"][0]["local_stability"]["status"]=="locally_asymptotically_stable"
    asyncio.run(exercise())
