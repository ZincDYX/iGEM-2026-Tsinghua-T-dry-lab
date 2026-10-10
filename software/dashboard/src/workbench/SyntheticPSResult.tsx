import {useState,lazy,Suspense} from 'react';
import {object} from '../contracts/validation';
import {show} from '../contracts/resultAdapters';
const Series=lazy(()=>import('./viewers/SeriesViewer').then(m=>({default:m.SeriesViewer})));
export function SyntheticPSResult({output,projectId}:{output:Record<string,unknown>;projectId?:string}){
  const [selected,setSelected]=useState('C1');
  if(output.source_type!=='synthetic'||output.formal_prediction_allowed!==false||!object(output.cases))
    return <p role="alert">Unsupported synthetic result contract. No formal result inferred.</p>;
  const entry=output.cases[selected];
  if(!object(entry)||!object(entry.m4)||!object(entry.m4.result)) return <p>Missing recorded scenario.</p>;
  const result=entry.m4.result;
  const m3=object(entry.m3)?entry.m3:undefined;
  const file=typeof entry.trajectory_artifact==='string'&&entry.trajectory_artifact.startsWith('asset:')?entry.trajectory_artifact.slice(6):undefined;
  return <section>
    <h2>Synthetic M3/M4 reference demonstration</h2>
    <p className="scope-warning"><strong>Synthetic demo.</strong> Not experimental validation, formal M1–M4 prediction, fermentation titer or ER advantage.</p>
    <label>Recorded scenario<select aria-label="Synthetic scenario" value={selected} onChange={e=>setSelected(e.target.value)}>
      {Object.keys(output.cases).map(id=><option key={id}>{id}</option>)}
    </select></label>
    <h3>M3 recruitment</h3>
    {m3?<div className="table-scroll"><table><thead><tr><th>Enzyme</th><th>Free dense (µM)</th><th>Bound dense (µM)</th><th>Total dense (µM)</th><th>Free dilute (µM)</th><th>Occupancy</th><th>Whole-system bound fraction</th><th>Whole-system dense fraction</th></tr></thead>
      <tbody>{['oc','dmt'].map(enzyme=>{const record=m3[enzyme];return object(record)?<tr key={enzyme}><td>{enzyme.toUpperCase()}</td>
        {['free_dense_um','bound_dense_um','total_dense_um','free_dilute_um','site_occupancy','bound_fraction_of_whole_cell_total','dense_phase_fraction_of_whole_cell_total'].map(key=><td key={key}>{show(record[key])}</td>)}</tr>:null;})}</tbody></table></div>
      :<p>Single-phase reference: no dense compartment. Dense values are not applicable, not zero.</p>}
    <h3>M4 pool-specific amounts and concentrations</h3>
    <p>Transient result: {show(result.status)}. The final time point is not a steady state. No fabricated uncertainty interval.</p>
    {file&&projectId?<Suspense fallback={<p>Loading recorded pool series…</p>}><Series key={file} fileId={file} projectId={projectId}/></Suspense>:<p>No registered trajectory available.</p>}
    <h3>E3: ER anchoring remains blocked</h3>
    <p>Actual membrane geometry, topology, site binding, area/volume and exchange evidence are required.</p>
    {object(output.E3)&&Array.isArray(output.E3.missing_inputs)&&<ul>{output.E3.missing_inputs.map((gap,i)=><li key={i}>{show(gap)}</li>)}</ul>}
  </section>;
}
