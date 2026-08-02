"""Parsers for outputs produced by external scientific tools."""

from .freesasa import FreeSasaResidueArea, PocketSasaResult, compute_pocket_sasa_retention
from .calvados import CalvadosResult, parse_calvados_output
from .structure_prediction import StructurePredictionSummary, parse_structure_prediction_output
from .vina import VinaPose, VinaResult, parse_vina_output

__all__ = [
    "CalvadosResult",
    "FreeSasaResidueArea",
    "PocketSasaResult",
    "StructurePredictionSummary",
    "VinaPose",
    "VinaResult",
    "compute_pocket_sasa_retention",
    "parse_calvados_output",
    "parse_structure_prediction_output",
    "parse_vina_output",
]
