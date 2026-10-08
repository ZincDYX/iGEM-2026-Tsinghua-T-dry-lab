"""Authoritative external-tool routes and deployment-budget auditing.

Scientific stages depend on capabilities, not on installation details.  This
module keeps the selected executable/API route, licensing boundary, and disk
footprint in one place so adapters and documentation cannot silently diverge.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


DEPLOYMENT_BUDGET_BYTES = 15_000_000_000


class ExternalToolSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    capability: str
    route: Literal[
        "local", "public_api", "licensed_local_or_api", "optional_local", "manual_artifact"
    ]
    formal_stage: Literal["M0", "M1", "M2", "M3", "M4"] | None = None
    official_url: str
    notes: str


TOOL_CATALOG: dict[str, ExternalToolSpec] = {
    item.name: item
    for item in (
        ExternalToolSpec(
            name="openalex",
            capability="literature metadata search",
            route="public_api",
            formal_stage="M0",
            official_url="https://docs.openalex.org/",
            notes="Metadata discovery only; never promotes a numeric value to reviewed evidence.",
        ),
        ExternalToolSpec(
            name="crossref",
            capability="DOI metadata lookup",
            route="public_api",
            formal_stage="M0",
            official_url="https://www.crossref.org/documentation/retrieve-metadata/rest-api/",
            notes="Use the polite REST pool and cache DOI metadata.",
        ),
        ExternalToolSpec(
            name="scopus",
            capability="licensed literature metadata search",
            route="licensed_local_or_api",
            formal_stage="M0",
            official_url="https://dev.elsevier.com/sc_apis.html",
            notes="Requires an Elsevier API key and, for some records, institutional entitlement.",
        ),
        ExternalToolSpec(
            name="rcsb_pdb",
            capability="structure and chain metadata retrieval",
            route="public_api",
            formal_stage="M0",
            official_url="https://data.rcsb.org/",
            notes="Store entry and chain identifiers with downloaded structures.",
        ),
        ExternalToolSpec(
            name="uniprot",
            capability="reviewed protein sequence retrieval",
            route="public_api",
            formal_stage="M0",
            official_url="https://rest.uniprot.org/",
            notes="Record accession and release metadata; verify species and isoform.",
        ),
        ExternalToolSpec(
            name="brenda",
            capability="enzyme evidence lookup",
            route="licensed_local_or_api",
            formal_stage="M0",
            official_url="https://www.brenda-enzymes.org/soap.php",
            notes="Credentials and BRENDA terms apply; entries still require substrate and assay review.",
        ),
        ExternalToolSpec(
            name="kegg",
            capability="reaction and pathway metadata retrieval",
            route="public_api",
            formal_stage="M0",
            official_url="https://www.kegg.jp/kegg/rest/keggapi.html",
            notes="Use REST for identifiers and reaction context, subject to KEGG terms.",
        ),
        ExternalToolSpec(
            name="iupred2a",
            capability="per-residue intrinsic-disorder prediction",
            route="local",
            formal_stage="M1",
            official_url="https://github.com/saezlab/iupred",
            notes="Use the basic IUPred2 route; AIUPred weights are not required.",
        ),
        ExternalToolSpec(
            name="jpred",
            capability="secondary-structure prediction",
            route="public_api",
            formal_stage="M1",
            official_url="https://www.compbio.dundee.ac.uk/jpred/api.shtml",
            notes="Official REST API; cache the returned result archive by sequence hash.",
        ),
        ExternalToolSpec(
            name="psipred",
            capability="secondary-structure prediction",
            route="optional_local",
            formal_stage="M1",
            official_url="https://github.com/psipred/psipred",
            notes="Alternative to JPred; its sequence-search database is not part of the lean deployment.",
        ),
        ExternalToolSpec(
            name="seg",
            capability="low-complexity masking",
            route="local",
            formal_stage="M1",
            official_url="https://www.ncbi.nlm.nih.gov/books/NBK279690/",
            notes="Use the standalone NCBI SEG program on FASTA input; no sequence database is required.",
        ),
        ExternalToolSpec(
            name="protparam",
            capability="protein physicochemical cross-check",
            route="local",
            formal_stage="M1",
            official_url="https://biopython.org/docs/latest/api/Bio.SeqUtils.ProtParam.html",
            notes="Biopython ProteinAnalysis supplies the local reproducible calculation.",
        ),
        ExternalToolSpec(
            name="signalp",
            capability="signal-peptide and cleavage-site prediction",
            route="licensed_local_or_api",
            formal_stage="M1",
            official_url="https://services.healthtech.dtu.dk/services/SignalP-6.0/",
            notes="Academic portable package or DTU BioLib SignalP-6; do not scrape the web form.",
        ),
        ExternalToolSpec(
            name="deeptmhmm",
            capability="transmembrane-topology prediction",
            route="licensed_local_or_api",
            formal_stage="M1",
            official_url="https://services.healthtech.dtu.dk/services/DeepTMHMM-1.0/",
            notes="Academic local package or DTU BioLib DeepTMHMM; preserve the returned topology artifact.",
        ),
        ExternalToolSpec(
            name="tango",
            capability="aggregation-hotspot prediction",
            route="licensed_local_or_api",
            formal_stage="M1",
            official_url="https://tango.crg.eu/",
            notes="TANGO requires an academic/commercial license; no unlicensed binary is bundled.",
        ),
        ExternalToolSpec(
            name="pasta2",
            capability="aggregation-hotspot prediction",
            route="licensed_local_or_api",
            formal_stage="M1",
            official_url="https://www.elixir-italy.org/services/pasta/",
            notes="Alternative to TANGO; use the academic command-line distribution when obtained.",
        ),
        ExternalToolSpec(
            name="colabfold",
            capability="protein and complex structure prediction",
            route="local",
            formal_stage="M2",
            official_url="https://github.com/sokrypton/ColabFold",
            notes="Local GPU inference with cached model parameters; public MSA service only for small serial jobs.",
        ),
        ExternalToolSpec(
            name="freesasa",
            capability="solvent-accessible surface area",
            route="local",
            formal_stage="M2",
            official_url="https://freesasa.github.io/",
            notes="Use the Python API so reference and fusion structures share one parameter object.",
        ),
        ExternalToolSpec(
            name="autodock_vina",
            capability="small-molecule docking negative screen",
            route="local",
            formal_stage="M2",
            official_url="https://autodock-vina.readthedocs.io/en/latest/",
            notes="Use Vina with Meeko-prepared receptor and ligand artifacts; scores are not kinetic constants.",
        ),
        ExternalToolSpec(
            name="pymol",
            capability="optional structure inspection and scripted measurements",
            route="optional_local",
            formal_stage="M2",
            official_url="https://github.com/schrodinger/pymol-open-source",
            notes="Optional inspection layer; production metrics remain code-generated artifacts.",
        ),
        ExternalToolSpec(
            name="chimerax",
            capability="optional structure inspection and assembly analysis",
            route="licensed_local_or_api",
            formal_stage="M2",
            official_url="https://www.rbvi.ucsf.edu/chimerax/",
            notes="Optional desktop tool with its own license; not required by the headless formal route.",
        ),
        ExternalToolSpec(
            name="gromacs",
            capability="optional molecular-dynamics validation",
            route="optional_local",
            formal_stage="M2",
            official_url="https://manual.gromacs.org/current/install-guide/index.html",
            notes="Optional high-cost validation; no trajectory is treated as required M2 evidence by default.",
        ),
        ExternalToolSpec(
            name="catgranule",
            capability="optional LLPS propensity cross-check",
            route="optional_local",
            official_url="https://github.com/tartaglialabIIT/catGRANULE2.0",
            notes="Optional raw predictor output; never substitutes for measured M3 inputs.",
        ),
        ExternalToolSpec(
            name="calvados",
            capability="optional coarse-grained phase-behaviour simulation",
            route="optional_local",
            official_url="https://github.com/KULL-Centre/CALVADOS",
            notes="Optional M1/M2 evidence only; not a formal M3 concentration input.",
        ),
        ExternalToolSpec(
            name="mpipi",
            capability="optional coarse-grained phase-behaviour simulation",
            route="optional_local",
            official_url="https://doi.org/10.1038/s43588-021-00155-3",
            notes="Original Mpipi method; verify its code and conditions before enabling. Mpipi-Recharged is a distinct variant, not an automatic substitution. Optional M1/M2 evidence only.",
        ),
        ExternalToolSpec(
            name="fuzdrop",
            capability="optional LLPS propensity cross-check",
            route="manual_artifact",
            official_url="https://fuzdrop.bio.unipd.it/",
            notes="No undocumented web scraping; ingest a user-exported artifact if no supported API is available.",
        ),
        ExternalToolSpec(
            name="pspredictor",
            capability="optional LLPS propensity cross-check",
            route="manual_artifact",
            official_url="http://www.pkumdl.cn:8000/PSPredictor/",
            notes="Optional only; no formal route is claimed until a stable supported API is verified.",
        ),
        ExternalToolSpec(
            name="pscore", capability="Original PScore LLPS propensity cross-check", route="optional_local",
            formal_stage="M1", official_url="https://github.com/haocai1992/PScore-online",
            notes="Unmodified author implementation and lookup data; educational/research license. Cropped IDRs and artificial fusions are extrapolations, not validated probabilities.",
        ),
        ExternalToolSpec(
            name="abcfold",
            capability="optional structure-prediction orchestration",
            route="optional_local",
            official_url="https://github.com/rigdenlab/ABCFold",
            notes="Optional cross-validation, not part of the lean formal route.",
        ),
        ExternalToolSpec(
            name="boltz",
            capability="optional structure-prediction cross-validation",
            route="optional_local",
            official_url="https://github.com/jwohlwend/boltz",
            notes="Optional cross-validation, not installed in the lean environment; current combined budget is 15 GB.",
        ),
        ExternalToolSpec(
            name="chai",
            capability="optional structure-prediction cross-validation",
            route="optional_local",
            official_url="https://github.com/chaidiscovery/chai-lab",
            notes="Optional cross-validation, not installed in the lean environment; current combined budget is 15 GB.",
        ),
    )
}


class DeploymentUsage(BaseModel):
    budget_bytes: int = Field(default=DEPLOYMENT_BUDGET_BYTES, gt=0)
    used_bytes: int = Field(ge=0)
    within_budget: bool
    paths: dict[str, int]


def tool_spec(name: str) -> ExternalToolSpec | None:
    return TOOL_CATALOG.get(name)


def audit_deployment(paths: list[Path], *, budget_bytes: int = DEPLOYMENT_BUDGET_BYTES) -> DeploymentUsage:
    """Measure unique deployment roots without double-counting nested paths."""

    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"declared_deployment_root_missing:{','.join(missing)}")
    roots = _independent_existing_roots(paths)
    measured = {str(path): _tree_size(path) for path in roots}
    used = sum(measured.values())
    return DeploymentUsage(
        budget_bytes=budget_bytes,
        used_bytes=used,
        within_budget=used <= budget_bytes,
        paths=measured,
    )


def _independent_existing_roots(paths: list[Path]) -> list[Path]:
    resolved = sorted({path.resolve() for path in paths if path.exists()}, key=lambda item: len(item.parts))
    roots: list[Path] = []
    for path in resolved:
        if not any(path == root or root in path.parents for root in roots):
            roots.append(path)
    return roots


def _tree_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
