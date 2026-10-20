"""Exact M2 site co-occupancy analysis without inventing binding efficiency."""

from __future__ import annotations

from typing import Literal, TYPE_CHECKING

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

if TYPE_CHECKING:
    from scipy.optimize import Bounds, LinearConstraint


class GeometrySite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    site_id: str
    species: Literal["OC", "DMT"]
    geometrically_accessible: bool = True


class M2SiteGeometryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scaffold_id: str
    assembly_applicability_confirmed: bool = False
    assembly_subunit_count: int | None = Field(default=None, ge=1)
    sh3_sites_per_subunit: int | None = Field(default=None, ge=0)
    pdz_sites_per_subunit: int | None = Field(default=None, ge=0)
    sites: list[GeometrySite] = Field(min_length=1)
    conflict_edges: list[tuple[str, str]] = Field(default_factory=list)
    model_ids: list[str] = Field(min_length=1)
    clash_rule_provenance: str

    @model_validator(mode="after")
    def _validate_graph_and_topology(self) -> "M2SiteGeometryInput":
        ids = [site.site_id for site in self.sites]
        if len(set(ids)) != len(ids):
            raise ValueError("site_id values must be unique")
        known = set(ids)
        canonical_edges: set[tuple[str, str]] = set()
        for first, second in self.conflict_edges:
            if first == second:
                raise ValueError("conflict graph cannot contain self edges")
            if first not in known or second not in known:
                raise ValueError("conflict edge references an unknown site")
            edge = tuple(sorted((first, second)))
            if edge in canonical_edges:
                raise ValueError("conflict graph contains duplicate edges")
            canonical_edges.add(edge)
        topology_fields = (
            self.assembly_subunit_count,
            self.sh3_sites_per_subunit,
            self.pdz_sites_per_subunit,
        )
        if self.assembly_applicability_confirmed and any(value is None for value in topology_fields):
            raise ValueError("confirmed assembly requires subunit and per-subunit site counts")
        if self.scaffold_id.upper() == "FTH1" and self.assembly_applicability_confirmed:
            if self.assembly_subunit_count != 24:
                raise ValueError("confirmed FTH1 topology must declare 24 subunits")
        if self.assembly_applicability_confirmed:
            assert self.assembly_subunit_count is not None
            assert self.sh3_sites_per_subunit is not None
            assert self.pdz_sites_per_subunit is not None
            expected_oc = self.assembly_subunit_count * self.sh3_sites_per_subunit
            expected_dmt = self.assembly_subunit_count * self.pdz_sites_per_subunit
            if sum(site.species == "OC" for site in self.sites) != expected_oc:
                raise ValueError("concrete OC site list does not match confirmed SH3 topology")
            if sum(site.species == "DMT" for site in self.sites) != expected_dmt:
                raise ValueError("concrete DMT site list does not match confirmed PDZ topology")
        return self


class CooccupancyCombination(BaseModel):
    oc_count: int = Field(ge=0)
    dmt_count: int = Field(ge=0)
    occupied_site_ids: list[str]


class M2SiteGeometryResult(BaseModel):
    scaffold_id: str
    status: Literal["valid", "insufficient_data"]
    m3_ready: bool
    nominal_sh3_sites: int | None = Field(default=None, ge=0)
    nominal_pdz_sites: int | None = Field(default=None, ge=0)
    accessible_oc_sites: list[str]
    accessible_dmt_sites: list[str]
    maximum_total_cooccupancy: int = Field(ge=0)
    oc_occupancy_range: tuple[int, int]
    dmt_occupancy_range: tuple[int, int]
    pareto_cooccupancy_combinations: list[CooccupancyCombination]
    model_ids: list[str]
    clash_rule_provenance: str
    eta_binding_geometry: None = None
    binding_site_efficiency: None = None
    warnings: list[str] = Field(default_factory=list)


