import {useState} from 'react';
import type {ModuleMethodView,ProjectView} from '../contracts/generated';
import {show} from '../contracts/resultAdapters';
import {ParameterTable} from './ParameterTable';

export function ModuleParameters({project,method,frozen,onChange,onScalarChange}:{project:ProjectView;method:ModuleMethodView;frozen:boolean;
  onChange:(value:ProjectView)=>Promise<void>;onScalarChange:(name:string,value:number,unit:string)=>Promise<void>}) {
  const [binding,setBinding]=useState<string>(),[sourceId,setSourceId]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const rows=method.parameter_records.filter(record=>!method.parameter_records.some(other=>other.supersedes===record.parameter_id));
  async function save(id:string,value:number,unit:string) {
    const scope=project.scientific_project!;
    const original=scope.config.parameters.find(p=>p.parameter_id===id)!;
    const timestamp=new Date().toISOString();
    const replacement={...original,parameter_id:crypto.randomUUID(),value,unit,
      parameter_version:original.parameter_version+1,supersedes:original.parameter_id,
      review_status:'extracted' as const,approved_by:null,uncertainty:null,validation_flags:['requires_human_approval_before_model_use'],updated_at:timestamp,created_at:timestamp,
      notes:`${original.notes}\nUnreviewed value override: ${original.value} ${original.unit} → ${value} ${unit}. Original source retained for comparison, not confirmation of this value.`};
    await onChange({...project,scientific_project:{...scope,config:{...scope.config,parameters:[...scope.config.parameters,replacement]}}});
  }
  async function bindSource() {
    const scope=project.scientific_project!;
    const original=scope.config.parameters.find(p=>p.parameter_id===binding)!;
    const source=scope.config.parameters.find(p=>p.parameter_id===sourceId)!;
    const timestamp=new Date().toISOString();setBusy(true);setError('');
    try {
      const replacement={...source,parameter_id:crypto.randomUUID(),parameter_version:original.parameter_version+1,
        supersedes:original.parameter_id,review_status:'extracted' as const,approved_by:null,validation_flags:['requires_human_approval_before_model_use'],
        created_at:timestamp,updated_at:timestamp,notes:`${source.notes}\nRebound from existing compatible evidence; review this new version before formal use.`};
      await onChange({...project,scientific_project:{...scope,config:{...scope.config,parameters:[...scope.config.parameters,replacement]}}});
      setBinding(undefined);setSourceId('');
    }catch(reason){setError(String(reason));}finally{setBusy(false);}
  }
  const scalar=method.scalar_method?.execution_spec;
  return <section aria-label="Module parameters">
    {frozen&&<p>Recorded run values · read-only.</p>}{error&&<p role="alert">{error}</p>}
    {scalar?<ParameterTable frozen={frozen} rows={Object.entries(scalar.variables).map(([name,v])=>({id:name,name,...v,status:'exploratory'}))} onSave={onScalarChange}/>
      :<ParameterTable frozen={frozen} rows={[
        ...rows.map(record=>({id:String(record.parameter_id),name:String(record.name),value:typeof record.value==='number'?record.value:show(record.value),unit:show(record.unit),
          source:`${show(record.source_reference)} · ${show(record.review_status)}. Conditions: ${show(record.condition_id)}. Version ${show(record.parameter_version)}.${record.binding_reason?' '+record.binding_reason:''}`,
          readOnly:record.derivation_type==='model_fit'||record.binding_read_only===true,status:record.binding_read_only===true?'versioned model binding · read-only':record.derivation_type==='model_fit'?'calculated result':['extracted','validated'].includes(String(record.review_status))?'pending review · not used yet':undefined})),
        ...method.parameter_requirements.filter(requirement=>!rows.some(p=>p.name===requirement.name)).map(requirement=>({id:String(requirement.name),name:String(requirement.name),value:'Required · add evidence in Inputs',unit:show(requirement.canonical_unit),readOnly:true}))
      ]} onSave={save} sourceActions={row=>!frozen&&!row.readOnly&&<button disabled={busy} onClick={()=>{setBinding(row.id);setSourceId('');}}>Choose existing source</button>}/>}
    {binding&&<fieldset disabled={busy}><legend>Choose existing compatible evidence</legend>
      <label>Source<select aria-label="Parameter source" value={sourceId} onChange={e=>setSourceId(e.target.value)}><option value="">Choose a reviewed source</option>
        {project.scientific_project?.config.parameters.filter(p=>method.parameter_source_options?.[binding]?.includes(p.parameter_id)).map(p=><option key={p.parameter_id} value={p.parameter_id}>{p.source_reference??p.name} · {p.value} {p.unit}</option>)}</select></label>
      <button disabled={!sourceId} onClick={()=>void bindSource()}>Bind source as new version</button><button onClick={()=>setBinding(undefined)}>Cancel</button>
      <p>Only compatible reviewed sources are offered. Import new evidence in Inputs. This new version still requires review.</p></fieldset>}
    {!scalar&&!rows.length&&!method.parameter_requirements.length&&<p>No editable parameter bindings in this module. Fixed baseline rules and imported model definitions remain read-only; changing their display would not change execution.</p>}
  </section>;
}
