"""ER amount-conserving recruitment with a versioned hard-conflict partition.

New review-proposed method, not the original S1–E10 formula or project proof.
No avidity energy is added. Geometric capacities never replace equilibrium.
"""
from math import log, exp
from functools import lru_cache
from typing import Literal
import numpy as np
from pydantic import Field, model_validator

from .compartments import CompartmentContract, ScientificQuantity

AVOGADRO_PER_MOL = 6.02214076e23
ER_M3_VERSION = "m3-er-amount-independent-set-v1-2026-10-10"


class BindingSite(CompartmentContract):
    site_id: str
    species: Literal["OC", "DMT"]
    kd: ScientificQuantity
    geometry_ref: str = Field(min_length=1)
    binding_pair_ref: str = Field(min_length=1)

    @model_validator(mode="after")
    def units(self):
        self.kd.require("uM", positive=True)
        return self


class BindingGraph(CompartmentContract):
    sites: list[BindingSite]
    conflict_edges: list[tuple[str,str]]
    entity_basis: Literal["complete_assembly"]
    geometry_ref: str = Field(min_length=1)
    method_assumption: Literal["hard_exclusion_no_additional_cooperativity"]
    applicability_reference: str = Field(min_length=1)

    @model_validator(mode="after")
    def graph(self):
        ids = [site.site_id for site in self.sites]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate_binding_site")
        edges = set()
        for first,second in self.conflict_edges:
            edge = tuple(sorted((first,second)))
            if first == second or first not in ids or second not in ids or edge in edges:
                raise ValueError("invalid_or_duplicate_binding_conflict")
            edges.add(edge)
        return self


class PartitionBudgetExceeded(ValueError):
    pass


def binding_partition(graph: BindingGraph, free_dense_um: dict[str,float], max_states: int) -> dict:
    """Exact log-partition and first moments; factor disconnected components.

    Recursion is memoized and has an explicit numerical state budget. Budget
    exhaustion blocks the result, never changes to an unreviewed approximation.
    """
    if set(free_dense_um) != {"OC","DMT"} or any(not np.isfinite(c) or c < 0 for c in free_dense_um.values()):
        raise ValueError("binding_partition_requires_nonnegative_free_OC_DMT")
    ids = {site.site_id:i for i,site in enumerate(graph.sites)}
    neighbours = [0]*len(ids)
    for first,second in graph.conflict_edges:
        i,j = ids[first],ids[second]
        neighbours[i] |= 1 << j
        neighbours[j] |= 1 << i
    weights = [log(free_dense_um[site.species])-log(site.kd.value)
               if free_dense_um[site.species] else -np.inf for site in graph.sites]
    visited = 0

    def components(mask):
        groups = []
        while mask:
            frontier = mask & -mask
            group = 0
            while frontier:
                bit = frontier & -frontier
                frontier ^= bit
                i = bit.bit_length()-1
                group |= bit
                frontier |= neighbours[i] & mask & ~group
            groups.append(group)
            mask &= ~group
        return groups

    @lru_cache(None)
    def partition(mask):
        nonlocal visited
        visited += 1
        if visited > max_states:
            raise PartitionBudgetExceeded("exact_binding_partition_state_budget_exhausted")
        if not mask:
            return 0.,np.zeros(2)
        groups = components(mask)
        if len(groups) > 1:
            terms = [partition(group) for group in groups]
            return sum(term[0] for term in terms),sum((term[1] for term in terms),start=np.zeros(2))
        i = max((i for i in range(len(ids)) if mask & (1 << i)), key=lambda i:(neighbours[i]&mask).bit_count())
        remaining = mask & ~(1 << i)
        log0,mean0 = partition(remaining)
        log1,mean1 = partition(remaining & ~neighbours[i])
        log1 += weights[i]
        total = float(np.logaddexp(log0,log1))
        p1 = exp(log1-total) if np.isfinite(log1) else 0.
        selected = np.array([1.,0.]) if graph.sites[i].species == "OC" else np.array([0.,1.])
        return total,(1-p1)*mean0+p1*(mean1+selected)

    full = (1 << len(ids))-1
    log_z,mean = partition(full)
    return {"log_partition":log_z,"expected_bound_per_assembly":{"OC":float(mean[0]),"DMT":float(mean[1])},
        "exact":True,"evaluated_states":visited,"connected_components":len(components(full)),"max_states":max_states}


