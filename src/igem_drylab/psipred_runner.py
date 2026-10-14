"""Original PSIPRED V4 profile route, full sequence, no single-sequence fallback.

Commands follow the author's classic BLAST runpsipred script. Databases and
weights remain separately installed; do not bundle native code or a database.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from .jpred_runner import _save_state


def main():
    from Bio import SeqIO
    from .constructs.linker_features import parse_secondary_structure_output
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fasta',type=Path,required=True)
    parser.add_argument('--record',required=True)
    parser.add_argument('--psipred-root',type=Path,required=True)
    parser.add_argument('--ncbi-bin',type=Path,required=True)
    parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--database-release',required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--threads',type=int,default=1)
    args=parser.parse_args()
    records=list(SeqIO.parse(args.fasta,'fasta'))
    if len(records)!=1 or records[0].id!=args.record:raise ValueError('PSIPRED_requires_one_exact_complete_FASTA_record')
    sequence=str(records[0].seq)
    if not sequence or set(sequence)-set('ACDEFGHIKLMNPQRSTVWY'):raise ValueError('PSIPRED_requires_standard_full_sequence')
    if args.threads<1:raise ValueError('PSIPRED_threads_must_be_positive')
    root=args.psipred_root.resolve();ncbi=args.ncbi_bin.resolve();database=args.database.resolve()
    output=args.output_dir.resolve();output.mkdir(parents=True,exist_ok=True)
    version=(root/'VERSION').read_text().strip()
    state=output/'native-state.json'
    identity=dict(input_sha256=sha256(sequence.encode()).hexdigest(),database=str(database),database_release=args.database_release,tool_version=version)
    if state.exists():
        old=json.loads(state.read_text())
        if old.get('identity')!=identity:raise ValueError('PSIPRED_saved_input_or_database_changed')
        if old['status']=='validated':print(json.dumps(dict(status='validated',reused=True)));return
        raise ValueError('PSIPRED_interrupted_native_job_requires_explicit_attempt_review')
    _save_state(state,dict(status='prepared',identity=identity))
    fasta=output/'input.fasta';fasta.write_text('>'+args.record+'\n'+sequence+'\n')
    checkpoint=output/'native.chk';commands=[]
    def run(command,filename):
        commands.append(list(map(str,command)))
        with (output/filename).open('w') as log:
            subprocess.run(command,cwd=output,stdout=log,stderr=subprocess.STDOUT,check=True)
    _save_state(state,dict(status='running_native_profile',identity=identity))
    run([str(ncbi/'blastpgp'),'-b','0','-j','3','-h','0.001','-v','5000','-a',str(args.threads),
         '-d',str(database),'-i',str(fasta),'-C',str(checkpoint)],'native.blast')
    (output/'native.pn').write_text(str(checkpoint)+'\n');(output/'native.sn').write_text(str(fasta)+'\n')
    run([str(ncbi/'makemat'),'-P',str(output/'native')],'makemat.log')
    data=root/'data';binary=root/'bin'
    run([str(binary/'psipred'),str(output/'native.mtx'),str(data/'weights.dat'),str(data/'weights.dat2'),str(data/'weights.dat3')],'native.ss')
    raw=output/'native.ss2'
    run([str(binary/'psipass2'),str(data/'weights_p2.dat'),'1','1.0','1.0',str(raw),str(output/'native.ss')],'native.horiz')
    homologs=sorted(set(re.findall(r'^UniRef90_\S+', (output/'native.blast').read_text(),re.M)))
    record=dict(tool_name='PSIPRED',tool_version=version,origin='automated',returncode=0,
        input_sha256=identity['input_sha256'],output_sha256=sha256(raw.read_bytes()).hexdigest(),
        command=commands,database_release=args.database_release,profile_route='author_classic_BLAST_runpsipred',
        reported_homolog_count=len(homologs),source_reference='https://github.com/psipred/psipred')
    raw.with_suffix('.run.json').write_text(json.dumps(record,indent=2))
    secondary=parse_secondary_structure_output(raw,tool_name='PSIPRED',tool_version=version,input_sha256=identity['input_sha256'])
    (output/'secondary.json').write_text(secondary.model_dump_json(indent=2))
    _save_state(state,dict(status='validated',identity=identity,reported_homolog_count=len(homologs),
        method_applicability='profile_present_requires_sequence_context_review' if homologs else 'no_reported_homologs_not_a_calibrated_hard_veto'))
    print(json.dumps(dict(status='validated',input_length=len(sequence),reported_homolog_count=len(homologs))))


if __name__=='__main__':main()
