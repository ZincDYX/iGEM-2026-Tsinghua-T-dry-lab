from dataclasses import replace
from pathlib import Path
import json

import numpy as np
import pytest

from igem_drylab.full_network import COMPOUNDS, ENZYME_SUBSTRATES, REACTIONS, FullNetworkParameters, PhaseDistribution, ReactionKinetics, TemporalGate, TransportParameters, simulate_full_network
from igem_drylab.kinetics import InductionGate
from igem_drylab.pipeline import load_config
from igem_drylab.pipeline.config import FitPlanConfig, FullNetworkInitialStateConfig, M4Config
from igem_drylab.pipeline.models import M4ReactionPrediction
from igem_drylab.pipeline.stages import _fit_plan_candidate, _full_network_reactions, _aggregate_fit_groups
from igem_drylab.prediction import dynamic_contract, observe_prediction, replay_prediction
from igem_drylab.wetlab import WetLabResult, compare_prediction


def parameters(phi=0.2, enzymes=1):
    return FullNetworkParameters(phi=phi, enzyme_distributions={name: PhaseDistribution(enzymes, enzymes) for name in ENZYME_SUBSTRATES},
        metabolite_kp={name: 1.0 for name in COMPOUNDS}, reactions=tuple(ReactionKinetics(*row, kcat=1, km=1) for row in REACTIONS),
        scenario="galatea_spatial" if phi else "homogeneous_constitutive")


def state(**updates):
    return {name: updates.get(f"x{name}", 0.0) for name in COMPOUNDS}


@pytest.mark.parametrize("phi", [0, 0.2, 0.7])
@pytest.mark.parametrize("access", ["cell_average", "dilute_phase"])
@pytest.mark.parametrize("reverse", [False, True])
def test_unequal_volume_transport_conserves_amount(phi, access, reverse):
    params = replace(parameters(phi, enzymes=0), transport=TransportParameters(enabled=True, rate=2,
        access=access, outside_over_inside={name: 1.0 for name in COMPOUNDS}, intracellular_volume_l=1, extracellular_volume_l=10))
    inside, outside = (state(), state(x8=1)) if reverse else (state(x8=1), state())
    result = simulate_full_network(params, initial_intracellular=inside, initial_extracellular=outside, t_end=2)
    amount = result.intracellular.sum(axis=0) + 10 * result.extracellular.sum(axis=0)
    assert np.allclose(amount, amount[0], atol=1e-8)
    assert result.diagnostics["backbone_amount_balance_error_umol"] < 1e-8


def test_zero_reaction_initial_product_and_feed_from_10_metrics():
    result = simulate_full_network(parameters(enzymes=0), initial_intracellular=state(x10=1, x15=2), t_end=1)
    assert result.diagnostics["net_15_generated_cell_volume_equivalent"] == 0
    assert result.diagnostics["target_yield_fraction"] == 0
    assert result.diagnostics["early_dmt_fraction"] is None
    assert result.diagnostics["side_product_fraction_13"] is None
    assert result.diagnostics["initial_convertible_backbone_cell_volume_equivalent"] == 1


@pytest.mark.parametrize("compartment,basis", [("intracellular", "cell_volume"), ("extracellular", "medium_volume"), ("total_extract", "extraction_volume")])
def test_observation_roundtrip_in_each_compartment(tmp_path, compartment, basis):
    params = replace(parameters(), transport=TransportParameters(enabled=True, rate=1, outside_over_inside={name: 1 for name in COMPOUNDS},
        intracellular_volume_l=1, extracellular_volume_l=10))
    initial = state(x8=1)
    result = simulate_full_network(params, initial_intracellular=initial, t_end=1, points=21)
    contract = dynamic_contract(params, result, initial, state(), 1, 21)
    observation = WetLabResult(experiment_id="synthetic", construct_id="c", condition_id="d", replicate_id="r",
        measurement_compartment=compartment, concentration_basis=basis, extraction_volume_l=2 if compartment == "total_extract" else None,
        metabolite_time=result.time.tolist(), metabolite_concentration_unit="uM")
    _, series = observe_prediction(contract, observation)
    observation.metabolites = {name: series[name].tolist() for name in ("13", "15")}
    path = tmp_path / "trajectory.json"
    path.write_text(json.dumps({"prediction_contract": contract}), encoding="utf-8")
    compared = compare_prediction(path, observation)
    assert all(row.residual_final == 0 for row in compared.values())
    assert all(row.comparison_status == "trajectory_aligned" for row in compared.values())


