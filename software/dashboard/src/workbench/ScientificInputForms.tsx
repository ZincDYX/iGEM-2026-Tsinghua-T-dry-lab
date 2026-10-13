import {useEffect,useRef,useState} from 'react';
import type {ProjectView} from '../contracts/generated';
import {parsePublicAsync as parsePublic} from '../contracts/validation';
import {requestJson} from '../api';

export function ConstructObject({project,selected,onChange}:{project:ProjectView;selected:string;onChange:(value:ProjectView)=>void}) {
  const scope=project.scientific_project;
  const [edit,setEdit]=useState(false);
  const [partId,setPartId]=useState('');
  useEffect(()=>{setEdit(false);setPartId('');},[selected,project.id]);
  if(!scope)return null;
  const definition=scope.config.inputs.constructs.find(row=>'definition:'+row.id===selected);
  const record=scope.config.inputs.construct_records.find(row=>'record:'+row.construct_id===selected||definition&&row.construct_id===definition.id);
  if(!definition&&!record)return null;
  function changeDefinition(patch:Partial<NonNullable<typeof definition>>) {
    onChange({...project,scientific_project:{...scope!,config:{...scope!.config,inputs:{...scope!.config.inputs,
      constructs:scope!.config.inputs.constructs.map(row=>row.id===definition!.id?{...row,...patch,m1_review:null}:row)}}}});
  }
  function changeRecord(patch:Partial<NonNullable<typeof record>>) {
    onChange({...project,scientific_project:{...scope!,config:{...scope!.config,inputs:{...scope!.config.inputs,
      construct_records:scope!.config.inputs.construct_records.map(row=>row.construct_id===record!.construct_id?
        {...row,...patch,review_status:'extracted',m1_review:null}:row)}}}});
  }
  return <section aria-label="Selected construct"><h3>{definition?.id??record?.construct_id}</h3>
    {definition&&<><p>Ordered parts: {(definition.parts.length?definition.parts.map(p=>p.id):definition.components).join(' → ')}</p>
      <p>Localization: {definition.localization_context??'Not declared'}. Orientation: {definition.fusion_orientation??'Not declared'}.</p>
      <p>Source: {definition.sequence_source_ref??'Not declared'}</p>
      <table><thead><tr><th>Part</th><th>Declared role</th></tr></thead><tbody>{definition.parts.map(part=><tr key={part.id}><td><button onClick={()=>setPartId(part.id)}>{part.id}</button></td><td>{part.kind.replaceAll('_',' ')}</td></tr>)}</tbody></table>
      {partId&&<p className="sequence-text">{definition.parts.find(part=>part.id===partId)?.sequence??'Sequence or boundary missing; no part is inferred.'}</p>}
      <button onClick={()=>setEdit(v=>!v)}>Edit construct declaration</button>{edit&&<fieldset><legend>Declaration</legend>
        <label>Fusion orientation<input aria-label="Fusion orientation" value={definition.fusion_orientation??''} onChange={e=>changeDefinition({fusion_orientation:e.target.value||null})}/></label>
        <label>Localization<select aria-label="Construct localization" value={definition.localization_context??''} onChange={e=>changeDefinition({localization_context:(e.target.value||null) as typeof definition.localization_context})}>
          <option value="">Not declared</option><option value="cytosolic">Cytosolic</option><option value="er_anchored">ER anchored</option></select></label>
        <p>Changing a declaration clears its M1 review. Topology and evidence are not inferred; import their actual source through Biological data.</p></fieldset>}</>}
    {record&&<><h4>Source / measurements declaration</h4>{definition&&<p>This declaration uses the same name. Its identity and scientific compatibility still require review; the records have not been merged.</p>}
      <p>Host: {record.host??'Not declared'} — {record.review_status.replaceAll('_',' ')}</p>
      {Object.entries(record).filter(([key,value])=>['strain','temperature_c','pH','assay_system','condition_id','source_reference','localization_context','membrane_topology'].includes(key)&&value!=null&&typeof value!=='object').map(([key,value])=><p key={key}>{key.replaceAll('_',' ')}: {String(value)}</p>)}
      <button onClick={()=>setEdit(v=>!v)}>Correct declaration</button>
      {edit&&<label>Host<input aria-label="Construct host" value={record.host??''} onChange={e=>changeRecord({host:e.target.value||null})}/></label>}</>}
  </section>;
}

export function NewConstruct({project,onChange}:{project:ProjectView;onChange:(value:ProjectView)=>void}) {
  const [open,setOpen]=useState(false),[name,setName]=useState(''),[components,setComponents]=useState<string[]>([]),[pending,setPending]=useState(false),[error,setError]=useState('');
  const current=useRef(project);current.current=project;
  const scope=project.scientific_project;
  if(!scope)return null;
  return <section><button onClick={()=>setOpen(v=>!v)}>Add design</button>{open&&<fieldset disabled={pending}><legend>New protein design</legend>
    <label>Name<input aria-label="New construct name" value={name} onChange={e=>setName(e.target.value)}/></label>
    <label>Imported protein component<select aria-label="Add design component" value="" onChange={event=>{if(event.target.value)setComponents(values=>[...values,event.target.value]);}}><option value="">Choose component</option>{project.sequences.map(sequence=><option key={sequence.id} value={sequence.id}>{sequence.id} — {sequence.sequence.length} aa</option>)}</select></label>
    <ol>{components.map((id,index)=><li key={index}>{id}<button disabled={!index} onClick={()=>setComponents(values=>{const next=[...values];[next[index-1],next[index]]=[next[index],next[index-1]];return next;})}>Move up</button><button onClick={()=>setComponents(values=>values.filter((_,i)=>i!==index))}>Remove</button></li>)}</ol>
    {error&&<p role="alert">{error}</p>}<button disabled={!name.trim()||!components.length} onClick={async()=>{
      setPending(true);setError('');
      try {
        const value=await parsePublic('ScientificRecordView',await requestJson('/scientific-records/preview',{kind:'construct',value:{id:name,parts:components.map((id,index)=>{
          const sequence=project.sequences.find(row=>row.id===id)!;return {id:`part-${index+1}`,kind:['idr','enzyme_ligand_linker','scaffold_linker','rigid_linker'].includes(sequence.role)?sequence.role:'protein',sequence:sequence.sequence};
        }),sequence_source_ref:'Explicit ordered selection from imported protein records; not experimental confirmation.'}}));
        if(current.current!==project)throw Error('Inputs changed during validation; retry against the current draft.');
        if(!value.construct_record)throw Error('No validated construct was returned.');
        if(scope.config.inputs.constructs.some(c=>c.id===name))throw Error('Construct name already exists.');
        onChange({...project,scientific_project:{...scope,config:{...scope.config,inputs:{...scope.config.inputs,constructs:[...scope.config.inputs.constructs,value.construct_record]}}}});
        setOpen(false);setName('');setComponents([]);
      }catch(e){setError(e instanceof Error?e.message:String(e));}finally{setPending(false);}
    }}>Validate and add construct</button></fieldset>}</section>;
}
