import {useEffect,useState} from 'react';
import type {ProjectView,Workflow,ToolCatalogPage} from '../contracts/generated';
import {requestJson} from '../api';
import {parsePublicAsync as parsePublic} from '../contracts/validation';
import {PredictionTools} from './PredictionTools';
import {PluginPanel} from './PluginPanel';
import {SkillsPanel} from './SkillsPanel';

export function ExtensionsPanel({workspace,project,busy,action,onPlan,onOpenResource}:{workspace:string;project?:ProjectView;busy:boolean;
  action:(job:()=>Promise<unknown>)=>Promise<void>;onPlan:(workflow:Workflow)=>void;onOpenResource:(id:string)=>void}) {
  const preference=`fusionlab.extensions.${workspace}`;
  const [tab,setTab]=useState<'tools'|'plugins'|'skills'>(()=>{
    const saved=localStorage.getItem(preference);
    return saved==='plugins'||saved==='skills'?saved:'tools';
  }),[offset,setOffset]=useState(0),[page,setPage]=useState<ToolCatalogPage>(),[error,setError]=useState('');
  useEffect(()=>{localStorage.setItem(preference,tab);},[preference,tab]);
  useEffect(()=>{const controller=new AbortController();if(tab==='tools')void requestJson(`/tool-catalog?offset=${offset}`,undefined,controller.signal)
    .then(async raw=>{const value=await parsePublic('ToolCatalogPage',raw);if(!controller.signal.aborted)setPage(value);}).catch(reason=>{if(!controller.signal.aborted)setError(String(reason));});return()=>controller.abort();},[tab,offset]);
  return <section aria-label="Tools and extensions"><h2>Tools &amp; extensions</h2><p>Tool checks do not approve scientific evidence.</p>
    <div role="tablist" aria-label="Extension pages">{(['tools','plugins','skills'] as const).map(value=><button role="tab" key={value} aria-selected={tab===value} onClick={()=>setTab(value)}>{value==='tools'?'Connected tools':value==='plugins'?'Plugins':'Skills'}</button>)}</div>
    {tab==='tools'&&<>{error&&<p role="alert">{error}</p>}
      {project?.revision?<PredictionTools catalog={page?.items??[]} project={project} busy={busy} onPlan={onPlan} onOpenResource={onOpenResource}/>:<p>Save a project to check its tools.</p>}
      <nav aria-label="Tool pages"><button disabled={!offset} onClick={()=>setOffset(value=>Math.max(0,value-50))}>Previous tools</button><button disabled={!page?.has_more} onClick={()=>setOffset(value=>value+50)}>Next tools</button></nav>
    </>}
    {tab==='plugins'&&<PluginPanel busy={busy} action={action}/>}
    {tab==='skills'&&<SkillsPanel/>}
  </section>;
}
