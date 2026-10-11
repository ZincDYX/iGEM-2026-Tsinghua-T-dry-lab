import {useState,lazy,Suspense} from 'react';
import {object} from '../contracts/validation';
import {show} from '../contracts/resultAdapters';
const Series=lazy(()=>import('./viewers/SeriesViewer').then(m=>({default:m.SeriesViewer})));
export function SyntheticPSResult({output,projectId}:{output:Record<string,unknown>;projectId?:string}){
  const [selected,setSelected]=useState('E1');
  if(output.source_type!=='synthetic'||output.formal_prediction_allowed!==false||!object(output.cases))
    return <p role="alert">Unsupported synthetic result contract. No formal result inferred.</p>;
  if(selected==='E3')return <section><h2>E3 · blocked · synthetic</h2><label>Recorded scenario<select aria-label="Synthetic scenario" value={selected} onChange={e=>setSelected(e.target.value)}>{[...Object.keys(output.cases),'E3'].map(id=><option key={id}>{id}</option>)}</select></label><p>ER anchoring needs actual geometry, topology, binding and exchange evidence.</p>{object(output.E3)&&<p>{show(output.E3.missing_inputs)}</p>}</section>;
  const entry=output.cases[selected];
  if(!object(entry)||!object(entry.m4)||!object(entry.m4.result)) return <p>Missing recorded scenario.</p>;
  const result=entry.m4.result;
  const m3=object(entry.m3)?entry.m3:undefined;
  const file=typeof entry.trajectory_artifact==='string'&&entry.trajectory_artifact.startsWith('asset:')?entry.trajectory_artifact.slice(6):undefined;
  return <section>
    <h2>{selected} · M3/M4</h2>
    <p className="scope-warning"><strong>Synthetic demo · {String(result.status).replaceAll("_"," ")}</strong>. Not experimental validation.</p>
    <label>Recorded scenario<select aria-label="Synthetic scenario" value={selected} onChange={e=>setSelected(e.target.value)}>
      {[...Object.keys(output.cases),"E3"].map(id=><option key={id}>{id}</option>)}
    </select></label>
    <h3>M3 recruitment</h3>
    {m3?<div className="table-scroll"><table><thead><tr><th>Enzyme</th><th>Total dense (µM)</th><th>Free dilute (µM)</th><th>Dense fraction (1)</th></tr></thead>
      <tbody>{['oc','dmt'].map(enzyme=>{const record=m3[enzyme];return object(record)?<tr key={enzyme}><td>{enzyme.toUpperCase()}</td>
        {['total_dense_um','free_dilute_um','dense_phase_fraction_of_whole_cell_total'].map(key=><td key={key}>{show(record[key])}</td>)}</tr>:null;})}</tbody></table></div>
      :<p>Single-phase reference: no dense compartment. Dense values are not applicable, not zero.</p>}
    {m3&&<p>OC:DMT dense ratio: {show(m3.dense_oc_dmt_ratio)}</p>}
    <h3>M4 target product</h3>
    <p>The final time point is a transient endpoint, not a steady state.</p>
    {file&&projectId?<Suspense fallback={<p>Loading recorded pool series…</p>}><Series key={file} fileId={file} projectId={projectId} targetSpecies="15" scopeMarked/></Suspense>:<p>No registered trajectory available.</p>}
  </section>;
}
