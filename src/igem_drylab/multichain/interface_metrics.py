from __future__ import annotations

import math
from pathlib import Path

from .models import AtomRecord, InterfaceAssessment


def assess_interface(
    *,
    pdb_file: Path,
    chain_a: str,
    chain_b: str,
    contact_cutoff_angstrom: float = 5.0,
    clash_cutoff_angstrom: float = 2.0,
) -> InterfaceAssessment:
    if contact_cutoff_angstrom <= 0 or clash_cutoff_angstrom <= 0:
        raise ValueError("Distance cutoffs must be positive")
    atoms = read_pdb_atoms(pdb_file)
    atoms_a = [atom for atom in atoms if atom.chain_id == chain_a]
    atoms_b = [atom for atom in atoms if atom.chain_id == chain_b]
    if not atoms_a:
        raise ValueError(f"No atoms found for chain '{chain_a}'")
    if not atoms_b:
        raise ValueError(f"No atoms found for chain '{chain_b}'")

    contact_count = 0
    clash_count = 0
    min_distance: float | None = None
    residues_a: set[int] = set()
    residues_b: set[int] = set()
    for atom_a in atoms_a:
        for atom_b in atoms_b:
            distance = _distance(atom_a, atom_b)
            min_distance = distance if min_distance is None else min(min_distance, distance)
            if distance <= contact_cutoff_angstrom:
                contact_count += 1
                residues_a.add(atom_a.residue_id)
                residues_b.add(atom_b.residue_id)
            if distance <= clash_cutoff_angstrom:
                clash_count += 1

    return InterfaceAssessment(
        pdb_file=pdb_file,
        chain_a=chain_a,
        chain_b=chain_b,
        atom_count_a=len(atoms_a),
        atom_count_b=len(atoms_b),
        contact_cutoff_angstrom=contact_cutoff_angstrom,
        clash_cutoff_angstrom=clash_cutoff_angstrom,
        interface_contact_count=contact_count,
        clash_count=clash_count,
        min_distance_angstrom=round(min_distance, 3) if min_distance is not None else None,
        unique_contact_residues_a=len(residues_a),
        unique_contact_residues_b=len(residues_b),
        assessment=_classify_interface(contact_count, clash_count),
    )


def read_pdb_atoms(path: Path) -> list[AtomRecord]:
    atoms: list[AtomRecord] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.startswith(("ATOM  ", "HETATM")):
            continue
        try:
            atoms.append(
                AtomRecord(
                    atom_name=line[12:16].strip(),
                    residue_name=line[17:20].strip(),
                    chain_id=line[21].strip(),
                    residue_id=int(line[22:26]),
                    x=float(line[30:38]),
                    y=float(line[38:46]),
                    z=float(line[46:54]),
                )
            )
        except ValueError:
            continue
    return atoms


def _distance(atom_a: AtomRecord, atom_b: AtomRecord) -> float:
    return math.sqrt((atom_a.x - atom_b.x) ** 2 + (atom_a.y - atom_b.y) ** 2 + (atom_a.z - atom_b.z) ** 2)


def _classify_interface(contact_count: int, clash_count: int) -> str:
    if clash_count > 0:
        return "clashing"
    if contact_count >= 20:
        return "well_contacted"
    if contact_count > 0:
        return "weak_contact"
    return "separated"
