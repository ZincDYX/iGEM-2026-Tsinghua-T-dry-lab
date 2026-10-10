"""Fixed-geometry amount balances for the independently versioned ER model.

Uses the existing ten-reaction competitive MM kernel, with explicit reaction
locations. Finite exchange and rapid-equilibrium interfaces are mutually
exclusive. Rates in uM/h become umol/h only through sourced volumes in litres.
"""
from typing import Literal
from itertools import combinations
import numpy as np
from pydantic import Field, model_validator

from .compartments import CompartmentContract, ScientificQuantity
from .full_network import COMPOUNDS, REACTIONS, ENZYME_SUBSTRATES, ReactionKinetics, phase_competitive_rates
from .m4_steady_state import M4ReactionInput

ER_M4_VERSION = "m4-compartment-amount-v1-2026-10-10"


class ReactionPool(CompartmentContract):
    pool_id: str
    role: Literal["cytosol", "anchored_droplet", "er_lumen", "extracellular"]
    volume: ScientificQuantity
    geometry_ref: str
    enzyme_amounts: dict[str,ScientificQuantity]
    enzyme_activity_ratios: dict[str,ScientificQuantity]

    @model_validator(mode="after")
    def units(self):
        self.volume.require("L",positive=True)
        if set(self.enzyme_amounts) != set(ENZYME_SUBSTRATES) or set(self.enzyme_activity_ratios) != set(ENZYME_SUBSTRATES):
            raise ValueError("each_reaction_pool_requires_explicit_four_enzyme_amounts_and_activity")
        for quantity in self.enzyme_amounts.values(): quantity.require("umol")
        for quantity in self.enzyme_activity_ratios.values(): quantity.require("1")
        return self


class ExchangeInterface(CompartmentContract):
    interface_id: str
    first_pool: str
    second_pool: str
    mode: Literal["finite_exchange", "rapid_equilibrium"]
    second_over_first_partition: dict[str,ScientificQuantity]
    conductance: dict[str,ScientificQuantity] | None
    applicability_reference: str = Field(min_length=1)
    timescale_evidence_reference: str | None

    @model_validator(mode="after")
    def exchange_model(self):
        if set(self.second_over_first_partition) != set(COMPOUNDS):
            raise ValueError("exchange_requires_matching_partition_for_each_metabolite")
        for quantity in self.second_over_first_partition.values(): quantity.require("1",positive=True)
        if self.mode == "finite_exchange":
            if self.conductance is None or set(self.conductance) != set(COMPOUNDS):
                raise ValueError("finite_exchange_requires_each_conductance_not_ksec")
            for quantity in self.conductance.values(): quantity.require("L/h")
        elif self.conductance is not None or not self.timescale_evidence_reference:
            raise ValueError("rapid_equilibrium_requires_timescale_evidence_and_no_finite_conductance")
        return self


class AmountBoundary(CompartmentContract):
    boundary_id: str
    pool_id: str
    compound: Literal["8","9","10","11","12","13","14","15"]
    kind: Literal["constant_feed", "first_order_loss"]
    quantity: ScientificQuantity
    normalization: Literal["physical_amount"]

    @model_validator(mode="after")
    def units(self):
        self.quantity.require("umol/h" if self.kind == "constant_feed" else "1/h")
        return self


class CompartmentNumerics(CompartmentContract):
    method: Literal["BDF", "Radau", "LSODA"]
    relative_tolerance: float = Field(gt=0,lt=1)
    amount_absolute_tolerance_umol: float = Field(gt=0)
    steady_relative_tolerance: float = Field(gt=0,lt=1)
    steady_absolute_tolerance_umol_per_h: float = Field(gt=0)
    eigenvalue_tolerance_per_h: float = Field(gt=0)
    steady_max_evaluations: int = Field(ge=1)


