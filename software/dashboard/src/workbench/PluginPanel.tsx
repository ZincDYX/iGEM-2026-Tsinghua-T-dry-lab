import { useEffect, useState } from "react";
import type { PluginInspectionView } from "../contracts/generated";
import * as client from "./client";

export function PluginPanel({
  busy,
  action,
}: {
  busy: boolean;
  action: (job: () => Promise<unknown>) => Promise<void>;
}) {
  const [url, setUrl] = useState("");
  const [commit, setCommit] = useState("");
  const [inspection, setInspection] = useState<PluginInspectionView>();
  const [trusted, setTrusted] = useState(false);
  const [installed,setInstalled]=useState<PluginInspectionView[]>([]);
  const [error,setError]=useState(''),[operation,setOperation]=useState('');
  const [add,setAdd]=useState(false),[versions,setVersions]=useState<string>();
  async function perform(label:string,job:()=>Promise<unknown>) {
    await action(async()=>{setOperation(label);setError('');try{return await job();}catch(reason){setError(reason instanceof Error?reason.message:String(reason));throw reason;}finally{setOperation('');}});
  }
  useEffect(()=>{let active=true;void client.installedPlugins().then(value=>{if(active)setInstalled(value);}).catch(reason=>{if(active)setError(String(reason));});return()=>{active=false;};},[]);
  return (
    <section>
      <h3>Plugins</h3>
      <p>
        Install only code you trust. Shared deployments require administrator authorization; plugins are not a security sandbox.
      </p>
      {operation&&<p role="status">{operation}</p>}{error&&<p role="alert">{error}</p>}
      <button disabled={busy} onClick={()=>setAdd(value=>!value)}>Add plugin</button>
      {add&&<>
      <label>
        Public iGEM GitLab or GitHub repository
        <input
          disabled={busy}
          value={url}
          onChange={(e) => {
            setUrl(e.target.value);
            setInspection(undefined);
            setTrusted(false);
          }}
        />
      </label>
      <details><summary>Advanced source version</summary><label>
        Branch, tag or pinned revision (blank uses repository HEAD)
        <input
          disabled={busy}
          value={commit}
          onChange={(e) => {
            setCommit(e.target.value);
            setInspection(undefined);
            setTrusted(false);
          }}
        />
      </label><p>The backend resolves this ref to one immutable commit before download. Future branch changes are not automatically installed.</p></details>
      <button
        disabled={busy || !url}
        onClick={() =>
          void perform("Fetching and inspecting source…",async () => {
            const value = await client.fetchPlugin(url, commit);
            if (!value.source_path)
              throw new Error("Registered source identity missing.");
            setInspection(value);
            setTrusted(false);
          })
        }
      >
        Review plugin
      </button>
      <label>Import local source ZIP<input type="file" accept=".zip" disabled={busy} onChange={event=>{const file=event.target.files?.[0];
        if(file)void perform("Inspecting imported source…",async()=>{setInspection(await client.uploadPluginSource(file));setTrusted(false);});event.target.value='';}}/></label>
      {inspection && (
        <>
          <h4>{inspection.manifest.name} — {inspection.manifest.version}</h4><p>{inspection.manifest.description}</p>
          <p>License: {inspection.manifest.license}. Runtime: {inspection.manifest.runtime}. Requested capabilities: {inspection.capability_requests.join(', ')||'No additional declared capabilities'}.</p>
          <p>Source: {url || "Imported source ZIP"}</p>
          <label>
            <input
              type="checkbox"
              disabled={busy}
              checked={trusted}
              onChange={(e) => setTrusted(e.target.checked)}
            />
            I trust this code; capabilities/secrets still require individual
            maintainer grants
          </label>
          <button
            disabled={busy || !trusted || !inspection.source_path}
            onClick={() =>
              void perform("Installing inspected version…",async () => {
                setInspection(await client.installPlugin(inspection.source_path!, inspection.hash));
                setInstalled(await client.installedPlugins());
              })
            }
          >
            Install inspected plugin
          </button>
        </>
      )}
      </>}
      <h4>Installed plugins</h4>
      {[...new Set(installed.map(value=>value.manifest.id))].map(id=>{const entries=installed.filter(value=>value.manifest.id===id),plugin=entries[0];return <section key={id}>
        <strong>{plugin.manifest.name}</strong> — {entries.some(value=>value.enabled)?'Enabled':'Disabled'} <button onClick={()=>setVersions(versions===id?undefined:id)}>Versions</button>
        {versions===id&&<><p>Disabling a version blocks new tasks, not already-running processes.</p><ul>{entries.map(value=><li key={value.hash}>{value.manifest.version} — {value.enabled?'Enabled':'Disabled'}
        <button disabled={busy} onClick={()=>void action(async()=>{await client.pluginEnabled(value.hash,!value.enabled);setInstalled(await client.installedPlugins());})}>{value.enabled?'Disable':'Enable'} {value.manifest.name}</button></li>)}</ul>
        </>}
      </section>;})}
    </section>
  );
}
