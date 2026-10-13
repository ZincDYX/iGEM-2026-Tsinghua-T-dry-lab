"""Independent synthetic mathematical oracles; execute on server only.

Fixture quantities and source strings are deliberately not project parameters.
They check the review's new equations, not biological applicability.
"""
import asyncio
from copy import deepcopy
from math import exp,log,sqrt
import sys
from pathlib import Path

import numpy as np
import pytest
from mcp import Client
from mcp.client.stdio import StdioServerParameters

from igem_drylab.m3_er import BindingGraph, binding_partition, ERRecruitmentInput, solve_er_recruitment, PartitionBudgetExceeded
from igem_drylab.m4_compartments import CompartmentNetworkInput, compartment_evaluator, solve_compartment_network
from igem_drylab.full_network import REACTIONS


def quantity(value,unit="1",identifier="fixture"):
    return dict(value=value,unit=unit,entity_basis="synthetic_oracle_not_project",parameter_id=identifier,
        source_reference="SYNTHETIC MATHEMATICAL FIXTURE; NOT WETLAB OR PROJECT INPUT")


def graph(edges=(),count=2):
    return BindingGraph.model_validate(dict(sites=[dict(site_id=str(i),species="OC" if i%2 == 0 else "DMT",
        kd=quantity(2 if i%2 == 0 else 3,"uM"),geometry_ref="synthetic-geometry",binding_pair_ref="synthetic-binding") for i in range(count)],
        conflict_edges=list(edges),entity_basis="complete_assembly",geometry_ref="synthetic-geometry",
        method_assumption="hard_exclusion_no_additional_cooperativity",applicability_reference="synthetic-method-oracle"))


def test_exact_no_edge_partition_and_mutual_exclusion_against_closed_form():
    free = {"OC":4.,"DMT":9.}
    independent = binding_partition(graph(),free,100)
    assert independent["log_partition"] == pytest.approx(log(3*4))
    assert independent["expected_bound_per_assembly"] == pytest.approx({"OC":2/3,"DMT":3/4})
    excluded = binding_partition(graph([("0","1")]),free,100)
    # Allowed states {}, {OC}, {DMT}: Z = 1+2+3, not (1+2)(1+3).
    assert excluded["log_partition"] == pytest.approx(log(6))
    assert excluded["expected_bound_per_assembly"] == pytest.approx({"OC":2/6,"DMT":3/6})
    assert sum(excluded["expected_bound_per_assembly"].values()) < 1


def test_96_sites_are_factorized_and_budget_exhaustion_is_not_an_approximation():
    result = binding_partition(graph(count=96),{"OC":4.,"DMT":9.},1000)
    assert result["expected_bound_per_assembly"] == pytest.approx({"OC":48*2/3,"DMT":48*3/4})
    assert result["connected_components"] == 96 and result["evaluated_states"] < 200
    with pytest.raises(PartitionBudgetExceeded):
        binding_partition(graph(),{"OC":4.,"DMT":9.},1)


def recruitment():
    return ERRecruitmentInput.model_validate(dict(construct_id="synthetic",condition_id="synthetic",topology_evidence_ref="fixture-only",
        body_side="cytosolic",geometry_ref="synthetic-geometry",cytosol_volume=quantity(2,"L"),droplet_volume=quantity(1,"L"),
        er_area=quantity(1,"um2"),scaffold_surface_density=quantity(6.02214076e17,"copies/um2"),density_entity_basis="complete_assembly",
        subunits_per_assembly=1,anchors_per_assembly=1,composition_source="synthetic",total_scaffold_monomer_amount=quantity(1,"umol"),
        unanchored_scaffold_binding="excluded_with_evidence",unanchored_scaffold_applicability_source="synthetic-no-unanchored",
        enzyme_total_amounts={"OC":quantity(10,"umol"),"DMT":quantity(7,"umol")},free_enzyme_partition={"OC":quantity(2),"DMT":quantity(3)},
        binding_graph=graph().model_dump(),max_partition_states=1000,solver_max_evaluations=200,relative_mass_tolerance=1e-9))


def test_er_recruitment_independent_quadratic_mass_oracle_and_surface_units():
    result = solve_er_recruitment(recruitment())
    assert result["status"] == "numerically_solved"
    assert result["anchored_assembly_amount_umol"] == pytest.approx(1)
    for enzyme,kd,k,total in (("OC",2,2,10),("DMT",3,3,7)):
        a = 2/k+1
        # total = a*x + x/(Kd+x); independent positive root.
        b = a*kd+1-total
        x = (-b+sqrt(b*b+4*a*total*kd))/(2*a)
        observed = result["enzymes"][enzyme]
        assert observed["free_droplet_um"] == pytest.approx(x,rel=1e-9)
        assert observed["free_cytosol_amount_umol"]+observed["free_droplet_amount_umol"]+observed["bound_droplet_amount_umol"] == pytest.approx(total,rel=1e-9)
    raw = recruitment().model_dump()
    raw.update(density_entity_basis="effective_anchor",subunits_per_assembly=24,anchors_per_assembly=24,
        total_scaffold_monomer_amount=quantity(1,"umol"))
    result = solve_er_recruitment(ERRecruitmentInput.model_validate(raw))
    assert result["anchored_assembly_amount_umol"] == pytest.approx(1/24)
    assert result["anchored_scaffold_monomer_amount_umol"] == pytest.approx(1)
    raw["body_side"]="unknown"
    assert solve_er_recruitment(ERRecruitmentInput.model_validate(raw))["status"] == "blocked"


