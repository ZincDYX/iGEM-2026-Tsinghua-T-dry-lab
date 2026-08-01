from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class ProteinChain(BaseModel):
    chain_id: str = Field(min_length=1, max_length=8)
    name: str
    sequence: str = Field(min_length=1)
    copies: int = Field(default=1, ge=1)
    role: str = ""


class MultichainInputResult(BaseModel):
    complex_id: str
    output_dir: Path
    fasta_file: Path
    manifest_file: Path
    chains: list[ProteinChain]


class BindingEquilibriumResult(BaseModel):
    ligand: str
    receptor: str
    kd: float = Field(gt=0)
    receptor_total: float = Field(ge=0)
    ligand_total: float = Field(ge=0)
    receptor_valency: int = Field(ge=1)
    ligand_valency: int = Field(ge=1)
    receptor_site_total: float = Field(ge=0)
    ligand_site_total: float = Field(ge=0)
    bound_site_concentration: float = Field(ge=0)
    receptor_site_occupancy: float = Field(ge=0, le=1)
    ligand_site_occupancy: float = Field(ge=0, le=1)
    limiting_component: str


class AtomRecord(BaseModel):
    chain_id: str
    residue_id: int
    residue_name: str
    atom_name: str
    x: float
    y: float
    z: float


class InterfaceAssessment(BaseModel):
    pdb_file: Path
    chain_a: str
    chain_b: str
    atom_count_a: int
    atom_count_b: int
    contact_cutoff_angstrom: float
    clash_cutoff_angstrom: float
    interface_contact_count: int
    clash_count: int
    min_distance_angstrom: float | None
    unique_contact_residues_a: int
    unique_contact_residues_b: int
    assessment: str
