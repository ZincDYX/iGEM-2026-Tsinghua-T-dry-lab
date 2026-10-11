import {useEffect,useRef,useState} from 'react';
import type {ImportTransactionPreview,ProjectView} from '../contracts/generated';
import * as client from './client';
import {LazyJson} from '../contracts/LazyJson';
import {object} from '../contracts/validation';

export function UnifiedImport({project,busy,dirty,action,prepare,onCommitted}:{
  project:ProjectView;busy:boolean;dirty:boolean;action:(job:()=>Promise<unknown>)=>Promise<void>;
  prepare:()=>Promise<ProjectView|undefined>;onCommitted:(project:ProjectView)=>void;
}){
  const [preview,setPreview]=useState<ImportTransactionPreview>();
  const [options,setOptions]=useState<Record<string,Record<string,unknown>>>({});
  const [choices,setChoices]=useState<Record<string,string>>({});
  const [pending,setPending]=useState<string[]>([]);
  const [restoreError,setRestoreError]=useState(false);
  const [relativeName,setRelativeName]=useState('');
  const fileInput=useRef<HTMLInputElement>(null),folderInput=useRef<HTMLInputElement>(null);
  const additionalInput=useRef<HTMLInputElement>(null);
  const generation=useRef(0);
  useEffect(()=>{
    const stamp=++generation.current;setPreview(undefined);setOptions({});setChoices({});setPending([]);setRestoreError(false);
    void client.pendingImports(project.id).then(ids=>{
      if(stamp===generation.current)setPending(ids);
    }).catch(()=>{if(stamp===generation.current)setRestoreError(true);});
    return()=>{++generation.current};
  },[project.id]);
  async function choose(files:File[],append=false){
    if(!files.length)return;
    const stamp=++generation.current;
    await action(async()=>{
      const saved=await prepare();
      if(!saved||stamp!==generation.current)return;
      const value=await client.importTransaction(saved.id,files,append?preview?.id:undefined,append?relativeName:undefined);
      if(stamp===generation.current){setPreview(value);setOptions({});setChoices({});}
    });
  }
  const blocking=preview?.items.some(item=>item.issues.some(issue=>issue.severity==='error'||issue.severity==='confirmation'));
  return <section id="input-import" aria-label="Unified data import" className="input-section">
    <div className="import-dropzone" onDragOver={e=>e.preventDefault()} onDrop={e=>{
      e.preventDefault();if(!busy)void choose(Array.from(e.dataTransfer.files));
    }}>
      <p>Drop data files or ZIP here. Files, folders and ZIP use the same preview and confirmation.</p>
      <button disabled={busy} onClick={()=>fileInput.current?.click()}>Import files</button>
      <button disabled={busy} onClick={()=>folderInput.current?.click()}>Import folder</button>
      <input hidden id="input-import-file" ref={fileInput} aria-label="Import data file" type="file" multiple
        onChange={e=>{void choose(Array.from(e.target.files??[]));e.target.value='';}}/>
      <input hidden id="input-import-folder" ref={node=>{folderInput.current=node;node?.setAttribute('webkitdirectory','');}}
        aria-label="Import data folder" type="file" multiple onChange={e=>{void choose(Array.from(e.target.files??[]));e.target.value='';}}/>
    </div>
    {restoreError&&<p role="alert">Saved import previews could not be loaded. Reconnect and reopen Inputs; existing files have not been discarded.</p>}
    {!preview&&pending.length>0&&<div><p>An unfinished import was saved. Resume it without uploading the original files again.</p>
      {pending.map((id,index)=><button key={id} disabled={busy} onClick={()=>void action(async()=>{
        setPreview(await client.inspectImport(project.id,id));setOptions({});setChoices({});
      })}>Resume saved import {index+1}</button>)}
    </div>}
    {preview&&<article aria-label="Import transaction preview">
      <h3>Review imported objects</h3>
      <p>Original bytes are retained. Import is not tool execution or scientific approval.</p>
      {(dirty||preview.expected_revision!==project.revision)&&<p role="alert">Inputs changed since this preview. Save changes and refresh the import before confirmation; no unsaved changes will be overwritten.</p>}
      {preview.items.map(item=><section key={item.file.id}>
        <h4>{item.filename}</h4><p>{item.detected_format} · {item.semantic_type} · {item.records.length} parsed records</p>
        <p>{item.supported_scope}</p>
        {item.semantic_type==='DesignRecord'&&<p>Missing CDS translations remain explicit gaps; DNA is not automatically translated.</p>}
        {item.semantic_type==='SyntheticDemonstration'&&<p><strong>Synthetic demo.</strong> Not formal prediction or experimental validation. E3 remains blocked.</p>}
        {item.issues.map((issue,index)=><p key={index} role={issue.severity==='error'?'alert':undefined}>
          {issue.severity}: {issue.message}{issue.field&&` (${issue.field.replaceAll('_',' ')})`}
        </p>)}
        {item.semantic_type==='SequenceCollection'&&item.issues.some(i=>i.field==='molecule_type')&&<label>Molecule type for {item.filename}
          <select aria-label={`Molecule type for ${item.filename}`} value={String(options[item.filename]?.molecule_type??'')}
            onChange={e=>setOptions({...options,[item.filename]:{...options[item.filename],molecule_type:e.target.value}})}>
            <option value="">Choose molecule type</option><option value="protein">Protein</option><option value="DNA">DNA</option><option value="RNA">RNA</option>
          </select></label>}
        {(item.semantic_type==='UnclassifiedConfiguration'||item.issues.some(i=>i.code==='multiple_project_configurations'))&&<label>Configuration role for {item.filename}
          <select value={String(options[item.filename]?.role??'')} onChange={e=>setOptions({...options,[item.filename]:{role:e.target.value}})}>
            <option value="">Choose role</option>{item.input_roles.map(role=><option key={role} value={role}>{role.replaceAll('_',' ')}</option>)}
          </select></label>}
        {(item.semantic_type==='UnmappedTable'||item.semantic_type==='MeasurementTable')&&<details><summary>Map measurement columns</summary>
          <p>Declare column roles and units. Values are not fitted or approved here.</p>
          {Array.isArray(item.records[0]?.columns)&&item.records[0].columns.filter(object).map(column=>{
            const name=String(column.name),configured=options[item.filename]?.column_mapping;
            const mappings=object(configured)?configured:{};
            const current=object(mappings[name])?mappings[name]:{};
            function update(field:string,value:string){
              const next={...current,[field]:value};
              setOptions({...options,[item.filename]:{...options[item.filename],column_mapping:{...mappings,[name]:next}}});
            }
            return <div className="field-grid" key={name}><label>Role for {name}<select value={String(current.role??'')} onChange={e=>update('role',e.target.value)}>
              <option value="">Choose column role</option>{['time','value','unit','condition','replicate','censoring','construct','source','ignore'].map(role=><option key={role}>{role}</option>)}
            </select></label><label>Unit for {name}<input value={String(current.unit??'')} onChange={e=>update('unit',e.target.value)}/></label></div>;
          })}
        </details>}
        {item.semantic_type==='UnmappedTable'&&<label>Retain {item.filename} as an evidence table instead of a measurement
          <input type="checkbox" checked={options[item.filename]?.role==='evidence_attachment'} onChange={e=>setOptions({...options,
            [item.filename]:{...options[item.filename],role:e.target.checked?'evidence_attachment':undefined}})}/>
        </label>}
        {item.semantic_type==='CompoundRecord'&&<div className="field-grid">
          <label>Compound identity for {item.filename}<input value={String(options[item.filename]?.compound_identity??'')}
            onChange={e=>setOptions({...options,[item.filename]:{...options[item.filename],compound_identity:e.target.value}})}/></label>
          <label>Identity source for {item.filename}<input value={String(options[item.filename]?.source_reference??'')}
            onChange={e=>setOptions({...options,[item.filename]:{...options[item.filename],source_reference:e.target.value}})}/></label>
          <p>This declares the intended substrate. Chemical parsing is not a binding pose, sample certificate or scientific approval.</p>
        </div>}
        {item.duplicate_file_id&&<label>Duplicate: {item.filename}
          <select aria-label={`Duplicate: ${item.filename}`} value={choices[item.filename]??''} onChange={e=>setChoices({...choices,[item.filename]:e.target.value})}>
            <option value="">Choose reuse or version action</option><option value="reuse">Reuse existing</option><option value="replace">Replace in new revision</option><option value="new_version">Keep as new version</option>
          </select></label>}
        <LazyJson value={item.records} label="Parsed source details"/>
      </section>)}
      <p>{preview.proposed_links.length} source/sequence binding proposals. None implies pocket or enzyme identity approval.</p>
      <label>Relative filename for one missing file (optional)<input value={relativeName} onChange={e=>setRelativeName(e.target.value)} placeholder="study/proteins.faa"/></label>
      <button disabled={busy||dirty||preview.expected_revision!==project.revision} onClick={()=>additionalInput.current?.click()}>Add missing files to this import</button>
      <input hidden ref={additionalInput} aria-label="Add missing import files" type="file" multiple onChange={e=>{
        void choose(Array.from(e.target.files??[]),true);e.target.value='';
      }}/>
      <button disabled={busy} onClick={()=>void action(async()=>{
        const saved=await prepare();
        if(saved)setPreview(await client.reviseImport(saved.id,preview.id,options,saved.revision));
      })}>Update preview with confirmed roles</button>
      <button disabled={busy||dirty||preview.expected_revision!==project.revision||blocking||preview.items.some(i=>i.duplicate_file_id&&!choices[i.filename])}
        onClick={()=>void action(async()=>{const value=await client.commitImport(project.id,preview.id,choices);onCommitted(value);setPending(p=>p.filter(id=>id!==preview.id));setPreview(undefined);})}>Confirm import</button>
      <button disabled={busy} onClick={()=>void action(async()=>{await client.discardImport(project.id,preview.id);setPending(p=>p.filter(id=>id!==preview.id));setPreview(undefined);})}>Discard import</button>
    </article>}
  </section>;
}
