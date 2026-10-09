"""Version-specific full-fusion parsers, never infer aggregation thresholds."""
import csv
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Literal

from pydantic import Field, model_validator

from .design_analysis import ScientificAnalysisInput
from .constructs.linker_features import normalize_amino_acid_sequence, FusionToolEvidence
from .constructs.tool_evidence import ToolEvidenceProvenance


class AggregationRule(ScientificAnalysisInput):
    high_score_percent: float = Field(ge=0,le=100)
    minimum_run_length: int = Field(ge=1)
    source_reference: str = Field(min_length=1)


class NativeFusionArtifact(ScientificAnalysisInput):
    path: Path
    tool_version: str = Field(min_length=1)
    format: Literal["signalp6_summary", "deeptmhmm1_3line", "tango_residue_out"]
    record_id: str
    aggregation_rule: AggregationRule | None = None

    @model_validator(mode="after")
    def rule_scope(self):
        if (self.format == "tango_residue_out") != (self.aggregation_rule is not None):
            raise ValueError("TANGO_requires_explicit_high_score_run_definition_other_tools_do_not")
        return self


def parse_native_artifact(artifact: NativeFusionArtifact, sequence: str) -> dict:
    sequence = normalize_amino_acid_sequence(sequence)
    text = artifact.path.read_text(encoding="utf-8-sig")
    if artifact.format == "signalp6_summary":
        lines = text.splitlines()
        headers = [i for i,line in enumerate(lines) if line.lstrip("# ").split("\t")[0] == "ID"]
        if len(headers) != 1:
            raise ValueError("SignalP6_requires_documented_tabular_header")
        index = headers[0]
        rows = list(csv.DictReader([lines[index].lstrip("# "), *[l for l in lines[index+1:] if l.strip() and not l.startswith("#")]], delimiter="\t"))
        rows = [r for r in rows if r.get("ID") == artifact.record_id]
        if len(rows)!=1 or rows[0].get("Prediction") not in {"OTHER","SP","LIPO","TAT","TATLIPO","PILIN"}:
            raise ValueError("SignalP6_missing_or_duplicate_prediction_for_exact_input_ID")
        row = rows[0]
        prediction = row["Prediction"]
        cs = re.search(r"CS pos:\s*(\d+)\s*-\s*(\d+)\.\s*Pr:\s*([0-9.eE+-]+)", row.get("CS Position", ""))
        if cs and (int(cs[2]) != int(cs[1])+1 or not 1 <= int(cs[1]) < len(sequence) or not 0 <= float(cs[3]) <= 1):
            raise ValueError("SignalP6_invalid_cleavage_position_or_probability")
        if prediction != "OTHER" and cs is None:
            raise ValueError("SignalP6_positive_prediction_has_no_unambiguous_reported_cleavage")
        return {"signal_peptide_with_clear_cleavage":prediction != "OTHER" and cs is not None}
    if artifact.format == "deeptmhmm1_3line":
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if len(lines)%3:
            raise ValueError("DeepTMHMM_requires_complete_three_line_records")
        rows = [(lines[i][1:].split("|")[0].strip().split()[0],lines[i+1],lines[i+2])
                for i in range(0,len(lines),3) if lines[i].startswith(">")]
        rows = [(seq,top) for identifier,seq,top in rows if identifier == artifact.record_id]
        if len(rows)!=1 or rows[0][0] != sequence or len(rows[0][1]) != len(sequence):
            raise ValueError("DeepTMHMM_native_sequence_or_length_mismatch")
        topology = rows[0][1]
        if set(topology)-set("IOMBSX"):
            raise ValueError("unsupported_DeepTMHMM1_topology_labels_no_version2_substitution")
        if "X" in topology:
            raise ValueError("ambiguous_DeepTMHMM_topology_not_a_complete_negative_screen")
        if "B" in topology:
            raise ValueError("beta_barrel_topology_requires_explicit_membrane_rule_not_zero_helix_pass")
        return {"transmembrane_helix_count":len(re.findall("M+",topology))}
    rows = []
    for line in text.splitlines():
        fields = next(csv.reader([line])) if "," in line else line.split()
        if fields and fields[0].strip().isdigit():
            if len(fields)!=7:
                raise ValueError("TANGO_requires_seven_documented_residue_columns")
            rows.append((int(fields[0]),fields[1].strip(),float(fields[5])))
    if [r[0] for r in rows] != list(range(1,len(sequence)+1)) or "".join(r[1] for r in rows) != sequence:
        raise ValueError("TANGO_native_residue_sequence_or_indices_mismatch")
    if any(not 0 <= r[2] <= 100 for r in rows):
        raise ValueError("TANGO_aggregation_percentage_out_of_range")
    runs = [m for m in re.finditer("1+","".join("1" if r[2] > artifact.aggregation_rule.high_score_percent else "0" for r in rows))
            if m.end()-m.start() >= artifact.aggregation_rule.minimum_run_length]
    return {"continuous_high_aggregation_hotspots":len(runs)}


class FusionImportInput(ScientificAnalysisInput):
    sequence: str
    artifacts: list[NativeFusionArtifact] = Field(min_length=1)
    reviewer: str = Field(min_length=1)
    source_reference: str = Field(min_length=1)
    output_dir: Path


def import_fusion_tools(payload: FusionImportInput) -> dict:
    """Import actual raw results; review binds their job to the submitted input."""
    sequence = normalize_amino_acid_sequence(payload.sequence)
    digest = sha256(sequence.encode()).hexdigest()
    evidence = FusionToolEvidence(input_sha256=digest, native_formats={}, native_rules={})
    names = {"signalp6_summary":("SignalP","signalp"), "deeptmhmm1_3line":("DeepTMHMM","deeptmhmm"),
             "tango_residue_out":("TANGO","aggregation")}
    if len({a.format for a in payload.artifacts}) != len(payload.artifacts):
        raise ValueError("one_exact_native_result_per_fusion_tool")
    payload.output_dir.mkdir(parents=True,exist_ok=True)
    for artifact in payload.artifacts:
        name,prefix = names[artifact.format]
        observations = parse_native_artifact(artifact,sequence)
        record = {"origin":"manual_review","reviewer":payload.reviewer,"source_reference":payload.source_reference,
            "decision":"approved","tool_name":name,"tool_version":artifact.tool_version,"input_sha256":digest,
            "output_sha256":sha256(artifact.path.read_bytes()).hexdigest(),"reviewed_observations":observations,
            "scope":"raw_result_import_not_an_automatically_executed_job","record_id":artifact.record_id,
            "native_format":artifact.format,"aggregation_rule":artifact.aggregation_rule.model_dump() if artifact.aggregation_rule else None}
        path = payload.output_dir/(prefix+"-import.json")
        path.write_text(json.dumps(record,indent=2),encoding="utf-8")
        evidence.provenance[name] = ToolEvidenceProvenance(origin="manual_review",output_sha256=record["output_sha256"],
            record_file=path,record_sha256=sha256(path.read_bytes()).hexdigest())
        setattr(evidence,prefix+"_source_file",artifact.path.resolve())
        setattr(evidence,prefix+"_tool_version",artifact.tool_version)
        if prefix=="aggregation":
            evidence.aggregation_tool="TANGO"
        for key,value in observations.items():
            setattr(evidence,key,value)
        evidence.native_formats[name] = artifact.format
        evidence.native_rules[name] = artifact.aggregation_rule.model_dump() if artifact.aggregation_rule else None
    return {"fusion":evidence.model_dump(mode="json"),"scope":"native_raw_result_import_not_executed_job"}