class ERRecruitmentInput(CompartmentContract):
    """Proposed ER M3 method with explicit physical amounts and geometry."""
    formula_version: Literal["m3-er-amount-independent-set-v1-2026-10-10"] = ER_M3_VERSION
    construct_id: str
    condition_id: str
    topology_evidence_ref: str
    body_side: Literal["cytosolic", "luminal", "unknown"]
    geometry_ref: str
    cytosol_volume: ScientificQuantity
    droplet_volume: ScientificQuantity
    er_area: ScientificQuantity
    scaffold_surface_density: ScientificQuantity
    density_entity_basis: Literal["scaffold_monomer", "complete_assembly", "effective_anchor"]
    subunits_per_assembly: int = Field(ge=1)
    anchors_per_assembly: int = Field(ge=1)
    composition_source: str = Field(min_length=1)
    total_scaffold_monomer_amount: ScientificQuantity
    unanchored_scaffold_binding: Literal["included_in_droplet", "excluded_with_evidence"]
    unanchored_scaffold_applicability_source: str = Field(min_length=1)
    enzyme_total_amounts: dict[str,ScientificQuantity]
    free_enzyme_partition: dict[str,ScientificQuantity]
    binding_graph: BindingGraph
    max_partition_states: int = Field(ge=1)
    solver_max_evaluations: int = Field(ge=1)
    relative_mass_tolerance: float = Field(gt=0,lt=1)

    @model_validator(mode="after")
    def physical_contract(self):
        self.cytosol_volume.require("L",positive=True)
        self.droplet_volume.require("L",positive=True)
        self.er_area.require("um2",positive=True)
        self.scaffold_surface_density.require("copies/um2")
        self.total_scaffold_monomer_amount.require("umol")
        if self.anchors_per_assembly > self.subunits_per_assembly:
            raise ValueError("anchors_per_assembly_exceeds_actual_subunits")
        if set(self.enzyme_total_amounts) != {"OC","DMT"} or set(self.free_enzyme_partition) != {"OC","DMT"}:
            raise ValueError("ER_recruitment_requires_both_enzyme_amounts_and_free_partition")
        for quantity in self.enzyme_total_amounts.values(): quantity.require("umol")
        for quantity in self.free_enzyme_partition.values(): quantity.require("1",positive=True)
        if self.binding_graph.geometry_ref != self.geometry_ref:
            raise ValueError("ER_binding_graph_geometry_identity_mismatch")
        return self


def solve_er_recruitment(payload: ERRecruitmentInput) -> dict:
    from scipy.optimize import least_squares
    result = {"schema_version":"m3-er-amount-v1","formula_version":payload.formula_version,
        "construct_id":payload.construct_id,"condition_id":payload.condition_id,
        "compartment_scenario":"er_anchored","topology_evidence_ref":payload.topology_evidence_ref,
        "geometry_ref":payload.geometry_ref,"status":"blocked","missing":[],
        "claim_scope":"conditional_proposed_ER_model_not_project_experimental_validation"}
    if payload.body_side != "cytosolic":
        result["missing"] = ["confirmed_cytosolic_scaffold_body_required_for_this_ER_model"]
        return result
    surface_amount = payload.er_area.value*payload.scaffold_surface_density.value/AVOGADRO_PER_MOL*1e6
    assembly_amount = (surface_amount if payload.density_entity_basis == "complete_assembly" else
        surface_amount/payload.subunits_per_assembly if payload.density_entity_basis == "scaffold_monomer" else
        surface_amount/payload.anchors_per_assembly)
    anchored_monomers = assembly_amount*payload.subunits_per_assembly
    scaffold_total = payload.total_scaffold_monomer_amount.value
    if anchored_monomers > scaffold_total:
        result["missing"] = ["anchored_scaffold_amount_exceeds_total_scaffold_amount"]
        return result
    binding_assembly_amount = assembly_amount + ((scaffold_total-anchored_monomers)/payload.subunits_per_assembly
        if payload.unanchored_scaffold_binding == "included_in_droplet" else 0.)
    vc,vd = payload.cytosol_volume.value,payload.droplet_volume.value
    species = ("OC","DMT")
    totals = np.array([payload.enzyme_total_amounts[e].value for e in species])
    partitions = np.array([payload.free_enzyme_partition[e].value for e in species])
    coefficients = vc/partitions+vd
    upper = totals/coefficients
    scale = np.where(totals > 0,totals,1.)
    active = totals > 0
    def evaluate(fractions):
        free = np.zeros(2)
        free[active] = upper[active]*fractions
        occupancy = binding_partition(payload.binding_graph,dict(zip(species,free)),payload.max_partition_states)
        bound = binding_assembly_amount*np.array([occupancy["expected_bound_per_assembly"][e] for e in species])
        return (coefficients*free+bound-totals)/scale,free,bound,occupancy
    try:
        if active.any():
            solved = least_squares(lambda x:evaluate(x)[0][active], np.ones(int(active.sum())),
                bounds=(0.,1.),xtol=1e-12,ftol=1e-12,gtol=1e-12,max_nfev=payload.solver_max_evaluations)
            residual,free,bound,partition = evaluate(solved.x)
            converged = solved.success and float(np.max(np.abs(residual))) <= payload.relative_mass_tolerance
            evaluations = solved.nfev
        else:
            residual,free,bound,partition = evaluate(np.array([]))
            converged,evaluations = True,0
    except PartitionBudgetExceeded as error:
        result["missing"] = [str(error)]
        return result
    enzymes = {e:{"free_cytosol_um":float(free[i]/partitions[i]),"free_droplet_um":float(free[i]),
        "free_cytosol_amount_umol":float(vc*free[i]/partitions[i]),"free_droplet_amount_umol":float(vd*free[i]),
        "bound_droplet_amount_umol":float(bound[i]),"total_amount_umol":float(totals[i]),
        "mass_balance_residual_umol":float(residual[i]*scale[i])} for i,e in enumerate(species)}
    result.update(status="numerically_solved" if converged else "solver_failed",enzymes=enzymes,
        cytosol_volume_l=vc,droplet_volume_l=vd,
        anchored_scaffold_monomer_amount_umol=anchored_monomers,anchored_assembly_amount_umol=assembly_amount,
        unanchored_scaffold_monomer_amount_umol=scaffold_total-anchored_monomers,
        binding_assembly_amount_umol=binding_assembly_amount,
        anchor_fraction=anchored_monomers/scaffold_total if scaffold_total else None,
        partition=partition,solver_evaluations=evaluations,
        relative_mass_residuals=dict(zip(species,map(float,residual))))
    return result
