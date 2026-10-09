from __future__ import annotations

from pathlib import Path
import json
from types import SimpleNamespace

import numpy as np
import pytest

from igem_drylab.full_network import (
    COMPOUNDS, ENZYME_SUBSTRATES, FullNetworkParameters, PhaseDistribution,
    ReactionKinetics, TemporalGate, TransportParameters, effective_ratio_recruitment,
    phase_partition, simulate_full_network,
)
from igem_drylab.galatea_m3_m4 import M3EffectiveRatioInputs, load_author_native_reactions, run_galatea_full_m4, run_m3_effective_ratio
from igem_drylab.published_reference import run_published_reference, write_published_reference_reproduction
from igem_drylab.pipeline.config import AuthorNativeEnzymeScales, FullNetworkInitialStateConfig, InductionGateConfig, M4Config, load_config
from igem_drylab.pipeline.models import M3ConcentrationAssessment, M4CandidateContext
from igem_drylab.pipeline.stages import _full_network_reactions, _full_network_units, run_m4
from igem_drylab.parameters.requirements import requirements_for_stage


def reactions() -> tuple[ReactionKinetics, ...]:
    definitions = (
        ("R1", "PTR", "8", "9"), ("R2", "PT", "9", "10"), ("R3", "OC", "10", "11"),
        ("R4", "DMT", "8", "12"), ("R5", "DMT", "9", "13"), ("R6", "DMT", "10", "14"),
        ("R7", "DMT", "11", "15"), ("R8", "PTR", "12", "13"), ("R9", "PT", "13", "14"),
        ("R10", "OC", "14", "15"),
    )
    return tuple(ReactionKinetics(*item, kcat=1.0, km=1.0) for item in definitions)


def full_params(phi: float = 0.2) -> FullNetworkParameters:
    return FullNetworkParameters(
        phi=phi,
        enzyme_distributions={enzyme: PhaseDistribution(1.0, 1.0) for enzyme in ENZYME_SUBSTRATES},
        metabolite_kp={compound: 1.0 for compound in COMPOUNDS},
        reactions=reactions(),
        scenario="homogeneous_constitutive" if phi == 0 else "galatea_spatial",
    )


def initial() -> dict[str, float]:
    return {compound: 10.0 if compound == "8" else 0.0 for compound in COMPOUNDS}


def test_phase_partition_conserves_mass_and_kp_one_is_homogeneous() -> None:
    result = phase_partition(4.0, 3.0, 0.2)
    assert np.isclose(result.cell_average(0.2), 4.0)
    neutral = phase_partition(4.0, 1.0, 0.2)
    assert neutral.dense == neutral.dilute == 4.0
    assert phase_partition(4.0, 8.0, 0.0) == PhaseDistribution(0.0, 4.0)


def test_effective_ratio_recruitment_conserves_enzyme_and_caps() -> None:
    result = effective_ratio_recruitment(
        oc_total=1.0, dmt_total=9.0, phi=0.1, slot_ratio_sh3_to_pdz=20.0,
        total_recruited_fraction=0.9,
    )
    assert np.isclose(result.oc.cell_average(0.1), 1.0)
    assert np.isclose(result.dmt.cell_average(0.1), 9.0)
    assert result.oc_bound <= 1.0 and result.dmt_bound <= 9.0
    with pytest.raises(ValueError, match="invalid_effective"):
        effective_ratio_recruitment(oc_total=1, dmt_total=1, phi=1, slot_ratio_sh3_to_pdz=1, total_recruited_fraction=.5)


def test_slot_ratio_increases_dense_oc_dmt_ratio_before_caps() -> None:
    kp = {compound: 1.0 for compound in COMPOUNDS}
    low = run_m3_effective_ratio(M3EffectiveRatioInputs(phi=0.1, oc_total=10, dmt_total=10, slot_ratio_sh3_to_pdz=1, total_recruited_fraction=.4, metabolite_kp=kp))
    high = run_m3_effective_ratio(M3EffectiveRatioInputs(phi=0.1, oc_total=10, dmt_total=10, slot_ratio_sh3_to_pdz=3, total_recruited_fraction=.4, metabolite_kp=kp))
    assert high.enzyme_distributions["OC"].dense / high.enzyme_distributions["DMT"].dense > low.enzyme_distributions["OC"].dense / low.enzyme_distributions["DMT"].dense