class CompartmentNetworkInput(CompartmentContract):
    """ER M4 amount-state network; original cytosolic secretion is unchanged."""
    formula_version: Literal["m4-compartment-amount-v1-2026-10-10"] = ER_M4_VERSION
    construct_id: str
    condition_id: str
    scenario: Literal["no_LLPS", "cytosolic_LLPS", "ER_anchored_LLPS"]
    topology_evidence_ref: str | None
    reaction_location_reference: str = Field(min_length=1)
    pools: list[ReactionPool] = Field(min_length=1)
    interfaces: list[ExchangeInterface]
    reactions: list[M4ReactionInput]
    reaction_locations: dict[str,list[str]]
    boundaries: list[AmountBoundary]
    initial_amounts_umol: dict[str,dict[str,ScientificQuantity]]
    time_grid_h: list[float] = Field(min_length=2)
    steady_initial_guesses_umol: list[dict[str,dict[str,float]]]
    numerics: CompartmentNumerics
    evidence_mode: Literal["conditional_model", "reviewed_project_binding"]

    @model_validator(mode="after")
    def complete(self):
        known = {pool.pool_id for pool in self.pools}
        if len(known) != len(self.pools): raise ValueError("duplicate_reaction_pool")
        if tuple((r.reaction_id,r.enzyme,r.substrate,r.product) for r in self.reactions) != REACTIONS:
            raise ValueError("ER_M4_requires_exact_ten_reactions_R10_is_14_to_15")
        if set(self.reaction_locations) != {r[0] for r in REACTIONS}:
            raise ValueError("all_ten_reaction_locations_required")
        for locations in self.reaction_locations.values():
            if not locations or len(set(locations)) != len(locations) or set(locations)-known:
                raise ValueError("invalid_or_missing_reaction_location")
        for enzyme in ENZYME_SUBSTRATES:
            locations = [set(self.reaction_locations[r[0]]) for r in REACTIONS if r[1] == enzyme]
            if any(location != locations[0] for location in locations[1:]):
                raise ValueError("same_enzyme_reactions_require_consistent_accessible_pools")
            if any(pool.enzyme_amounts[enzyme].value > 0 and pool.pool_id not in locations[0] for pool in self.pools):
                raise ValueError("enzyme_amount_exists_outside_its_declared_reaction_location")
        if self.scenario == "ER_anchored_LLPS" and not self.topology_evidence_ref:
            raise ValueError("ER_quantification_requires_topology_evidence_reference")
        pairs = set()
        for interface in self.interfaces:
            pair = frozenset((interface.first_pool,interface.second_pool))
            if len(pair) != 2 or not pair <= known or pair in pairs:
                raise ValueError("duplicate_interface_or_simultaneous_equilibrium_and_exchange")
            pairs.add(pair)
        if any(boundary.pool_id not in known for boundary in self.boundaries):
            raise ValueError("unknown_boundary_pool")
        if len({b.boundary_id for b in self.boundaries}) != len(self.boundaries):
            raise ValueError("duplicate_amount_boundary")
        if set(self.initial_amounts_umol) != known:
            raise ValueError("every_pool_requires_actual_initial_amounts")
        for row in self.initial_amounts_umol.values():
            if set(row) != set(COMPOUNDS): raise ValueError("each_pool_requires_all_eight_initial_amounts")
            for quantity in row.values(): quantity.require("umol")
        for guess in self.steady_initial_guesses_umol:
            if set(guess) != known or any(set(row) != set(COMPOUNDS) or any(not np.isfinite(v) or v < 0 for v in row.values()) for row in guess.values()):
                raise ValueError("steady_initial_guesses_are_explicit_complete_nonnegative_numerical_settings")
        if self.time_grid_h[0] != 0 or any(b <= a for a,b in zip(self.time_grid_h,self.time_grid_h[1:])):
            raise ValueError("explicit_increasing_time_grid_must_start_at_zero")
        return self


