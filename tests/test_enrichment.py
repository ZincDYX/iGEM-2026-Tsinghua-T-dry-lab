from pathlib import Path

import pytest

from igem_drylab.enrichment import EnrichmentInput, RecruitmentInput, calculate_enrichment, calculate_recruitment
from igem_drylab.pipeline import load_config
from igem_drylab.pipeline.stages import run_m1, run_m2, run_m3
from igem_drylab.parameters import ParameterRecord


def test_phase_concentration_mass_conservation():
    result = calculate_enrichment(EnrichmentInput(species_id="OC", total_concentration=8.0, partition_coefficient=20.0, partition_source="wet lab"), phi=0.1)
    assert pytest.approx(8.0) == 0.1 * result.dense_concentration + 0.9 * result.dilute_concentration


def test_fraction_dense_bounds_and_partition_one():
    result = calculate_enrichment(EnrichmentInput(species_id="DMT", total_concentration=5.0, partition_coefficient=1.0, partition_source="assumption"), phi=0.2)
    assert result.dense_concentration == result.dilute_concentration == 5.0
    assert result.fraction_in_dense == pytest.approx(0.2)


def test_finite_site_and_hill_recruitment_require_explicit_inputs():
    independent = calculate_recruitment(RecruitmentInput(enzyme_id="OC", enzyme_total=5, site_total=3, kd=1))
    hill = calculate_recruitment(RecruitmentInput(enzyme_id="DMT", enzyme_total=5, site_total=3, kd=1, binding_model="hill", hill_coefficient=2))
    assert 0 <= independent.recruited_fraction <= 1
    assert 0 <= hill.site_occupancy <= 1


def test_m3_uses_independent_oc_and_dmt_partition_inputs(tmp_path):
    config = load_config(Path("configs/m1_m4_real_scoring_example.yaml"))
    config.execution.allow_assumptions = True
    config.parameters = [ParameterRecord(parameter_id=name, name=name, value=value, unit="uM", source_type="assumption", source_reference="synthetic test", review_status="approved") for name, value in {
        "phi": 0.1, **{f"x{species}_total": 10.0 for species in ("9", "10", "11", "13", "15")},
        "pt_total": 1.0, "oc_total": 2.0, "dmt_total": 3.0,
        **{f"partition_x{species}": 1.0 for species in ("9", "10", "11", "13", "15")},
        "partition_pt": 1.0, "partition_oc": 20.0, "partition_dmt": 2.0,
    }.items()]
    candidates, _ = run_m1(config, tmp_path)
    m2, _ = run_m2(config, tmp_path, candidates)
    records, _ = run_m3(config, tmp_path, m2)
    assert records[0].status == "valid"
    assert records[0].concentrations["OC"]["partition_coefficient"] == 20.0
    assert records[0].concentrations["DMT"]["partition_coefficient"] == 2.0
