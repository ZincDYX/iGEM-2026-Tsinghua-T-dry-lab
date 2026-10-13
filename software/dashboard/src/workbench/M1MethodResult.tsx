import {useState} from 'react';
import {object} from '../contracts/validation';
import {m1Checks, show} from '../contracts/resultAdapters';

export function M1MethodResult({output}: {output: Record<string, unknown>}) {
  const rows = m1Checks(output);
  const [selected,setSelected] = useState('');
  if (!rows) return <p role="alert">M1 candidate records could not be read.</p>;
  if (!rows.length) return <p>No candidate records on this page.</p>;
  const current = rows.find(row=>row.candidate_id===selected) ?? rows[0];
  const screen = object(current.screen) ? current.screen : {};
  const precheck = object(current.precheck) ? current.precheck : {};
  const features = object(precheck.features) ? precheck.features : {};
  const featureLabels: Record<string,string> = {length:'Length (aa)',gs_fraction:'Glycine / serine fraction',pro_fraction:'Proline fraction',
    aromatic_fraction:'Aromatic fraction',hydrophobic_fraction:'Hydrophobic fraction',charged_fraction:'Charged fraction',polar_fraction:'Polar fraction',
    top2_fraction:'Top two residues fraction',fcr:'Fraction charged residues',ncpr:'Net charge per residue',
    mean_hydropathy:'Mean hydropathy',shannon_entropy:'Shannon entropy',net_charge_proxy:'Net charge proxy',max_hydrophobic_run:'Longest hydrophobic run (aa)'};
  const gaps = screen.missing_required_evidence ?? current.missing;
  return <section aria-label="M1 method checks"><h2>M1 candidates</h2><p>Sequence checks; not experimental validation.</p>
    <table><thead><tr><th>Candidate</th><th>Decision</th><th>Risk / reason</th><th>Key features</th></tr></thead><tbody>
      {rows.map(row=>{const p=object(row.precheck)?row.precheck:{};const s=object(row.screen)?row.screen:{};const f=object(p.features)?p.features:{};
        return <tr key={row.candidate_id}><td><button onClick={()=>setSelected(row.candidate_id)}>{row.candidate_id}</button></td><td>{row.verdict}</td>
          <td>{show([...(Array.isArray(s.hard_reject_reasons)?s.hard_reject_reasons:Array.isArray(p.hard_reject_reasons)?p.hard_reject_reasons:[]), ...(Array.isArray(s.review_reasons)?s.review_reasons:[]), ...(row.verdict==='blocked'?['Needs missing evidence']:[])])}</td><td>{show(p.sequence_kind)} · {show(f.length)} aa</td></tr>;})}
    </tbody></table><h3>{current.candidate_id}</h3>
    {Array.isArray(gaps)&&gaps.length>0&&<p>Missing evidence: {show(gaps.map(value=>typeof value==='string'?value.replaceAll('_',' '):value))}</p>}
    <details><summary>Features</summary><table aria-label="Computed sequence features"><thead><tr><th>Feature</th><th>Value</th></tr></thead><tbody>
      {Object.entries(featureLabels).filter(([key])=>typeof features[key]==='number').map(([key,label])=><tr key={key}><td>{label}</td><td>{show(features[key])}</td></tr>)}
    </tbody></table></details>
    <details><summary>Calculation details</summary><p>Decision: {current.verdict}. {show(screen.hard_reject_reasons??precheck.hard_reject_reasons)}</p>{Array.isArray(screen.review_reasons)&&screen.review_reasons.length>0&&<p>Review reasons: {show(screen.review_reasons)}</p>}</details>
  </section>;
}