def test_full_fit_uses_same_kernel_and_value_changes_fingerprint(tmp_path):
    from test_experimental_condition_chain import assay
    initial = state(x8=1)
    params = parameters()
    simulated = simulate_full_network(params, initial_intracellular=initial, t_end=2, points=21)
    contract = dynamic_contract(params, simulated, initial, state(), 2, 21)
    result = WetLabResult(experiment_id="synthetic", construct_id="c", condition_id="d", replicate_id="r",
        metabolite_time=simulated.time.tolist(), metabolite_concentration_unit="uM", measurement_compartment="intracellular",
        concentration_basis="cell_volume", assay_conditions=assay(), metabolites={name: simulated.intracellular[COMPOUNDS.index(name)].tolist() for name in ("13", "15")})
    config = load_config(Path("configs/m1_m4_real_scoring_example.yaml"))
    config.execution.mode = "demo"
    config.stages.m4_reaction = M4Config(network_mode="galatea_full_competitive", scenario_mode="galatea_spatial", reaction_network_file=tmp_path / "identity.csv",
        full_network_initial_state=FullNetworkInitialStateConfig(intracellular=initial))
    config.stages.m5_feedback.fit_plan = FitPlanConfig(parameter_name="kcat_r3", bounds=(0.2, 2), observables=["13", "15"])
    path = tmp_path / "trajectory.json"
    path.write_text(json.dumps({"prediction_contract": contract}), encoding="utf-8")
    prediction = M4ReactionPrediction(candidate_id="c", construct_id="c", condition_id="d", target_product="15",
        simulation_inputs={"prediction_contract": contract, "parameters": {"kcat_r3": 1.0}}, parameter_ids=["synthetic-only"])
    first = _fit_plan_candidate(config, prediction, result, compare_prediction(path, result))
    assert first["fit"]["best_fit"] == pytest.approx(1, abs=1e-4)
    assert first["candidate"]["review_status"] == "validated"
    assert first["candidate"]["conditions"] == result.assay_conditions.parameter_conditions()
    assert first["candidate"]["construct_id"] == 'c'
    result.raw_data_sha256 = "different-raw-JSON-format"
    unchanged = _fit_plan_candidate(config, prediction, result, compare_prediction(path, result))
    assert unchanged["candidate"]["parameter_id"] == first["candidate"]["parameter_id"]
    assert "raw_data_sha256=different-raw-JSON-format" in unchanged["candidate"]["notes"]
    result.metabolites["15"][-1] += 0.001
    second = _fit_plan_candidate(config, prediction, result, compare_prediction(path, result))
    assert first["candidate"]["parameter_id"] != second["candidate"]["parameter_id"]
    replayed = replay_prediction(contract, "kcat_r3", 1.0)
    assert np.allclose(replayed["concentrations"]["intracellular"]["15"], contract["concentrations"]["intracellular"]["15"])


def test_fits_never_average_inside_and_outside_replicates():
    common = dict(experiment_id="e", construct_id="c", condition_id="d", metabolite_time=[0, 1], metabolite_concentration_unit="uM", metabolites={"15": [0, 1]})
    records = [WetLabResult(replicate_id=str(index), measurement_compartment=compartment,
        concentration_basis="cell_volume" if compartment == "intracellular" else "medium_volume", **common)
        for index, compartment in enumerate(("intracellular", "intracellular", "extracellular", "extracellular"))]
    assert len(_aggregate_fit_groups(records)) == 2


def test_physical_identity_table_needs_no_author_numeric_columns(tmp_path):
    path = tmp_path / "identity.csv"
    path.write_text("reaction_id,enzyme,substrate,product\n" + "".join(",".join(row) + "\n" for row in REACTIONS), encoding="utf-8")
    from types import SimpleNamespace
    selected = {f"{prefix}_{reaction[0].lower()}": SimpleNamespace(canonical_value=1) for reaction in REACTIONS for prefix in ("kcat", "km")}
    reactions = _full_network_reactions(SimpleNamespace(unit_mode="physical", reaction_network_file=path), selected)
    assert len(reactions) == 10


