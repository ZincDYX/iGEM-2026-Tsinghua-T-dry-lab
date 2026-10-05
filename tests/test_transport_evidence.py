"""Software-only audited input records, never project wetlab measurements."""
from dataclasses import replace
from types import SimpleNamespace
import numpy as np
import pytest
from igem_drylab.parameters import ParameterRecord
from igem_drylab.pipeline.config import ExperimentalContext
from igem_drylab.full_network import COMPOUNDS, REACTIONS, FullNetworkParameters, PhaseDistribution, ReactionKinetics, simulate_full_network
from igem_drylab.transport_evidence import TransportEvidenceBinding, resolve_transport_evidence, match_configured_transport, RATE_DEFINITION, RATIO_DEFINITION


def fixture_records(access="cell_average"):
    shared=dict(host="fixture-host",strain="fixture-strain",temperature_c=30.,pH=7.,assay_system="fixture-cell",
        raw_data_sha256="a"*64)
    def record(identifier,value,unit,kind,conditions,species=None):
        return ParameterRecord(parameter_id=identifier,name=identifier,value=value,unit=unit,parameter_type=kind,
            species_id=species,construct_id="fixture-c",condition_id="fixture-d",source_type="wetlab",
            source_reference="software_fixture_only_not_actual_measurement",review_status="approved",approved_by="fixture-reviewer",
            conditions={**shared,**conditions})
    records=[record("rate",1/30,"1/min","export_rate",dict(rate_definition=RATE_DEFINITION,transport_access=access,normalization="cell_volume_equivalent_flux")),
        record("vi",2000,"mL","other",dict(compartment="intracellular",volume_definition="effective_intracellular_reaction_volume")),
        record("ve",5,"L","other",dict(compartment="extracellular",volume_definition="extracellular_medium_volume"))]
    records += [record("ratio-"+c,2.,"1","other",dict(ratio_definition=RATIO_DEFINITION,transport_access=access),c) for c in COMPOUNDS]
    binding=TransportEvidenceBinding(rate_parameter_id="rate",intracellular_volume_parameter_id="vi",extracellular_volume_parameter_id="ve",
        outside_over_inside_parameter_ids={c:"ratio-"+c for c in COMPOUNDS})
    context=ExperimentalContext(host="fixture-host",strain="fixture-strain",temperature_c=30.,pH=7.,assay_system="fixture-cell")
    return records,binding,context


def resolve(records,binding,context,access="cell_average"):
    return resolve_transport_evidence(records,binding,context,construct_id="fixture-c",condition_id="fixture-d",access=access)


@pytest.mark.parametrize("access",["cell_average","dilute_phase"])
def test_verified_units_and_definitions_reach_actual_unequal_volume_transport(access):
    records,binding,context=fixture_records(access)
    transport,evidence=resolve(records,binding,context,access)
    assert transport.rate==pytest.approx(2,abs=1e-14)
    assert (transport.intracellular_volume_l,transport.extracellular_volume_l)==(2.,5.)
    assert evidence["parameter_ids"]==["rate","vi","ve",*["ratio-"+c for c in COMPOUNDS]]
    params=FullNetworkParameters(phi=.2,enzyme_distributions={e:PhaseDistribution(0,0) for e in ("PTR","PT","OC","DMT")},
        metabolite_kp={c:3 for c in COMPOUNDS},reactions=tuple(ReactionKinetics(*r,kcat=1,km=1) for r in REACTIONS),transport=transport)
    result=simulate_full_network(params,initial_intracellular={c:float(c=="13") for c in COMPOUNDS},t_end=1e-6,points=2)
    # k+ = 2*2/(1+2)=4/3 h^-1. Dilute C13=1/(.8+.2*3)=5/7 uM.
    expected=(4/3)*(1 if access=="cell_average" else 5/7)
    assert result.transport_integrals["13"]["total_outflow_cell_volume_equivalent"]/1e-6==pytest.approx(expected,rel=0,abs=3e-6)
    np.testing.assert_allclose(2*result.raw_intracellular[5]+5*result.raw_extracellular[5],2.,rtol=0,atol=1e-10)


@pytest.mark.parametrize("identifier,field,value",[("vi","compartment","extracellular"),("vi","raw_data_sha256",""),
    ("ratio-13","ratio_definition","inside/outside"),("rate","rate_definition","secretion_only"),
    ("ratio-13","transport_access","dilute_phase"),("ve","pH",5.)])
def test_wrong_provenance_compartment_direction_or_conditions_are_rejected(identifier,field,value):
    records,binding,context=fixture_records()
    record=next(r for r in records if r.parameter_id==identifier)
    record.conditions[field]=value
    with pytest.raises(ValueError,match="transport_"):
        resolve(records,binding,context)


@pytest.mark.parametrize("change",["unapproved","wrong_species","wrong_units","wrong_scope","assumption","missing"])
def test_formal_transport_cannot_use_unreviewed_or_incompatible_records(change):
    records,binding,context=fixture_records()
    if change=="missing":records=records[:-1]
    else:
        r=records[-1]
        if change=="unapproved":r.review_status="validated"
        if change=="wrong_species":r.species_id="13"
        if change=="wrong_units":r.unit="uM"
        if change=="wrong_scope":r.construct_id="different"
        if change=="assumption":r.source_type="assumption"
    with pytest.raises(ValueError,match="transport_"):
        resolve(records,binding,context)


