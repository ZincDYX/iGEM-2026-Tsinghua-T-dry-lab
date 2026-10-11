import {useRef,useState} from 'react';
import type {ProjectView,ScientificPreviewView} from '../contracts/generated';
import {requestJson} from '../api';
import {parsePublicAsync as parsePublic} from '../contracts/validation';

/** Narrow setup for sequence screening; richer scientific models are imported as plans. */
export function ScientificSetup({project,dirty,busy,onPreview}:{project:ProjectView;dirty:boolean;busy:boolean;onPreview:(v:ScientificPreviewView)=>void}) {
  const [fileId,setFileId]=useState(''),[pending,setPending]=useState(false),[error,setError]=useState('');
  const current=useRef(project);current.current=project;
  const files=project.files.filter(file=>project.datasets.some(row=>row.file_id===file.id&&row.kind==='SequenceCollection'&&Array.isArray(row.records)&&row.records.length>0&&row.records.every(record=>typeof record==='object'&&record!==null&&'molecule_type' in record&&record.molecule_type==='protein')));
  return <section id="input-scientific-setup"><h3>Sequence-screening plan</h3>
    <p>Choose imported protein FASTA for M1. For M2–M4, import a plan with its structure, model and evidence bindings through Plan / configuration; no missing parameters are invented.</p>
    <fieldset disabled={dirty||busy||pending}><label>Protein FASTA<select aria-label="Scientific protein FASTA" value={fileId} onChange={e=>setFileId(e.target.value)}>
      <option value="">Choose imported protein FASTA</option>{files.map(file=><option key={file.id} value={file.id}>{file.name}</option>)}</select></label>
      <button disabled={!fileId} onClick={async()=>{
        setPending(true);setError('');
        try {
          const file=files.find(item=>item.id===fileId)!;
          const value=await parsePublic('ScientificPreviewView',await requestJson('/scientific-projects/create-preview',{project_id:project.id,expected_revision:project.revision,
            config:{prepared_through:'m1',execution:{mode:'real',allow_assumptions:false},inputs:{protein_fasta:file.path,enzymes:[],scaffolds:[],linkers:[]}}}));
          if(current.current!==project)throw Error('Project changed; retry against saved inputs.');
          onPreview(value);
        }catch(e){setError(e instanceof Error?e.message:String(e));}finally{setPending(false);}
      }}>Validate M1 plan</button></fieldset>
      {dirty&&<p>Save imported data before binding the plan.</p>}{pending&&<p role="status">Validating input bindings…</p>}{error&&<p role="alert">{error}</p>}
  </section>;
}
