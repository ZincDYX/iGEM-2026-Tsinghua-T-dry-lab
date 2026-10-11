import {useEffect,useRef,useState} from 'react';
import type {ProjectView} from '../contracts/generated';
import {parsePublicAsync as parsePublic} from '../contracts/validation';
import {requestJson} from '../api';

export function ConstructObject({project,selected,onChange}:{project:ProjectView;selected:string;onChange:(value:ProjectView)=>void}) {
  const scope=project.scientific_project;
  const [edit,setEdit]=useState(false);
  useEffect(()=>setEdit(false),[selected,project.id]);
  if(!scope)return null;
  const definition=scope.config.inputs.constructs.find(row=>'definition:'+row.id===selected);
  const record=scope.config.inputs.construct_records.find(row=>'record:'+row.construct_id===selected);
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
      <table><thead><tr><th>Part</th><th>Role</th><th>Sequence</th></tr></thead><tbody>{definition.parts.map(part=><tr key={part.id}><td>{part.id}</td><td>{part.kind.replaceAll('_',' ')}</td><td>{part.sequence??'Bound by source'}</td></tr>)}</tbody></table>
      <button onClick={()=>setEdit(v=>!v)}>Edit construct declaration</button>{edit&&<fieldset><legend>Declaration</legend>
        <label>Fusion orientation<input aria-label="Fusion orientation" value={definition.fusion_orientation??''} onChange={e=>changeDefinition({fusion_orientation:e.target.value||null})}/></label>
        <label>Localization<select aria-label="Construct localization" value={definition.localization_context??''} onChange={e=>changeDefinition({localization_context:(e.target.value||null) as typeof definition.localization_context})}>
          <option value="">Not declared</option><option value="cytosolic">Cytosolic</option><option value="er_anchored">ER anchored</option></select></label>
        <p>Changing a declaration clears its M1 review. Topology and evidence are not inferred; import their actual source through Biological data.</p></fieldset>}</>}
    {record&&<><p>Host: {record.host??'Not declared'} · review: {record.review_status}</p><button onClick={()=>setEdit(v=>!v)}>Edit construct conditions</button>
      {edit&&<label>Host<input aria-label="Construct host" value={record.host??''} onChange={e=>changeRecord({host:e.target.value||null})}/></label>}</>}
  </section>;
}

export function NewConstruct({project,onChange}:{project:ProjectView;onChange:(value:ProjectView)=>void}) {
  const [open,setOpen]=useState(false),[name,setName]=useState(''),[components,setComponents]=useState(''),[pending,setPending]=useState(false),[error,setError]=useState('');
  const current=useRef(project);current.current=project;
  const scope=project.scientific_project;
  if(!scope)return null;
  return <section><button onClick={()=>setOpen(v=>!v)}>Add construct</button>{open&&<fieldset disabled={pending}><legend>New ordered construct</legend>
    <label>Name<input aria-label="New construct name" value={name} onChange={e=>setName(e.target.value)}/></label>
    <label>Ordered parts (comma separated)<input aria-label="New construct parts" value={components} onChange={e=>setComponents(e.target.value)}/></label>
    {error&&<p role="alert">{error}</p>}<button disabled={!name.trim()||!components.trim()} onClick={async()=>{
      setPending(true);setError('');
      try {
        const value=await parsePublic('ScientificRecordView',await requestJson('/scientific-records/preview',{kind:'construct',value:{id:name,components:components.split(',').map(v=>v.trim()).filter(Boolean)}}));
        if(current.current!==project)throw Error('Inputs changed during validation; retry against the current draft.');
        if(!value.construct_record)throw Error('No validated construct was returned.');
        if(scope.config.inputs.constructs.some(c=>c.id===name))throw Error('Construct name already exists.');
        onChange({...project,scientific_project:{...scope,config:{...scope.config,inputs:{...scope.config.inputs,constructs:[...scope.config.inputs.constructs,value.construct_record]}}}});
        setOpen(false);setName('');setComponents('');
      }catch(e){setError(e instanceof Error?e.message:String(e));}finally{setPending(false);}
    }}>Validate and add construct</button></fieldset>}</section>;
}
