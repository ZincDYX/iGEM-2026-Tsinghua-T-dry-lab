import {useEffect,useState} from 'react';
import type {SkillPage,SkillView} from '../contracts/generated';
import * as client from './client';

export function SkillsPanel() {
  const [page,setPage]=useState<SkillPage>(),[offset,setOffset]=useState(0),[selected,setSelected]=useState<SkillView>();
  const [name,setName]=useState(''),[text,setText]=useState(''),[enabled,setEnabled]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[refresh,setRefresh]=useState(0);
  useEffect(()=>{let active=true;void client.skills(offset).then(value=>{if(active)setPage(value);}).catch(reason=>{if(active)setError(String(reason));});return()=>{active=false;};},[offset,refresh]);
  function edit(value?:SkillView) {setSelected(value);setName(value?.name??'');setText(value?.text.split(/^---\s*$/m).slice(2).join('---').trim()??'');setEnabled(value?.enabled??false);setError('');}
  return <section aria-label="Skills"><h3>Skills</h3><p>Versioned instructions only, not executable plugins. Enabled text guides the optional model within its fixed scientific contract. No scripts, file reads or permission grants are executed by importing a Skill.</p>
    {error&&<p role="alert">{error}</p>}
    <button disabled={busy} onClick={()=>{edit();setName("New instruction");}}>New instruction Skill</button>
    <label>Import SKILL.md<input type="file" accept=".md" disabled={busy} onChange={event=>{const file=event.target.files?.[0];if(!file)return;
      if(file.size>65536){setError('Skill is limited to 64 KiB.');return;}void file.text().then(value=>client.saveSkill(value,false)).then(value=>{edit(value);setRefresh(v=>v+1);}).catch(reason=>setError(String(reason)));event.target.value='';}}/></label>
    <ul>{page?.items.map(value=><li key={value.id}><button disabled={busy} onClick={()=>edit(value)}>{value.name} — {value.enabled?'Enabled':'Disabled'}</button><p>{value.description}</p><button onClick={()=>{const url=URL.createObjectURL(new Blob([value.text],{type:"text/markdown"}));const a=document.createElement("a");a.href=url;a.download="SKILL.md";a.click();URL.revokeObjectURL(url);}}>Export SKILL.md</button></li>)}</ul>
    <nav aria-label="Skill pages"><button disabled={!offset||busy} onClick={()=>setOffset(value=>value-20)}>Previous Skills</button><button disabled={!page?.has_more||busy} onClick={()=>setOffset(value=>value+20)}>Next Skills</button></nav>
    {(selected||name||text)&&<fieldset disabled={busy}><legend>{selected?`Edit ${selected.name}`:'New Skill'}</legend><label>Name<input aria-label="Skill name" value={name} onChange={event=>setName(event.target.value)}/></label><label>Instructions<textarea aria-label="Skill instructions" value={text} maxLength={65536} rows={14} onChange={event=>setText(event.target.value)}/></label>
      <label><input type="checkbox" checked={enabled} onChange={event=>setEnabled(event.target.checked)}/>Enable instruction guidance</label>
      <button disabled={!name.trim()||!text.trim()} onClick={()=>{setBusy(true);setError('');void client.saveSkillFields(name,text,enabled,selected?.id,selected?.revision).then(value=>{edit(value);setRefresh(value=>value+1);}).catch(reason=>setError(String(reason))).finally(()=>setBusy(false));}}>Save Skill revision</button></fieldset>}
  </section>;
}
