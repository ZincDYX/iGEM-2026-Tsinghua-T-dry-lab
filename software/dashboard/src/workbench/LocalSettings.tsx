import {lazy,Suspense} from 'react';
import {DesktopConnectionPanel} from '../DesktopConnectionPanel';
import {defaultLayout,type Layout} from './layout';
import type {RuntimeInfoView} from '../contracts/generated';
import type {Goal} from '../types';
const Assistant=lazy(()=>import('./AssistantSettings').then(m=>({default:m.AssistantSettings})));
export function LocalSettings({layout,onLayout,info,onRefresh,mode,onMode,section,onSection}:{layout:Layout;onLayout:(value:Layout)=>void;info?:RuntimeInfoView;onRefresh:()=>void;
  mode:'template'|'hybrid';onMode:(value:'template'|'hybrid')=>void;goal:Goal;onGoal:(value:Goal)=>void;
  section:'appearance'|'assistant'|'connection';onSection:(value:'appearance'|'assistant'|'connection')=>void}){
  return <section><h2>Settings</h2><div role="tablist" aria-label="Settings sections">{(['appearance','assistant','connection'] as const).map(value=><button key={value} role="tab" aria-selected={section===value} onClick={()=>onSection(value)}>{value[0].toUpperCase()+value.slice(1)}</button>)}</div>
    {section==='appearance'&&<><label>Theme<select value={layout.theme} onChange={event=>onLayout({...layout,theme:event.target.value==='dark'?'dark':'light'})}><option value="light">Light</option><option value="dark">Dark</option></select></label>
      <label>Table density<select value={layout.density} onChange={event=>onLayout({...layout,density:event.target.value==='comfortable'?'comfortable':'compact'})}><option value="compact">Compact</option><option value="comfortable">Comfortable</option></select></label>
      <button onClick={()=>onLayout(defaultLayout())}>Reset layout</button></>}
    {section==='assistant'&&<><label>Planner<select aria-label="Planner source" value={mode} onChange={event=>onMode(event.target.value as typeof mode)}><option value="template">Built-in registered tasks</option><option value="hybrid" disabled={info?.capabilities.hybrid_planning!=='ready'}>Configured model</option></select></label>
      <Suspense fallback={<p>Opening model settings…</p>}><Assistant onSaved={onRefresh}/></Suspense></>}
    {section==='connection'&&<><DesktopConnectionPanel/><button onClick={onRefresh}>Refresh connection</button></>}
  </section>;
}
