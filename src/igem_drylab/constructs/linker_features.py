"""Transparent linker feature extraction; this is not an LLPS predictor."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import log2

HYDROPHOBIC = frozenset("AVILMFWY")
CHARGED = frozenset("DEKRH")


@dataclass(frozen=True)
class LinkerFeatures:
    length: int
    gly_ser_fraction: float
    hydrophobic_fraction: float
    net_charge_proxy: int
    charged_fraction: float
    pro_fraction: float
    sequence_complexity: float
    forbidden_motifs: tuple[str, ...]
    aggregation_risk_flag: bool

    def as_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def assess_linker(sequence: str, *, forbidden_motifs: tuple[str, ...] = ()) -> LinkerFeatures:
    """Describe explicit sequence properties without inferring condensate formation.

    The aggregation flag is a conservative sequence warning: a hydrophobic
    fraction >=0.45 or a run of five hydrophobic residues. It is a project
    engineering screen, not a biophysical aggregation prediction.
    """
    normalized = sequence.strip().upper()
    if not normalized or any(residue not in "ACDEFGHIKLMNPQRSTVWY" for residue in normalized):
        raise ValueError("linker sequence must contain only standard amino-acid letters")
    length = len(normalized)
    counts = Counter(normalized)
    hydrophobic_fraction = sum(counts[item] for item in HYDROPHOBIC) / length
    charged_fraction = sum(counts[item] for item in CHARGED) / length
    net_charge = counts["K"] + counts["R"] + counts["H"] - counts["D"] - counts["E"]
    complexity = -sum((count / length) * log2(count / length) for count in counts.values())
    found = tuple(motif for motif in forbidden_motifs if motif and motif.upper() in normalized)
    long_hydrophobic_run = any(all(residue in HYDROPHOBIC for residue in normalized[index:index + 5]) for index in range(max(0, length - 4)))
    return LinkerFeatures(
        length=length,
        gly_ser_fraction=(counts["G"] + counts["S"]) / length,
        hydrophobic_fraction=hydrophobic_fraction,
        net_charge_proxy=net_charge,
        charged_fraction=charged_fraction,
        pro_fraction=counts["P"] / length,
        sequence_complexity=complexity,
        forbidden_motifs=found,
        aggregation_risk_flag=hydrophobic_fraction >= 0.45 or long_hydrophobic_run,
    )
