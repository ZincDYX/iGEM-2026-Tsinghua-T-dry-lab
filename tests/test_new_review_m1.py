"""N01/N02 regression fixtures; none are experimental tool predictions."""
import json
from hashlib import sha256
from pathlib import Path

import pytest

from igem_drylab.constructs.linker_features import (
    DisorderEvidence, FusionToolEvidence, M1FeatureDefinitions, M1V3Rules,
    compute_sequence_features, compute_protparam_evidence, parse_iupred2a_output,
    parse_secondary_structure_output, parse_seg_fasta, screen_sequence_v3,
)
from igem_drylab.constructs.tool_evidence import ToolEvidenceProvenance
from igem_drylab.pipeline import load_config
from igem_drylab.pipeline.config import ConstructDefinition
from igem_drylab.pipeline.stages import _screen_m1_sequence, run_m1

ROOT = Path(__file__).parents[1]
SEQUENCE = 'GS' * 15


def features(sequence=SEQUENCE):
    definitions, digest = M1FeatureDefinitions.from_yaml(ROOT/'configs/m1_feature_definitions.yaml')
    return compute_sequence_features(sequence, definitions=definitions, definitions_sha256=digest)


def audited(tmp_path):
    """Byte-bound manual fixture records, not claims of external execution."""
    h = features().sequence_sha256
    def attach(evidence, name, path, observations):
        record = dict(origin='manual_review',tool_name=name,tool_version='fixture',input_sha256=h,
                      output_sha256=sha256(path.read_bytes()).hexdigest(),reviewer='fixture-reviewer',
                      source_reference='software-test-only',decision='approved',reviewed_observations=observations)
        ledger = tmp_path/(name+'.review.json')
        ledger.write_text(json.dumps(record))
        return ToolEvidenceProvenance(origin='manual_review',output_sha256=record['output_sha256'],
                                      record_file=ledger,record_sha256=sha256(ledger.read_bytes()).hexdigest())
    disorder_file=tmp_path/'iupred.txt'
    disorder_file.write_text(''.join(f'{i} {a} 0.9\n' for i,a in enumerate(SEQUENCE,1)))
    disorder=parse_iupred2a_output(disorder_file,tool_version='fixture',input_sha256=h)
    fields=('scores','disorder_mean','disorder_fraction','longest_disordered_run','longest_folded_run')
    disorder.provenance=attach(disorder,'IUPred2A',disorder_file,{k:getattr(disorder,k) for k in fields})
    secondary_file=tmp_path/'psipred.ss2'
    secondary_file.write_text(''.join(f'{i} {a} C 1 0 0\n' for i,a in enumerate(SEQUENCE,1)))
    secondary=parse_secondary_structure_output(secondary_file,tool_name='PSIPRED',tool_version='fixture',input_sha256=h)
    secondary.provenance=attach(secondary,'PSIPRED',secondary_file,{k:getattr(secondary,k) for k in ('states','ss_fraction','longest_ss_run')})
    seg_file=tmp_path/'seg.fasta';seg_file.write_text('>fixture\n'+SEQUENCE+'\n')
    seg=parse_seg_fasta(seg_file,tool_version='fixture',input_sha256=h,expected_length=len(SEQUENCE))
    seg.provenance=attach(seg,'SEG',seg_file,{k:getattr(seg,k) for k in ('sequence_length','low_complexity_positions','low_complexity_fraction')})
    fusion=FusionToolEvidence(input_sha256=h,signalp_tool_version='fixture',deeptmhmm_tool_version='fixture',
                              aggregation_tool='PASTA2',aggregation_tool_version='fixture',
                              signal_peptide_with_clear_cleavage=False,transmembrane_helix_count=0,
                              continuous_high_aggregation_hotspots=0)
    for name,attribute,observation in [('SignalP','signalp_source_file','signal_peptide_with_clear_cleavage'),
                                      ('DeepTMHMM','deeptmhmm_source_file','transmembrane_helix_count'),
                                      ('PASTA2','aggregation_source_file','continuous_high_aggregation_hotspots')]:
        path=tmp_path/(name+'.raw.txt');path.write_text('synthetic software fixture; not a tool run\n')
        setattr(fusion,attribute,path)
        fusion.provenance[name]=attach(fusion,name,path,{observation:getattr(fusion,observation)})
    return dict(features=features(),sequence=SEQUENCE,sequence_kind='idr',rules=M1V3Rules(rule_version='fixture'),
                disorder=disorder,secondary_structure=secondary,seg=seg,
                protparam=compute_protparam_evidence(SEQUENCE,input_sha256=h),fusion_evidence=fusion,full_fusion_sha256=h)


