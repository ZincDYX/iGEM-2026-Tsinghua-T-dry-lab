import {useEffect, useRef, useState} from 'react';
import temml from 'temml';
import 'temml/dist/Temml-Local.css';
import type {ModuleMethodView, ProjectView,MethodDefinition,MethodDraftPage,MethodDraftView} from '../contracts/generated';
import {requestJson} from '../api';
import {parsePublicAsync as parsePublic} from '../contracts/validation';
import {ScientificInputForms} from './ScientificInputForms';
import type {FieldSchema} from './ScientificFields';
import * as client from './client';

function FormulaDraftEditor({project,methods,disabled}:{project:ProjectView;methods:MethodDefinition[];disabled:boolean}) {
  const [page,setPage]=useState<MethodDraftPage>(),[offset,setOffset]=useState(0),[refresh,setRefresh]=useState(0),[previous,setPrevious]=useState<MethodDraftView>();
  const [methodId,setMethodId]=useState(''),[formulaId,setFormulaId]=useState(''),[latex,setLatex]=useState('');
  const [title,setTitle]=useState(''),[reason,setReason]=useState(''),[source,setSource]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const method=methods.find(value=>value.id===methodId);
  const original=method?.formulas.find(value=>value.id===formulaId);
  useEffect(()=>{let active=true;void client.methodDrafts(project.id,offset).then(value=>{if(active)setPage(value);}).catch(reason=>{if(active)setError(String(reason));});return()=>{active=false;};},[project.id,offset,refresh]);
  return <section aria-label="Custom formula versions"><h4>Propose a separate formula version</h4>
    <p>Original methods stay read-only. A draft is explicitly unvalidated and cannot be executed. It needs a separately implemented and verified backend tool version; saving LaTeX is not scientific computation or approval.</p>
    {error&&<p role="alert">{error}</p>}
    <fieldset disabled={disabled||busy}><legend>Custom formula draft</legend>
      <label>Original method<select aria-label="Formula base method" value={methodId} onChange={event=>{setMethodId(event.target.value);setFormulaId('');setLatex('');setPrevious(undefined);}}><option value="">Choose original version</option>{methods.map(value=><option key={value.id} value={value.id}>{value.title} ({value.version})</option>)}</select></label>
      <label>Formula<select aria-label="Formula to revise" value={formulaId} onChange={event=>{setFormulaId(event.target.value);setLatex(method!.formulas.find(value=>value.id===event.target.value)?.latex??'');setPrevious(undefined);}}><option value="">Choose original formula</option>{method?.formulas.map(value=><option key={value.id} value={value.id}>{value.id}: {value.title}</option>)}</select></label>
      {original&&<><label>New method title<input aria-label="Custom formula title" value={title} maxLength={200} onChange={event=>setTitle(event.target.value)}/></label>
        <label>Exact proposed LaTeX<textarea aria-label="Proposed formula LaTeX" value={latex} maxLength={8000} rows={4} onChange={event=>setLatex(event.target.value)}/></label>
        <Formula latex={latex}/><label>Source reference<input aria-label="Custom formula source" value={source} maxLength={2000} onChange={event=>setSource(event.target.value)}/></label>
        <label>Reason and changed assumptions<textarea aria-label="Custom formula reason" value={reason} maxLength={4000} onChange={event=>setReason(event.target.value)}/></label>
        <button disabled={!latex.trim()||!title.trim()||!reason.trim()||!source.trim()} onClick={()=>{setBusy(true);setError('');
          void client.saveMethodDraft(project.id,{base_method_id:method!.id,base_version:method!.version,title,formula_id:formulaId,latex,reason,source_reference:source,
            previous_id:previous?.id??null,expected_project_revision:project.revision}).then(value=>{setPrevious(value);setRefresh(value=>value+1);}).catch(reason=>setError(String(reason))).finally(()=>setBusy(false));}}>Save separate unvalidated version</button>
      </>}
    </fieldset>
    <ul>{page?.items.map(value=><li key={value.id}><details><summary>{value.title} — version {value.version}, unvalidated / not executable</summary><p>Original {value.base_method_id} ({value.base_version}), formula {value.formula_id}. {value.reason}</p><p>Source: {value.source_reference}</p><Formula latex={value.latex}/>
      <button disabled={disabled||busy} onClick={()=>{setPrevious(value);setMethodId(value.base_method_id);setFormulaId(value.formula_id);setLatex(value.latex);setTitle(value.title);setSource(value.source_reference);setReason(value.reason);}}>Revise as a new version</button></details></li>)}</ul>
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

export function MethodPanel({project, toolId, runId, disabled, onChange, onReview}: {
  project: ProjectView; toolId: string; runId?: string; disabled: boolean; onChange: (value: ProjectView) => void;
  onReview: (id: string, stage: 'm3'|'m4', name: string, reviewer: string, reason: string) => Promise<void>;
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
        {!runId && value.methods.length>0 && <FormulaDraftEditor key={project.id+toolId} project={project} methods={value.methods} disabled={disabled}/>}
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
