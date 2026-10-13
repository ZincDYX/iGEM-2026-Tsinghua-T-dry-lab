import {useEffect,useState} from 'react';
import type {AssistantSettingsView,AssistantProbeView} from '../contracts/generated';
import * as client from './client';

export function AssistantSettings({onSaved}:{onSaved:()=>void}) {
  const [view,setView]=useState<AssistantSettingsView>();
  const [provider,setProvider]=useState<'none'|'compatible_api'|'local_endpoint'>('none');
  const [model,setModel]=useState(''),[endpoint,setEndpoint]=useState(''),[secret,setSecret]=useState('');
  const [clear,setClear]=useState(false),[style,setStyle]=useState('');
  const [probe,setProbe]=useState<AssistantProbeView>(),[busy,setBusy]=useState(false),[error,setError]=useState('');
  function adopt(value:AssistantSettingsView) {setView(value);setProvider(value.provider);setModel(value.model);setStyle(value.style_instructions);setSecret('');setEndpoint('');setClear(false);}
  useEffect(()=>{let active=true;void client.assistantSettings().then(value=>{if(active)adopt(value);}).catch(reason=>{if(active)setError(String(reason));});return()=>{active=false;};},[]);
  async function save() {
    setBusy(true);setError('');setProbe(undefined);
    try {adopt(await client.saveAssistantSettings({provider,model,endpoint:endpoint.trim()||undefined,secret:secret||undefined,clear_secret:clear,style_instructions:style}));
      onSaved();if(provider!=='none')setProbe(await client.testAssistantSettings());}
    catch(reason){setError(String(reason));}finally{setBusy(false);}
  }
  return <section aria-label="Assistant model settings"><h2>Assistant Settings</h2>
    <p>This is the optional language model, not the compute backend. None keeps deterministic tools and manual workflows available.</p>
    {error&&<p role="alert">{error}</p>}
    <fieldset disabled={busy||!view}><legend>Private workspace profile</legend>
      <label>Provider<select aria-label="Assistant provider" value={provider} onChange={event=>setProvider(event.target.value as typeof provider)}>
        <option value="none">None</option><option value="compatible_api">Compatible API</option>
        <option value="local_endpoint" disabled={!view?.local_workspace}>Local endpoint (local workspace only)</option></select></label>
      {provider!=='none'&&<><label>Model<input aria-label="Assistant model" value={model} list="assistant-models" onChange={event=>setModel(event.target.value)}/></label>
        <datalist id="assistant-models">{probe?.models.map(name=><option key={name} value={name}/>)}</datalist>
        <label>Chat completions endpoint<input aria-label="Assistant endpoint" type="url" value={endpoint} placeholder="https://provider.example/v1/chat/completions" onChange={event=>setEndpoint(event.target.value)}/></label>
        <p>Leave blank to retain the saved endpoint. It is not read back or exported. Hosted workspaces require an administrator-authorized endpoint; their localhost is not your computer.</p>
        <label>API secret (write-only)<input aria-label="Assistant API secret" type="password" autoComplete="new-password" value={secret} onChange={event=>setSecret(event.target.value)}/></label>
        <p>{view?.has_secret?'A secret is saved; leave blank to retain it only for the same endpoint/provider.':'No secret is saved.'} Changing the target clears the old credential unless you supply a new one. Secrets never enter project files or browser storage.</p>
        <label><input type="checkbox" checked={clear} onChange={event=>setClear(event.target.checked)}/>Clear saved secret</label></>}
      <label>Optional response style<textarea aria-label="Assistant response style" maxLength={4000} value={style} onChange={event=>setStyle(event.target.value)}/></label>
      <p>Style and Skills cannot override scientific contracts, provide missing evidence, grant permissions or approve parameters.</p>
      {provider!=='none'&&<p>Save and test sends three small public test requests; your provider may charge for them.</p>}
      <button onClick={()=>void save()}>{provider==='none'?'Save':'Save and test'}</button>
    </fieldset>
    <p>Save scope: private workspace runtime. {view?.configured?'Configured; Hybrid planning remains unavailable until the actual JSON connection test passes.':'Model disabled or not configured.'}</p>
    <dl>{Object.entries(probe?.capabilities??view?.capabilities??{}).map(([name,state])=><div key={name}><dt>{name.replaceAll('_',' ')}</dt><dd>{state==='observed'?'Observed in actual public connection test':'Not verified'}</dd></div>)}</dl>
    {probe&&<p>{probe.explanation}</p>}
  </section>;
}
