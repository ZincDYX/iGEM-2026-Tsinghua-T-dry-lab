import {useEffect, useRef, useState} from 'react';
import temml from 'temml';
import 'temml/dist/Temml-Local.css';
import type {ModuleMethodView, ProjectView,MethodDefinition,MethodDraftPage,MethodDraftView,Workflow} from '../contracts/generated';
import {requestJson} from '../api';
import {parsePublicAsync as parsePublic} from '../contracts/validation';
import {ScientificInputForms} from './ScientificInputForms';
import type {FieldSchema} from './ScientificFields';
import * as client from './client';

function FormulaDraftEditor({project,methods,disabled,onPlan}:{project:ProjectView;methods:MethodDefinition[];disabled:boolean;onPlan:(value:Workflow)=>void}) {
  const [page,setPage]=useState<MethodDraftPage>(),[offset,setOffset]=useState(0),[refresh,setRefresh]=useState(0),[previous,setPrevious]=useState<MethodDraftView>();
  const [methodId,setMethodId]=useState(''),[formulaId,setFormulaId]=useState(''),[latex,setLatex]=useState('');
  const [title,setTitle]=useState(''),[reason,setReason]=useState(''),[source,setSource]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const [expression,setExpression]=useState(''),[outputUnit,setOutputUnit]=useState('');
  const [variables,setVariables]=useState<{name:string;value:string;unit:string;source:string}[]>([]);
  const incomplete=!!expression.trim()&&(!outputUnit.trim()||!variables.length||variables.some(v=>!v.name.trim()||!v.value.trim()||!Number.isFinite(Number(v.value))||!v.unit.trim()||!v.source.trim())||new Set(variables.map(v=>v.name)).size!==variables.length);
  const method=methods.find(value=>value.id===methodId);
  const original=method?.formulas.find(value=>value.id===formulaId);
  useEffect(()=>{let active=true;void client.methodDrafts(project.id,offset).then(value=>{if(active)setPage(value);}).catch(reason=>{if(active)setError(String(reason));});return()=>{active=false;};},[project.id,offset,refresh]);
  return <section aria-label="Custom formula versions"><h4>Propose a separate formula version</h4>
    <p>Original methods stay read-only. LaTeX alone is not executable. Add an explicit scalar expression and sourced inputs to prepare a separate exploratory workflow; review and Accept, then Start. Its result remains scientifically unvalidated, never formal M1–M4 evidence.</p>
    {error&&<p role="alert">{error}</p>}
    <fieldset disabled={disabled||busy}><legend>Custom formula draft</legend>
      <label>Original method<select aria-label="Formula base method" value={methodId} onChange={event=>{setMethodId(event.target.value);setFormulaId('');setLatex('');setPrevious(undefined);setExpression('');setOutputUnit('');setVariables([]);}}><option value="">Choose original version</option>{methods.map(value=><option key={value.id} value={value.id}>{value.title} ({value.version})</option>)}</select></label>
      <label>Formula<select aria-label="Formula to revise" value={formulaId} onChange={event=>{setFormulaId(event.target.value);setLatex(method!.formulas.find(value=>value.id===event.target.value)?.latex??'');setPrevious(undefined);setExpression('');setOutputUnit('');setVariables([]);}}><option value="">Choose original formula</option>{method?.formulas.map(value=><option key={value.id} value={value.id}>{value.id}: {value.title}</option>)}</select></label>
      {original&&<><label>New method title<input aria-label="Custom formula title" value={title} maxLength={200} onChange={event=>setTitle(event.target.value)}/></label>
        <label>Exact proposed LaTeX<textarea aria-label="Proposed formula LaTeX" value={latex} maxLength={8000} rows={4} onChange={event=>setLatex(event.target.value)}/></label>
        <Formula latex={latex}/><label>Source reference<input aria-label="Custom formula source" value={source} maxLength={2000} onChange={event=>setSource(event.target.value)}/></label>
        <label>Reason and changed assumptions<textarea aria-label="Custom formula reason" value={reason} maxLength={4000} onChange={event=>setReason(event.target.value)}/></label>
        <label>Optional executable expression<input aria-label="Executable scalar expression" value={expression} maxLength={2000} onChange={event=>setExpression(event.target.value)}/></label>
        <p>Supported: + − * /, integer powers ** (-16 to 16), sqrt, exp, ln, log10, abs. No automatic LaTeX translation, summation, ODEs or code execution. Units: 1, M/mM/uM/nM, mol, L, m/mm/um/nm, s/min/h, kg/g and products/ratios/powers. Inputs are explicitly converted to SI before evaluation; the result is converted to your chosen unit. No inferred biological values.</p>
        {!!expression.trim()&&<><label>Result unit<input aria-label="Formula result unit" value={outputUnit} onChange={event=>setOutputUnit(event.target.value)}/></label>
          {variables.map((variable,index)=><fieldset key={index}><legend>Input {index+1}</legend>{(['name','value','unit','source'] as const).map(field=><label key={field}>{field}<input aria-label={`Formula input ${index+1} ${field}`} value={variable[field]} onChange={event=>setVariables(values=>values.map((v,i)=>i===index?{...v,[field]:event.target.value}:v))}/></label>)}
            <button onClick={()=>setVariables(values=>values.filter((_,i)=>i!==index))}>Remove input {index+1}</button></fieldset>)}
          <button disabled={variables.length>=64} onClick={()=>setVariables(values=>[...values,{name:'',value:'',unit:'',source:''}])}>Add formula input</button></>}
        <button disabled={incomplete||!latex.trim()||!title.trim()||!reason.trim()||!source.trim()} onClick={()=>{setBusy(true);setError('');
          void client.saveMethodDraft(project.id,{base_method_id:method!.id,base_version:method!.version,title,formula_id:formulaId,latex,reason,source_reference:source,
            execution_spec:expression.trim()?{expression,output_unit:outputUnit,variables:Object.fromEntries(variables.map(v=>[v.name,{value:Number(v.value),unit:v.unit,source:v.source}]))}:null,
            previous_id:previous?.id??null,expected_project_revision:project.revision}).then(value=>{setPrevious(value);setRefresh(value=>value+1);}).catch(reason=>setError(String(reason))).finally(()=>setBusy(false));}}>Save separate unvalidated version</button>
      </>}
    </fieldset>
    <ul>{page?.items.map(value=><li key={value.id}><details><summary>{value.title} — version {value.version}, unvalidated / {value.executable?'exploratory execution available':'not executable'}</summary><p>Original {value.base_method_id} ({value.base_version}), formula {value.formula_id}. {value.reason}</p><p>Source: {value.source_reference}</p><Formula latex={value.latex}/>
      {value.execution_spec&&<><p>Executed expression (not inferred from LaTeX): <code>{value.execution_spec.expression}</code>. Result unit: {value.execution_spec.output_unit}</p>
        <table><thead><tr><th>Input</th><th>Value</th><th>Unit</th><th>Source</th></tr></thead><tbody>{Object.entries(value.execution_spec.variables).map(([name,v])=><tr key={name}><td>{name}</td><td>{v.value}</td><td>{v.unit}</td><td>{v.source}</td></tr>)}</tbody></table>
        <button disabled={disabled||busy} onClick={()=>{setBusy(true);void client.methodWorkflow(project.id,value.id).then(onPlan).catch(reason=>setError(String(reason))).finally(()=>setBusy(false));}}>Prepare exploratory workflow</button></>}
      <button disabled={disabled||busy} onClick={()=>{setPrevious(value);setMethodId(value.base_method_id);setFormulaId(value.formula_id);setLatex(value.latex);setTitle(value.title);setSource(value.source_reference);setReason(value.reason);
        setExpression(value.execution_spec?.expression??'');setOutputUnit(value.execution_spec?.output_unit??'');setVariables(Object.entries(value.execution_spec?.variables??{}).map(([name,v])=>({name,...v,value:String(v.value)})));}}>Revise as a new version</button></details></li>)}</ul>
    <nav aria-label="Formula draft pages"><button disabled={!offset} onClick={()=>setOffset(value=>value-20)}>Previous versions</button><button disabled={!page?.has_more} onClick={()=>setOffset(value=>value+20)}>Next versions</button></nav>
  </section>;
}

