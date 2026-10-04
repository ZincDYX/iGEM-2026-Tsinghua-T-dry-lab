"""Package actual air-lab review runs and verify the deployed committed tree."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import xml.etree.ElementTree as ET
import zipfile


def save(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results',type=Path,required=True)
    parser.add_argument('--repository',type=Path,required=True)
    parser.add_argument('--release-tar',type=Path,required=True)
    parser.add_argument('--commit',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    results=args.results.resolve();repo=args.repository.resolve()
    checks=[]
    with tarfile.open(args.release_tar) as archive:
        for entry in archive.getmembers():
            if not entry.isfile():continue
            path=repo.joinpath(entry.name).resolve()
            if not path.is_relative_to(repo):raise ValueError('archive_path_outside_repository')
            expected=archive.extractfile(entry).read()
            actual=path.read_bytes()
            if actual!=expected:raise ValueError(f'deployment_mismatch:{entry.name}')
            checks.append({'path':entry.name,'bytes':len(actual),'sha256':hashlib.sha256(actual).hexdigest()})
    deployment={'commit':args.commit,'verified_files':len(checks),'files':checks,
        'scope':'Complete committed first-party tree; ignored input/output/credentials retained, third-party submodule contents not embedded',
        'verified_at_utc':datetime.now(timezone.utc).isoformat()}
    save(results/'deployment_source_checks.json',deployment)
    save(repo/'new_review_deployment_manifest.json',deployment)
    for name,python in [('production','/mnt/data/dyx/miniconda3/envs/drylab-m1m2/bin/python'),
                        ('historical','/mnt/data/dyx/drylab-envs/glabridin-reference/bin/python')]:
        freeze=subprocess.check_output([python,'-m','pip','freeze','--all'],text=True)
        (results/f'{name}_environment.lock.txt').write_text(freeze,encoding='utf-8')
    supplied=results/'input-review-evidence.zip'
    with zipfile.ZipFile(supplied) as archive:
        manifest=json.loads(archive.read('MANIFEST.json'))
        for record in manifest['files']:
            raw=archive.read(record['path'])
            if len(raw)!=record['bytes'] or hashlib.sha256(raw).hexdigest()!=record['sha256']:
                raise ValueError(f'supplied_review_evidence_hash_mismatch:{record["path"]}')
    save(results/'supplied_review_identity.json',{'zip_sha256':hashlib.sha256(supplied.read_bytes()).hexdigest(),
        'verified_manifest_entries':len(manifest['files']),'reviewed_baseline':manifest['reviewed_commit'],
        'software_counterexamples_are_not_scientific_parameters':True})
    historical=json.loads((results/'final-historical/numerical_comparisons.json').read_text())
    modern=json.loads((results/'final-modern/numerical_comparisons.json').read_text())
    control=json.loads((results/'final-interpolation-control/lsoda_interpolation_diagnosis.json').read_text())
    targets=[]
    for old,new in zip(historical,modern,strict=True):
        if old['target_id']!=new['target_id']:raise ValueError('target_order_mismatch')
        target=old['target_id']
        cause=('confirmed_dense_output_implementation_difference' if target=='Fig4h' or target.endswith('undocumented_ungated') else
               'documented_zero_branch_contradiction' if target.endswith('documented_zero') else
               'consistent_with_dense_output_difference_not_all_scenarios_separately_controlled' if target=='SupplementaryFig18b' else
               'small_published_scan_difference_cause_unconfirmed' if target=='SupplementaryFig18c' else 'author_adapter_identity')
        targets.append({'target_id':target,'source_kind':old['source_kind'],'historical':old,'modern':new,'diagnosis':cause})
    suites=ET.parse(results/'tests.xml').getroot().findall('testsuite')
    totals={key:sum(int(suite.attrib.get(key,0)) for suite in suites) for key in ('tests','failures','errors','skipped')}
    save(results/'review_validation_summary.json',{'code_commit':args.commit,'backend_tests':totals,'targets':targets,
        'lsoda_control_endpoint_invariance':control['endpoint_invariance'],
        'known_uncertainties':['Original complete author environment and per-figure configurations',
            'Source scientific reporting precision; storage identity is not biological acceptance',
            'S18 remaining tiny differences; source units and transport labels; kinetic panels d/j',
            'Full M3 S4/r_target/F2/F3 and ER model; independent wet-lab predictive validation'],
        'external_tools':'No new installs, licensed predictions or full MD runs claimed in this revision'})
    files=[]
    for directory in ('final-historical','final-modern','final-interpolation-control'):
        files.extend(path for path in (results/directory).rglob('*') if path.is_file())
    files.extend(results/name for name in ('tests.xml','tests-first-pass.xml','final-historical.log','final-modern.log',
        'deployment_source_checks.json','production_environment.lock.txt','historical_environment.lock.txt',
        'supplied_review_identity.json','review_validation_summary.json'))
    # Deliver the previously cited independent raw diagnostic too; not rerun here.
    for name in ('reference_diagnosis_20261004.json','source_workbook_versions.json'):
        path=results.parent/name
        if path.exists():files.append(path)
    for path in files:
        if not path.exists():raise FileNotFoundError(path)
    records=[{'path':path.relative_to(results).as_posix() if path.is_relative_to(results) else 'prior-evidence/'+path.name,
              'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for path in sorted(files)]
    save(results/'EVIDENCE_MANIFEST.json',{'commit':args.commit,'files':records,
        'scope':'Actual air-lab software regression and numerical reproduction evidence, not new wet-lab measurements'})
    with zipfile.ZipFile(args.output,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for path,record in zip(sorted(files),records,strict=True):archive.write(path,record['path'])
        archive.write(results/'EVIDENCE_MANIFEST.json','EVIDENCE_MANIFEST.json')
    print(json.dumps({'output':str(args.output),'files':len(records),'bytes':args.output.stat().st_size,
        'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),'backend_tests':totals,'verified_source_files':len(checks)},indent=2))


if __name__=='__main__':main()
