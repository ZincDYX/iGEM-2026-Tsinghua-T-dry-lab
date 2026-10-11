import {useEffect,useState} from 'react';
import type {SkillPage,SkillView} from '../contracts/generated';
import * as client from './client';

export function SkillsPanel() {
  const [page,setPage]=useState<SkillPage>(),[offset,setOffset]=useState(0),[selected,setSelected]=useState<SkillView>();
  const [text,setText]=useState(''),[enabled,setEnabled]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[refresh,setRefresh]=useState(0);
  useEffect(()=>{let active=true;void client.skills(offset).then(value=>{if(active)setPage(value);}).catch(reason=>{if(active)setError(String(reason));});return()=>{active=false;};},[offset,refresh]);
  function edit(value?:SkillView) {setSelected(value);setText(value?.text??'---\nname: New workflow skill\ndescription: Explain the intended use\ntrigger: Describe when to use this instruction\nversion: "1"\nsource: User-authored\nlicense: Apache-2.0\n---\nDescribe the workflow. Do not invent scientific data or override approval gates.\n');setEnabled(value?.enabled??false);setError('');}
  return <section aria-label="Skills"><h3>Skills</h3><p>Versioned instructions only, not executable plugins. Enabled text guides the optional model within its fixed scientific contract. No scripts, file reads or permission grants are executed by importing a Skill.</p>
    {error&&<p role="alert">{error}</p>}
    <button disabled={busy} onClick={()=>edit()}>New instruction Skill</button>
    <label>Import SKILL.md<input type="file" accept=".md" disabled={busy} onChange={event=>{const file=event.target.files?.[0];if(!file)return;
      if(file.size>65536){setError('Skill is limited to 64 KiB.');return;}void file.text().then(value=>{edit();setText(value);}).catch(reason=>setError(String(reason)));event.target.value='';}}/></label>
    <ul>{page?.items.map(value=><li key={value.id}><button disabled={busy} onClick={()=>edit(value)}>{value.name} — {value.enabled?'Enabled':'Disabled'}</button><p>{value.description} Trigger: {value.trigger}. Version {value.version}; {value.source}; {value.license}.</p></li>)}</ul>
    <nav aria-label="Skill pages"><button disabled={!offset||busy} onClick={()=>setOffset(value=>value-20)}>Previous Skills</button><button disabled={!page?.has_more||busy} onClick={()=>setOffset(value=>value+20)}>Next Skills</button></nav>
    {text&&<fieldset disabled={busy}><legend>{selected?`Edit ${selected.name}`:'New Skill'}</legend><label>SKILL.md source<textarea aria-label="SKILL.md source" value={text} maxLength={65536} rows={14} onChange={event=>setText(event.target.value)}/></label>
      <label><input type="checkbox" checked={enabled} onChange={event=>setEnabled(event.target.checked)}/>Enable instruction guidance</label>
      <button onClick={()=>{setBusy(true);setError('');void client.saveSkill(text,enabled,selected?.id,selected?.revision).then(value=>{edit(value);setRefresh(value=>value+1);}).catch(reason=>setError(String(reason))).finally(()=>setBusy(false));}}>Save Skill revision</button></fieldset>}
  </section>;
}
