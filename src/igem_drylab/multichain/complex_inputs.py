from __future__ import annotations

import re
from pathlib import Path

from .models import MultichainInputResult, ProteinChain


def build_multichain_input(
    *,
    complex_id: str,
    chains: list[ProteinChain],
    output_dir: Path,
) -> MultichainInputResult:
    if not chains:
        raise ValueError("At least one chain is required")
    output_dir.mkdir(parents=True, exist_ok=True)
    _validate_unique_chain_ids(chains)

    fasta_file = output_dir / f"{complex_id}.fasta"
    manifest_file = output_dir / f"{complex_id}.multichain_manifest.json"
    fasta_file.write_text(_render_multifasta(chains), encoding="utf-8")
    result = MultichainInputResult(
        complex_id=complex_id,
        output_dir=output_dir,
        fasta_file=fasta_file,
        manifest_file=manifest_file,
        chains=chains,
    )
    manifest_file.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return result


def _validate_unique_chain_ids(chains: list[ProteinChain]) -> None:
    chain_ids = [chain.chain_id for chain in chains]
    if len(chain_ids) != len(set(chain_ids)):
        raise ValueError("Chain IDs must be unique")
    for chain in chains:
        if not re.fullmatch(r"[A-Za-z0-9_]+", chain.chain_id):
            raise ValueError(f"Invalid chain_id '{chain.chain_id}'")
        sequence = chain.sequence.replace("*", "")
        if not re.fullmatch(r"[A-Za-z]+", sequence):
            raise ValueError(f"Sequence for chain '{chain.chain_id}' contains non-letter characters")


def _render_multifasta(chains: list[ProteinChain]) -> str:
    records: list[str] = []
    for chain in chains:
        sequence = re.sub(r"\s+", "", chain.sequence).upper()
        for copy_index in range(1, chain.copies + 1):
            suffix = f"_copy{copy_index}" if chain.copies > 1 else ""
            header = f">{chain.chain_id}{suffix} name={chain.name} role={chain.role}".strip()
            records.append(header)
            records.extend(sequence[i : i + 80] for i in range(0, len(sequence), 80))
    return "\n".join(records) + "\n"