def analyse_site_cooccupancy(payload: M2SiteGeometryInput) -> M2SiteGeometryResult:
    """Solve the exact binary conflict graph and return species-specific ranges."""
    from scipy.optimize import Bounds, LinearConstraint
    from scipy.sparse import csr_matrix

    sites = payload.sites
    ids = [site.site_id for site in sites]
    index = {site_id: position for position, site_id in enumerate(ids)}
    accessible = np.array([site.geometrically_accessible for site in sites], dtype=float)
    constraints: list[np.ndarray] = []
    upper_bounds: list[float] = []
    for first, second in payload.conflict_edges:
        row = np.zeros(len(sites), dtype=float)
        row[index[first]] = 1.0
        row[index[second]] = 1.0
        constraints.append(row)
        upper_bounds.append(1.0)
    base_constraint = _linear_constraint(constraints, upper_bounds, len(sites))
    bounds = Bounds(np.zeros(len(sites)), accessible)
    species_oc = np.array([site.species == "OC" for site in sites], dtype=float)
    species_dmt = np.array([site.species == "DMT" for site in sites], dtype=float)

    max_total, _ = _solve_binary(-np.ones(len(sites)), bounds, base_constraint)
    max_oc, _ = _solve_binary(-species_oc, bounds, base_constraint)
    max_dmt, _ = _solve_binary(-species_dmt, bounds, base_constraint)
    max_total_count = int(round(-max_total))
    max_oc_count = int(round(-max_oc))
    max_dmt_count = int(round(-max_dmt))

    candidates: list[CooccupancyCombination] = []
    for oc_count in range(max_oc_count + 1):
        equality = LinearConstraint(csr_matrix(species_oc.reshape(1, -1)), [oc_count], [oc_count])
        objective, vector = _solve_binary(-species_dmt, bounds, (base_constraint, equality), allow_infeasible=True)
        if vector is None:
            continue
        dmt_count = int(round(-objective))
        candidates.append(
            CooccupancyCombination(
                oc_count=oc_count,
                dmt_count=dmt_count,
                occupied_site_ids=[ids[position] for position, value in enumerate(vector) if value > 0.5],
            )
        )
    pareto = [
        item
        for item in candidates
        if not any(
            other.oc_count >= item.oc_count
            and other.dmt_count >= item.dmt_count
            and (other.oc_count > item.oc_count or other.dmt_count > item.dmt_count)
            for other in candidates
        )
    ]
    nominal_sh3 = None
    nominal_pdz = None
    warnings: list[str] = []
    if payload.assembly_applicability_confirmed:
        assert payload.assembly_subunit_count is not None
        assert payload.sh3_sites_per_subunit is not None
        assert payload.pdz_sites_per_subunit is not None
        nominal_sh3 = payload.assembly_subunit_count * payload.sh3_sites_per_subunit
        nominal_pdz = payload.assembly_subunit_count * payload.pdz_sites_per_subunit
    else:
        warnings.append("assembly_applicability_not_confirmed_nominal_multimer_site_counts_withheld")

    return M2SiteGeometryResult(
        scaffold_id=payload.scaffold_id,
        status="valid" if payload.assembly_applicability_confirmed else "insufficient_data",
        m3_ready=payload.assembly_applicability_confirmed,
        nominal_sh3_sites=nominal_sh3,
        nominal_pdz_sites=nominal_pdz,
        accessible_oc_sites=[site.site_id for site in sites if site.species == "OC" and site.geometrically_accessible],
        accessible_dmt_sites=[site.site_id for site in sites if site.species == "DMT" and site.geometrically_accessible],
        maximum_total_cooccupancy=max_total_count,
        oc_occupancy_range=(0, max_oc_count),
        dmt_occupancy_range=(0, max_dmt_count),
        pareto_cooccupancy_combinations=sorted(pareto, key=lambda item: item.oc_count),
        model_ids=payload.model_ids,
        clash_rule_provenance=payload.clash_rule_provenance,
        warnings=warnings,
    )


def _linear_constraint(rows: list[np.ndarray], upper: list[float], size: int) -> LinearConstraint:
    from scipy.optimize import LinearConstraint
    from scipy.sparse import csr_matrix
    matrix = np.vstack(rows) if rows else np.empty((0, size), dtype=float)
    return LinearConstraint(csr_matrix(matrix), np.full(len(rows), -np.inf), np.asarray(upper))


def _solve_binary(
    objective: np.ndarray,
    bounds: Bounds,
    constraint: LinearConstraint | tuple[LinearConstraint, ...],
    *,
    allow_infeasible: bool = False,
) -> tuple[float, np.ndarray | None]:
    constraints = constraint if isinstance(constraint, tuple) else (constraint,)
    from scipy.optimize import milp
    result = milp(
        c=objective,
        integrality=np.ones(len(objective), dtype=int),
        bounds=bounds,
        constraints=constraints,
        options={"presolve": True},
    )
    if not result.success or result.fun is None or result.x is None:
        if allow_infeasible:
            return 0.0, None
        raise RuntimeError(f"site cooccupancy MILP failed: {result.message}")
    return float(result.fun), np.rint(result.x)
