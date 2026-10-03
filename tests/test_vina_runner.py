from __future__ import annotations

from pathlib import Path

import pytest

from igem_drylab.vina_runner import run_vina


def test_vina_runner_validates_box_before_importing_optional_engine(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="exactly_three"):
        run_vina(
            receptor=tmp_path / "receptor.pdbqt",
            ligand=tmp_path / "ligand.pdbqt",
            output=tmp_path / "poses.pdbqt",
            summary=tmp_path / "summary.json",
            center=[1.0, 2.0],
            size=[20.0, 20.0, 20.0],
            exhaustiveness=1,
            num_modes=1,
            seed=17,
        )