def compartment_evaluator(payload: CompartmentNetworkInput):
    """Return amount RHS and exact Jacobian, reducing rapid interfaces first."""
    pools = {pool.pool_id:pool for pool in payload.pools}
    ids = list(pools)
    parent = {pool:pool for pool in ids}
    def root(pool):
        while parent[pool] != pool: pool = parent[pool]
        return pool
    rapid = [interface for interface in payload.interfaces if interface.mode == "rapid_equilibrium"]
    for interface in rapid:
        a,b = root(interface.first_pool),root(interface.second_pool)
        if a == b:
            raise ValueError("rapid_equilibrium_cycles_require_separate_consistency_analysis")
        parent[b] = a
    if any(root(interface.first_pool) == root(interface.second_pool)
           for interface in payload.interfaces if interface.mode == "finite_exchange"):
        raise ValueError("finite_exchange_cannot_join_pools_already_forced_to_rapid_equilibrium")
    groups = []
    for pool in ids:
        matched = next((group for group in groups if root(group[0]) == root(pool)),None)
        if matched is None: groups.append([pool])
        else: matched.append(pool)
    index = {(pool,compound):i*8+j for i,pool in enumerate(ids) for j,compound in enumerate(COMPOUNDS)}
    reduced_index = {(group[0],compound):i*8+j for i,group in enumerate(groups) for j,compound in enumerate(COMPOUNDS)}
    distribute = np.zeros((len(ids)*8,len(groups)*8))
    aggregate = np.zeros((len(groups)*8,len(ids)*8))
    for group in groups:
        for compound in COMPOUNDS:
            ratios = {group[0]:1.}
            while len(ratios) < len(group):
                progress = False
                for interface in rapid:
                    a,b = interface.first_pool,interface.second_pool
                    k = interface.second_over_first_partition[compound].value
                    if a in ratios and b in group and b not in ratios:
                        ratios[b] = ratios[a]*k; progress=True
                    elif b in ratios and a in group and a not in ratios:
                        ratios[a] = ratios[b]/k; progress=True
                if not progress: raise ValueError("disconnected_rapid_equilibrium_group")
            normalizer = sum(pools[pool].volume.value*ratios[pool] for pool in group)
            column = reduced_index[group[0],compound]
            for pool in group:
                row = index[pool,compound]
                distribute[row,column] = pools[pool].volume.value*ratios[pool]/normalizer
                aggregate[column,row] = 1.
    kinetics = tuple(ReactionKinetics(r.reaction_id,r.enzyme,r.substrate,r.product,r.kcat_per_h,r.km_um) for r in payload.reactions)
    def evaluate(state):
        amounts = distribute @ state
        derivative = np.zeros(len(ids)*8)
        jacobian = np.zeros((len(ids)*8,len(ids)*8))
        reaction_fluxes,exchange_fluxes = {},{}
        for pool_id,pool in pools.items():
            volume = pool.volume.value
            substrate = {c:float(amounts[index[pool_id,c]]/volume) for c in COMPOUNDS}
            enzymes = {e:q.value/volume for e,q in pool.enzyme_amounts.items()}
            activities = {e:q.value for e,q in pool.enzyme_activity_ratios.items()}
            rates = phase_competitive_rates(substrate,enzymes,kinetics,activities,1.)
            reaction_fluxes[pool_id] = {}
            for reaction in payload.reactions:
                if pool_id not in payload.reaction_locations[reaction.reaction_id]: continue
                flux = volume*rates[reaction.reaction_id]
                reaction_fluxes[pool_id][reaction.reaction_id] = flux
                s,p = index[pool_id,reaction.substrate],index[pool_id,reaction.product]
                derivative[s] -= flux; derivative[p] += flux
                entries = [r for r in payload.reactions if r.enzyme == reaction.enzyme]
                denominator = 1+sum(substrate[r.substrate]/r.km_um for r in entries)
                numerator = substrate[reaction.substrate]/reaction.km_um
                prefactor = enzymes[reaction.enzyme]*activities[reaction.enzyme]*reaction.kcat_per_h
                for competitor in entries:
                    j = index[pool_id,competitor.substrate]
                    value = prefactor*((denominator/reaction.km_um if j == s else 0.)-numerator/competitor.km_um)/denominator**2
                    jacobian[s,j] -= value; jacobian[p,j] += value
        for interface in payload.interfaces:
            if interface.mode != "finite_exchange": continue
            exchange_fluxes[interface.interface_id] = {}
            for compound in COMPOUNDS:
                a,b = index[interface.first_pool,compound],index[interface.second_pool,compound]
                va,vb = pools[interface.first_pool].volume.value,pools[interface.second_pool].volume.value
                g,k = interface.conductance[compound].value,interface.second_over_first_partition[compound].value
                flux = g*(amounts[a]/va-amounts[b]/vb/k)
                exchange_fluxes[interface.interface_id][compound] = float(flux)
                derivative[a] -= flux; derivative[b] += flux
                jacobian[a,a] -= g/va; jacobian[b,a] += g/va
                jacobian[a,b] += g/(vb*k); jacobian[b,b] -= g/(vb*k)
        feed,loss = 0.,0.
        for boundary in payload.boundaries:
            i = index[boundary.pool_id,boundary.compound]
            if boundary.kind == "constant_feed":
                derivative[i] += boundary.quantity.value; feed += boundary.quantity.value
            else:
                flux = boundary.quantity.value*amounts[i]
                derivative[i] -= flux; loss += flux
                jacobian[i,i] -= boundary.quantity.value
        return aggregate@derivative,aggregate@jacobian@distribute,amounts,reaction_fluxes,exchange_fluxes,feed,loss
    return evaluate,distribute,aggregate,index,groups


