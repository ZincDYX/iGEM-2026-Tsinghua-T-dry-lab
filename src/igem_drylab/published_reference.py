"""Adapter for the immutable uploaded glabridin publication model.

The author files under :mod:`published_reference/author_uploaded` are never
edited.  This adapter imports the author's reaction RHS directly, parses the
author-native text inputs without unit conversion, and writes reproducible
author-native trajectories separately from the Galatea production kernel.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import numpy as np


@dataclass(frozen=True)
class PublishedReferenceResult:
    time: np.ndarray
    state: np.ndarray
    source_sha256: str


def _author_paths(root: Path) -> tuple[Path, Path]:
    base = root / "published_reference" / "author_uploaded"
    return base / "simulation-network-glabridin-final.py", base / "simulation-data.txt"


def _safe_expression(value: str) -> float:
    node = ast.parse(value, mode="eval").body
    def evaluate(item: ast.AST) -> float:
        if isinstance(item, ast.Constant) and isinstance(item.value, (int, float)):
            return float(item.value)
        if isinstance(item, ast.BinOp) and isinstance(item.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            left, right = evaluate(item.left), evaluate(item.right)
            return {ast.Add: left + right, ast.Sub: left - right, ast.Mult: left * right, ast.Div: left / right}[type(item.op)]
        raise ValueError("author_data_contains_unsupported_expression")
    return evaluate(node)


def load_author_native_parameters(data_path: Path) -> dict[str, float]:
    values: dict[str, float] = {}
    for raw_line in data_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("|", 1)[0].strip()
        if "=" not in line:
            continue
        name, value = (part.strip() for part in line.split("=", 1))
        if name:
            values[name] = _safe_expression(value)
    return values


def _load_author_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("galatea_uploaded_author_reference", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable_to_import_uploaded_author_reference")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_published_reference(repository_root: Path, *, points: int = 1000) -> PublishedReferenceResult:
    from scipy.integrate import solve_ivp
    """Execute the uploaded author's RHS with author-native values and LSODA."""
    code_path, data_path = _author_paths(repository_root)
    if not code_path.exists() or not data_path.exists():
        raise FileNotFoundError("immutable_author_reference_files_missing")
    values = load_author_native_parameters(data_path)
    module = _load_author_module(code_path)
    kcat_over_km = [values[f"kcat{index}dkm{index}"] for index in range(1, 11)]
    km = [values[f"km{index}"] for index in range(1, 11)]
    kcat = [first * second for first, second in zip(kcat_over_km, km, strict=True)]
    outside_ratio = [values[f"K{index}"] for index in range(8, 16)]
    rate = values["rate"]
    params = {
        "kcat": kcat,
        "Km": km,
        "disable_times": {index: values["time_ratio"] * values["total_time"] for index in range(4, 8)},
        "K_out": [(ratio * rate / (ratio + 1.0), rate / (ratio + 1.0)) for ratio in outside_ratio],
        "E": values["E"],
    }
    initial = np.asarray([7.4e-5] + [0.0] * 15, dtype=float)
    time = np.linspace(0.0, values["total_time"], points)
    solved = solve_ivp(module.reaction_kinetics, (0.0, values["total_time"]), initial, args=(params,), t_eval=time, method="LSODA")
    if not solved.success:
        raise RuntimeError(solved.message)
    return PublishedReferenceResult(solved.t, solved.y, hashlib.sha256(code_path.read_bytes()).hexdigest())


def write_published_reference_reproduction(repository_root: Path, output: Path) -> Path:
    """Write author-native trajectory without asserting unverified physical units."""
    result = run_published_reference(repository_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time_author_native", *[f"intracellular_{index}" for index in range(8, 16)], *[f"extracellular_{index}" for index in range(8, 16)]])
        for row in zip(result.time, *result.state, strict=True):
            writer.writerow(row)
    return output
