import type {ReactNode} from 'react';
import {EditableValue} from './EditableValue';
export type ParameterRow={id:string;name:string;value:number|string;unit:string;source?:string;readOnly?:boolean;status?:string};
export function ParameterTable({rows,frozen,onSave,sourceActions}:{rows:ParameterRow[];frozen:boolean;onSave:(id:string,value:number,unit:string)=>Promise<void>;sourceActions?:(row:ParameterRow)=>ReactNode}){
  if(!rows.length)return null;
  return <table><thead><tr><th>Parameter</th><th>Value</th><th>Unit</th></tr></thead><tbody>{rows.map(row=><tr key={row.id}>
    <td>{row.name}{row.status&&<small> — {row.status}</small>}{row.source&&<details><summary>View source</summary><p>{row.source}</p>{sourceActions?.(row)}</details>}</td><td>{typeof row.value==='number'?<EditableValue name={row.name} value={row.value} unit={row.unit} showUnit={false} frozen={frozen||row.readOnly} onSave={(value,unit)=>onSave(row.id,value,unit)}/>:row.value}</td>
    <td>{row.unit}</td>
  </tr>)}</tbody></table>;
}