def test_m3_effective_ratio_distribution_is_consumed_by_full_m4() -> None:
    kp = {compound: 1.0 for compound in COMPOUNDS}
    m3 = run_m3_effective_ratio(M3EffectiveRatioInputs(phi=.1, ptr_total=1, pt_total=1, oc_total=2, dmt_total=2, slot_ratio_sh3_to_pdz=3, total_recruited_fraction=.5, metabolite_kp=kp))
    result = run_galatea_full_m4(
        enzyme_distributions=m3.enzyme_distributions, phi=.1, metabolite_kp=m3.metabolite_kp,
        reactions=reactions(), initial_intracellular=initial(), t_end=.5,
    )
    assert result.diagnostics["mass_balance_error"] < 1e-7


def test_full_network_mass_balance_nonnegative_and_flux_competition() -> None:
    result = simulate_full_network(full_params(), initial_intracellular=initial(), t_end=5.0)
    assert result.diagnostics["mass_balance_error"] < 1e-7
    assert np.all(result.intracellular >= 0) and np.all(result.extracellular >= 0)
    # Raising substrate 9 at fixed DMT pool must not raise R7 (11 -> 15) at a fixed state.
    from igem_drylab.full_network import phase_competitive_rates
    base = phase_competitive_rates({"8": 0, "9": 0, "10": 0, "11": 1, "12": 0, "13": 0, "14": 0, "15": 0}, {enzyme: 1 for enzyme in ENZYME_SUBSTRATES}, reactions(), {enzyme: 1 for enzyme in ENZYME_SUBSTRATES}, 1)["R7"]
    competitor = phase_competitive_rates({"8": 0, "9": 10, "10": 0, "11": 1, "12": 0, "13": 0, "14": 0, "15": 0}, {enzyme: 1 for enzyme in ENZYME_SUBSTRATES}, reactions(), {enzyme: 1 for enzyme in ENZYME_SUBSTRATES}, 1)["R7"]
    assert competitor < base


def test_each_enzyme_uses_one_competing_pool() -> None:
    from igem_drylab.full_network import phase_competitive_rates
    enzymes = {enzyme: 1.0 for enzyme in ENZYME_SUBSTRATES}
    activity = {enzyme: 1.0 for enzyme in ENZYME_SUBSTRATES}
    zeros = {compound: 0.0 for compound in COMPOUNDS}
    for reaction_id, primary, alternative in (("R1", "8", "12"), ("R2", "9", "13"), ("R3", "10", "14")):
        only_primary = {**zeros, primary: 1.0}
        with_alternative = {**only_primary, alternative: 10.0}
        assert phase_competitive_rates(with_alternative, enzymes, reactions(), activity, 1.0)[reaction_id] < phase_competitive_rates(only_primary, enzymes, reactions(), activity, 1.0)[reaction_id]


def test_full_kernel_exposes_no_structure_or_docking_activity_input() -> None:
    parameter_fields = set(FullNetworkParameters.__dataclass_fields__)
    forbidden = {"docking_score", "pocket_rmsd", "sasa", "m1_score", "m2_score", "recruitment_score"}
    assert parameter_fields.isdisjoint(forbidden)


def test_spatial_requires_constitutive_dmt_and_transport_phi_zero_is_homogeneous() -> None:
    try:
        FullNetworkParameters(**{**full_params().__dict__, "scenario": "galatea_spatial", "dmt_gate": TemporalGate(mode="published_delayed_ramp", disable_time=2)}).validate()
    except ValueError as error:
        assert "constitutive" in str(error)
    else:
        raise AssertionError("spatial scenario must reject hidden temporal control")
    # Explicit equal-volume software fixture, not a measured project volume.
    params = FullNetworkParameters(**{**full_params(0).__dict__, "transport": TransportParameters(enabled=True, access="dilute_phase", rate=2, outside_over_inside={compound: 1 for compound in COMPOUNDS}, intracellular_volume_l=1, extracellular_volume_l=1)})
    result = simulate_full_network(params, initial_intracellular=initial(), t_end=.1)
    assert result.diagnostics["mass_balance_error"] < 1e-7


