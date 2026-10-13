"""Reuse exact model pairs, then run missing full sequences on a verified GPU.

Run this in the user's configured computation environment. No structural metric,
pocket, topology, concentration, or physical condition is filled by this command.
"""
import argparse
import csv
import json
from pathlib import Path
import subprocess
from hashlib import sha256

from Bio import SeqIO
from prepare_m2_models import inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-pack',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--models-root',type=Path,action='append',default=[])
    parser.add_argument('--prediction-python',type=Path,
                        help='Python executable in the installed ColabFold/JAX GPU environment.')
    parser.add_argument('--include-unconfirmed-reporter',action='store_true')
    parser.add_argument('--run',action='store_true',help='Execute actual missing-target predictions.')
    args=parser.parse_args()
    pack=args.input_pack.resolve(strict=True);out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    with (pack/'M2_prediction_targets.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    selected=[r for r in rows if args.include_unconfirmed_reporter or r['priority']!='B_confirm_adoption']
    sequences={}
    for row in selected:
        found=[r for r in SeqIO.parse(pack/row['source_fasta'],'fasta') if r.id==row['record_id']]
        if len(found)!=1 or len(found[0].seq)!=int(row['aa_length']):
            raise ValueError('target_requires_one_exact_length_checked_sequence')
        sequences[row['record_id']]=found[0]
    selected_file=out/'selected_targets.csv'
    with selected_file.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(selected)
    roots=[r.resolve(strict=True) for r in args.models_root]
    models=out/'colabfold';models.mkdir(exist_ok=True);roots.append(models)
    report=inventory(selected_file,pack,roots)
    (out/'model_inventory_before.json').write_text(json.dumps(report,indent=2)+'\n')
    missing=[r for r in report['targets'] if not r['models']]
    plan={'scope':'actual full-sequence model preparation, not full M2 scientific approval',
          'selected_target_ids':[r['record_id'] for r in report['targets']],
          'missing_target_ids':[r['record_id'] for r in missing],
          'unconfirmed_reporter_included':args.include_unconfirmed_reporter,
          'status':'models_already_available' if not missing else 'execution_required'}
    (out/'preparation_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    if not missing or not args.run:
        print(json.dumps(plan));return
    if args.prediction_python is None:
        parser.error('--run requires --prediction-python; never guess the private GPU runtime path')
    # Retain the venv entrypoint; resolving its symlink loses its dependencies.
    py=args.prediction_python.absolute()
    probe='''import json,importlib.metadata,jax
v=importlib.metadata.version("colabfold")
d=jax.devices()
assert v=="1.6.2", "Use the project-pinned ColabFold1.6.2, or explicitly review a version change."
assert any(x.platform=="gpu" for x in d), "The prediction interpreter has no usable JAX GPU; CPU fallback is not approved."
print(json.dumps({"colabfold_version":v,"devices":[{"platform":x.platform,"kind":x.device_kind} for x in d]}))
'''
    check=subprocess.run([str(py),'-c',probe],capture_output=True,text=True)
    (out/'gpu_probe.stdout.txt').write_text(check.stdout)
    (out/'gpu_probe.stderr.txt').write_text(check.stderr)
    if check.returncode:
        plan.update(status='gpu_environment_failed',returncode=check.returncode)
        (out/'preparation_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
        raise SystemExit('GPU environment probe failed; inspect private backend logs. No model was generated.')
    # One task per target retains all native model/seed/PAE/MSA outputs and allows resumption.
    order=sorted(missing,key=lambda r:(len(sequences[r['record_id']].seq),r['record_id']))
    executions=[]
    for target in order:
        identifier=target['record_id'];sequence=sequences[identifier]
        input_file=out/(identifier+'.fasta');SeqIO.write(sequence,input_file,'fasta')
        digest=sha256(str(sequence.seq).encode()).hexdigest()
        target_out=models/(identifier+'-'+digest[:16]);target_out.mkdir(exist_ok=True)
        argv=[str(py),'-m','colabfold.batch',str(input_file),str(target_out)]
        (target_out/'requested_execution.json').write_text(json.dumps({'argv':argv,
            'settings_source':'unpadded complete input; original installed ColabFold1.6.2 algorithm defaults',
            'biological_parameters_supplied':False},indent=2)+'\n')
        with (target_out/'execution.stdout.txt').open('w') as stdout,(target_out/'execution.stderr.txt').open('w') as stderr:
            job=subprocess.run(argv,stdout=stdout,stderr=stderr)
        executions.append({'record_id':identifier,'returncode':job.returncode,'argv':argv})
        (out/'executions.json').write_text(json.dumps(executions,indent=2)+'\n')
        if job.returncode:raise SystemExit('Native prediction failed; original partial outputs retained. Do not substitute a model.')
        after=inventory(selected_file,pack,roots)
        (out/'model_inventory_current.json').write_text(json.dumps(after,indent=2)+'\n')
        matched=next(t for t in after['targets'] if t['record_id']==identifier)
        if not matched['models']:raise SystemExit('No exact complete paired model after native execution.')
    final=inventory(selected_file,pack,roots)
    (out/'model_inventory_after.json').write_text(json.dumps(final,indent=2)+'\n')
    print(json.dumps({'model_inputs_ready':final['model_inputs_ready'],'generated_targets':[r['record_id'] for r in executions],
                      'full_M2_acceptance':False}))
    if not final['model_inputs_ready']:raise SystemExit(2)


if __name__=='__main__':main()
