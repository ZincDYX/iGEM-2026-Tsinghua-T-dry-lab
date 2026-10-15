"""Original LLPS output formats; no probabilities derived from local profiles.

FuzDrop's TSV lacks the global pLLPS: it is a profile, not a ranking score.
catGRANULE uses the original 2016 service's scores.txt and matching prot.fa.
"""
import csv
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Literal

from Bio import SeqIO
from pydantic import Field

from .design_analysis import ScientificAnalysisInput
from .constructs.tool_evidence import ToolEvidenceProvenance
from .m1_prioritization import PredictorScore


def _number(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("LLPS_native_nonfinite_value")
    return number


def read_native_llps(path, *, format, sequence, sequence_file=None, record_id="sequence_input", profile_file=None,
                     dpr_definition=None):
    if dpr_definition is not None and (dpr_definition!='2022_gkac386' or not format.startswith('fuzdrop_')):
        raise ValueError('DPR_reference_definition_requires_FuzDrop_profile_and_explicit_2022_paper')
    if format == "pscore_native":
        from .pscore_runner import parse_pscore_output
        native = parse_pscore_output(Path(path), sequence=sequence)
        return dict(tool="PScore", raw_score=native["pscore"], interpretation=native["interpretation"])
    if format == "catgranule2016_scores":
        if sequence_file is None:
            raise ValueError("catGRANULE_requires_native_input_FASTA")
        records = list(SeqIO.parse(sequence_file, "fasta"))
        matches = [row for row in records if row.id == record_id]
        if len(matches) != 1 or str(matches[0].seq) != sequence:
            raise ValueError("catGRANULE_native_input_sequence_mismatch")
        rows = [line.split() for line in Path(path).read_text().splitlines() if line.strip()]
        if any(len(row) != 2 for row in rows) or len({r[0] for r in rows}) != len(rows):
            raise ValueError("catGRANULE_requires_original_identifier_score_columns")
        selected = [row for row in rows if row[0] == record_id]
        if len(selected) != 1:
            raise ValueError("catGRANULE_requires_one_selected_global_score")
        result = {"tool": "catGRANULE_2016", "raw_score": _number(selected[0][1]),
                  "interpretation": "Original propensity score, not LLPS probability."}
        if profile_file is not None:
            profile = []
            for line in Path(profile_file).read_text().splitlines():
                fields = line.split()
                if not fields: continue
                if len(fields) != 3:
                    raise ValueError("catGRANULE_requires_original_profile_columns")
                if fields[2] == record_id:
                    position, value = map(_number, fields[:2])
                    if not 0 <= position <= len(sequence) or profile and position <= profile[-1]["native_position"]:
                        raise ValueError("catGRANULE_profile_position_mismatch")
                    profile.append(dict(native_position=position, score=value))
            if not profile:
                raise ValueError("catGRANULE_selected_native_profile_missing")
            result["native_profile"] = profile
        return result
    if format == "fuzdrop_response_json":
        data = json.loads(Path(path).read_text())
        if data.get("sequence") != sequence:
            raise ValueError("FuzDrop_native_sequence_mismatch")
        rows = [{"position": r["position"], "residue": r["aa"], "pDP": r["pDP"], "Sbind": r["Shae"]}
                for r in data["result"] if r.get("position") is not None]
        score = _number(data["pLLPS"])
        if not 0 <= score <= 1:
            raise ValueError("FuzDrop_pLLPS_outside_native_probability_range")
    elif format == "fuzdrop_scores_tsv":
        with Path(path).open(newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if reader.fieldnames != ["position", "residue", "pDP", "Sbind"]:
                raise ValueError("FuzDrop_requires_original_export_columns")
            rows = list(reader)
        score = None
    else:
        raise ValueError("unsupported_original_LLPS_format")
    positions = [int(r["position"]) for r in rows]
    if positions not in [list(range(len(sequence))), list(range(1, len(sequence)+1))]:
        raise ValueError("FuzDrop_requires_complete_contiguous_native_profile")
    if "".join(r["residue"] for r in rows) != sequence:
        raise ValueError("FuzDrop_native_profile_sequence_mismatch")
    for row in rows:
        row["pDP"], row["Sbind"] = _number(row["pDP"]), _number(row["Sbind"])
        if not 0 <= row["pDP"] <= 1:
            raise ValueError("FuzDrop_pDP_outside_native_probability_range")
    result={"tool": "FuzDrop", "raw_score": score, "residue_profile": rows,
            "missing": [] if score is not None else ["native_global_pLLPS_not_in_TSV"],
            "interpretation": "Original predictor output; local pDP is not global pLLPS or experimental validation."}
    if dpr_definition is not None:
        # Explicit paper-defined descriptive reanalysis, not a declaration of
        # the unversioned website's binary version or a project acceptance gate.
        spans=[];start=None
        for index in range(len(rows)+1):
            above=index<len(rows) and rows[index]['pDP']>=.60
            if above and start is None:start=index
            if not above and start is not None:
                if index-start>=10:spans.append(dict(start_1based=start+1,end_1based=index,length=index-start))
                start=None
        result['DPR_reference_reanalysis']=dict(definition=dpr_definition,source='https://doi.org/10.1093/nar/gkac386',
            residue_pDP_minimum=.60,minimum_consecutive_residues=10,regions=spans,
            scope='paper_defined_profile_description_not_server_version_or_M1_pass')
    return result


class NativeLLPSArtifact(ScientificAnalysisInput):
    path: Path
    format: Literal["catgranule2016_scores", "fuzdrop_response_json", "fuzdrop_scores_tsv", "pscore_native"]
    tool_version: str = Field(min_length=1)
    sequence_file: Path | None = None
    profile_file: Path | None = None
    record_id: str = "sequence_input"
    dpr_definition: Literal['2022_gkac386'] | None = None


class LLPSImportInput(ScientificAnalysisInput):
    """Review original exports; downloading/reviewing does not prove tool execution."""
    candidate_id: str
    sequence: str = Field(min_length=1)
    artifacts: list[NativeLLPSArtifact] = Field(min_length=1)
    reviewer: str = Field(min_length=1)
    source_reference: str = Field(min_length=1)


def import_llps_results(payload: LLPSImportInput):
    scores, profiles = [], []
    digest = sha256(payload.sequence.encode()).hexdigest()
    for artifact in payload.artifacts:
        observations = read_native_llps(artifact.path, format=artifact.format, sequence=payload.sequence,
            sequence_file=artifact.sequence_file, record_id=artifact.record_id, profile_file=artifact.profile_file,
            dpr_definition=artifact.dpr_definition)
        profiles.append({"format": artifact.format, **observations})
        if observations["raw_score"] is None:
            continue
        output_digest = sha256(artifact.path.read_bytes()).hexdigest()
        record = dict(tool_name=observations["tool"], tool_version=artifact.tool_version,
            input_sha256=digest, output_sha256=output_digest, origin="manual_review",
            reviewer=payload.reviewer, source_reference=payload.source_reference, decision="approved",
            reviewed_observations={"raw_score": observations["raw_score"]},
            native_format=artifact.format, sequence_file=str(artifact.sequence_file) if artifact.sequence_file else None,
            record_id=artifact.record_id)
        record_bytes = json.dumps(record, sort_keys=True, indent=2).encode()
        record_digest = sha256(record_bytes).hexdigest()
        # A shared native batch table may be reviewed for different records.
        # Never overwrite another candidate's already-bound interpretation.
        record_path = artifact.path.with_suffix(artifact.path.suffix+".review-"+record_digest[:16]+".json")
        record_path.write_bytes(record_bytes)
        score = PredictorScore(tool=observations["tool"], tool_version=artifact.tool_version,
            input_sequence_sha256=digest, source_file=artifact.path, raw_score=observations["raw_score"],
            provenance=ToolEvidenceProvenance(origin="manual_review", output_sha256=output_digest,
                record_file=record_path, record_sha256=record_digest))
        scores.append(score.model_dump(mode="json"))
    return dict(candidate_id=payload.candidate_id, input_sequence_sha256=digest,
                predictor_scores=scores, observations=profiles, formal_ranking=None)


def automated_predictor_score(output, *, tool, sequence, raw_score):
    """Use the native runner's existing execution record, not an invented review."""
    record_path = output.with_suffix(".run.json")
    record = json.loads(record_path.read_text())
    return PredictorScore(tool=tool, tool_version=record["tool_version"],
        input_sequence_sha256=sha256(sequence.encode()).hexdigest(), source_file=output, raw_score=raw_score,
        provenance=ToolEvidenceProvenance(origin="automated", output_sha256=record["output_sha256"],
            record_file=record_path, record_sha256=sha256(record_path.read_bytes()).hexdigest()))


def verify_native_predictor_score(observation):
    record = json.loads(observation.provenance.record_file.read_text())
    format = record.get("native_format")
    if format == "catgranule2016_scores":
        sequence_file = Path(record["sequence_file"])
        records = [r for r in SeqIO.parse(sequence_file, "fasta") if r.id == record["record_id"]]
        if len(records) != 1:
            raise ValueError("catGRANULE_missing_selected_native_input")
        sequence = str(records[0].seq)
    elif format == "fuzdrop_response_json":
        sequence_file = None
        sequence = json.loads(observation.source_file.read_text())["sequence"]
    else:
        raise ValueError("predictor_requires_supported_native_format")
    if sha256(sequence.encode()).hexdigest() != observation.input_sequence_sha256:
        raise ValueError("LLPS_native_input_identity_changed")
    native = read_native_llps(observation.source_file, format=format, sequence=sequence,
        sequence_file=sequence_file, record_id=record.get("record_id", "sequence_input"))
    if native["tool"] != observation.tool or native["raw_score"] != observation.raw_score:
        raise ValueError("LLPS_native_global_score_mismatch")