def test_full_parameter_contract_rejects_wrong_reaction_identity_and_activity_keys() -> None:
    params = full_params()
    wrong = list(params.reactions)
    wrong[0] = ReactionKinetics("R1", "PTR", "9", "8", 1, 1)
    with pytest.raises(ValueError, match="full_ten"):
        FullNetworkParameters(**{**params.__dict__, "reactions": tuple(wrong)}).validate()
    with pytest.raises(ValueError, match="activity"):
        FullNetworkParameters(**{**params.__dict__, "activity_dense": {"OC": 1}}).validate()
    with pytest.raises(ValueError, match="positive"):
        FullNetworkParameters(**{**params.__dict__, "metabolite_kp": {compound: (0 if compound == "8" else 1) for compound in COMPOUNDS}}).validate()


def test_homogeneous_published_like_temporal_requires_zero_phi_and_delayed_gate() -> None:
    params = FullNetworkParameters(**{
        **full_params(0).__dict__, "scenario": "homogeneous_published_like_temporal",
        "dmt_gate": TemporalGate(mode="published_delayed_ramp", disable_time=1),
    })
    params.validate()
    with pytest.raises(ValueError, match="phi_zero"):
        FullNetworkParameters(**{**params.__dict__, "phi": .1}).validate()


def test_m4_route_contract_fails_fast_for_invalid_network_scenario_pairs() -> None:
    with pytest.raises(ValueError, match="published_reference_network"):
        M4Config(network_mode="published_reference", scenario_mode="homogeneous_constitutive")
    with pytest.raises(ValueError, match="published_reference_scenario"):
        M4Config(network_mode="galatea_full_competitive", scenario_mode="published_reference")


def test_m4_author_native_mode_requires_author_native_initial_state() -> None:
    states = {compound: 0.0 for compound in COMPOUNDS}
    with pytest.raises(ValueError, match="unit_must_match"):
        M4Config(
            network_mode="galatea_full_competitive", scenario_mode="galatea_spatial",
            unit_mode="author_native_sensitivity", reaction_network_file=Path("reactions.csv"),
            full_network_initial_state=FullNetworkInitialStateConfig(intracellular=states, concentration_unit="uM"),
        )
    M4Config(
        network_mode="galatea_full_competitive", scenario_mode="galatea_spatial",
        unit_mode="author_native_sensitivity", reaction_network_file=Path("reactions.csv"),
        full_network_initial_state=FullNetworkInitialStateConfig(intracellular=states, concentration_unit="author_native"),
    )


def test_author_native_requirements_exclude_physical_abundance_and_kinetics(tmp_path: Path) -> None:
    states = {compound: 0.0 for compound in COMPOUNDS}
    m4 = M4Config(
        network_mode="galatea_full_competitive", scenario_mode="galatea_spatial",
        unit_mode="author_native_sensitivity", reaction_network_file=tmp_path / "reactions.csv",
        full_network_initial_state=FullNetworkInitialStateConfig(intracellular=states, concentration_unit="author_native"),
    )
    project = SimpleNamespace(stages=SimpleNamespace(
        m3_concentration=SimpleNamespace(recruitment_mode="effective_ratio"), m4_reaction=m4,
    ))
    m3_names = {item.name for item in requirements_for_stage(project, "m3")}
    m4_names = {item.name for item in requirements_for_stage(project, "m4")}
    assert m3_names == {"phi", *(f"partition_x{compound}" for compound in COMPOUNDS)}
    assert not m4_names
    assert "oc_total" not in m3_names and "kcat_r1" not in m4_names and "km_r1" not in m4_names


def test_physical_requirements_remain_strict_for_abundance_and_kinetics(tmp_path: Path) -> None:
    states = {compound: 0.0 for compound in COMPOUNDS}
    m4 = M4Config(
        network_mode="galatea_full_competitive", scenario_mode="galatea_spatial",
        unit_mode="physical", reaction_network_file=tmp_path / "reactions.csv",
        full_network_initial_state=FullNetworkInitialStateConfig(intracellular=states, concentration_unit="uM"),
    )
    project = SimpleNamespace(stages=SimpleNamespace(
        m3_concentration=SimpleNamespace(recruitment_mode="effective_ratio"), m4_reaction=m4,
    ))
    m3 = {item.name: item for item in requirements_for_stage(project, "m3")}
    m4 = {item.name: item for item in requirements_for_stage(project, "m4")}
    assert m3["oc_total"].canonical_unit == "uM"
    assert m4["kcat_r1"].canonical_unit == "1/h" and m4["km_r1"].canonical_unit == "uM"


