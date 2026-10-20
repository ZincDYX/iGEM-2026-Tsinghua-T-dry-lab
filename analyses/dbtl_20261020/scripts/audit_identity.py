"""Targeted source/translation identity review; no prediction or structure rerun."""
from pathlib import Path
import os
from hashlib import sha256
from zipfile import ZipFile
from datetime import datetime,timezone
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.Align import PairwiseAligner
import csv
import io
import json
import difflib

ROOT=Path(os.environ.get('GALATEA_STUDY_ROOT',str(Path(__file__).resolve().parents[1]))).resolve()
SOURCEZIP=Path(os.environ.get('GALATEA_CONSTRUCT_ARCHIVE',str(ROOT/'inputs/constructs.zip')))
OVERRIDE=Path(os.environ.get('GALATEA_Q29_OVERRIDE',str(ROOT/'inputs/Q29_override.dna')))
def rows(name):return list(csv.DictReader((ROOT/name).open(encoding='utf-8-sig')))
def save(name,data):(ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
def out(name,data):
    with (ROOT/name).open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)

def find_product(sequence,protein):
    n=len(sequence);hits=[]
    for strand,dna in [(1,sequence),(-1,str(Seq(sequence).reverse_complement()))]:
        extended=dna+dna
        for frame in range(3):
            cut=extended[frame:];translated=str(Seq(cut[:len(cut)//3*3]).translate())
            i=translated.find(protein)
            if i>=0 and frame+3*i<n:
                start=frame+3*i
                hits.append({'strand':strand,'oriented_nt_start_zero_based':start,'nt_length_without_stop':3*len(protein),
                    'full_peptide_found':True,'genomic_start_zero_based':start if strand==1 else (n-start-3*len(protein))%n})
    return hits

def main():
    if (ROOT/'identity_tests.json').exists():raise ValueError('Use a new directory; do not overwrite completed identity results')
    products=rows('inputs/protein_products.csv');constructs={r['q_id']:r for r in rows('inputs/construct_manifest.csv')}
    provenance=json.loads((ROOT/'inputs/M1_provenance.json').read_text(encoding='utf8'))
    ziphash=sha256(SOURCEZIP.read_bytes()).hexdigest();overridehash=sha256(OVERRIDE.read_bytes()).hexdigest()
    assert ziphash==provenance['source_zip_sha256'] and overridehash==provenance['q29_override_sha256']
    selected=('Q05','Q21','Q24','Q29','Q10','Q13');features=[];checks=[];snapshots=[]
    with ZipFile(SOURCEZIP) as archive:
        for qid in selected:
            source=constructs[qid]['source_file']
            if qid=='Q29':raw=OVERRIDE.read_bytes();member=None
            else:
                names=[n for n in archive.namelist() if n.endswith('/'+source)]
                assert len(names)==1,(qid,source,names)
                member=names[0];raw=archive.read(member)
            destination=ROOT/'inputs/DNA'/f'{qid}.dna';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
            record=SeqIO.read(io.BytesIO(raw),'snapgene');dna=str(record.seq).upper()
            snapshots.append({'q_id':qid,'original':str(OVERRIDE if qid=='Q29' else SOURCEZIP),'member':member,
                'copy':str(destination.relative_to(ROOT)),'file_sha256':sha256(raw).hexdigest(),'plasmid_bp':len(dna)})
            for f in record.features:
                label='; '.join(f.qualifiers.get('label',[]))
                if f.type=='CDS' or any(term.lower() in label.lower() for term in ('anchor','linker','IDR','LLPS','SH3','FTH1')):
                    features.append({'q_id':qid,'feature_type':f.type,'label':label,'location':str(f.location),'nt_length':len(f),
                        'strand':f.location.strand,'start_zero_based':int(f.location.start),'end_exclusive':int(f.location.end)})
            for p in [p for p in products if p['q_id']==qid]:
                digest=sha256(p['sequence'].encode()).hexdigest();assert digest==p['sequence_sha256']
                hits=find_product(dna,p['sequence'])
                checks.append({'q_id':qid,'product_id':p['product_id'],'aa_length':len(p['sequence']),
                    'sequence_sha256':digest,'found_in_unchanged_source_DNA':bool(hits),'DNA_hits':json.dumps(hits),
                    'existing_topology':p['deeptmhmm_topology'],'seed_label':p['seed_label'],
                    'new_full_prediction_run':False})
        # Preserve the superseded Q29 source for an explicit, non-overwriting comparison.
        old=archive.read(next(n for n in archive.namelist() if n.endswith('/对照组正常表达DMT.dna')))
        oldrecord=SeqIO.read(io.BytesIO(old),'snapgene')
    assert all(c['found_in_unchanged_source_DNA'] for c in checks)
    aligner=PairwiseAligner(mode='local',match_score=2,mismatch_score=-1,open_gap_score=-5,extend_gap_score=-.5)
    seq={r['product_id']:r['sequence'] for r in products}
    alignment=aligner.align(seq['Q05_P02'],seq['Q29_P01'])[0]
    q05={'local_aligned_blocks_zero_based':alignment.aligned.tolist(),'score':alignment.score,
        'interpretation':'Q05_P02 begins with the 211-aa exact segment aligning to positions 150:361 of Q29_P01; not a full DMT CDS',
        'prior_annotation_overlap_nt':633,'prior_annotation_length_nt':1080,'prior_overlap_source':'preserved anomalies.txt; 633=211*3',
        'wetlab_identity':'BLOCKED until intended construct and sequencing/sample records are reconciled'}
    a,b=seq['Q10_P02'],seq['Q13_P02'];matcher=difflib.SequenceMatcher(None,a,b,autojunk=False)
    changes=[{'operation':op,'Q10_range_zero_based':[i,j],'Q13_range_zero_based':[k,l],
        'Q10_sequence':a[i:j],'Q13_sequence':b[k:l]} for op,i,j,k,l in matcher.get_opcodes() if op!='equal']
    anchor={'Q10_P02_first_73':a[:73],'Q13_P02_first_73':b[:73],'first_73_identical':a[:73]==b[:73],
        'length_difference_aa':len(a)-len(b),'full_sequence_differences':changes,
        'orientation':'DeepTMHMM and Phobius opposite body sides; not resolved by unchanged-sequence audit'}
    audit=json.loads((ROOT/'inputs/ER_static_audit.json').read_text(encoding='utf8'))
    geometry=[]
    for record in audit['records']:
        fit=record['direct_saved_coordinate_planar_fit'];reach=record['flexible_tether_reachability'];clash=record['existing_rigid_copy_clashes']
        geometry.append({'product_id':record['wetlab_id'],'model_sha256':record['model_sha256'],'subunits':record['subunits'],
            'membrane_thickness_A':fit['thickness_angstrom'],'saved_coordinates_common_plane':fit['common_plane_exists_for_saved_coordinates'],
            'common_interval_gap_A':fit['common_interval_gap_angstrom'],'necessary_contour_bound_pass':reach['all_tethers_within_maximum_contour_bound'],
            'max_reach_contour_ratio':reach['maximum_required_to_contour_ratio'],'noncore_atom_pairs_below_2_5_A':clash['outside_mapped_core_pairs_below_2_5A'],
            'ready_for_direct_membrane_MD':record['ready_for_direct_membrane_MD'],
            'data_class':'historical_static_geometry_not_new_MD'})
    out('identity_translation_recheck.csv',checks);out('source_feature_coordinates.csv',features);out('ER_geometry_recheck.csv',geometry)
    save('DNA_input_sources.json',snapshots)
    save('identity_tests.json',{'status':'PASS_source_identity_review_not_biological_validation','reviewed_at_UTC':datetime.now(timezone.utc).isoformat(),
        'original_zip_hash_matches_prior':True,'override_hash_matches_prior':True,'all_saved_selected_proteins_found_in_unchanged_DNA':True,
        'Q05':q05,'Q21':'encoded DMT annotation conflicts with delete-N OC filename; wet-lab intent unresolved',
        'Q24':'encoded OC/BBE006 annotation conflicts with DMT filename; wet-lab intent unresolved',
        'Q29':{'adopted_bp':len(SeqIO.read(OVERRIDE,'snapgene')),'superseded_bp':len(oldrecord),'adopted_sequence_already_used':True,'new_reprediction_required':False},
        'ER_anchor':anchor,'new_expensive_M1_or_M2_jobs':0,
        'blocked':['Q05 intended full-length coding construct','Q21/Q24 name-to-sequence-to-sample identity','ER body orientation',
            'non-crossing collision-free 24-tether ensemble','membrane-compatible assembly and catalytic pocket access',
            'formal whole-system membrane MD; no new membrane-stability result']})
    print(json.dumps({'selected_constructs':6,'selected_products':len(checks),'all_peptides_found':True,'ER_saved_models':len(geometry),'new_prediction_jobs':0}))

if __name__=='__main__':main()
