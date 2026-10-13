import {useEffect,useState} from 'react';
import {requestJson} from '../api';
import {parseList,parsePublicAsync} from '../contracts/validation';
import type {PredictionToolView,ProjectView,SequencePage,Workflow} from '../contracts/generated';
import type {ModuleTool} from '../contracts/ToolCatalogPage.generated';
import {defaultPolicy} from './client';
import type {FileContext} from './FileDocument';
const statusLabels={not_configured:'Not configured',configured_unverified:'Configured — task not verified',available:'Real output produced and parsed',failed:'Last task failed'};
const purposes:Record<string,string>={'project.m1':'Sequence checks','project.m2':'Fusion structure assessment','project.m3':'Enzyme recruitment','project.m4':'Reaction model',
  'fusion.sequence_metrics':'Sequence properties','workflow.custom_formula':'Exploratory scalar calculation'};
export function PredictionTools({project,persisted=false,busy,onPlan,onOpenResource,catalog=[],onMethod}:{project?:ProjectView;persisted?:boolean;busy:boolean;
  catalog?:ModuleTool[];onPlan:(workflow:Workflow)=>void;onOpenResource:(id:string,context?:Partial<FileContext>)=>void;onMethod:(method:'original-m1'|'original-m2'|'original-m3'|'original-m4')=>void}){
  const [rows,setRows]=useState<PredictionToolView[]>([]),[selected,setSelected]=useState(''),[sequenceId,setSequenceId]=useState(''),[sequences,setSequences]=useState<SequencePage>();
  const [offset,setOffset]=useState(0),[refresh,setRefresh]=useState(0),[error,setError]=useState('');
  const tool=catalog.find(value=>value.id===selected),prediction=rows.find(value=>value.id===selected);
  const needsSequence=selected.startsWith('prediction.')||selected==='fusion.sequence_metrics';
  useEffect(()=>{const controller=new AbortController();
    void requestJson(project&&persisted?`/projects/${encodeURIComponent(project.id)}/prediction-tools`:'/prediction-tools',undefined,controller.signal)
      .then(raw=>parseList('PredictionToolView',raw)).then(value=>{if(!controller.signal.aborted)setRows(value);}).catch(reason=>{if(!controller.signal.aborted)setError(String(reason));});
    return()=>controller.abort();
  },[project?.id,project?.revision,persisted,refresh]);
  useEffect(()=>{const controller=new AbortController();setSequences(undefined);setSequenceId('');
    if(needsSequence&&project&&persisted)void requestJson(`/projects/${encodeURIComponent(project.id)}/sequences?offset=${offset}&limit=100`,undefined,controller.signal)
      .then(raw=>parsePublicAsync('SequencePage',raw)).then(value=>{if(!controller.signal.aborted){setSequences(value);setSequenceId(value.items.length?'0':'');}}).catch(reason=>{if(!controller.signal.aborted)setError(String(reason));});
    return()=>controller.abort();
  },[project?.id,project?.revision,persisted,needsSequence,selected,offset]);
  function prepare(){
    if(!project||!tool)return;
    if(['project.m1','project.m2','project.m3','project.m4'].includes(tool.id)){onMethod(('original-'+tool.id.slice(-2)) as 'original-m1');return;}
    const item=sequences?.items[Number(sequenceId)];if(!item||sequences?.project_revision!==project.revision)return;
    onPlan({id:tool.id==='fusion.sequence_metrics'?'sequence-statistics':'sequence-prediction',name:`${tool.name}: ${item.label}`,version:'1',description:'Diagnostic task; formal evidence review remains separate.',execution_policy:defaultPolicy(),
      nodes:[{id:tool.id==='fusion.sequence_metrics'?'metrics':'prediction',label:tool.name,tool_id:tool.id,inputs:{item:item.ref},depends_on:[],map:null}]});
  }
  return <section aria-label="Scientific prediction tools">{error&&<p role="alert">{error}</p>}<button disabled={busy} onClick={()=>{setError('');setRefresh(value=>value+1);}}>Check availability</button>
    <table><thead><tr><th>Name</th><th>Purpose</th><th>Status</th><th>Action</th></tr></thead><tbody>{catalog.map(item=>{
      const status=rows.find(value=>value.id===item.id);
      return <tr key={item.id}><td>{item.name}</td><td>{purposes[item.id]??(item.id.startsWith('prediction.')?'Sequence / structure prediction':'Registered calculation')}</td>
        <td>{status?statusLabels[status.status]:'Registered — not tested'}</td><td><button aria-pressed={selected===item.id} onClick={()=>setSelected(item.id)}>Select</button></td></tr>;
    })}</tbody></table>
    {tool&&<section aria-label="Selected tool"><h3>{tool.name}</h3><p>{tool.description}</p><p>{tool.license}</p>
      {needsSequence&&<><label>Input sequence<select aria-label="Prediction input" disabled={!sequences} value={sequenceId} onChange={event=>setSequenceId(event.target.value)}>
        <option value="">Choose input</option>{sequences?.items.map((item,index)=><option key={index} value={String(index)}>{item.label} ({item.length} aa; {item.role})</option>)}</select></label>
        {sequences&&sequences.total>100&&<nav><button disabled={!offset} onClick={()=>setOffset(value=>Math.max(0,value-100))}>Previous sequences</button><button disabled={offset+100>=sequences.total} onClick={()=>setOffset(value=>value+100)}>Next sequences</button></nav>}</>}
      {prediction?.status==='not_configured'?<p>Not configured. A deployment administrator must provide a usable installation or API route; check the tool's access and license requirements.</p>
        :needsSequence||['project.m1','project.m2','project.m3','project.m4'].includes(selected)?<><button disabled={busy||!project||(needsSequence?!sequenceId:!project.scientific_project)} onClick={prepare}>Review task</button><p>Review this task once in Assistant, then Run approved task.</p></>
        :<p>This calculation needs its model inputs in Workflow: {tool.input_names.join(', ')}.</p>}
      {prediction?.problem&&<p role="alert">{prediction.failure_step}: {prediction.problem.message}</p>}{prediction?.problem?.actions.map(value=><p key={value}>{value}</p>)}
      {prediction?.latest_file_id&&<button onClick={()=>onOpenResource(prediction.latest_file_id!,{name:prediction.name+' output'})}>View output</button>}
      {prediction?.source_reference&&<a href={prediction.source_reference} target="_blank" rel="noreferrer">Installation and access requirements</a>}
    </section>}
  </section>;
}