def test_author_native_scale_contract_is_not_a_physical_abundance() -> None:
    scale = AuthorNativeEnzymeScales(ptr_scale=.01, pt_scale=.01, oc_scale=.01, dmt_scale=.01)
    assert "uM" not in json.dumps(scale.model_dump())
    assert scale.interpretation == "relative_enzyme_scale_not_measured_abundance"


def test_author_native_csv_kinetics_enter_full_kernel(tmp_path: Path) -> None:
    header = "reaction_id,enzyme,substrate,product,kcat_derived_author_native,Km_author_native\n"
    rows = [f"{reaction.reaction_id},{reaction.enzyme},{reaction.substrate},{reaction.product},1,1\n" for reaction in reactions()]
    # ReactionKinetics carries the canonical identity; the first CSV is baseline.
    first_path = tmp_path / "first.csv"; first_path.write_text(header + "".join(rows), encoding="utf-8")
    changed_rows = list(rows); changed_rows[0] = changed_rows[0].replace(",1,1\n", ",5,1\n")
    second_path = tmp_path / "second.csv"; second_path.write_text(header + "".join(changed_rows), encoding="utf-8")
    settings = SimpleNamespace(unit_mode="author_native_sensitivity", reaction_network_file=first_path)
    first_reactions = _full_network_reactions(settings, {})
    settings.reaction_network_file = second_path
    second_reactions = _full_network_reactions(settings, {})
    assert first_reactions[0].kcat == 1 and second_reactions[0].kcat == 5
    kwargs = dict(enzyme_distributions={enzyme: PhaseDistribution(1, 1) for enzyme in ENZYME_SUBSTRATES}, phi=.1, metabolite_kp={compound: 1 for compound in COMPOUNDS}, initial_intracellular=initial(), t_end=.2, unit_mode="author_native_sensitivity")
    first_result = run_galatea_full_m4(reactions=first_reactions, **kwargs)
    second_result = run_galatea_full_m4(reactions=second_reactions, **kwargs)
    assert second_result.flux_integrals["R1"] > first_result.flux_integrals["R1"]


def test_author_native_transport_fails_fast() -> None:
    states = {compound: 0.0 for compound in COMPOUNDS}
    with pytest.raises(ValueError, match="transport"):
        M4Config(
            network_mode="galatea_full_competitive", scenario_mode="galatea_spatial",
            unit_mode="author_native_sensitivity", transport_enabled=True,
            reaction_network_file=Path("reactions.csv"),
            full_network_initial_state=FullNetworkInitialStateConfig(intracellular=states, concentration_unit="author_native"),
        )


def test_author_native_output_units_never_claim_physical_quantities() -> None:
    units = _full_network_units(SimpleNamespace(unit_mode="author_native_sensitivity", author_native_time_label="author_native_day_axis"))
    serialized = json.dumps(units)
    assert "uM" not in serialized and "mM" not in serialized and "1/h" not in serialized
    assert units["absolute_titer_supported"] is False and units["physical_rate_supported"] is False