def test_byte_bound_reviewed_raw_evidence_and_tampering(tmp_path):
    arguments=audited(tmp_path)
    assert screen_sequence_v3(**arguments).verdict=='pass'
    arguments['disorder'].source_file.write_text('1 G 0.1\n')
    with pytest.raises(ValueError,match='output_hash_mismatch'):
        screen_sequence_v3(**arguments)


def test_missing_original_files_do_not_pass(tmp_path):
    arguments=audited(tmp_path)
    arguments['secondary_structure'].source_file.unlink()
    assert screen_sequence_v3(**arguments).verdict=='blocked'


def test_length_and_declared_summary_cannot_override_raw_arrays(tmp_path):
    arguments=audited(tmp_path)
    arguments['disorder'].scores=[.9]
    with pytest.raises(ValueError,match='length_mismatch'):
        screen_sequence_v3(**arguments)
    arguments=audited(tmp_path)
    arguments['disorder'].longest_disordered_run=100
    with pytest.raises(ValueError,match='summary_or_array_mismatch'):
        screen_sequence_v3(**arguments)


@pytest.mark.parametrize('raw',['2 G 0.9\n1 S 0.9\n','1 G nan\n','1 G 1.2\n','1 A 0.9\n'])
def test_bad_residue_or_score_cannot_be_parsed(tmp_path,raw):
    path=tmp_path/'iupred.txt';path.write_text(raw)
    with pytest.raises(ValueError):
        parse_iupred2a_output(path,tool_version='fixture',input_sha256=sha256(b'GS').hexdigest())


@pytest.mark.parametrize('orientation',['N-terminal','C_terminal_scaffold_appendage','enzyme-linker-ligand'])
def test_orientation_is_not_localization(orientation):
    config=load_config(ROOT/'configs/m1_m4_example.yaml');config.execution.mode='demo'
    definitions,digest=M1FeatureDefinitions.from_yaml(ROOT/'configs/m1_feature_definitions.yaml')
    construct=ConstructDefinition(id='fixture',components=['a'],fusion_orientation=orientation,localization_context='cytosolic')
    result=_screen_m1_sequence('MA','full_fusion',{}, {'fusion':dict(input_sha256=sha256(b'MA').hexdigest(),
        signal_peptide_with_clear_cleavage=True,transmembrane_helix_count=1,continuous_high_aggregation_hotspots=0)},
        definitions,digest,M1V3Rules(rule_version='fixture'),config.stages.m1_llps,config,sha256(b'MA').hexdigest(),construct)
    assert result.localization_context=='cytosolic' and result.verdict=='reject'


def test_missing_location_and_unapproved_review_block_real_path(tmp_path):
    config=load_config(ROOT/'configs/m1_m4_example.yaml');config.execution.mode='real'
    config.stages.m1_llps.require_external_evidence_in_real_mode=False
    config.inputs.idr_id=None
    construct=ConstructDefinition(id='fixture',components=['a'],sequences={'a':'MA'},coding_dna='ATGGCTTAA',
        sequence_source_ref='software-fixture',forbidden_restriction_sites={})
    config.inputs.constructs=[construct]
    rows,_=run_m1(config,tmp_path/'missing')
    assert not rows[0].recommended_for_m2
    assert 'localization_context_not_specified' in rows[0].screen_flags
    construct.localization_context='er_anchored';construct.localization_design_evidence='software-fixture'
    evidence=tmp_path/'evidence.json'
    evidence.write_text(json.dumps({'fixture':{'fusion':dict(input_sha256=sha256(b'MA').hexdigest(),
        signal_peptide_with_clear_cleavage=True,transmembrane_helix_count=0,continuous_high_aggregation_hotspots=0)}}))
    config.stages.m1_llps.predictor_evidence_file=evidence
    rows,_=run_m1(config,tmp_path/'review')
    assert rows[0].sequence_screen_verdict=='review' and not rows[0].recommended_for_m2