def network(mode="finite_exchange"):
    def pool(name,volume):
        return dict(pool_id=name,role="cytosol" if name=="a" else "anchored_droplet",volume=quantity(volume,"L"),geometry_ref="synthetic",
            enzyme_amounts={e:quantity(0,"umol") for e in ("PTR","PT","OC","DMT")},
            enzyme_activity_ratios={e:quantity(1) for e in ("PTR","PT","OC","DMT")})
    compounds = [str(i) for i in range(8,16)]
    return CompartmentNetworkInput.model_validate(dict(construct_id="synthetic",condition_id="synthetic",scenario="cytosolic_LLPS",
        topology_evidence_ref=None,reaction_location_reference="synthetic",pools=[pool("a",2),pool("b",1)],
        interfaces=[dict(interface_id="a-b",first_pool="a",second_pool="b",mode=mode,
            second_over_first_partition={c:quantity(4) for c in compounds},
            conductance={c:quantity(3,"L/h") for c in compounds} if mode=="finite_exchange" else None,
            applicability_reference="synthetic-linear-exchange",timescale_evidence_reference="synthetic-timescale" if mode=="rapid_equilibrium" else None)],
        reactions=[dict(reaction_id=r,enzyme=e,substrate=s,product=p,kcat_per_h=1,km_um=3,parameter_ids=["synthetic-kcat","synthetic-km"]) for r,e,s,p in REACTIONS],
        reaction_locations={r:["a","b"] for r,*_ in REACTIONS},boundaries=[],
        initial_amounts_umol={p:{c:quantity((3 if p=="a" else 0) if mode=="finite_exchange" else (1 if p=="a" else 2),"umol") if c=="8" else quantity(0,"umol") for c in compounds} for p in ("a","b")},
        time_grid_h=[0,0.2,1,3],steady_initial_guesses_umol=[],evidence_mode="conditional_model",
        numerics=dict(method="Radau",relative_tolerance=1e-10,amount_absolute_tolerance_umol=1e-12,
            steady_relative_tolerance=1e-9,steady_absolute_tolerance_umol_per_h=1e-10,eigenvalue_tolerance_per_h=1e-8,steady_max_evaluations=500)))


def test_finite_exchange_matches_independent_exponential_and_conserves_amount():
    result = solve_compartment_network(network())
    assert result["status"] == "numerically_solved"
    expected = [1+2*exp(-2.25*t) for t in (0,.2,1,3)]
    assert result["pools"]["a"]["amounts_umol"]["8"] == pytest.approx(expected,rel=1e-9)
    assert result["pools"]["b"]["amounts_umol"]["8"] == pytest.approx([3-v for v in expected],abs=1e-9)
    assert result["max_mass_conservation_residual_umol"] < 1e-10
    evaluate,_,_,_,_ = compartment_evaluator(network())
    matrix = evaluate(np.zeros(16))[1]
    assert matrix[np.ix_([0,8],[0,8])] == pytest.approx(np.array([[-1.5,.75],[1.5,-.75]]))


def test_rapid_equilibrium_preserves_amount_and_does_not_apply_independent_exchange():
    from igem_drylab.m4_compartments import conserved_amount_basis
    payload = network("rapid_equilibrium")
    _, _, aggregate, index, _ = compartment_evaluator(payload)
    # With no active reactions, exchanges or boundaries, every reduced amount
    # is conserved independently. This also admits SciPy's declared 1.12 floor.
    assert np.array_equal(conserved_amount_basis(payload, aggregate, index), np.eye(8))
    result = solve_compartment_network(network("rapid_equilibrium"))
    assert result["status"] == "numerically_solved"
    assert result["pools"]["a"]["amounts_umol"]["8"] == pytest.approx([1]*4)
    assert result["pools"]["b"]["amounts_umol"]["8"] == pytest.approx([2]*4)
    raw = network("rapid_equilibrium").model_dump()
    raw["interfaces"].append(network().model_dump()["interfaces"][0])
    with pytest.raises(ValueError,match="simultaneous_equilibrium_and_exchange"):
        CompartmentNetworkInput.model_validate(raw)


def test_competitive_reaction_amount_and_exact_jacobian_have_independent_values():
    raw = network().model_dump()
    raw["interfaces"]=[]
    raw["pools"][0]["enzyme_amounts"]["PTR"] = quantity(1,"umol")
    raw["initial_amounts_umol"]["a"]["8"] = quantity(6,"umol")
    for reaction in raw["reactions"]: reaction["kcat_per_h"] = 2 if reaction["reaction_id"]=="R1" else 0
    payload = CompartmentNetworkInput.model_validate(raw)
    evaluate,_,_,_,_ = compartment_evaluator(payload)
    state = np.zeros(16); state[0]=6
    rhs,jac,*_ = evaluate(state)
    assert rhs[0] == pytest.approx(-1) and rhs[1] == pytest.approx(1)
    assert rhs.sum() == pytest.approx(0)
    # flux = 2*n/(6+n), derivative at n=6 is 12/144.
    assert jac[0,0] == pytest.approx(-1/12) and jac[1,0] == pytest.approx(1/12)


def test_new_er_methods_are_callable_over_real_stdio_not_an_inprocess_alias():
    async def call():
        async with Client(StdioServerParameters(command=sys.executable,args=["-B","-m","igem_drylab.mcp.server"],
            env={"PYTHONPATH":str(Path(__file__).parents[1]/"src")}),read_timeout_seconds=60) as client:
            listing = await client.list_tools()
            assert {"igem.m3.er_recruitment","igem.m4.compartment_amounts","igem.m2.membrane_geometry"} <= {tool.name for tool in listing.tools}
            response = await client.call_tool("igem.m3.er_recruitment",{"payload":recruitment().model_dump(mode="json")})
            assert not response.is_error
            assert response.structured_content["result"]["anchored_assembly_amount_umol"] == pytest.approx(1)
    asyncio.run(call())