def test_supported_induction_fields_and_unsupported_configuration():
    params = replace(parameters(), scenario="galatea_spatiotemporal_ablation", dmt_gate=TemporalGate(mode="configured_induction",
        induction=InductionGate(on_time=.3, off_time=.7, basal=.1, induced=.5, mode="step")))
    result = simulate_full_network(params, initial_intracellular=state(x11=1), t_end=1, points=11)
    assert .3 in result.time and .7 in result.time
    assert params.dmt_gate.value(.2) == .1
    assert params.dmt_gate.value(.5) == .5
    assert params.dmt_gate.value(.8) == .1
    with pytest.raises(ValueError, match="degradation_not_supported"):
        M4Config(enable_degradation=True)
    with pytest.raises(ValueError, match="steady_state_does_not_support"):
        M4Config(dmt_gate={"on_time": 1})


def test_steady_state_observations_and_replay_are_not_dynamic_substitutions(tmp_path):
    from igem_drylab.m4_steady_state import M4SteadyStateInput, solve_m4_steady_state
    from igem_drylab.prediction import steady_contract
    payload = M4SteadyStateInput(candidate_id="c", construct_id="c", condition_id="d", phi=0.1,
        enzymes={name: {"dense_um": 1, "dilute_um": 1, "m3_source_id": "test-only"} for name in ENZYME_SUBSTRATES},
        metabolite_kp={name: 1 for name in COMPOUNDS}, input_flux_um_per_h=.1,
        secretion_rate_per_h={name: .2 for name in COMPOUNDS}, secretion_normalization="original_unweighted_dilute_concentration",
        initial_guess_um=state(**{f"x{name}": 1 for name in COMPOUNDS}), input_parameter_ids=["test-only"],
        reactions=[{"reaction_id": identity[0], "enzyme": identity[1], "substrate": identity[2], "product": identity[3],
                    "kcat_per_h": 1, "km_um": 1, "parameter_ids": ["test-kcat", "test-km"]} for identity in REACTIONS])
    solved = solve_m4_steady_state(payload)
    assert solved.status == "valid"
    contract = steady_contract(payload, solved)
    observation = WetLabResult(experiment_id="e", construct_id="c", condition_id="d", replicate_id="r", metabolite_time=[12, 24],
        metabolite_concentration_unit="uM", measurement_compartment="intracellular", concentration_basis="cell_volume",
        observation_kind="steady_state", metabolites={name: [solved.concentrations_cell_average_um[name]] * 2 for name in ("13", "15")})
    path = tmp_path / "steady.json"
    path.write_text(json.dumps({"prediction_contract": contract}), encoding="utf-8")
    assert compare_prediction(path, observation)["15"].residual_final == 0
    replayed = replay_prediction(contract, "kcat_r3", 1)
    assert replayed["concentrations"] == contract["concentrations"]
    observation.observation_kind = "time_course"
    with pytest.raises(ValueError, match="confirmed_steady_state"):
        compare_prediction(path, observation)
    observation.observation_kind = "steady_state"
    observation.measurement_compartment = "extracellular"
    observation.concentration_basis = "medium_volume"
    with pytest.raises(ValueError, match="does_not_predict_requested_compartment"):
        compare_prediction(path, observation)


def test_missing_model_adapter_is_structured_m5_insufficient_data(tmp_path):
    from igem_drylab.pipeline.models import M4CandidateContext
    from igem_drylab.pipeline.stages import run_m5
    artifact = tmp_path / "broken-old-full.json"
    artifact.write_text(json.dumps({"concentration_unit": "uM", "time": [0, 1], "intracellular_cell_average": {"15": [0, 1]}}), encoding="utf-8")
    result = WetLabResult(experiment_id="e", construct_id="c", condition_id="d", replicate_id="r", metabolite_time=[0, 1],
        metabolite_concentration_unit="uM", metabolites={"15": [0, 1]}, biological_replicate_count=2, control_available=True)
    records = tmp_path / "measurements.json"
    records.write_text(json.dumps([result.model_dump(mode="json")]), encoding="utf-8")
    config = load_config(Path("configs/m1_m4_real_scoring_example.yaml"))
    config.stages.m5_feedback.wetlab_results_file = records
    prediction = M4ReactionPrediction(candidate_id="c", construct_id="c", condition_id="d", target_product="15", trajectory_artifact=artifact,
        candidate_context=M4CandidateContext(candidate_id="c", construct_id="c", condition_id="d", phi=0, enzyme_distribution={}))
    feedback, _ = run_m5(config, tmp_path, [prediction])
    assert feedback[0].status == "insufficient_data"
    assert any("missing_trajectory_model_adapter" in flag for flag in feedback[0].qc_flags)


