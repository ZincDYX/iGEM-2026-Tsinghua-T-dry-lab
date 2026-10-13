import {useEffect,useState} from 'react';
import {parsePublicAsync} from '../contracts/validation';
import type {FormulaResult} from '../contracts/generated';

export function CustomFormulaResult({output}:{output:unknown}) {
  const [result,setResult]=useState<FormulaResult>(),[error,setError]=useState('');
  const [details,setDetails]=useState(false);
  useEffect(()=>{let active=true;setResult(undefined);setError('');
    void parsePublicAsync('FormulaResult',output).then(value=>{if(active)setResult(value);}).catch(()=>{if(active)setError('Invalid custom formula result contract; no number displayed.');});
    return()=>{active=false;};},[output]);
  if(error)return <p role="alert">{error}</p>;
  if(!result)return <p>Loading recorded formula result…</p>;
  return <section aria-label="Custom formula result"><h3>{result.method.title} — version {result.method.method_version}</h3>
    <p>Exploratory scalar calculation · scientifically unvalidated · not formal M1–M4 evidence.</p>
    <p>Result: <output>{result.value} {result.unit}</output></p>
    <button onClick={()=>setDetails(value=>!value)}>Method / Data</button>
    {details&&<><p>Expression: <code>{result.method.spec.expression}</code></p><table><thead><tr><th>Input</th><th>Value</th><th>Unit</th><th>Source</th></tr></thead><tbody>
      {Object.entries(result.method.spec.variables).map(([name,v])=><tr key={name}><td>{name}</td><td>{v.value}</td><td>{v.unit}</td><td>{v.source}</td></tr>)}
    </tbody></table><p>Source: {result.method.source_reference}. Changed assumptions: {result.method.reason}</p>
    </>}
  </section>;
}
