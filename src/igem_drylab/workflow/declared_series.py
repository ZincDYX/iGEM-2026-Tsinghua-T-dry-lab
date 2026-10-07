"""Declared CSV/NPZ display columns, never guessed scientific semantics."""
import csv
import math
from typing import Literal
from zipfile import ZipFile

from pydantic import Field
from .models import Contract, WorkflowError


class DeclaredColumn(Contract):
    key: str = Field(min_length=1)
    compartment: str = Field(min_length=1)
    species: str = Field(min_length=1)
    unit: str = Field(min_length=1)


class DeclaredSeries(Contract):
    schema_version: Literal["display-series-source-v1"]
    target_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_reference: str = Field(min_length=1)
    format: Literal["csv", "tsv", "npz"]
    time_key: str = Field(min_length=1)
    time_unit: str = Field(min_length=1)
    missing_token: Literal["", "nan"]
    columns: list[DeclaredColumn] = Field(min_length=1, max_length=128)


def target(resources, project_id, declaration):
    with resources.store.connection() as db:
        row = db.execute("SELECT id FROM file_assets WHERE project_id=? AND hash=? ORDER BY rowid LIMIT 1",
                         (project_id, declaration.target_sha256)).fetchone()
    if row is None:
        raise WorkflowError("declared_series_target_not_granted", status_code=403)
    path, identity, _ = resources.source(project_id, row["id"])
    if path.suffix.lower() != "."+declaration.format:
        raise WorkflowError("declared_series_format_mismatch")
    return path, identity


def read_columns(path, declaration):
    """Bound bytes before loading compressed arrays; no pickle or conversion."""
    keys = [declaration.time_key, *(c.key for c in declaration.columns)]
    if len(set(keys)) != len(keys):
        raise WorkflowError("declared_series_duplicate_column")
    if declaration.format in {"csv", "tsv"}:
        if declaration.missing_token != "":
            raise WorkflowError("csv_requires_explicit_empty_missing_token")
        with path.open(encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source, delimiter="\t" if declaration.format == "tsv" else ",")
            if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames) or not set(keys).issubset(reader.fieldnames):
                raise WorkflowError("declared_series_column_missing_or_duplicate")
            columns = {k: [] for k in keys}
            for index, row in enumerate(reader):
                if index >= 100_000 or None in row:
                    raise WorkflowError("declared_series_row_budget_or_shape_invalid")
                for key in keys:
                    value = row[key]
                    if value is None:
                        raise WorkflowError("declared_series_row_shape_invalid")
                    columns[key].append(None if value == "" else float(value))
    else:
        import numpy as np
        if declaration.missing_token != "nan":
            raise WorkflowError("npz_requires_explicit_nan_missing_token")
        with ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) > 129 or sum(m.file_size for m in members) > 20_000_000 or len({m.filename for m in members}) != len(members):
                raise WorkflowError("declared_series_expansion_budget_exceeded")
            for key in keys:
                if key+".npy" not in archive.namelist():
                    raise WorkflowError("declared_series_column_missing_or_duplicate")
                member = archive.getinfo(key+".npy")
                with archive.open(member) as stream:
                    version = np.lib.format.read_magic(stream)
                    if version not in {(1, 0), (2, 0)}:
                        raise WorkflowError("declared_series_npy_header_version_unsupported")
                    read_header = np.lib.format.read_array_header_1_0 if version == (1, 0) else np.lib.format.read_array_header_2_0
                    shape, _, dtype = read_header(stream, max_header_size=10_000)
                    if len(shape) != 1 or shape[0] > 100_000 or dtype.kind not in "iuf" or member.file_size-stream.tell() != shape[0]*dtype.itemsize:
                        raise WorkflowError("declared_series_numeric_vector_required")
        columns = {}
        with np.load(path, allow_pickle=False, max_header_size=10_000) as arrays:
            for key in keys:
                if key not in arrays.files:
                    raise WorkflowError("declared_series_column_missing_or_duplicate")
                value = arrays[key]
                if value.ndim != 1 or len(value) > 100_000 or value.dtype.kind not in "iuf":
                    raise WorkflowError("declared_series_numeric_vector_required")
                columns[key] = [None if np.isnan(v) else float(v) for v in value]
    time = columns.pop(declaration.time_key)
    if any(t is None for t in time) or any(len(v) != len(time) for v in columns.values()):
        raise WorkflowError("declared_series_lengths_or_time_invalid")
    if not time or not all(math.isfinite(t) for t in time) or any(a >= b for a, b in zip(time, time[1:])):
        raise WorkflowError("invalid_trajectory_contract")
    if any(not math.isfinite(v) for values in columns.values() for v in values if v is not None):
        raise WorkflowError("invalid_trajectory_contract")
    contract = dict(schema_version=declaration.schema_version,
                    model_kind="registered_source_not_prediction",
                    formula_version="not_applicable_no_recalculation", time_unit=declaration.time_unit,
                    time=time, concentrations={})
    # Preserve each declared key as a separate series; do not merge same-name species.
    for column in declaration.columns:
        contract["concentrations"].setdefault(column.compartment, {})[column.key] = columns[column.key]
    return contract
