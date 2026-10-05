"""Reviewed-topology software fixtures; not claims of actual genetic absence."""
from pathlib import Path
from hashlib import sha256
import json
from dataclasses import replace
import numpy as np
import pytest
from pydantic import ValidationError
from igem_drylab.full_network import COMPOUNDS,REACTIONS,PhaseDistribution,ReactionKinetics,FullNetworkParameters,simulate_full_network,ACTIVE_NETWORK_FORMULA_VERSION
from igem_drylab.active_network import AbsenceEvidenceBinding,verify_absence_evidence
from igem_drylab.pipeline import load_config
from igem_drylab.pipeline.config import M4Config,FullNetworkInitialStateConfig,ExperimentalContext
from igem_drylab.pipeline.models import M2FusionAssessment
from igem_drylab.pipeline.stages import run_m3,run_m4
from igem_drylab.parameters import ParameterRecord
from igem_drylab.parameters.requirements import requirements_for_stage
from igem_drylab.prediction import dynamic_contract,replay_prediction,PredictionContract


def absence_file(tmp_path):
    path=tmp_path/"software-absence.json"
    path.write_text(json.dumps(dict(construct_id="c",condition_id="d",host="fixture-host",strain="fixture-strain",
        confirmed_absent_enzymes={e:"genetic_and_background_activity_absent" for e in ("PTR","PT")},
        source_reference="software_fixture_only",verification_method="fixture declaration, not actual genetics",reviewed_by="fixture-reviewer")))
    return AbsenceEvidenceBinding(artifact=path,sha256=sha256(path.read_bytes()).hexdigest(),reviewed_by="fixture-reviewer")


def verified(binding):
    return verify_absence_evidence(binding,construct_id="c",condition_id="d",host="fixture-host",strain="fixture-strain")


def parameters(binding):
    return FullNetworkParameters(phi=.2,enzyme_distributions={e:PhaseDistribution(2,.5) for e in ("OC","DMT")},
        metabolite_kp={c:5. if c=="10" else 1. for c in COMPOUNDS},
        reactions=tuple(ReactionKinetics(*r,kcat=1.,km=1.) for r in REACTIONS if r[1] in {"OC","DMT"}),
        activity_dense={e:1. for e in ("OC","DMT")},activity_dilute={e:1. for e in ("OC","DMT")},
        network_variant="oc_dmt_verified_absence",absence_evidence=verified(binding))


def test_active_topology_matches_full_network_structural_zero_control_without_fake_kinetics(tmp_path):
    params=parameters(absence_file(tmp_path));initial={c:float(c=="10") for c in COMPOUNDS}
    active=simulate_full_network(params,initial_intracellular=initial,t_end=.1,points=11)
    control=replace(params,network_variant="full_ten",absence_evidence={},
        reactions=tuple(ReactionKinetics(*r,kcat=1.,km=1.) for r in REACTIONS),
        enzyme_distributions={**params.enzyme_distributions,"PTR":PhaseDistribution(0,0),"PT":PhaseDistribution(0,0)},
        activity_dense={e:1. for e in ("PTR","PT","OC","DMT")},activity_dilute={e:1. for e in ("PTR","PT","OC","DMT")})
    full=simulate_full_network(control,initial_intracellular=initial,t_end=.1,points=11)
    np.testing.assert_allclose(active.raw_intracellular,full.raw_intracellular,rtol=0,atol=1e-10)
    # Independently derive initial R3/R6: .2*2*25/34 + .8*.5*5/14 uM/h.
    expected=.4*(25/34)+.4*(5/14)
    assert active.fluxes[2,0]==pytest.approx(expected,rel=0,abs=1e-12)
    assert active.fluxes[5,0]==pytest.approx(expected,rel=0,abs=1e-12)
    assert [r.reaction_id for r in params.reactions]==["R3","R4","R5","R6","R7","R10"]
    np.testing.assert_array_equal(active.fluxes[[0,1,7,8]],0.)
    assert active.intracellular[7,-1]>0
    np.testing.assert_allclose(active.raw_intracellular.sum(axis=0),1.,rtol=0,atol=1e-10)
    contract=dynamic_contract(params,active,initial,{c:0 for c in COMPOUNDS},.1,11)
    assert contract["formula_version"]==ACTIVE_NETWORK_FORMULA_VERSION
    assert replay_prediction(contract,"kcat_r3",2.)["concentrations"]["intracellular"]["11"][-1]>contract["concentrations"]["intracellular"]["11"][-1]
    with pytest.raises(ValueError,match="not_in_selected_model"):
        replay_prediction(contract,"kcat_r1",2.)
    contract["formula_version"]="galatea-dynamic-volume-v2-2026-10-04"
    with pytest.raises(ValidationError,match="network_variant_formula"):
        PredictionContract.model_validate(contract)


