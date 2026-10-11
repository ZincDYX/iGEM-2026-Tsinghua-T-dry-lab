import {useState} from 'react';
import type {ModuleMethodView,ProjectView} from '../contracts/generated';
import {show} from '../contracts/resultAdapters';

export function ModuleParameters({project,method,frozen,onChange}:{project:ProjectView;method:ModuleMethodView;frozen:boolean;onChange:(value:ProjectView)=>void}) {
  const [editing,setEditing]=useState<string>(),[value,setValue]=useState(''),[unit,setUnit]=useState(''),[error,setError]=useState('');
  const rows=method.parameter_records;
  const [binding,setBinding]=useState<string>(),[sourceId,setSourceId]=useState('');
  function save() {
    const scope=project.scientific_project;
    const original=scope?.config.parameters.find(p=>p.parameter_id===editing);
    if(!scope||!original)return;
    if(!value.trim()||!Number.isFinite(Number(value))||!unit.trim()){setError('Enter a finite value and its unit.');return;}
    const replacement={...original,parameter_id:crypto.randomUUID(),value:Number(value),unit,
      parameter_version:original.parameter_version+1,supersedes:original.parameter_id,
      review_status:'extracted' as const,approved_by:null,validation_flags:[],updated_at:new Date().toISOString(),created_at:new Date().toISOString(),
      notes:`${original.notes}\nUnreviewed value override: ${original.value} ${original.unit} → ${value} ${unit}. Original source retained for comparison, not confirmation of this value.`};
    onChange({...project,scientific_project:{...scope,config:{...scope.config,parameters:[...scope.config.parameters,replacement]}}});
    setEditing(undefined);setError('');
  }
  function bindSource() {
    const scope=project.scientific_project;
    const original=scope?.config.parameters.find(p=>p.parameter_id===binding);
    const source=scope?.config.parameters.find(p=>p.parameter_id===sourceId);
    if(!scope||!original||!source||!method.parameter_source_options?.[original.parameter_id]?.includes(source.parameter_id))return;
    const timestamp=new Date().toISOString();
    const replacement={...source,parameter_id:crypto.randomUUID(),parameter_version:original.parameter_version+1,
      supersedes:original.parameter_id,review_status:'extracted' as const,approved_by:null,validation_flags:[],
      created_at:timestamp,updated_at:timestamp,notes:`${source.notes}\nRebound from an existing compatible source; review this new version before formal use.`};
    onChange({...project,scientific_project:{...scope,config:{...scope.config,parameters:[...scope.config.parameters,replacement]}}});
    setBinding(undefined);setSourceId('');
  }
  return <section aria-label="Module parameters">
    {frozen&&<p>Recorded run values · read-only.</p>}{error&&<p role="alert">{error}</p>}
    <table><thead><tr><th>Parameter</th><th>Value</th><th>Unit</th></tr></thead><tbody>
      {rows.filter(record=>!rows.some(other=>other.supersedes===record.parameter_id)).map(record=>{
        const calculated=record.derivation_type==='model_fit'||(Array.isArray(record.derived_from)&&record.derived_from.length>0);
        return <tr key={String(record.parameter_id)}><td>{String(record.name)}{calculated?' · calculated result':''}
          <details><summary>Source</summary><p>{show(record.source_reference)} · {show(record.review_status)}</p><p>Conditions: {show(record.condition_id)}. Version {show(record.parameter_version)}.</p>{!frozen&&!calculated&&<button onClick={()=>{setBinding(String(record.parameter_id));setSourceId('');}}>Choose existing source</button>}</details></td>
          <td>{!frozen&&!calculated&&typeof record.value==='number'?<button onClick={()=>{setEditing(String(record.parameter_id));setValue(String(record.value));setUnit(String(record.unit??''));}}>{show(record.value)}</button>:show(record.value)}</td><td>{show(record.unit)}</td></tr>;})}
      {method.parameter_requirements.filter(requirement=>!rows.some(p=>p.name===requirement.name)).map(requirement=><tr key={String(requirement.name)}><td>{String(requirement.name)}</td><td>Required · add evidence in Inputs</td><td>{show(requirement.canonical_unit)}</td></tr>)}
    </tbody></table>
    {editing&&<fieldset><legend>Edit value</legend><label>Value<input aria-label="Parameter value" type="number" step="any" value={value} onChange={e=>setValue(e.target.value)}/></label>
      <label>Unit<input aria-label="Parameter unit" value={unit} onChange={e=>setUnit(e.target.value)}/></label>
      <button onClick={save}>Save new parameter version</button><button onClick={()=>setEditing(undefined)}>Cancel</button>
      <p>The source stays bound. The changed value requires review before formal execution.</p></fieldset>}
    {binding&&<fieldset><legend>Choose existing compatible evidence</legend>
      <label>Source<select aria-label="Parameter source" value={sourceId} onChange={e=>setSourceId(e.target.value)}><option value="">Choose a reviewed source</option>
        {project.scientific_project?.config.parameters.filter(p=>method.parameter_source_options?.[binding]?.includes(p.parameter_id)).map(p=><option key={p.parameter_id} value={p.parameter_id}>{p.source_reference??p.name} · {p.value} {p.unit}</option>)}</select></label>
      <button disabled={!sourceId} onClick={bindSource}>Bind source as new version</button><button onClick={()=>setBinding(undefined)}>Cancel</button>
      <p>Only sources compatible with the module, construct and conditions are offered. If none are listed, import evidence in Inputs. Rebinding uses the source's recorded value and unit; it does not approve this new version.</p></fieldset>}
    {!rows.length&&!method.parameter_requirements.length&&<p>No parameter records consumed by this module.</p>}
  </section>;
}
