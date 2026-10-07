"""Authorized display projections. No solver, parameter, or evidence mutation."""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import json
import math
from pathlib import Path
import re
from typing import Literal

from pydantic import Field

from .models import Contract, WorkflowError

DISPLAY_SCHEMA = "display-resource-v1"
MAX_SOURCE_BYTES = 20_000_000
MAX_POINTS = 100_000
MAX_SERIES = 128
MAX_IMAGE_PIXELS = 16_000_000


class ResourceIdentity(Contract):
    project_id: str
    file_id: str
    source_sha256: str
    run_id: str | None = None
    snapshot_hash: str | None = None
    node_id: str | None = None
    attempt: int | None = None
    candidate_id: str | None = None
    construct_id: str | None = None
    condition_id: str | None = None


class ImageResource(Contract):
    kind: Literal["image"] = "image"
    identity: ResourceIdentity
    name: str
    media_type: Literal["image/png", "image/jpeg"]
    byte_count: int
    role: Literal["registered_source"] = "registered_source"
    claim_scope: Literal["display_only_not_experimental_validation"] = "display_only_not_experimental_validation"


class StructureResource(Contract):
    kind: Literal["structure"] = "structure"
    identity: ResourceIdentity
    name: str
    format: Literal["pdb", "mmcif"]
    byte_count: int
    role: Literal["registered_source"] = "registered_source"
    claim_scope: Literal["geometry_only_no_inferred_activity_or_confidence"] = "geometry_only_no_inferred_activity_or_confidence"


class SeriesResource(Contract):
    kind: Literal["series"] = "series"
    identity: ResourceIdentity
    name: str
    byte_count: int
    result_schema_version: Literal["m4-prediction-v2"] = "m4-prediction-v2"
    role: Literal["prediction_contract"] = "prediction_contract"


class TableResource(Contract):
    kind: Literal["table"] = "table"
    identity: ResourceIdentity
    name: str
    media_type: str
    byte_count: int
    role: Literal["registered_source"] = "registered_source"


class ResourcePage(Contract):
    schema_version: Literal["display-resource-v1"] = DISPLAY_SCHEMA
    project_id: str
    run_id: str | None
    snapshot_hash: str | None
    offset: int
    total: int
    has_more: bool
    items: list[ImageResource | StructureResource | SeriesResource | TableResource] = Field(discriminator=None)


class SeriesDescriptor(Contract):
    id: str
    compartment: str
    species: str
    unit: str


class SeriesPage(Contract):
    schema_version: Literal["display-series-v1"] = "display-series-v1"
    identity: ResourceIdentity
    result_schema_version: str
    model_kind: str
    formula_version: str
    time_unit: str
    offset: int
    total: int
    has_more: bool
    display_policy: Literal["exact_contiguous_page_no_decimation"] = "exact_contiguous_page_no_decimation"
    time: list[float]
    series: list[SeriesDescriptor]
    values: dict[str, list[float | None]]


class ResidueIdentity(Contract):
    model: str
    chain: str
    residue_number: str
    insertion_code: str
    residue_name: str


class ResidueAnnotation(Contract):
    residue: ResidueIdentity
    full_fusion_position: int | None = Field(default=None, ge=1)
    region: Literal["enzyme", "scaffold", "idr", "linker", "ligand_tail", "tag"] | None = None
    reference_residue: ResidueIdentity | None = None
    reference_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    pocket: bool = False
    clash: bool = False
    plddt: float | None = Field(default=None, ge=0, le=100)


class StructureAnnotations(Contract):
    schema_version: Literal["structure-display-annotations-v1"]
    target_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_reference: str = Field(min_length=1)
    source_tool: str | None = None
    source_tool_version: str | None = None
    fusion_sequence_file_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    fusion_sequence_id: str | None = None
    confidence_semantics: Literal["plddt", "not_provided"]
    rows: list[ResidueAnnotation] = Field(max_length=100_000)