def solve_compartment_network(payload: CompartmentNetworkInput) -> dict:
    from scipy.integrate import solve_ivp
    from scipy.optimize import least_squares
    from .m4_steady_state import classify_local_stability
    evaluate,distribute,aggregate,index,groups = compartment_evaluator(payload)
    initial = np.array([payload.initial_amounts_umol[pool.pool_id][compound].value for pool in payload.pools for compound in COMPOUNDS])
    reduced = aggregate@initial
    mismatch = float(np.max(np.abs(distribute@reduced-initial)))
    if mismatch > payload.numerics.amount_absolute_tolerance_umol:
        return {"status":"blocked","missing":["initial_amounts_inconsistent_with_declared_rapid_equilibrium"],"initial_equilibrium_amount_residual_umol":mismatch}
    size = len(reduced)
    def rhs(time,state):
        derivative,_,_,_,_,feed,loss = evaluate(state[:size])
        return np.concatenate((derivative,[feed,loss]))
    def jac(time,state):
        matrix = np.zeros((size+2,size+2))
        matrix[:size,:size] = evaluate(state[:size])[1]
        for boundary in payload.boundaries:
            if boundary.kind == "first_order_loss":
                matrix[size+1,:size] += boundary.quantity.value*distribute[index[boundary.pool_id,boundary.compound],:]
        return matrix
    n = payload.numerics
    solved = solve_ivp(rhs,(0.,payload.time_grid_h[-1]),np.concatenate((reduced,[0.,0.])),
        t_eval=payload.time_grid_h,method=n.method,rtol=n.relative_tolerance,atol=n.amount_absolute_tolerance_umol,jac=jac)
    result = {"schema_version":"m4-compartment-amount-v1","formula_version":payload.formula_version,
        "construct_id":payload.construct_id,"condition_id":payload.condition_id,"scenario":payload.scenario,
        "evidence_mode":payload.evidence_mode,"status":"solver_failed","numerical_settings":n.model_dump(),
        "claim_scope":"conditional_compartment_prediction_not_global_stability_or_wetlab_validation"}
    if not solved.success or solved.y.shape[1] != len(payload.time_grid_h):
        result["missing"] = ["amount_ODE_integration_not_complete"]; return result
    amounts = distribute@solved.y[:size]
    if float(amounts.min()) < -n.amount_absolute_tolerance_umol:
        result["missing"] = ["negative_amount_exceeds_declared_numerical_tolerance"]; return result
    conservation = amounts.sum(axis=0)-initial.sum()-solved.y[size]+solved.y[size+1]
    pools = {pool.pool_id:{"amounts_umol":{c:amounts[index[pool.pool_id,c]].tolist() for c in COMPOUNDS},
        "concentrations_um":{c:(amounts[index[pool.pool_id,c]]/pool.volume.value).tolist() for c in COMPOUNDS}} for pool in payload.pools}
    flux_rows = [evaluate(solved.y[:size,i]) for i in range(len(payload.time_grid_h))]
    steady = []
    for guess in payload.steady_initial_guesses_umol:
        full = np.array([guess[pool.pool_id][c] for pool in payload.pools for c in COMPOUNDS])
        start = aggregate@full
        scale = max(sum(b.quantity.value for b in payload.boundaries if b.kind == "constant_feed"),n.steady_absolute_tolerance_umol_per_h)
        root = least_squares(lambda x:evaluate(x)[0]/scale,start,bounds=(0,np.inf),jac=lambda x:evaluate(x)[1]/scale,
            max_nfev=n.steady_max_evaluations,xtol=1e-12,ftol=1e-12,gtol=1e-12)
        residual,jacobian,_,fluxes,exchanges,feed,loss = evaluate(root.x)
        valid = root.success and float(np.max(np.abs(residual))) <= n.steady_absolute_tolerance_umol_per_h+n.steady_relative_tolerance*scale
        stability = classify_local_stability(jacobian,n.eigenvalue_tolerance_per_h) if valid else None
        if stability: stability["analysis_version"] = "ER_amount_exact_competitive_exchange_jacobian_v1"
        steady.append({"status":"steady_state_found" if valid else "no_accepted_root_from_this_guess",
            "amounts_umol":{pool.pool_id:{c:float((distribute@root.x)[index[pool.pool_id,c]]) for c in COMPOUNDS} for pool in payload.pools},
            "residual_umol_per_h":residual.tolist(),"local_stability":stability,"scope":"multistart_search_not_global_uniqueness_or_nonexistence_proof"})
        production = sum(pool.get("R7",0.)+pool.get("R10",0.) for pool in fluxes.values())
        product_losses = sum(b.quantity.value*(distribute@root.x)[index[b.pool_id,b.compound]]
            for b in payload.boundaries if b.kind == "first_order_loss" and b.compound == "15")
        pure_m8_feed = all(b.compound == "8" for b in payload.boundaries if b.kind == "constant_feed")
        steady[-1].update(reaction_fluxes_umol_per_h=fluxes,exchange_fluxes_umol_per_h=exchanges,
            product_formation_umol_per_h=production,
            yield_abs=production/feed if valid and feed > 0 and pure_m8_feed else None,
            loss_fraction_8_to_14=(loss-product_losses)/feed if valid and feed > 0 and pure_m8_feed else None,
            yield_plus_loss_residual=(production+loss-product_losses)/feed-1 if valid and feed > 0 and pure_m8_feed else None)
    result.update(status="numerically_solved",time_h=solved.t.tolist(),pools=pools,
        cumulative_feed_umol=solved.y[size].tolist(),cumulative_loss_umol=solved.y[size+1].tolist(),
        total_mass_conservation_residual_umol=conservation.tolist(),
        max_mass_conservation_residual_umol=float(np.max(np.abs(conservation))),
        reaction_fluxes_umol_per_h=[row[3] for row in flux_rows],exchange_fluxes_umol_per_h=[row[4] for row in flux_rows],
        steady_state_candidates=steady,steady_state_existence="at_least_one_accepted_root" if any(r["status"] == "steady_state_found" for r in steady) else "not_established")
    return result


