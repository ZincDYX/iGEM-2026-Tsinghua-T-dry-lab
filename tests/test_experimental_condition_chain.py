"""C01: software fixtures for measured-condition applicability, not biological data."""
from pathlib import Path
import pytest

from igem_drylab.parameters import ParameterRegistry, resolve_requirement
from igem_drylab.parameters.requirements import requirements_for_stage
from igem_drylab.pipeline import load_config
from igem_drylab.pipeline.config import ExperimentalContext
from igem_drylab.wetlab.models import AssayConditions, WetLabResult, MetabolitePartitionMeasurement
from igem_drylab.wetlab import MeasurementMapping, quality_control, parameter_updates_from_measurements
from igem_drylab.wetlab.parameter_update import validate_candidate_against_registry


def assay(**changes):
    return AssayConditions(**{**dict(condition_id='d', source_reference='software-fixture-protocol',
        raw_data_sha256='a'*64, verified_by='fixture-reviewer', host='yeast', strain='s',
        temperature_c=30., pH=7., assay_system='in_cell', enzyme_sequence_sha256='b'*64,
        enzyme_concentration_definition='active enzyme uM', cofactor_conditions='explicit fixture cofactors'), **changes})


@pytest.mark.parametrize('stage,name,field,unit,value', [
    ('m3','phi','imaging.phi','1',.2),
    ('m3','oc_total','protein_abundance.OC','uM',2.),
    ('m4','partition_x9','partition_measurements.9','1',4.),
    ('m4','activity_dense_dmt','enzyme_activity.DMT','1',.8),
])
def test_measurement_approval_to_formal_resolver_has_exact_conditions(stage,name,field,unit,value):
    project = load_config(Path('configs/m1_m4_real_scoring_example.yaml'))
    requirement = next(r for r in requirements_for_stage(project,stage) if r.name == name)
    if requirement.parameter_type == 'activity_ratio':
        requirement = requirement.model_copy(update={'enzyme_sequence_sha256':'b'*64})
    conditions = assay(phase=requirement.phase)
    record = WetLabResult(experiment_id='fixture',construct_id='c',condition_id='d',replicate_id='r',
        assay_conditions=conditions,metabolite_time=[0.,1.],imaging={'phi':.2},
        protein_abundance={'OC':2.},enzyme_activity={'DMT':.8}, partition_measurements={'9':
        MetabolitePartitionMeasurement(dense_concentration_um=2.,dilute_concentration_um=.5,
            source_reference='fixture',raw_data_sha256='a'*64,calibration_reference='fixture',
            recovery_reference='fixture',phase_volume_reference='fixture')})
    candidate = parameter_updates_from_measurements(project,[record],quality_control([record]),
        [MeasurementMapping(target_stage=stage,target_requirement_name=name,source_field=field,unit=unit)])[0]
    target = ExperimentalContext(host='yeast',strain='s',temperature_c=30.,pH=7.,assay_system='in_cell')
    validate_candidate_against_registry([],candidate,requirement,'reviewer',formal_context=target)
    approved = candidate.model_copy(update={'review_status':'approved','approved_by':'reviewer'})
    resolved = resolve_requirement(ParameterRegistry([approved]),requirement,target,allow_assumptions=False,
        construct_id='c',condition_id='d',require_provenance=True)
    assert resolved.status == 'resolved'
    assert resolved.canonical_value == pytest.approx(value,rel=1e-12,abs=1e-12)
    assert resolved.selected_parameter.conditions == conditions.parameter_conditions()
    for key in ('host','strain','temperature_c','pH','assay_system'):
        broken = candidate.model_copy(update={'conditions':{k:v for k,v in candidate.conditions.items() if k!=key}})
        with pytest.raises(ValueError,match='candidate_not_formally_applicable'):
            validate_candidate_against_registry([],broken,requirement,'reviewer',formal_context=target)
    wrong = target.model_copy(update={'pH':5.})
    with pytest.raises(ValueError,match='candidate_not_formally_applicable'):
        validate_candidate_against_registry([],candidate,requirement,'reviewer',formal_context=wrong)
    if requirement.parameter_type == 'activity_ratio':
        with pytest.raises(ValueError,match='enzyme_sequence'):
            validate_candidate_against_registry([],candidate,requirement.model_copy(update={'enzyme_sequence_sha256':'c'*64}),
                'reviewer',formal_context=target)


def test_per_measurement_protocol_override_does_not_use_project_defaults():
    record = WetLabResult(experiment_id='fixture',construct_id='c',condition_id='d',replicate_id='r',
        assay_conditions=assay(),measurement_conditions={'activity-assay':assay(condition_id='activity-assay',pH=6.)},
        measurement_condition_ids={'enzyme_activity.DMT':'activity-assay'})
    assert record.conditions_for('enzyme_activity.DMT').pH == 6.
    assert record.conditions_for('protein_abundance.OC').pH == 7.
    record.measurement_condition_ids['enzyme_activity.DMT']='missing'
    with pytest.raises(ValueError,match='unverified_measurement_condition_reference'):
        record.conditions_for('enzyme_activity.DMT')
    assert WetLabResult(experiment_id='x',construct_id='c',condition_id='d',replicate_id='r').conditions_for('imaging.phi') is None
