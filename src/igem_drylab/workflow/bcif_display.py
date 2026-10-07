"""Atom-column decoding for display, not a structure/scientific calculation.

Reuse Python-IHM 2.11's codecs. The small bounded wrapper prevents a compressed
column from allocating an unbounded expanded array. Keep the binary original.
"""
from itertools import islice
import struct

from .models import WorkflowError

ATOM_FIELDS = {
    "group_PDB", "id", "type_symbol", "label_atom_id", "label_alt_id",
    "label_comp_id", "label_asym_id", "label_entity_id", "label_seq_id",
    "pdbx_PDB_ins_code", "Cartn_x", "Cartn_y", "Cartn_z", "occupancy",
    "B_iso_or_equiv", "pdbx_formal_charge", "auth_seq_id", "auth_comp_id",
    "auth_asym_id", "auth_atom_id", "pdbx_PDB_model_num",
}


def _decode(data, encodings, limit):
    from ihm.format_bcif import _decoder_map  # Version-pinned codec interface.
    for encoding in reversed(encodings):
        kind = encoding["kind"]
        if kind == "StringArray":
            if any(e["kind"] == "StringArray" for e in [*encoding["offsetEncoding"], *encoding["dataEncoding"]]):
                raise ValueError("nested_string_encoding")
            offsets = _decode(encoding["offsets"], encoding["offsetEncoding"], limit + 1)
            indices = _decode(data, encoding["dataEncoding"], limit)
            text = encoding["stringData"]
            if not offsets or any(not 0 <= a <= b <= len(text) for a, b in zip(offsets, offsets[1:])):
                raise ValueError("invalid_string_offsets")
            strings = [text[a:b] for a, b in zip(offsets, offsets[1:])]
            if any(i < -1 or i >= len(strings) for i in indices):
                raise ValueError("invalid_string_index")
            data = [None if i == -1 else strings[i] for i in indices]
        else:
            if kind == "ByteArray":
                width = {1: 1, 2: 2, 3: 4, 4: 1, 5: 2, 6: 4, 32: 4, 33: 8}[encoding["type"]]
                if len(data) > limit * width:
                    raise WorkflowError("display_source_budget_exceeded")
            data = list(islice(_decoder_map[kind](encoding, data), limit + 1))
        if len(data) > limit:
            raise WorkflowError("display_source_budget_exceeded")
    return data


def binary_atom_columns(path, max_atoms):
    """Return only original decoded atom columns in the existing mmCIF shape."""
    import msgpack
    try:
        frame = msgpack.unpackb(path.read_bytes(), raw=False, max_array_len=2 * max_atoms + 1)
        blocks = frame["dataBlocks"]
        if len(blocks) != 1:
            raise ValueError("ambiguous_structure_blocks")
        categories = [c for c in blocks[0]["categories"] if c["name"] == "_atom_site"]
        if len(categories) != 1:
            raise ValueError("missing_or_ambiguous_atom_site")
        category = categories[0]
        count = category["rowCount"]
        if type(count) is not int or count < 1:
            raise ValueError("invalid_atom_count")
        if count > max_atoms:
            raise WorkflowError("display_source_budget_exceeded")
        result = {}
        for column in category["columns"]:
            name = column["name"]
            if name not in ATOM_FIELDS:
                continue
            if "_atom_site." + name in result:
                raise ValueError("duplicate_atom_column")
            values = _decode(column["data"]["data"], column["data"]["encoding"], 2 * count + 1)
            mask = column.get("mask")
            mask = _decode(mask["data"], mask["encoding"], 2 * count + 1) if mask else [0] * count
            if len(values) != count or len(mask) != count or any(m not in {0, 1, 2} for m in mask):
                raise ValueError("atom_column_length_or_mask")
            if any(v is None and m == 0 for v, m in zip(values, mask)):
                raise ValueError("unmasked_missing_value")
            result["_atom_site." + name] = [
                "." if m == 1 else "?" if m == 2 else str(v) for v, m in zip(values, mask)
            ]
        return result
    except WorkflowError:
        raise
    except (ValueError, TypeError, KeyError, IndexError, OverflowError, ZeroDivisionError, struct.error) as exc:
        raise WorkflowError("invalid_structure_source") from exc
