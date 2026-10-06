"""Actual server evidence and byte-exact committed release verification."""
import argparse
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository',type=Path,required=True)
    parser.add_argument('--release-tar',type=Path,required=True)
    parser.add_argument('--results',type=Path,required=True)
    parser.add_argument('--commit',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--scope',default='server_software_regressions_not_biological_validation')
    parser.add_argument('--mutation-summary',type=Path)
    args = parser.parse_args()
    repo = args.repository.resolve()
    checked = []
    with tarfile.open(args.release_tar) as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            target = (repo/member.name).resolve()
            if not target.is_relative_to(repo):
                raise ValueError('release_path_outside_repository')
            raw = archive.extractfile(member).read()
            if target.read_bytes()!=raw:
                raise ValueError('server_source_differs_from_bundle:'+member.name)
            checked.append({'path':member.name,'bytes':len(raw),'sha256':sha256(raw).hexdigest()})
    source = {'commit':args.commit,'verified_files':len(checked),'files':checked,
              'verified_at':datetime.now(timezone.utc).isoformat()}
    (args.results/'deployment_source_checks.json').write_text(json.dumps(source,indent=2))
    (repo/'latest_review_deployment_manifest.json').write_text(json.dumps(source,indent=2))
    suites = ET.parse(args.results/'full-tests.xml').getroot().findall('testsuite')
    counts = {key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ('tests','failures','errors','skipped')}
    if not counts['tests'] or any(counts[k] for k in ('failures','errors','skipped')):
        raise ValueError('final_server_tests_not_fully_passed')
    groups={}
    risk_ids=set()
    for suite in suites:
        for case in suite.findall('testcase'):
            properties=case.find('properties')
            metadata={p.attrib['name']:p.attrib.get('value','') for p in properties} if properties is not None else {}
            group=metadata.get('test_group','regression')
            groups[group]=groups.get(group,0)+1
            if metadata.get('risk_id'):risk_ids.add(metadata['risk_id'])
    mutations=None
    if args.mutation_summary:
        mutations=json.loads(args.mutation_summary.read_text())
        if not mutations.get('passed') or not mutations.get('production_sources_unchanged'):
            raise ValueError('directed_numeric_fault_audit_not_passed')
    lock = subprocess.check_output([sys.executable,'-m','pip','freeze','--all'],text=True)
    (args.results/'production_environment.lock.txt').write_text(lock)
    summary = {'commit':args.commit,'backend_tests':counts,
        'duration_seconds':sum(float(s.attrib.get('time',0)) for s in suites),
        'scope':args.scope,
        'test_groups':groups,'tracked_risk_ids':sorted(risk_ids),
        'directed_numeric_fault_audit':mutations,
        'paper_reproduction':'prior_c1da257_evidence_retained_not_rerun_in_this_release',
        'pending':['real_fusion_phase_and_activity_inputs_and_independent_holdout','actual_project_genetic_and_background_absence_evidence',
            'correlated_parameter_sampling_and_verified_IDR_mapping','new_licensed_predictor_jobs_and_version_specific_parsers',
            'actual_project_transport_calibration_and_applicability_evidence','ER_and_non_equilibrium_model_specification_and_data',
            'global_stability_and_exhaustive_root_completeness_not_proven'],
        'verified_files':len(checked)}
    (args.results/'validation_summary.json').write_text(json.dumps(summary,indent=2))
    files = [p for p in sorted(args.results.rglob('*')) if p.is_file() and p.suffix in {'.xml','.log','.json','.txt','.md','.csv'} and p.name!='EVIDENCE_MANIFEST.json']
    records = [{'path':str(p.relative_to(args.results)),'bytes':p.stat().st_size,'sha256':sha256(p.read_bytes()).hexdigest()} for p in files]
    manifest = {'commit':args.commit,'scope':summary['scope'],'files':records}
    manifest_file = args.results/'EVIDENCE_MANIFEST.json'
    manifest_file.write_text(json.dumps(manifest,indent=2))
    if args.output.exists():
        raise ValueError('evidence_package_exists_preserve_previous_release')
    with zipfile.ZipFile(args.output,'w',compression=zipfile.ZIP_DEFLATED) as package:
        for path,record in zip(files,records,strict=True):
            package.write(path,record['path'])
        package.write(manifest_file,'EVIDENCE_MANIFEST.json')
    print(json.dumps({**summary,'evidence_files':len(records),'output_sha256':sha256(args.output.read_bytes()).hexdigest()}))


if __name__=='__main__':
    main()