export function Formula({latex}: {latex: string}) {
  const element = useRef<HTMLDivElement>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    setError('');
    try {
      const markup = temml.renderToString(latex, {displayMode: true, xml: true, trust: false, throwOnError: true, maxExpand: 1000, maxSize: [20,200]});
      // Import renderer-generated MathML as XML, never evaluate user HTML.
      const parsed = new DOMParser().parseFromString(markup, 'application/xml');
      if (parsed.documentElement.localName !== 'math' || parsed.querySelector('parsererror')) throw Error('Invalid MathML output.');
      element.current!.replaceChildren(document.importNode(parsed.documentElement, true));
    } catch (reason) {
      element.current!.replaceChildren();
      setError(`Formula rendering unavailable; exact source expression retained below. ${reason instanceof Error ? reason.message : ''}`);
    }
  }, [latex]);
  return <><div ref={element} className="method-formula"/>{error && <p role="alert">{error}</p>}
    <details><summary>Exact LaTeX source</summary><code>{latex}</code></details></>;
}

export function MethodPanel({project, toolId, runId, disabled, onChange, onReview,onPlan}: {
  project: ProjectView; toolId: string; runId?: string; disabled: boolean; onChange: (value: ProjectView) => void;
  onReview: (id: string, stage: 'm3'|'m4', name: string, reviewer: string, reason: string) => Promise<void>;
  onPlan:(value:Workflow)=>void;
}) {
  const [value, setValue] = useState<ModuleMethodView>();
  const [schema, setSchema] = useState<FieldSchema>();
  const [error, setError] = useState('');
  const [tab, setTab] = useState<'tools'|'formulas'|'parameters'>('tools');
  const [parameter, setParameter] = useState(''), [reviewer, setReviewer] = useState(''), [reviewReason, setReviewReason] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    setValue(undefined); setSchema(undefined); setError('');
    void requestJson(`/projects/${encodeURIComponent(project.id)}/module-method?tool_id=${encodeURIComponent(toolId)}${runId ? `&run_id=${encodeURIComponent(runId)}` : ''}`, undefined, controller.signal)
      .then(async raw => {const value=await parsePublic('ModuleMethodView',raw);if (!controller.signal.aborted) setValue(value);})
      .catch(reason => {if (!controller.signal.aborted) setError(String(reason));});
    return () => controller.abort();
  }, [project.id, project.revision, toolId, runId]);
  useEffect(() => {
    if (tab !== 'parameters' || !project.scientific_project || runId) return;
    const controller = new AbortController();
    void requestJson(`/scientific-projects/form-schema?prepared_through=${project.scientific_project.config.prepared_through}`, undefined, controller.signal)
      .then(raw => {if (!controller.signal.aborted) setSchema(raw as FieldSchema);})
      .catch(reason => {if (!controller.signal.aborted) setError(String(reason));});
    return () => controller.abort();
  }, [tab, project.id, project.scientific_project?.config.prepared_through, runId]);
  return <section aria-label="Module method">
    <h3>Module method</h3>
    <div role="tablist" aria-label="Module method sections">{(['tools','formulas','parameters'] as const).map(id =>
      <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id)}>{id[0].toUpperCase()+id.slice(1)}</button>)}</div>
    {error && <p role="alert">{error}</p>}
    {value && <div role="tabpanel">
      {tab === 'tools' && <><h4>{value.tool.name} · {value.tool.version}</h4><p>{value.tool.description}</p>
        <p>Execution: {value.tool.runtime} on the connected compute backend · {value.tool.status.replaceAll('_',' ')}.</p>
        <p>License: {value.tool.license}</p><p>Inputs: {value.tool.input_names.join(', ')}</p><p>{value.tool.output_scope}</p>
        {value.methods.map(method => <p key={method.id}>Method tools: {method.tools.join(' · ')}. Each external program requires its own actual configuration, legal access and parsed real output.</p>)}
        {value.limitations.map(text => <p key={text}>{text}</p>)}
      </>}
      {tab === 'formulas' && <>
        {value.configured_mode && <p>Actually configured mode: <strong>{value.configured_mode}</strong>. Original method and extensions are not interchangeable.</p>}
        {!value.methods.length && <p>No reviewed formula catalog registered for this custom tool. Its output is not presented as an original M1–M4 method.</p>}
        {value.methods.map(method => <section key={method.id}><h4>{method.title}</h4><p>{method.scope}</p>
          <p>Version {method.version} · source {method.source_reference} · {method.source_version}</p>
          <details><summary>All method steps and gates</summary>{method.steps.map(step => <p key={step.id}><strong>{step.id}: {step.title}</strong> — {step.description}</p>)}</details>
          <details><summary>Symbols and units</summary><dl>{Object.entries(method.symbols).map(([symbol,meaning]) => <div key={symbol}><dt>{symbol}</dt><dd>{meaning}</dd></div>)}</dl></details>
          {method.discrepancies.map(text => <p key={text}>Source discrepancy / boundary: {text}</p>)}
          {method.formulas.map(formula => <details key={formula.id}><summary>{formula.id} · {formula.title} · {formula.status.replaceAll('_',' ')}</summary>
            <Formula latex={formula.latex}/>{formula.assumptions.map(text => <p key={text}>{text}</p>)}
            <p>Backend implementation: {formula.implementation.join(', ')}</p></details>)}
        </section>)}
        <p>Formal formulas are read-only. No calculation or formula simplification occurs in this viewer.</p>
        {!runId && value.methods.length>0 && <FormulaDraftEditor key={project.id+toolId} project={project} methods={value.methods} disabled={disabled} onPlan={onPlan}/>}
      </>}
      {tab === 'parameters' && <>{runId ? <><p>Frozen run parameters are read-only. These are from the recorded run revision, not the current draft. Create an iteration to change them.</p>
        <table><thead><tr><th>Parameter</th><th>Value</th><th>Unit</th><th>Condition</th><th>Source</th><th>Review</th></tr></thead><tbody>
          {value.parameter_records.slice(0,100).map((record,index)=><tr key={index}><td>{String(record.name)} v{String(record.parameter_version)}</td><td>{String(record.value)}</td>
            <td>{String(record.unit??'Missing unit')}</td><td>{String(record.condition_id??'Global; applicability still checked')}</td><td>{String(record.source_reference??'Missing source')}</td><td>{String(record.review_status)}</td></tr>)}
        </tbody></table>{value.parameter_records.length>100&&<p>First 100 frozen records shown. Export the original recorded inputs for the complete set.</p>}</> :
        <fieldset disabled={disabled}><ScientificInputForms project={project} section="parameters" onChange={onChange} schema={schema}/>
          {(toolId === 'project.m3' || toolId === 'project.m4') && project.scientific_project && <section aria-label="Human parameter review">
            <h4>Review a saved candidate</h4><p>Backend checks the actual requirement, units, identity, condition and source. Accepting an Assistant proposal does not perform this review.</p>
            <label>Candidate parameter<select aria-label="Candidate parameter" value={parameter} onChange={event => setParameter(event.target.value)}><option value="">Choose candidate</option>
              {project.scientific_project.config.parameters.filter(p => ['extracted','validated'].includes(p.review_status)).map(p => <option key={p.parameter_id} value={p.parameter_id}>{p.name} · version {p.parameter_version} · {p.source_reference ?? 'Missing source'}</option>)}</select></label>
            <label>Reviewer name<input aria-label="Reviewer name" value={reviewer} onChange={event => setReviewer(event.target.value)}/></label>
            <label>Scientific review reason<textarea aria-label="Scientific review reason" value={reviewReason} onChange={event => setReviewReason(event.target.value)}/></label>
            <button disabled={!parameter || !reviewer.trim() || !reviewReason.trim()} onClick={() => {
              const selected = project.scientific_project!.config.parameters.find(p => p.parameter_id === parameter)!;
              void onReview(parameter, toolId === 'project.m3' ? 'm3' : 'm4', selected.name, reviewer.trim(), reviewReason.trim());
            }}>Save and review candidate against this module</button>
          </section>}
        </fieldset>}</>}
    </div>}
  </section>;
}