def test_production_full_m4_to_m5_comparison_and_fit(tmp_path):
    from igem_drylab.parameters import ParameterRecord, full_m4_kinetic_requirements
    from igem_drylab.pipeline.models import M3ConcentrationAssessment, M4CandidateContext
    from igem_drylab.pipeline.stages import run_m4, run_m5
    identity = tmp_path / "reactions.csv"
    identity.write_text("reaction_id,enzyme,substrate,product\n" + "".join(",".join(row) + "\n" for row in REACTIONS), encoding="utf-8")
    config = load_config(Path("configs/m1_m4_real_scoring_example.yaml"))
    config.execution.mode = "demo"
    config.execution.allow_assumptions = True
    config.stages.m4_reaction = M4Config(network_mode="galatea_full_competitive", scenario_mode="galatea_spatial",
        t_end=2, solver_points=21, condition_id="d", reaction_network_file=identity,
        full_network_initial_state=FullNetworkInitialStateConfig(intracellular=state(x8=1)))
    config.parameters = [ParameterRecord(parameter_id=item.name, name=item.name, value=1, unit=item.canonical_unit,
        parameter_type=item.parameter_type, enzyme_id=item.enzyme_id, substrate_id=item.substrate_id, product_id=item.product_id,
        source_type="assumption", source_reference="synthetic-test-only", review_status="approved") for item in full_m4_kinetic_requirements()]
    context = M4CandidateContext(candidate_id="candidate", construct_id="c", condition_id="d", phi=.2,
        enzyme_distribution={name: {"dense": 1, "dilute": 1, "partition_coefficient": 1} for name in ENZYME_SUBSTRATES},
        metabolite_partition_coefficients={name: 1 for name in COMPOUNDS})
    predictions, _ = run_m4(config, tmp_path, [M3ConcentrationAssessment(candidate_id="candidate", construct_id="c", m4_candidate_context=context, recommended_for_m4=True)])
    assert predictions[0].numerically_solved and not predictions[0].evidence_ready
    artifact = json.loads(predictions[0].trajectory_artifact.read_text(encoding="utf-8"))
    data = artifact["prediction_contract"]
    assert set(artifact['raw_intracellular_cell_average'])==set(COMPOUNDS)
    assert set(artifact['raw_extracellular'])==set(COMPOUNDS)
    assert set(artifact['transport_integrals'])==set(COMPOUNDS)
    assert artifact['solver_settings']['integration_version']=='adaptive-cumulative-v1'
    assert artifact['diagnostics']['integrated_stoichiometry_max_abs_error']<1e-9
    records = [WetLabResult(experiment_id="synthetic", construct_id="c", condition_id="d", replicate_id=str(index),
        biological_replicate_count=2, control_available=True, measurement_compartment="intracellular", concentration_basis="cell_volume",
        metabolite_time=data["time"], metabolite_concentration_unit="uM", metabolites={name: data["concentrations"]["intracellular"][name] for name in ("13", "15")})
        for index in (1, 2)]
    measurements = tmp_path / "paired-replicates.json"
    measurements.write_text(json.dumps([row.model_dump(mode="json") for row in records]), encoding="utf-8")
    config.stages.m5_feedback.wetlab_results_file = measurements
    config.stages.m5_feedback.fit_plan = FitPlanConfig(parameter_name="kcat_r3", bounds=(.1, 2), observables=["13", "15"])
    feedback, _ = run_m5(config, tmp_path, predictions)
    assert all(row.status == "valid" and row.prediction_residual == 0 for row in feedback)
    assert all(row.fitted_parameter_candidate["review_status"] == "validated" for row in feedback)
