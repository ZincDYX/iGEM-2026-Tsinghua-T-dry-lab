from __future__ import annotations

from pathlib import Path
import json

from igem_drylab.pipeline import load_config, run_pipeline


def test_M1_failure_blocks_downstream_even_when_metric_files_are_configured(tmp_path):
    config = load_config(Path("configs/m1_m4_real_scoring_example.yaml"))
    config.run.output_dir = tmp_path

    manifest = run_pipeline(config)
    m2_text = (manifest.run_dir / "m2_structure_screen" / "fusion_assessments.json").read_text(encoding="utf-8")
    m4_text = manifest.stages[3].json_file.read_text(encoding="utf-8")

    m2_records = json.loads(m2_text)
    m1_records=json.loads(manifest.stages[0].json_file.read_text(encoding='utf-8'))
    expected={record['candidate_id'] for record in m1_records}
    assert expected and len(m2_records)==len(expected)
    assert {record['candidate_id'] for record in m2_records}==expected
    assert all(record["screen_verdict"] == "blocked" for record in m2_records)
    assert all(not record["recommended_for_m3"] for record in m2_records)
    assert all("M1 construct screen must pass" in record["missing_inputs"] for record in m2_records)
    assert '"status": "insufficient_data"' in m4_text


def test_complete_hash_verified_M2_metrics_are_consumed_and_each_resource_is_bound(tmp_path):
    """Actual pipeline gate with file-backed software fixtures, not structure validation."""
    from hashlib import sha256
    from igem_drylab.pipeline.models import M1Candidate
    from igem_drylab.pipeline.stages import run_m2
    config=load_config(Path('configs/m1_m4_real_scoring_example.yaml'))
    config.stages.m3_concentration.recruitment_mode='legacy_independent_partition'
    resources={}
    for name in ('model','reference','geometry','sasa'):
        path=tmp_path/name
        path.write_bytes(('software-fixture-'+name).encode())
        resources[name]=(str(path),sha256(path.read_bytes()).hexdigest())
    metric=dict(candidate_id='fixture',source_tool='fixture',source_tool_version='1',
        artifact_path=resources['model'][0],artifact_sha256=resources['model'][1],
        prediction_input_sequence_sha256='a'*64,chain_sequence_sha256={'A':'a'*64},reference_structure_id='fixture',
        reference_artifact_path=resources['reference'][0],reference_artifact_sha256=resources['reference'][1],
        geometry_input_path=resources['geometry'][0],geometry_input_sha256=resources['geometry'][1],
        sasa_configuration_path=resources['sasa'][0],sasa_configuration_hash=resources['sasa'][1],
        clash_rule_provenance='fixture',pocket_definition_source_ref='fixture',residue_mapping_source_ref='fixture',
        core_residue_ids=[1,2,3],pocket_residue_ids=[4],core_mean_plddt=90.,pocket_mean_plddt=90.,
        ligand_buried=False,recruitment_domain_buried=False,scaffold_interface_disrupted=False,
        core_ca_rmsd_angstrom=.25,pocket_rmsd_angstrom=.5,sasa_retention=.95,mean_plddt=90.,
        clash_count=0,clash_cutoff_angstrom=2.5)
    metrics_file=tmp_path/'metrics.json';metrics_file.write_text(json.dumps([metric]))
    config.stages.m2_fusion.structure_metrics_file=metrics_file
    candidate=M1Candidate(candidate_id='fixture',construct_id='fixture',construct_definition={},
        recommended_for_m2=True,full_sequence_sha256='a'*64)
    rows,_=run_m2(config,tmp_path/'valid',[candidate])
    assert [r.candidate_id for r in rows]==['fixture']
    assert rows[0].screen_verdict=='pass' and rows[0].recommended_for_m3
    assert rows[0].core_ca_rmsd_angstrom==.25 and rows[0].pocket_sasa_retention==.95
    for name,label in (('model','structure'),('reference','reference'),('geometry','geometry input'),('sasa','SASA configuration')):
        path=Path(resources[name][0]);original=path.read_bytes();path.write_bytes(b'tampered')
        broken,_=run_m2(config,tmp_path/('tampered-'+name),[candidate])
        assert broken[0].screen_verdict=='blocked'
        assert f'M2 {label} artifact SHA-256 match' in broken[0].missing_inputs
        path.write_bytes(original)