def test_numeric_config_does_not_override_verified_volumes_or_ratios():
    records,binding,context=fixture_records();params,_=resolve(records,binding,context)
    settings=SimpleNamespace(intracellular_volume_l=2.,extracellular_volume_l=5.,transport_outside_over_inside={c:2. for c in COMPOUNDS})
    match_configured_transport(params,settings,2.)
    settings.extracellular_volume_l=2.
    with pytest.raises(ValueError,match="disagrees.*extracellular_volume"):
        match_configured_transport(params,settings,2.)


def test_formal_pipeline_consumes_transport_evidence_and_keeps_invalid_binding_blocked(tmp_path):
    from pathlib import Path
    from igem_drylab.pipeline import load_config
    from igem_drylab.pipeline.config import M4Config,FullNetworkInitialStateConfig
    from igem_drylab.pipeline.models import M3ConcentrationAssessment,M4CandidateContext
    from igem_drylab.pipeline.stages import run_m4
    from igem_drylab.parameters.requirements import requirements_for_stage
    records,binding,experimental=fixture_records()
    config=load_config(Path("configs/m1_m4_example.yaml"))
    config.execution.mode="real";config.execution.analysis_grade="formal_measured"
    config.execution.allow_assumptions=False;config.execution.require_provenance=True
    config.experimental_context=experimental
    for enzyme in config.inputs.enzymes:enzyme.sequence_sha256="b"*64
    network=tmp_path/"network.csv"
    network.write_text("reaction_id,enzyme,substrate,product\n"+"".join(",".join(r)+"\n" for r in REACTIONS))
    initial={c:float(c=="13") for c in COMPOUNDS}
    config.stages.m4_reaction=M4Config(network_mode="galatea_full_competitive",scenario_mode="galatea_spatial",
        activity_mode="sensitivity_parameters",assay_mode="substrate_feeding_functional",expression_mode="constitutive",
        feeding_time_h=0,feed_mode="batch_initial_state",feed_compound_id="13",condition_id="fixture-d",
        reaction_network_file=network,t_end=1e-6,solver_points=2,transport_enabled=True,transport_access="cell_average",
        transport_rate_parameter="rate",transport_evidence=binding,intracellular_volume_l=2.,extracellular_volume_l=5.,
        transport_outside_over_inside={c:2. for c in COMPOUNDS},full_network_initial_state=FullNetworkInitialStateConfig(
            intracellular=initial,parameter_ids={f"{compartment}:{c}":f"initial-{compartment}-{c}" for compartment in ("intracellular","extracellular") for c in COMPOUNDS}))
    common=records[0].conditions
    for req in requirements_for_stage(config,"m4"):
        if req.name=="rate":continue
        records.append(ParameterRecord(parameter_id=req.name,name=req.name,value=1.,unit=req.canonical_unit,
            parameter_type=req.parameter_type,enzyme_id=req.enzyme_id,substrate_id=req.substrate_id,product_id=req.product_id,
            species_id=req.species_id,construct_id="fixture-c",condition_id="fixture-d",source_type="wetlab",
            source_reference="software_fixture_only",review_status="approved",approved_by="fixture-reviewer",conditions={
                **common,"phase":req.phase or "not_applicable","enzyme_sequence_sha256":"b"*64,
                "enzyme_concentration_definition":"active enzyme uM","cofactor_conditions":"software fixture"}))
    for compartment in ("intracellular","extracellular"):
        for c in COMPOUNDS:
            identifier=f"initial-{compartment}-{c}"
            records.append(ParameterRecord(parameter_id=identifier,name=identifier,value=initial[c] if compartment=="intracellular" else 0,
                unit="uM",parameter_type="abundance",species_id=c,construct_id="fixture-c",condition_id="fixture-d",
                source_type="wetlab",source_reference="software_fixture_only",review_status="approved",approved_by="fixture-reviewer",
                conditions={**common,"compartment":compartment,"measurement_time_h":0}))
    config.parameters=records
    context=M4CandidateContext(candidate_id="fixture",construct_id="fixture-c",condition_id="fixture-d",phi=.2,
        enzyme_distribution={e:dict(dense=0.,dilute=0.) for e in ("PTR","PT","OC","DMT")},
        enzyme_sequence_sha256={e:"b"*64 for e in ("PTR","PT","OC","DMT")},
        metabolite_partition_coefficients={c:3. for c in COMPOUNDS},evidence_ready=True)
    assessment=M3ConcentrationAssessment(candidate_id="fixture",construct_id="fixture-c",status="valid",
        recommended_for_m4=True,m4_candidate_context=context)
    output,_=run_m4(config,tmp_path/"valid",[assessment])
    assert output[0].status=="valid",output[0].missing_inputs
    assert output[0].transport_report["evidence"]["status"]=="formal_evidence_bound"
    assert set(binding.outside_over_inside_parameter_ids.values()) <= set(output[0].parameter_ids)
    assert output[0].simulation_inputs["prediction_contract"]["kernel_inputs"]["parameters"]["transport"]["rate"]==2.
    assert output[0].transport_report["integrals"]["13"]["total_outflow_cell_volume_equivalent"]/1e-6==pytest.approx(4/3,rel=0,abs=3e-6)
    records[1].conditions["compartment"]="extracellular"
    rejected,_=run_m4(config,tmp_path/"rejected",[assessment])
    assert rejected[0].status=="insufficient_data"
    assert any("definition_mismatch:compartment" in reason for reason in rejected[0].missing_inputs)
