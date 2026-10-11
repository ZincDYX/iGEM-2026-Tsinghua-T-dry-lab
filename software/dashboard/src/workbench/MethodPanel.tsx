import {useEffect, useRef, useState} from 'react';
import temml from 'temml';
import 'temml/dist/Temml-Local.css';
import type {ModuleMethodView, ProjectView,MethodDefinition,MethodDraftPage,MethodDraftView,Workflow} from '../contracts/generated';
import {requestJson} from '../api';
import {parsePublicAsync as parsePublic} from '../contracts/validation';
import {ModuleParameters} from './ModuleParameters';
import * as client from './client';

function FormulaDraftEditor({project,methods,disabled,onPlan,initial}:{project:ProjectView;methods:MethodDefinition[];disabled:boolean;onPlan:(value:Workflow)=>void;initial?:MethodDraftView}) {
  const [page,setPage]=useState<MethodDraftPage>(),[offset,setOffset]=useState(0),[refresh,setRefresh]=useState(0),[previous,setPrevious]=useState<MethodDraftView|undefined>(initial);
  const [methodId,setMethodId]=useState(initial?.base_method_id??''),[formulaId,setFormulaId]=useState(initial?.formula_id??''),[latex,setLatex]=useState(initial?.latex??'');
  const [title,setTitle]=useState(initial?.title??''),[reason,setReason]=useState(initial?.reason??''),[source,setSource]=useState(initial?.source_reference??''),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const [expression,setExpression]=useState(initial?.execution_spec?.expression??''),[outputUnit,setOutputUnit]=useState(initial?.execution_spec?.output_unit??'');
  const [variables,setVariables]=useState<{name:string;value:string;unit:string;source:string}[]>(Object.entries(initial?.execution_spec?.variables??{}).map(([name,v])=>({name,...v,value:String(v.value)})));
  const incomplete=!expression.trim()||!outputUnit.trim()||!variables.length||variables.some(v=>!v.name.trim()||!v.value.trim()||!Number.isFinite(Number(v.value))||!v.unit.trim())||new Set(variables.map(v=>v.name)).size!==variables.length;
  const method=methods.find(value=>value.id===methodId);
  const original=method?.formulas.find(value=>value.id===formulaId);
  useEffect(()=>{let active=true;void client.methodDrafts(project.id,offset).then(value=>{if(active)setPage(value);}).catch(reason=>{if(active)setError(String(reason));});return()=>{active=false;};},[project.id,offset,refresh]);
  return <section aria-label="Custom formula versions"><h4>Propose a separate formula version</h4>
    <p>Create an executable scalar method, not a display-only formula. Existing methods remain unchanged. Values are edited in Parameters once prepared; this new method remains scientifically unvalidated.</p>
    {error&&<p role="alert">{error}</p>}
    <fieldset disabled={disabled||busy}><legend>Custom formula draft</legend>
      <label>Original method<select aria-label="Formula base method" value={methodId} onChange={event=>{setMethodId(event.target.value);setFormulaId('');setLatex('');setPrevious(undefined);setExpression('');setOutputUnit('');setVariables([]);}}><option value="">Choose original version</option>{methods.map(value=><option key={value.id} value={value.id}>{value.title} ({value.version})</option>)}</select></label>
      <label>Formula<select aria-label="Formula to revise" value={formulaId} onChange={event=>{setFormulaId(event.target.value);setLatex(method!.formulas.find(value=>value.id===event.target.value)?.latex??'');setPrevious(undefined);setExpression('');setOutputUnit('');setVariables([]);}}><option value="">Choose original formula</option>{method?.formulas.map(value=><option key={value.id} value={value.id}>{value.id}: {value.title}</option>)}</select></label>
      {original&&<><label>New method title<input aria-label="Custom formula title" value={title} maxLength={200} onChange={event=>setTitle(event.target.value)}/></label>
        <h4>Original baseline · unchanged</h4><Formula latex={original.latex}/><label>Source reference<input aria-label="Custom formula source" value={source} maxLength={2000} onChange={event=>setSource(event.target.value)}/></label>
        <label>Reason and changed assumptions<textarea aria-label="Custom formula reason" value={reason} maxLength={4000} onChange={event=>setReason(event.target.value)}/></label>
        <label>Executable scalar expression<input aria-label="Executable scalar expression" value={expression} maxLength={2000} onChange={event=>setExpression(event.target.value)}/></label>
        <p>Supported: + − * /, integer powers ** (-16 to 16), sqrt, exp, ln, log10, abs. No automatic LaTeX translation, summation, ODEs or code execution. Units: 1, M/mM/uM/nM, mol, L, m/mm/um/nm, s/min/h, kg/g and products/ratios/powers. Inputs are explicitly converted to SI before evaluation; the result is converted to your chosen unit. No inferred biological values.</p>
        {!!expression.trim()&&<><label>Result unit<input aria-label="Formula result unit" value={outputUnit} onChange={event=>setOutputUnit(event.target.value)}/></label>
          <table aria-label="Formula parameter bindings"><thead><tr><th>Parameter</th><th>Value</th><th>Unit</th></tr></thead><tbody>{variables.map((variable,index)=><tr key={index}>
            {(['name','value','unit'] as const).map(field=><td key={field}><input aria-label={`Formula input ${index+1} ${field}`} value={variable[field]} onChange={event=>setVariables(values=>values.map((v,i)=>i===index?{...v,[field]:event.target.value}:v))}/>{field==='name'&&<button onClick={()=>setVariables(values=>values.filter((_,i)=>i!==index))}>Remove input {index+1}</button>}</td>)}
          </tr>)}</tbody></table><p>New exploratory bindings use the declared source above; it is not scientific approval. Revising an existing binding retains its recorded source.</p>
          <button disabled={variables.length>=64} onClick={()=>setVariables(values=>[...values,{name:'',value:'',unit:'',source:''}])}>Add formula input</button></>}
        <button disabled={incomplete||!latex.trim()||!title.trim()||!reason.trim()||!source.trim()} onClick={()=>{setBusy(true);setError('');
          void client.saveMethodDraft(project.id,{base_method_id:method!.id,base_version:method!.version,title,formula_id:formulaId,latex,reason,source_reference:source,
            execution_spec:{expression,output_unit:outputUnit,variables:Object.fromEntries(variables.map(v=>[v.name,{value:Number(v.value),unit:v.unit,source:v.source||source}]))},
            previous_id:previous?.id??null,expected_project_revision:project.revision}).then(value=>{setPrevious(value);setRefresh(value=>value+1);}).catch(reason=>setError(String(reason))).finally(()=>setBusy(false));}}>Save separate unvalidated version</button>
      </>}
    </fieldset>
    <ul>{page?.items.map(value=><li key={value.id}><details><summary>{value.title} — version {value.version}, unvalidated / {value.executable?'exploratory execution available':'not executable'}</summary><p>{value.reason}</p><p>Source: {value.source_reference}</p><h4>Reviewed baseline</h4><Formula latex={value.original_latex}/><h4>{value.executable?"Executed expression preview":"Display-only proposal · not executable"}</h4><Formula latex={value.latex}/>
      {value.execution_spec&&<><p>Executed expression (not inferred from LaTeX): <code>{value.execution_spec.expression}</code>. Result unit: {value.execution_spec.output_unit}</p>
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
    {error&&<code>{latex}</code>}</>;
}

export function MethodPanel({project, toolId, runId, workflowId, nodeId, disabled, onChange, onReview,onPlan,onWorkflowChange,onEditDraft}: {
  project: ProjectView; toolId: string; runId?: string; workflowId?:string; nodeId:string; disabled: boolean; onChange: (value: ProjectView) => Promise<void>;
  onReview: (id: string, stage: 'm3'|'m4', name: string, reviewer: string, reason: string) => Promise<void>;
  onPlan:(value:Workflow)=>void;
  onWorkflowChange:(value:Workflow)=>Promise<void>;onEditDraft:()=>void;
}) {
  const [value, setValue] = useState<ModuleMethodView>();
  const [error, setError] = useState('');
  const [tab, setTab] = useState<'tools'|'formulas'|'parameters'>('formulas');
  const [parameter, setParameter] = useState(''), [reviewer, setReviewer] = useState(''), [reviewReason, setReviewReason] = useState('');
  const [updated,setUpdated]=useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setValue(undefined); setError('');
    const binding=toolId==='workflow.custom_formula'&&(runId||workflowId)?`&node_id=${encodeURIComponent(nodeId)}${workflowId&&!runId?`&workflow_id=${encodeURIComponent(workflowId)}`:''}`:'';
    void requestJson(`/projects/${encodeURIComponent(project.id)}/module-method?tool_id=${encodeURIComponent(toolId)}${runId ? `&run_id=${encodeURIComponent(runId)}` : ''}${binding}`, undefined, controller.signal)
      .then(async raw => {const value=await parsePublic('ModuleMethodView',raw);if (!controller.signal.aborted) setValue(value);})
      .catch(reason => {if (!controller.signal.aborted) setError(String(reason));});
    return () => controller.abort();
  }, [project.id, project.revision, toolId, runId, workflowId,nodeId,updated]);
  async function saveScalar(name:string,next:number,unit:string) {
    const original=value!.scalar_method!;
    const spec=structuredClone(original.execution_spec!);
    const previous=spec.variables[name];
    spec.variables[name]={...previous,value:next,unit};
    const saved=await client.saveMethodDraft(project.id,{base_method_id:original.base_method_id,base_version:original.base_version,
      title:original.title,formula_id:original.formula_id,latex:original.latex,
      reason:`Parameter ${name}: ${previous.value} ${previous.unit} → ${next} ${unit}. Existing source retained for comparison; this override is exploratory and unvalidated.`,
      source_reference:original.source_reference,previous_id:original.id,expected_project_revision:project.revision,execution_spec:spec});
    await onWorkflowChange(await client.methodWorkflow(project.id,saved.id));
    setUpdated(count=>count+1);
  }
  return <section aria-label="Module method">
    <h3>Module method</h3>
    {runId&&<p>Historical snapshot · changes require a new run. <button disabled={disabled} onClick={onEditDraft}>Edit current draft</button></p>}
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
        {value.scalar_method&&<section><h4>{value.scalar_method.title} · version {value.scalar_method.version} · exploratory</h4>
          <Formula latex={value.scalar_method.latex}/><p>Inputs for this expression are in Parameters. The preview and execution share the same expression.</p>
          <details><summary>Method change</summary><p>{value.scalar_method.reason}</p><h4>Original baseline</h4><Formula latex={value.scalar_method.original_latex}/></details></section>}
        {value.configured_mode && <p>Actually configured mode: <strong>{value.configured_mode}</strong>. Original method and extensions are not interchangeable.</p>}
        {!value.methods.length&&!value.scalar_method && <p>No reviewed formula catalog registered for this custom tool. Its output is not presented as an original M1–M4 method.</p>}
        {!value.scalar_method&&value.methods.map(method => <section key={method.id}><h4>{method.title}</h4><p>{method.scope}</p>
          <p>Version {method.version} · source {method.source_reference} · {method.source_version}</p>
          <details><summary>All method steps and gates</summary>{method.steps.map(step => <p key={step.id}><strong>{step.id}: {step.title}</strong> — {step.description}</p>)}</details>
          <details><summary>Symbols and units</summary><dl>{Object.entries(method.symbols).map(([symbol,meaning]) => <div key={symbol}><dt>{symbol}</dt><dd>{meaning}</dd></div>)}</dl></details>
          {method.discrepancies.map(text => <p key={text}>Source discrepancy / boundary: {text}</p>)}
          {method.formulas.map(formula => <section key={formula.id}><h4>{formula.title} · {formula.status.replaceAll('_',' ')}</h4>
            <Formula latex={formula.latex}/>{formula.assumptions.map(text => <p key={text}>{text}</p>)}
            </section>)}
        </section>)}
        {!value.scalar_method&&<p>Formal formulas are read-only. No calculation or formula simplification occurs in this viewer.</p>}
        {!runId && value.methods.length>0 && <details><summary>Edit method · new exploratory version</summary><FormulaDraftEditor key={project.id+toolId+(value.scalar_method?.id??'')} project={project} methods={value.methods} disabled={disabled}
          onPlan={value.scalar_method?next=>{void onWorkflowChange(next).then(()=>setUpdated(count=>count+1)).catch(reason=>setError(String(reason)));}:onPlan} initial={value.scalar_method??undefined}/></details>}
      </>}
      {tab === 'parameters' && <><fieldset disabled={disabled}><ModuleParameters project={project} method={value} frozen={!!runId} onChange={onChange} onScalarChange={saveScalar}/>
          {!runId&&(toolId === 'project.m3' || toolId === 'project.m4') && project.scientific_project && <section aria-label="Human parameter review">
            <h4>Review a saved candidate</h4><p>Backend checks the actual requirement, units, identity, condition and source. Accepting an Assistant proposal does not perform this review.</p>
            <label>Candidate parameter<select aria-label="Candidate parameter" value={parameter} onChange={event => setParameter(event.target.value)}><option value="">Choose candidate</option>
              {project.scientific_project.config.parameters.filter(p => value.parameter_records.some(record=>record.parameter_id===p.parameter_id&&!record.binding_read_only) && ['extracted','validated'].includes(p.review_status)).map(p => <option key={p.parameter_id} value={p.parameter_id}>{p.name} · version {p.parameter_version} · {p.source_reference ?? 'Missing source'}</option>)}</select></label>
            <label>Reviewer name<input aria-label="Reviewer name" value={reviewer} onChange={event => setReviewer(event.target.value)}/></label>
            <label>Scientific review reason<textarea aria-label="Scientific review reason" value={reviewReason} onChange={event => setReviewReason(event.target.value)}/></label>
            <button disabled={!parameter || !reviewer.trim() || !reviewReason.trim()} onClick={() => {
              const selected = project.scientific_project!.config.parameters.find(p => p.parameter_id === parameter)!;
              void onReview(parameter, toolId === 'project.m3' ? 'm3' : 'm4', selected.name, reviewer.trim(), reviewReason.trim());
            }}>Save and review candidate against this module</button>
          </section>}
        </fieldset></>}
    </div>}
  </section>;
}