class DisplayResidueAnnotation(ResidueAnnotation):
    reference_file_id: str | None = None  # Derived from verified project grants.


class StructurePage(Contract):
    schema_version: Literal["display-structure-v1"] = "display-structure-v1"
    identity: ResourceIdentity
    format: str
    offset: int
    total: int
    chains: list[str]
    models: list[str]
    residues: list[ResidueIdentity]
    confidence_status: Literal["not_registered", "source_registered_not_scientific_approval"] = "not_registered"
    mapping_status: Literal["not_registered", "source_registered_not_scientific_approval"] = "not_registered"
    pocket_status: Literal["not_registered", "source_registered_not_scientific_approval"] = "not_registered"
    annotation_file_id: str | None = None
    annotation_sha256: str | None = None
    annotation_source_reference: str | None = None
    annotation_source_tool: str | None = None
    annotation_source_tool_version: str | None = None
    fusion_sequence_file_id: str | None = None
    fusion_sequence_file_sha256: str | None = None
    fusion_sequence_id: str | None = None
    annotations: list[DisplayResidueAnnotation] = Field(default_factory=list)
    preview_policy: Literal["atom_coordinates_only_original_sealed"] = "atom_coordinates_only_original_sealed"


def digest_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


class DisplayResources:
    def __init__(self, store, boundary):
        self.store, self.boundary = store, boundary
        with store.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS display_series_meta(
                  file_id TEXT NOT NULL, hash TEXT NOT NULL, schema TEXT NOT NULL,
                  payload TEXT NOT NULL, PRIMARY KEY(file_id,hash,schema));
                CREATE TABLE IF NOT EXISTS display_series_points(
                  file_id TEXT NOT NULL, hash TEXT NOT NULL, schema TEXT NOT NULL,
                  ordinal INTEGER NOT NULL, time REAL NOT NULL, values_json TEXT NOT NULL,
                  PRIMARY KEY(file_id,hash,schema,ordinal));
            """)

    def source(self, project_id, file_id):
        # Grant lookup precedes every cache lookup, including identical hashes.
        self.store.project(project_id)
        with self.store.connection() as db:
            row = db.execute("SELECT * FROM file_assets WHERE id=? AND project_id=?", (file_id, project_id)).fetchone()
        if row is None:
            raise WorkflowError("file_project_mismatch", status_code=403)
        path = Path(row["path"])
        if not path.is_file() or path.stat().st_size > MAX_SOURCE_BYTES:
            raise WorkflowError("display_source_budget_exceeded")
        if digest_file(path) != row["hash"]:
            raise WorkflowError("file_identity_changed", status_code=409)
        identity = ResourceIdentity(project_id=project_id, file_id=file_id, source_sha256=row["hash"])
        return path, identity, row["name"]

    def catalog(self, project_id, offset=0, limit=50, run_id=None):
        self.store.project(project_id)
        snapshot = None
        allowed = None
        associations = {}
        if run_id:
            run = self.store.run(run_id)
            if run["project_id"] != project_id:
                raise WorkflowError("resource_run_project_mismatch", status_code=403)
            snapshot = run["snapshot_hash"]
            allowed = set()
            def visit(value, node_id, attempt, candidate=None):
                if isinstance(value, dict):
                    candidate = value.get("candidate_id", candidate)
                    for child in value.values():
                        visit(child, node_id, attempt, candidate)
                elif isinstance(value, list):
                    for child in value:
                        visit(child, node_id, attempt, candidate)
                elif isinstance(value, str) and value.startswith("asset:"):
                    file_id = value[6:]
                    allowed.add(file_id)
                    associations[file_id] = dict(run_id=run_id, snapshot_hash=snapshot, node_id=node_id, attempt=attempt, candidate_id=candidate)
            with self.store.connection() as db:
                nodes = db.execute("SELECT id,attempts,json_remove(output,'$.trajectories') AS output FROM nodes WHERE run_id=? AND output IS NOT NULL", (run_id,)).fetchall()
            for node in nodes:
                visit(self.boundary.tree(json.loads(node["output"]), project_id=project_id), node["id"], node["attempts"])
        with self.store.connection() as db:
            rows = db.execute("SELECT id,name FROM file_assets WHERE project_id=? ORDER BY rowid", (project_id,)).fetchall()
        if allowed is not None:
            rows = [row for row in rows if row["id"] in allowed]
        items = []
        for row in rows[offset:offset + limit]:
            path, identity, name = self.source(project_id, row["id"])
            identity = identity.model_copy(update=associations.get(row["id"], {}))
            common = dict(identity=identity, name=name, byte_count=path.stat().st_size)
            extension = path.suffix.lower()
            if extension in {".png", ".jpg", ".jpeg"}:
                items.append(ImageResource(**common, media_type="image/png" if extension == ".png" else "image/jpeg"))
            elif extension in {".pdb", ".cif", ".mmcif"}:
                items.append(StructureResource(**common, format="pdb" if extension == ".pdb" else "mmcif"))
            elif extension == ".json":
                try:
                    data = json.loads(path.read_bytes())
                except json.JSONDecodeError:
                    data = None
                if isinstance(data, dict) and isinstance(data.get("prediction_contract"), dict) and data["prediction_contract"].get("schema_version") == "m4-prediction-v2":
                    items.append(SeriesResource(**common))
                else:
                    items.append(TableResource(**common, media_type="application/json"))
            else:
                items.append(TableResource(**common, media_type="text/plain"))
        result = ResourcePage(project_id=project_id, run_id=run_id, snapshot_hash=snapshot, offset=offset, total=len(rows), has_more=offset + limit < len(rows), items=items).model_dump(mode="json")
        self.boundary.check(result)
        return result

    def series(self, project_id, file_id, offset, limit, series_id=None):
        path, identity, _ = self.source(project_id, file_id)
        key = (file_id, identity.source_sha256, "display-series-v1")
        with self.store.connection() as db:
            row = db.execute("SELECT payload FROM display_series_meta WHERE file_id=? AND hash=? AND schema=?", key).fetchone()
        if row is None:
            data = json.loads(path.read_bytes())
            contract = data.get("prediction_contract") if isinstance(data, dict) else None
            if not isinstance(contract, dict) or contract.get("schema_version") != "m4-prediction-v2":
                raise WorkflowError("unsupported_trajectory_contract")
            time = contract.get("time")
            concentrations = contract.get("concentrations")
            if not isinstance(time, list) or len(time) > MAX_POINTS or not isinstance(concentrations, dict):
                raise WorkflowError("invalid_trajectory_contract")
            columns = {}
            descriptors = []
            def finite(value):
                return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)
            if not all(finite(t) for t in time) or any(a >= b for a, b in zip(time, time[1:])):
                raise WorkflowError("invalid_trajectory_contract")
            for compartment, species in concentrations.items():
                if not isinstance(species, dict):
                    raise WorkflowError("invalid_trajectory_contract")
                for name, values in species.items():
                    if not isinstance(values, list) or len(values) != len(time) or not all(v is None or finite(v) for v in values):
                        raise WorkflowError("invalid_trajectory_contract")
                    identifier = str(len(columns))
                    columns[identifier] = values
                    descriptors.append(SeriesDescriptor(id=identifier, compartment=compartment, species=name, unit=contract["concentration_unit"]).model_dump())
            if len(columns) > MAX_SERIES:
                raise WorkflowError("display_source_budget_exceeded")
            meta = {key: contract[key] for key in ("schema_version", "model_kind", "formula_version", "time_unit")}
            meta.update(total=len(time), series=descriptors)
            self.boundary.check(meta)
            with self.store.connection() as db:
                db.execute("BEGIN IMMEDIATE")
                if not db.execute("SELECT 1 FROM display_series_meta WHERE file_id=? AND hash=? AND schema=?", key).fetchone():
                    db.executemany("INSERT INTO display_series_points VALUES(?,?,?,?,?,?)", ((*key, i, t, json.dumps({k: v[i] for k, v in columns.items()})) for i, t in enumerate(time)))
                    db.execute("INSERT INTO display_series_meta VALUES(?,?,?,?)", (*key, json.dumps(meta)))
        else:
            meta = json.loads(row[0])
        selected = [item for item in meta["series"] if series_id is None or item["id"] == series_id]
        if series_id is not None and not selected:
            raise WorkflowError("unknown_registered_series")
        with self.store.connection() as db:
            points = db.execute("SELECT time,values_json FROM display_series_points WHERE file_id=? AND hash=? AND schema=? AND ordinal>=? ORDER BY ordinal LIMIT ?", (*key, offset, limit)).fetchall()
        result = SeriesPage(identity=identity, result_schema_version=meta["schema_version"], model_kind=meta["model_kind"], formula_version=meta["formula_version"], time_unit=meta["time_unit"], offset=offset, total=meta["total"], has_more=offset + len(points) < meta["total"], time=[p[0] for p in points], series=selected, values={s["id"]: [json.loads(p[1])[s["id"]] for p in points] for s in selected}).model_dump(mode="json")
        self.boundary.check(result)
        return result

    def image(self, project_id, file_id):
        from PIL import Image
        path, _, _ = self.source(project_id, file_id)
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            raise WorkflowError("unsupported_image_format")
        try:
            with Image.open(path) as source:
                expected_format = "PNG" if path.suffix.lower() == ".png" else "JPEG"
                if source.format != expected_format:
                    raise WorkflowError("image_media_type_mismatch")
                if source.width * source.height > MAX_IMAGE_PIXELS or source.n_frames != 1:
                    raise WorkflowError("image_decode_budget_exceeded")
                # Decode within budget. Export pixels only: EXIF/text/ICC is not public.
                pixels = source.convert("RGBA")
                target = BytesIO()
                pixels.save(target, format="PNG")
                raw = target.getvalue()
        except WorkflowError:
            raise
        except Exception as exc:
            raise WorkflowError("invalid_image_source") from exc
        self.boundary.check_bytes(raw)
        return raw

    def structure(self, project_id, file_id, offset=0, limit=100, *, annotations=True):
        path, identity, _ = self.source(project_id, file_id)
        extension = path.suffix.lower()
        residues = {}
        lines = []
        if extension == ".pdb":
            model = "1"
            for line in path.read_text(encoding="utf-8").splitlines():
                tag = line[:6].strip()
                if tag == "MODEL":
                    model = line[10:14].strip() or "1"
                if tag in {"ATOM", "HETATM"}:
                    if len(line) < 54 or not all(math.isfinite(float(line[a:b])) for a, b in ((30, 38), (38, 46), (46, 54))):
                        raise WorkflowError("invalid_structure_source")
                    key = (model, line[21:22].strip(), line[22:26].strip(), line[26:27].strip())
                    residues[key] = ResidueIdentity(model=model, chain=key[1], residue_number=key[2], insertion_code=key[3], residue_name=line[17:20].strip()).model_dump()
                    lines.append(line[:80])
                elif tag in {"MODEL", "ENDMDL", "TER", "END"}:
                    lines.append(line[:80])
            preview = "\n".join(lines).encode()
            format_name = "pdb"
        elif extension in {".cif", ".mmcif"}:
            from Bio.PDB.MMCIF2Dict import MMCIF2Dict
            data = MMCIF2Dict(str(path))
            atom_fields = {
                "group_PDB", "id", "type_symbol", "label_atom_id", "label_alt_id",
                "label_comp_id", "label_asym_id", "label_entity_id", "label_seq_id",
                "pdbx_PDB_ins_code", "Cartn_x", "Cartn_y", "Cartn_z", "occupancy",
                "B_iso_or_equiv", "pdbx_formal_charge", "auth_seq_id", "auth_comp_id",
                "auth_asym_id", "auth_atom_id", "pdbx_PDB_model_num",
            }
            fields = [k for k in data if k.startswith("_atom_site.") and k[11:] in atom_fields]
            if not fields:
                raise WorkflowError("invalid_structure_source")
            count = len(data[fields[0]])
            if any(len(data[k]) != count for k in fields) or count > 200_000:
                raise WorkflowError("display_source_budget_exceeded")
            def at(name, index, fallback="?"):
                values = data.get("_atom_site." + name)
                return values[index] if values else fallback
            for i in range(count):
                model = at("pdbx_PDB_model_num", i, "1")
                chain = at("auth_asym_id", i, at("label_asym_id", i))
                number = at("auth_seq_id", i, at("label_seq_id", i))
                insertion = at("pdbx_PDB_ins_code", i)
                insertion = "" if insertion in {"?", "."} else insertion
                for coordinate in ("Cartn_x", "Cartn_y", "Cartn_z"):
                    if not math.isfinite(float(at(coordinate, i))):
                        raise WorkflowError("invalid_structure_source")
                key = (model, chain, number, insertion)
                residues[key] = ResidueIdentity(model=model, chain=chain, residue_number=number, insertion_code=insertion, residue_name=at("auth_comp_id", i, at("label_comp_id", i))).model_dump()
            def quote(value):
                if "\n" in value or "\r" in value or ("'" in value and '"' in value):
                    raise WorkflowError("invalid_structure_source")
                return '"' + value + '"' if "'" in value else "'" + value + "'"
            preview = ("data_display\nloop_\n" + "\n".join(fields) + "\n" + "\n".join(" ".join(quote(data[k][i]) for k in fields) for i in range(count)) + "\n#\n").encode()
            format_name = "mmcif"
        else:
            raise WorkflowError("unsupported_structure_format")
        if not residues or len(lines) > 200_000:
            raise WorkflowError("invalid_structure_source")
        self.boundary.check_bytes(preview)
        # Atom fields are not free-form REMARK/metadata. Reject private-path tokens.
        if re.search(rb"(?:[A-Za-z]:[\\/]|/(?:home|mnt|Users)/)", preview):
            raise WorkflowError("disclosure_quarantined", status_code=403)
        values = list(residues.values())
        meta = StructurePage(identity=identity, format=format_name, offset=offset, total=len(values), chains=sorted({r["chain"] for r in values}), models=list(dict.fromkeys(r["model"] for r in values)), residues=values[offset:offset + limit]).model_dump(mode="json")
        if not annotations:
            self.boundary.check(meta)
            return meta, preview
        with self.store.connection() as db:
            candidates = db.execute("SELECT id,hash,path FROM file_assets WHERE project_id=? AND name LIKE '%.json'", (project_id,)).fetchall()
            references = {r["hash"]: r["id"] for r in db.execute("SELECT id,hash FROM file_assets WHERE project_id=?", (project_id,))}
        reference_residues = {}
        found = []
        for candidate in candidates:
            candidate_path = Path(candidate["path"])
            if candidate_path.stat().st_size > MAX_SOURCE_BYTES:
                continue
            # A dedicated sidecar schema, never a guessed M2 JSON or B-factor.
            try:
                raw = json.loads(candidate_path.read_bytes())
            except json.JSONDecodeError:
                continue
            if not isinstance(raw, dict) or raw.get("schema_version") != "structure-display-annotations-v1" or raw.get("target_sha256") != identity.source_sha256:
                continue
            self.source(project_id, candidate["id"])
            annotation = StructureAnnotations.model_validate(raw)
            self.boundary.check(annotation.model_dump(mode="json"))
            fusion_sequence = None
            if any(r.full_fusion_position is not None for r in annotation.rows):
                from Bio import SeqIO
                sequence_file_id = references.get(annotation.fusion_sequence_file_sha256)
                if not sequence_file_id or not annotation.fusion_sequence_id:
                    raise WorkflowError("structure_sequence_mapping_not_authorized", status_code=403)
                sequence_path, _, _ = self.source(project_id, sequence_file_id)
                matching = [str(r.seq).upper() for r in SeqIO.parse(sequence_path, "fasta") if r.id == annotation.fusion_sequence_id]
                if len(matching) != 1:
                    raise WorkflowError("structure_sequence_mapping_identity_mismatch")
                fusion_sequence = matching[0]
            seen = set()
            for entry in annotation.rows:
                residue = entry.residue
                key = (residue.model, residue.chain, residue.residue_number, residue.insertion_code)
                if key in seen or key not in residues or residues[key]["residue_name"] != residue.residue_name:
                    raise WorkflowError("structure_annotation_identity_mismatch")
                seen.add(key)
                if entry.full_fusion_position is not None:
                    from Bio.Data.IUPACData import protein_letters_3to1
                    position = entry.full_fusion_position - 1
                    amino_acid = protein_letters_3to1.get(residue.residue_name.title())
                    if position >= len(fusion_sequence) or amino_acid is None or fusion_sequence[position] != amino_acid:
                        raise WorkflowError("structure_sequence_mapping_identity_mismatch")
                if entry.plddt is not None and (annotation.confidence_semantics != "plddt" or not annotation.source_tool or not annotation.source_tool_version):
                    raise WorkflowError("structure_confidence_semantics_missing")
                if entry.reference_residue is not None:
                    reference_id = references.get(entry.reference_sha256)
                    if reference_id is None:
                        raise WorkflowError("structure_reference_not_authorized", status_code=403)
                    if reference_id not in reference_residues:
                        reference_meta, _ = self.structure(project_id, reference_id, limit=200_000, annotations=False)
                        reference_residues[reference_id] = reference_meta["residues"]
                    if entry.reference_residue.model_dump() not in reference_residues[reference_id]:
                        raise WorkflowError("structure_annotation_identity_mismatch")
            found.append((candidate, annotation))
        if len(found) > 1:
            raise WorkflowError("ambiguous_structure_annotations")
        if found:
            candidate, annotation = found[0]
            paged = {tuple(r[k] for k in ("model", "chain", "residue_number", "insertion_code")) for r in meta["residues"]}
            meta.update(annotation_file_id=candidate["id"], annotation_sha256=candidate["hash"], annotation_source_reference=annotation.source_reference,
                fusion_sequence_file_id=references.get(annotation.fusion_sequence_file_sha256) if fusion_sequence is not None else None,
                fusion_sequence_file_sha256=annotation.fusion_sequence_file_sha256 if fusion_sequence is not None else None,
                fusion_sequence_id=annotation.fusion_sequence_id if fusion_sequence is not None else None,
                annotation_source_tool=annotation.source_tool, annotation_source_tool_version=annotation.source_tool_version,
                annotations=[{**r.model_dump(mode="json"), "reference_file_id":references.get(r.reference_sha256) if r.reference_residue else None} for r in annotation.rows if tuple(getattr(r.residue, k) for k in ("model", "chain", "residue_number", "insertion_code")) in paged])
            registered = "source_registered_not_scientific_approval"
            if any(r.plddt is not None for r in annotation.rows):
                meta["confidence_status"] = registered
            if any(r.full_fusion_position is not None or r.reference_residue is not None or r.region is not None for r in annotation.rows):
                meta["mapping_status"] = registered
            if any(r.pocket for r in annotation.rows):
                meta["pocket_status"] = registered
        self.boundary.check(meta)
        return meta, preview
