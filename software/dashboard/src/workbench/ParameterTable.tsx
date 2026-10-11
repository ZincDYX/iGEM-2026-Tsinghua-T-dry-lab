import {useState} from 'react';

export type ParameterRow = {id:string;name:string;value:number|string;unit:string;source?:string;readOnly?:boolean;status?:string};

/** One value/unit editor for recorded parameters and scalar bindings. */
export function ParameterTable({rows,frozen,onSave,sourceActions}:{rows:ParameterRow[];frozen:boolean;
  onSave:(id:string,value:number,unit:string)=>Promise<void>;sourceActions?:(row:ParameterRow)=>React.ReactNode}) {
  const [editing,setEditing]=useState<string>(),[value,setValue]=useState(''),[unit,setUnit]=useState('');
  const [busy,setBusy]=useState(false),[error,setError]=useState('');
  async function save(id:string) {
    if(!value.trim()||!Number.isFinite(Number(value))||!unit.trim()){setError('Enter a finite value and its unit.');return;}
    setBusy(true);setError('');
    try {await onSave(id,Number(value),unit.trim());setEditing(undefined);}
    catch(reason){setError(reason instanceof Error?reason.message:String(reason));}
    finally{setBusy(false);}
  }
  return <>{error&&<p role="alert">{error}</p>}<table><thead><tr><th>Parameter</th><th>Value</th><th>Unit</th></tr></thead><tbody>
    {rows.map(row=><tr key={row.id}><td>{row.name}{row.status&&<small> · {row.status}</small>}
      {row.source&&<details><summary>Source</summary><p>{row.source}</p>{sourceActions?.(row)}</details>}</td>
      {editing===row.id?<><td><input aria-label={`Value for ${row.name}`} type="number" step="any" value={value} disabled={busy} onChange={event=>setValue(event.target.value)}/>
        <button disabled={busy} onClick={()=>void save(row.id)}>Save parameter</button><button disabled={busy} onClick={()=>{setEditing(undefined);setError('');}}>Cancel</button></td>
        <td><input aria-label={`Unit for ${row.name}`} value={unit} disabled={busy} onChange={event=>setUnit(event.target.value)}/></td></>
        :<><td>{!frozen&&!row.readOnly&&typeof row.value==='number'?<button disabled={busy} aria-label={`Edit ${row.name}`} onClick={()=>{setEditing(row.id);setValue(String(row.value));setUnit(row.unit);setError('');}}>{row.value}</button>:row.value}</td><td>{row.unit}</td></>}
    </tr>)}
  </tbody></table></>;
}
