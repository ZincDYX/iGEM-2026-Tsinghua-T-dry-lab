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
  return <section aria-label="Tools and extensions"><h2>Tools &amp; extensions</h2><p>Registration, connection and an actual parsed scientific job are different states. Installing an extension never approves its scientific output.</p>
    <div role="tablist" aria-label="Extension pages">{(['tools','plugins','skills'] as const).map(value=><button role="tab" key={value} aria-selected={tab===value} onClick={()=>setTab(value)}>{value==='tools'?'Connected tools':value==='plugins'?'Plugins':'Skills'}</button>)}</div>
    {tab==='tools'&&<><h3>All registered capabilities</h3>{error&&<p role="alert">{error}</p>}
      <ul>{page?.items.map(tool=><li key={tool.id}><details><summary>{tool.name} — registered, not tested</summary><p>{tool.description}</p><p>Version: {/^[a-f0-9]{40}$/.test(tool.version)?'Source revision retained in backend':tool.version}. Runtime: {tool.runtime}. License: {tool.license}</p><p>Declared input names: {tool.input_names.join(', ')||'No named inputs'}. {tool.output_scope}</p></details></li>)}</ul>
      <nav aria-label="Tool pages"><button disabled={!offset} onClick={()=>setOffset(value=>value-50)}>Previous tools</button><button disabled={!page?.has_more} onClick={()=>setOffset(value=>value+50)}>Next tools</button></nav>
      {project?.revision?<PredictionTools project={project} busy={busy} onPlan={onPlan} onOpenResource={onOpenResource}/>:<p>Save or import a project to prepare real prediction jobs on its sequences.</p>}
    </>}
    {tab==='plugins'&&<PluginPanel busy={busy} action={action}/>}
    {tab==='skills'&&<SkillsPanel/>}
  </section>;
}
