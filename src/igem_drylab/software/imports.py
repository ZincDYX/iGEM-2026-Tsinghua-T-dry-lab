"""Shared import preview, never executes uploaded files."""
from hashlib import sha256
from io import StringIO
from pathlib import Path
import csv
import json
from typing import Any
from Bio import SeqIO
from igem_drylab.workflow.models import Project, SequenceRecord, WorkflowError
from igem_drylab.workflow.pathway import Pathway


def preview_import(data_dir, boundary, filename, content, input_kind="auto"):
    from igem_drylab.workflow.disclosure import check_import_content
    check_import_content(filename, content.encode())
    boundary.check_bytes(content.encode())
    extension = Path(filename).suffix.lower()
    digest = sha256(content.encode()).hexdigest()
    root = data_dir / "imports"
    root.mkdir(parents=True, exist_ok=True)
    source = root / f"{digest}{extension}"
    # Parse before storing. The project itself changes only after confirmation.
    if extension in {".fasta", ".fa", ".faa", ".gb", ".gbk", ".genbank"}:
        format_name = "genbank" if extension in {".gb", ".gbk", ".genbank"} else "fasta"
        sequences: list[dict[str, Any]] = []
        design_parts = None
        if format_name == 'genbank':
            from igem_drylab.workflow.genbank_design import import_design
            summaries, bindings, proteins = import_design(content)
            sequences = [item.model_dump() for item in proteins]
            design_parts = (summaries, bindings)
        else:
            for record in SeqIO.parse(StringIO(content), format_name):
                sequences.append(SequenceRecord(id=record.id, sequence=str(record.seq)).model_dump())
            if not sequences:
                raise ValueError("no_protein_sequences")
        from igem_drylab.constructs.linker_features import normalize_amino_acid_sequence
        for item in sequences:
            item["sequence"] = normalize_amino_acid_sequence(item["sequence"])
        Project(id="preview", name="preview", sequences=sequences)
        patch: dict[str, Any] = {"sequences": sequences}
        kind = "genbank_design" if design_parts is not None else "sequences"
    elif extension == ".json" and input_kind == "wetlab":
        from igem_drylab.wetlab.models import WetLabResult
        raw = json.loads(content)
        rows = raw.get("records") if isinstance(raw, dict) else raw
        if not isinstance(rows, list) or not rows:
            raise ValueError("wetlab_requires_nonempty_typed_records")
        records = [WetLabResult.model_validate(row).model_dump(mode="json") for row in rows]
        from igem_drylab.wetlab import quality_control
        qc = quality_control([WetLabResult.model_validate(row) for row in records])
        patch, kind = {"datasets": [{"id": digest, "name": filename, "kind": "wetlab",
            "records": records, "qc": [item.model_dump(mode="json") for item in qc]}]}, "wetlab"
    elif extension == ".json" and input_kind == "pathway":
        pathway = Pathway.model_validate_json(content)
        patch, kind = {"pathway": pathway.model_dump(mode="json")}, "pathway"
    elif extension == ".json":
        json.loads(content)
        patch, kind = {}, "configuration_display_only"
    elif extension in {".csv", ".tsv"}:
        reader = csv.DictReader(StringIO(content), delimiter="\t" if extension == ".tsv" else ",")
        if not reader.fieldnames or len(reader.fieldnames) > 128 or len(set(reader.fieldnames)) != len(reader.fieldnames) or any(not c for c in reader.fieldnames):
            raise WorkflowError("table_columns_missing_or_duplicate")
        count = 0
        for row in reader:
            if None in row or any(v is None for v in row.values()) or count >= 100_000:
                raise WorkflowError("table_row_budget_or_shape_invalid")
            count += 1
        if not count:
            raise ValueError("empty_table")
        patch, kind = {}, "dataset"
    else:
        raise ValueError("supported_imports: FASTA, annotated GenBank, explicit-role JSON, CSV, TSV")
    source.write_bytes(content.encode("utf-8"))
    file = boundary.asset(source, fresh=True, logical_name=filename)
    if kind == 'genbank_design':
        from igem_drylab.workflow.genbank_design import GenBankDesign
        summaries, bindings = design_parts
        design = GenBankDesign(id=file['id'], file_id=file['id'], name=filename,
            records=summaries, cds_proteins=bindings)
        patch['datasets'] = [design.model_dump(mode='json')]
    for dataset in patch.get("datasets", []):
        dataset["file_id"] = file["id"]
    result = {"kind": kind, "patch": patch, "file": file}
    boundary.check(result)
    return result
