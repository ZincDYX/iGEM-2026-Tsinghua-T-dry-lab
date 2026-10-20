"""M2 region observations from exact, full-length prediction artifacts.

Uses the existing coordinate and FreeSASA implementations. Relative SASA is
against the same selected atoms isolated from the same conformation, not an
experimental free peptide or a binding affinity. No burial cutoff is invented.
"""
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from Bio.PDB import PDBParser
from Bio.SeqUtils import seq1
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .parsers.structure_prediction import parse_structure_prediction_output
from .structure_metrics import read_pdb_atoms, residue_sasa_areas


class Region(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    role: str
    start: int = Field(ge=1)
    end: int = Field(ge=1)

    @model_validator(mode="after")
    def ordered(self):
        if self.end < self.start:
            raise ValueError("region_end_precedes_start")
        return self


class RegionAssessmentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_id: str
    tool_input_id: str | None = None
    sequence: str
    confidence_file: Path
    regions: list[Region] = Field(min_length=1)
    calculate_accessibility: bool = True


def load_region_requests(path: Path) -> list[RegionAssessmentInput]:
    requests = [RegionAssessmentInput.model_validate(row) for row in json.loads(path.read_text())]
    for request in requests:
        if not request.confidence_file.is_absolute():
            request.confidence_file = (path.parent / request.confidence_file).resolve()
    return requests


def assess_regions(request: RegionAssessmentInput) -> dict:
    summary = parse_structure_prediction_output(request.confidence_file,
                                               candidate_id=request.tool_input_id or request.candidate_id)
    if summary.source != "colabfold_af2_ptm":
        raise ValueError("region_assessment_requires_paired_ColabFold_artifacts")
    model = PDBParser(QUIET=True).get_structure(request.candidate_id, summary.model_file)
    chains = list(next(model.get_models()).get_chains())
    if len(chains) != 1:
        raise ValueError("region_assessment_requires_one_complete_protein_chain")
    residues = [r for r in chains[0].get_residues() if r.id[0] == " "]
    sequence = "".join(seq1(r.resname) for r in residues)
    if sequence != request.sequence or len(residues) != summary.residue_count:
        raise ValueError("region_model_does_not_match_complete_input_sequence")
    if len({r.name for r in request.regions}) != len(request.regions):
        raise ValueError("duplicate_region_name")
    if any(r.end > len(sequence) for r in request.regions):
        raise ValueError("region_outside_complete_sequence")
    confidence = json.loads(request.confidence_file.read_text())
    plddt = np.asarray(confidence["plddt"], dtype=float)
    # JSON-to-PDB association is checked by the parser; verify the actual
    # coordinate confidence too, allowing only PDB's two-decimal rounding.
    if any("CA" not in r for r in residues) or not np.allclose(
            [r["CA"].bfactor for r in residues], plddt, atol=0.011, rtol=0):
        raise ValueError("coordinate_confidence_does_not_match_paired_scores")
    chain = chains[0].id
    atoms = read_pdb_atoms(summary.model_file)
    areas = None
    parameters = None
    if request.calculate_accessibility:
        import freesasa
        parameters = freesasa.Parameters()
        _, areas = residue_sasa_areas(summary.model_file, parameters=parameters)
    observations = []
    for region in request.regions:
        scores = plddt[region.start - 1:region.end]
        keys = [(chain, r.id[1], r.id[2].strip())
                for r in residues[region.start - 1:region.end]]
        row = dict(name=region.name, role=region.role, start=region.start, end=region.end,
                   mean_plddt=float(scores.mean()), minimum_plddt=float(scores.min()),
                   residues_below_50=int(np.count_nonzero(scores < 50)),
                   residues_at_or_below_70=int(np.count_nonzero(scores <= 70)),
                   confidence_gate="high" if scores.mean() > 70 else
                       "medium" if scores.mean() >= 50 else "low",
                   context_sasa_angstrom2=None, isolated_same_conformation_sasa_angstrom2=None,
                   sasa_retention=None, burial_verdict=None)
        if areas is not None:
            if any(key not in areas for key in keys):
                raise ValueError("incomplete_region_SASA_selection")
            selected = set(keys)
            with TemporaryDirectory(prefix="fusionlab-region-") as temporary:
                isolated = Path(temporary) / "isolated.pdb"
                isolated.write_text("\n".join(a.pdb_line for a in atoms
                    if (a.chain, a.residue, a.insertion) in selected) + "\nEND\n")
                _, free_areas = residue_sasa_areas(isolated, parameters=parameters)
            if any(key not in free_areas for key in keys):
                raise ValueError("incomplete_isolated_region_SASA_selection")
            context_area = sum(areas[key] for key in keys)
            isolated_area = sum(free_areas[key] for key in keys)
            row.update(context_sasa_angstrom2=context_area,
                       isolated_same_conformation_sasa_angstrom2=isolated_area,
                       sasa_retention=context_area / isolated_area if isolated_area > 0 else None)
            row["interpretation"] = ("Low-confidence/flexible conformation: reference only; not a burial decision."
                if row["confidence_gate"] != "high" or region.role in {"idr", "linker"} else
                "Predicted accessibility observation; no reviewed burial cutoff supplied.")
        observations.append(row)
    pairs = []
    if confidence.get("pae") is not None:
        pae = np.asarray(confidence["pae"], dtype=float)
        for i, first in enumerate(request.regions):
            for second in request.regions[i + 1:]:
                if max(first.start, second.start) <= min(first.end, second.end):
                    raise ValueError("interdomain_PAE_regions_must_be_disjoint")
                forward = pae[first.start - 1:first.end, second.start - 1:second.end]
                reverse = pae[second.start - 1:second.end, first.start - 1:first.end]
                pairs.append(dict(first=first.name, second=second.name,
                    first_to_second_mean_angstrom=float(forward.mean()),
                    second_to_first_mean_angstrom=float(reverse.mean()),
                    mean_interdomain_pae_angstrom=float((forward.sum()+reverse.sum())/(forward.size+reverse.size)),
                    interpretation="Relative-position uncertainty, not a rejection or binding score."))
    return dict(schema_version="m2-region-observations-v1", candidate_id=request.candidate_id,
                model_rank=summary.model_rank, source_tool="ColabFold",
                input_sequence_sha256=sha256(sequence.encode()).hexdigest(),
                model_file=str(summary.model_file), confidence_file=str(request.confidence_file),
                model_sha256=sha256(summary.model_file.read_bytes()).hexdigest(),
                confidence_sha256=sha256(request.confidence_file.read_bytes()).hexdigest(),
                regions=observations, interdomain_pae=pairs,
                formal_verdict="blocked", missing=["Q1 reviewed core/pocket definitions and reference comparison",
                    "Q2 reviewed accessibility decisions", "Q3 actual fusion assembly assessment",
                    "Q4 template placements and co-occupancy evidence"],
                claim_scope="predicted_region_observations_not_complete_M2_acceptance")
