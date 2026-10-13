import {useState} from 'react';
import {show} from '../contracts/resultAdapters';

/** One exact-value editor. Rendering never rounds the value submitted. */
export function EditableValue({name,value,unit,frozen=false,showUnit=true,onSave}:{name:string;value:number;unit:string;frozen?:boolean;showUnit?:boolean;onSave:(value:number,unit:string)=>Promise<void>}){
  const [editing,setEditing]=useState(false),[text,setText]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
  async function save(){
    if(!text.trim()||!Number.isFinite(Number(text))){setError('Enter a finite number.');return;}
    if(Number(text)===value){setEditing(false);return;}
    setBusy(true);setError('');try{await onSave(Number(text),unit);setEditing(false);}catch(reason){setError(String(reason));}finally{setBusy(false);}
  }
  return <span className="editable-value">{editing?<><input autoFocus aria-label={`Value for ${name}`} type="number" step="any" value={text} disabled={busy}
    onChange={event=>setText(event.target.value)} onKeyDown={event=>{if(event.key==='Enter'){event.preventDefault();void save();}else if(event.key==='Escape'){event.preventDefault();setEditing(false);setError('');}}}/>
    <button disabled={busy} onClick={()=>void save()}>Save parameter</button><button disabled={busy} onClick={()=>{setEditing(false);setError('');}}>Cancel</button></>
    :frozen?<span title={String(value)}>{show(value)}</span>:<button title={String(value)} aria-label={`Edit ${name}`} onClick={()=>{setText(String(value));setEditing(true);setError('');}}>{show(value)}</button>}
    {showUnit&&<span className="parameter-unit">{unit}</span>}{error&&<span role="alert">{error}</span>}
  </span>;
}
