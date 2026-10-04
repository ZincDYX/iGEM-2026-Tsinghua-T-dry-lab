"""Directed numerical fault audit in fresh isolated copies, never production files."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

FAULTS = {
    'MU01':('prediction.py',
        'params = FullNetworkParameters(**raw)',
        'params = FullNetworkParameters(**{**raw, "metabolite_kp": contract.kernel_inputs["parameters"]["metabolite_kp"]})',
        'test_MU01_active_kp_replay_matches_two_phase_initial_rate'),
    'MU02':('prediction.py',
        '(contract.intracellular_volume_l * np.asarray(inside[name]) + contract.extracellular_volume_l * np.asarray(outside[name])) / result.extraction_volume_l',
        '(np.asarray(inside[name]) + np.asarray(outside[name]))',
        'test_MU02_observation_matches_independent_amount_normalization'),
    'MU03':('research_validation.py',
        'float(np.linalg.norm(residual)/np.sqrt(len(indices))) if indices else None',
        '0.0 if indices else None',
        'test_MU03_holdout_nonzero_error_has_hand_computed_statistics'),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parents[1]
    test='tests/test_independent_numeric_oracles.py'
    protected={name:digest(root/'src/igem_drylab'/name) for name in {f[0] for f in FAULTS.values()}}
    def execute(name,target,fault=None):
        env={**os.environ,'PYTHONPATH':str(target/'src'),'PYTHONDONTWRITEBYTECODE':'1'}
        xml=args.output/f'{name}.xml'
        selector=test if fault is None else test+'::'+fault[3]
        run=subprocess.run([sys.executable,'-m','pytest','-q',selector,'--junitxml='+str(xml)],
            cwd=target,env=env,capture_output=True,text=True,timeout=120)
        (args.output/f'{name}.log').write_text(run.stdout+run.stderr,encoding='utf-8')
        tree=ET.parse(xml)
        failures=[n for n in tree.iter('failure')]
        errors=list(tree.iter('error'))
        if fault is None:
            accepted=run.returncode==0 and not errors and not failures
        else:
            # Import/setup/timeout/hash failures do not count as numerical detection.
            accepted=run.returncode==1 and not errors and bool(failures) and all(
                'AssertionError' in (n.text or '') and n.attrib.get('message','').startswith('assert ') for n in failures)
        return {'exit_code':run.returncode,'numerical_failures':len(failures),'errors':len(errors),'accepted':accepted,
            'target':selector,'log_sha256':digest(args.output/f'{name}.log')}
    reports={}
    with tempfile.TemporaryDirectory(prefix='igem-numeric-faults-') as scratch:
        scratch=Path(scratch)
        for name in ['correct',*FAULTS]:
            target=scratch/name
            target.mkdir()
            for directory in ('src','tests','data','configs','examples'):
                shutil.copytree(root/directory,target/directory,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            shutil.copy2(root/'pyproject.toml',target/'pyproject.toml')
            shutil.copy2(root/'test_risk_manifest.yaml',target/'test_risk_manifest.yaml')
            fault=FAULTS.get(name)
            if fault:
                path=target/'src/igem_drylab'/fault[0]
                source=path.read_text(encoding='utf-8')
                if source.count(fault[1])!=1:
                    raise RuntimeError(f'{name}: mutation anchor must occur exactly once')
                path.write_text(source.replace(fault[1],fault[2]),encoding='utf-8')
            reports[name]=execute(name,target,fault)
    unchanged=all(digest(root/'src/igem_drylab'/name)==sha for name,sha in protected.items())
    summary={'claim_scope':'directed_software_numeric_fault_detection_not_biological_validation',
        'production_sources_unchanged':unchanged,'source_sha256':protected,'runs':reports,
        'passed':unchanged and all(r['accepted'] for r in reports.values())}
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
    return 0 if summary['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