@pytest.mark.parametrize("fault",["tamper","wrong_construct","unconfirmed_background","missing_competing_reaction"])
def test_absence_and_topology_must_be_explicit_verified_and_complete(tmp_path,fault):
    binding=absence_file(tmp_path)
    if fault=="tamper":
        binding.artifact.write_text("{}")
        with pytest.raises(ValueError,match="hash_mismatch"):verified(binding)
    elif fault=="wrong_construct":
        with pytest.raises(ValueError,match="identity_or_condition"):
            verify_absence_evidence(binding,construct_id="other",condition_id="d",host="fixture-host",strain="fixture-strain")
    elif fault=="unconfirmed_background":
        raw=json.loads(binding.artifact.read_text());raw["confirmed_absent_enzymes"]["PTR"]="not_in_construct_only"
        binding.artifact.write_text(json.dumps(raw));binding.sha256=sha256(binding.artifact.read_bytes()).hexdigest()
        with pytest.raises(ValueError,match="genetic_and_background"):verified(binding)
    else:
        params=parameters(binding)
        with pytest.raises(ValueError,match="reaction_network"):
            replace(params,reactions=tuple(r for r in params.reactions if r.reaction_id!="R4")).validate()


def test_actual_finite_M3_and_M4_exclude_absent_parameters_not_zero_fill(tmp_path):
    binding=absence_file(tmp_path)
    config=load_config(Path("configs/m1_m4_real_scoring_example.yaml"))
    config.execution.mode="demo";config.execution.allow_assumptions=True;config.execution.require_provenance=False
    config.experimental_context=ExperimentalContext(host="fixture-host",strain="fixture-strain")
    config.stages.m3_concentration.recruitment_mode="finite_site"
    network=tmp_path/"network.csv";network.write_text("reaction_id,enzyme,substrate,product\n"+"".join(",".join(r)+"\n" for r in REACTIONS))
    config.stages.m4_reaction=M4Config(network_mode="galatea_full_competitive",network_variant="oc_dmt_verified_absence",
        confirmed_absent_enzymes={e:"software_fixture_only" for e in ("PTR","PT")},absence_evidence=binding,
        assay_mode="substrate_feeding_functional",feed_mode="batch_initial_state",feed_compound_id="10",feeding_time_h=0,
        expression_mode="constitutive",condition_id="d",scenario_mode="galatea_spatial",reaction_network_file=network,t_end=.1,solver_points=3,
        full_network_initial_state=FullNetworkInitialStateConfig(intracellular={c:float(c=="10") for c in COMPOUNDS}))
    catalog={r.name:r for stage in ("m3","m4") for r in requirements_for_stage(config,stage)}
    assert not {"ptr_total","pt_total","partition_ptr","partition_pt","kcat_r1","km_r1","kcat_r2","km_r8","kcat_r9"} & set(catalog)
    values={"phi":.2,"c_dense_scaffold":5.,"kd_sh3":.5,"kd_pdz":1.,"oc_total":1.,"dmt_total":1.,"partition_oc":1.,"partition_dmt":1.}
    values.update({f"partition_x{c}":5. if c=="10" else 1. for c in COMPOUNDS})
    values.update({f"{kind}_{r.lower()}":1. for r,e,_,_ in REACTIONS if e in {"OC","DMT"} for kind in ("kcat","km")})
    config.parameters=[ParameterRecord(parameter_id=name,name=name,value=values[name],unit=r.canonical_unit,
        parameter_type=r.parameter_type,enzyme_id=r.enzyme_id,substrate_id=r.substrate_id,product_id=r.product_id,species_id=r.species_id,
        source_type="assumption",source_reference="software_fixture_only",review_status="approved",
        conditions={"host":"fixture-host","strain":"fixture-strain",
            **({"entity_basis":"complete_assembly"} if name=="c_dense_scaffold" else {})}) for name,r in catalog.items()]
    m2=M2FusionAssessment(candidate_id="fixture",construct_id="c",construct_definition={},status="valid",recommended_for_m3=True,
        s_sh3=1,s_pdz=1,eta_acc_sh3=1.,eta_acc_pdz=1.,eta_bind_sh3=1.,eta_bind_pdz=1.,
        site_count_basis="complete_assembly",joint_occupancy_independent=True,m2_geometry_id="fixture-geometry")
    m3,_=run_m3(config,tmp_path/"run",[m2])
    assert m3[0].status=="valid",m3[0].missing_inputs
    assert set(m3[0].m4_candidate_context.enzyme_distribution)=={"OC","DMT"}
    m4,_=run_m4(config,tmp_path/"run",m3)
    assert m4[0].status=="valid",m4[0].missing_inputs
    assert m4[0].final_15>0
    assert m4[0].transport_report["13_role"]=="no_active_13_to_14_reaction_under_verified_PT_absence"
    inputs=m4[0].simulation_inputs["prediction_contract"]["kernel_inputs"]["parameters"]
    assert inputs["absence_evidence"]["artifact_sha256"]==binding.sha256
    assert {r["enzyme"] for r in inputs["reactions"]}=={"OC","DMT"}
    config.parameters=[r for r in config.parameters if r.name!="km_r6"]
    missing,_=run_m4(config,tmp_path/"missing",m3)
    assert missing[0].status=="insufficient_data"
    assert any("km_r6" in r for r in missing[0].missing_inputs)
    binding.artifact.write_text("{}")
    rejected,_=run_m3(config,tmp_path/"tampered",[m2])
    assert rejected[0].status=="insufficient_data"
    assert any("hash_mismatch" in r for r in rejected[0].missing_inputs)