def test_author_native_full_pipeline_output_keeps_only_normalized_diagnostics(tmp_path: Path) -> None:
    csv_path = tmp_path / "author_native_reactions.csv"
    csv_path.write_text(
        "reaction_id,enzyme,substrate,product,kcat_derived_author_native,Km_author_native\n"
        + "".join(f"{r.reaction_id},{r.enzyme},{r.substrate},{r.product},1,1\n" for r in reactions()),
        encoding="utf-8",
    )
    config = load_config(Path("configs/m1_m4_real_scoring_example.yaml"))
    config.execution.mode = "demo"
    config.execution.require_provenance = False
    config.stages.m3_concentration.recruitment_mode = "effective_ratio"
    config.stages.m3_concentration.slot_ratio_sh3_to_pdz = 1.0
    config.stages.m3_concentration.total_recruited_fraction = .5
    config.stages.m3_concentration.author_native_inputs = AuthorNativeEnzymeScales(
        ptr_scale=.01, pt_scale=.01, oc_scale=.01, dmt_scale=.01,
    )
    config.stages.m4_reaction = M4Config(
        network_mode="galatea_full_competitive",
        scenario_mode="galatea_spatial",
        unit_mode="author_native_sensitivity",
        t_end=.2,
        condition_id="author-native-test",
        reaction_network_file=csv_path,
        full_network_initial_state=FullNetworkInitialStateConfig(
            concentration_unit="author_native", intracellular={compound: (1.0 if compound == "8" else 0.0) for compound in COMPOUNDS},
        ),
    )
    context = M4CandidateContext(
        candidate_id="candidate", construct_id="construct", condition_id="author-native-test", phi=.1,
        enzyme_distribution={enzyme: {"dense": 1.0, "dilute": 1.0, "partition_coefficient": 1.0} for enzyme in ENZYME_SUBSTRATES},
        metabolite_partition_coefficients={compound: 1.0 for compound in COMPOUNDS},
        assumptions=["explicit author-native enzyme scales"],
    )
    m3 = M3ConcentrationAssessment(
        candidate_id="candidate", construct_id="construct", status="valid", recommended_for_m4=True,
        m4_candidate_context=context,
    )
    predictions, _ = run_m4(config, tmp_path, [m3])
    prediction = predictions[0]
    assert prediction.final_15 is None and prediction.final_13 is None and prediction.productivity is None
    required = {
        "target_yield_fraction", "branch_9_to_13_fraction", "dmt_late_selectivity",
        "early_dmt_fraction", "oc_before_dmt_route_fraction", "side_product_fraction_13",
        "mass_balance_error",
    }
    assert required <= set(prediction.mechanistic_diagnostics)
    trajectory = prediction.trajectory_artifact.read_text(encoding="utf-8")  # type: ignore[union-attr]
    assert "uM" not in trajectory and "mM" not in trajectory and "1/h" not in trajectory
    assert '"absolute_titer_supported": false' in trajectory


def test_machine_contract_agrees_with_author_native_stage_requirements() -> None:
    contract = json.loads((Path(__file__).parents[1] / "m3_m4_model_contract.json").read_text(encoding="utf-8"))
    author = contract["parameter_acquisition"]["author_native_sensitivity"]
    assert author["m3_registry"] == ["phi", "Kp_8_to_Kp_15"]
    assert "reaction_network_file:kcat_derived_author_native" in author["m4_local_source"]


def test_raw_negative_states_fail_before_clipping(monkeypatch: pytest.MonkeyPatch) -> None:
    class Solution:
        success = True
        message = ""
        t = np.array([0.0, 1.0])
        y = np.zeros((16, 2))

    Solution.y[0, 1] = -1e-6
    monkeypatch.setattr("scipy.integrate.solve_ivp", lambda *args, **kwargs: Solution())
    with pytest.raises(RuntimeError, match="numerical_negative"):
        simulate_full_network(full_params(), initial_intracellular=initial(), t_end=1)


def test_tiny_negative_states_are_clipped_only_within_tolerance(monkeypatch: pytest.MonkeyPatch) -> None:
    class Solution:
        success = True
        message = ""
        t = np.array([0.0, 1.0])
        y = np.zeros((42, 2))

    Solution.y[0, 1] = -1e-10
    monkeypatch.setattr("scipy.integrate.solve_ivp", lambda *args, **kwargs: Solution())
    result = simulate_full_network(full_params(), initial_intracellular={name: 0.0 for name in COMPOUNDS}, t_end=1)
    assert np.all(result.intracellular >= 0)
    assert result.raw_intracellular[0, 1] == -1e-10


def test_author_native_parser_is_unitless_and_public() -> None:
    from igem_drylab.published_reference import _safe_expression
    assert _safe_expression("46.59/53.41") == pytest.approx(46.59 / 53.41)


def test_uploaded_author_reference_matches_fixed_regression_fixture(tmp_path: Path,pytestconfig) -> None:
    root = Path(__file__).parents[1]
    author_file = root / "published_reference" / "author_uploaded" / "simulation-network-glabridin-final.py"
    if not author_file.exists():
        if pytestconfig.getoption('--require-author-reference'):
            pytest.fail('blocked: required immutable author reference input is unavailable')
        pytest.skip("private author_uploaded reference files are intentionally unavailable in a clean clone")
    fixture = json.loads((Path(__file__).parent / "fixtures" / "published_reference_regression.json").read_text(encoding="utf-8"))
    first = run_published_reference(root)
    assert first.time[-1] == pytest.approx(fixture["t_end"])
    assert np.allclose(first.state[:, -1], fixture["final_state"], rtol=1e-8, atol=1e-12)
    output = write_published_reference_reproduction(root, tmp_path / "published_reference_reproduction.csv")
    assert output.exists() and output.read_text(encoding="utf-8").startswith("time_author_native")