class CompartmentComparisonInput(CompartmentContract):
    cases: dict[str,CompartmentNetworkInput]
    matched_enzyme_relative_tolerance: float = Field(gt=0,lt=1)

    @model_validator(mode="after")
    def matched_controls(self):
        if set(self.cases) != {"no_LLPS","cytosolic_LLPS","ER_anchored_LLPS"}:
            raise ValueError("physical_comparison_requires_three_declared_controls")
        first = next(iter(self.cases.values()))
        totals = lambda case:{e:sum(p.enzyme_amounts[e].value for p in case.pools) for e in ENZYME_SUBSTRATES}
        baseline = totals(first)
        for name,case in self.cases.items():
            if case.scenario != name or case.condition_id != first.condition_id or case.reactions != first.reactions:
                raise ValueError("physical_controls_require_same_condition_and_reaction_parameters")
            if case.time_grid_h != first.time_grid_h:
                raise ValueError("physical_controls_require_same_time_grid")
            for enzyme,total in totals(case).items():
                if not np.isclose(total,baseline[enzyme],rtol=self.matched_enzyme_relative_tolerance,atol=0):
                    raise ValueError("physical_controls_require_equal_total_expression_for_all_four_enzymes")
            feeds = sorted((b.compound,b.quantity.value) for b in case.boundaries if b.kind == "constant_feed")
            reference = sorted((b.compound,b.quantity.value) for b in first.boundaries if b.kind == "constant_feed")
            if feeds != reference:
                raise ValueError("physical_controls_require_same_metabolite_feed_amounts")
        return self


def compare_compartment_controls(payload: CompartmentComparisonInput) -> dict:
    return {"formula_version":ER_M4_VERSION,"control_basis":"matched_four_enzyme_total_amounts_not_original_PTR_PT_dilute_background",
        "cases":{name:solve_compartment_network(case) for name,case in payload.cases.items()},
        "claim_scope":"physical_model_comparison_not_measured_channeling_gain"}
