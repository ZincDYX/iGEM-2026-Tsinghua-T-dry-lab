import { useEffect, useRef, useState } from 'react';
import type { Workflow, WorkflowDocument, RunSummaryView, ScientificPrecheckView } from '../contracts/generated';
import * as client from './client';
import { PlanPanel, dependencies } from './PlanPanel';
import { WorkflowGraph, defaultPositions } from './WorkflowGraph';

/** One persisted WorkflowDocument; Graph and List never own separate nodes. */
export function WorkflowWorkspace({projectId, projectRevision, seedId, seed, document, run, inputCheck, selected, busy, frozen,
  onDocument, onSelect}: {
  projectId?: string; projectRevision?: number; seedId?: string; seed?: Workflow; document?: WorkflowDocument;
  run?: RunSummaryView; inputCheck?: ScientificPrecheckView; selected: string; busy: boolean; frozen: boolean;
  onDocument: (value: WorkflowDocument) => void; onSelect: (id: string) => void;
}) {
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState<WorkflowDocument[]>([]);
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [connections,setConnections]=useState(false);
  const [frozenView, setFrozenView] = useState<'graph'|'list'>('graph');
  const live = useRef(document), locked = useRef(false), epoch = useRef(0);
  live.current = document;
  const workflow = frozen ? seed : document?.workflow ?? seed;
  const view = frozen ? frozenView : document?.view ?? 'graph';
  const choices = document && !frozen ? [...saved.filter(value => value.id !== document.id), document] : saved;
  useEffect(() => {
    if (projectId && document?.project_id === projectId)
      localStorage.setItem(`fusionlab.workflow-document.${projectId}`, document.id);
  }, [projectId, document?.id]);
  useEffect(() => {
    const stamp = ++epoch.current, controller = new AbortController();
    setError(''); setFrom(''); setTo(''); setSaved([]);
    if (!projectId || frozen) return () => controller.abort();
    void client.workflowDocuments(projectId, controller.signal).then(async values => {
      if (controller.signal.aborted || stamp !== epoch.current) return;
      setSaved(values);
      const current = live.current;
      if (current?.project_id === projectId) {
        const newer = values.find(value => value.id === current.id && value.revision > current.revision);
        if (newer) {live.current = newer; onDocument(newer); if (newer.selected_node_id) onSelect(newer.selected_node_id);}
        return;
      }
      const restoreId = seedId ?? (!seed ? localStorage.getItem(`fusionlab.workflow-document.${projectId}`) : null);
      const existing = values.find(d => d.id === restoreId);
      if (existing) {onDocument(existing); if (existing.selected_node_id) onSelect(existing.selected_node_id);}
      else if (seed && seedId && projectRevision) {
        const value = await client.saveWorkflowDocument(projectId, seedId, {workflow: seed, layout: {}, selected_node_id: seed.nodes[0].id, view: 'graph'}, projectRevision);
        if (stamp === epoch.current && !controller.signal.aborted) onDocument(value);
      }
    }).catch(reason => {if (!controller.signal.aborted && stamp === epoch.current) setError(String(reason instanceof Error ? reason.message : reason));});
    return () => {controller.abort(); ++epoch.current;};
    // Seed is immutable for this review ID; editor changes must not reload it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, seedId, frozen]);

  async function open(id: string) {
    if (!id || !projectId || locked.current || frozen) return;
    const stamp = epoch.current;
    locked.current = true; setSaving(true); setError('');
    try {
      const retrieved = await client.workflowDocument(projectId, id);
      if (stamp !== epoch.current) return;
      // A concurrent policy save can be newer than this read response.
      const current = live.current;
      const value = current?.id === id && current.revision > retrieved.revision ? current : retrieved;
      live.current = value; onDocument(value); if (value.selected_node_id) onSelect(value.selected_node_id);
    } catch (reason) {if (stamp === epoch.current) setError(reason instanceof Error ? reason.message : String(reason));}
    finally {locked.current = false; if (stamp === epoch.current) setSaving(false);}
  }

  async function persist(changes: Partial<Pick<WorkflowDocument, 'workflow'|'layout'|'selected_node_id'|'view'>>) {
    const current = live.current;
    if (!current || !projectId || !projectRevision || locked.current || frozen) return;
    const stamp = epoch.current;
    locked.current = true; setSaving(true); setError('');
    try {
      const value = await client.saveWorkflowDocument(projectId, current.id, {
        layout: current.layout, selected_node_id: current.selected_node_id, view: current.view, ...changes,
      }, projectRevision, current.revision);
      if (stamp === epoch.current) {live.current = value; onDocument(value); if (value.selected_node_id) onSelect(value.selected_node_id);}
    } catch (reason) {if (stamp === epoch.current) setError(reason instanceof Error ? reason.message : String(reason));}
    finally {locked.current = false; if (stamp === epoch.current) setSaving(false);}
  }
  const disabled = busy || saving || (!frozen && !document);
  const node = workflow?.nodes.find(n => n.id === selected);
  const select = (id: string) => {onSelect(id); if (!frozen) void persist({selected_node_id: id});};
  function revise(change: (value: Workflow) => void) {
    if (!workflow) return;
    const value = structuredClone(workflow); change(value);
    const ids = new Set(value.nodes.map(n => n.id));
    const layout = Object.fromEntries(Object.entries(document?.layout ?? {}).filter(([id]) => ids.has(id)));
    void persist({workflow: value, layout, selected_node_id: ids.has(selected) ? selected : value.nodes[0]?.id ?? null});
  }
  return <section aria-label="Workflow editor">
    <header className="panel-heading"><h2>Workflow</h2>{saving&&<span>Saving…</span>}</header>
    {frozen&&<p>Historical run — read-only.</p>}
    {!frozen && choices.length > 0 && <label>Open saved workflow<select aria-label="Open saved workflow" value={document?.id ?? ''} disabled={busy || saving} onChange={event => void open(event.target.value)}><option value="">Choose saved workflow</option>{choices.map(d => <option key={d.id} value={d.id}>{d.workflow.name} (revision {d.semantic_revision})</option>)}</select></label>}
    {error && <p role="alert">{error}</p>}
    {workflow ? <>
      <h3>{workflow.name}</h3>
      <p>{workflow.description}</p>
      <div className="workflow-view-switch" role="group" aria-label="Workflow view">
        {(['graph','list'] as const).map(value => <button key={value} aria-pressed={view === value} disabled={disabled} onClick={() => frozen ? setFrozenView(value) : void persist({view: value})}>{value === 'graph' ? 'Graph' : 'List'}</button>)}
        {!frozen && <button disabled={disabled} onClick={() => void persist({layout: defaultPositions(workflow)})}>Arrange modules</button>}
        {!frozen&&node&&<><button onClick={()=>{setConnections(value=>!value);setTo(node.id);}}>Connections</button><button disabled={disabled||workflow.nodes.length===1} onClick={()=>revise(w=>{w.nodes=w.nodes.filter(n=>n.id!==selected) as Workflow['nodes'];})}>Remove module</button>
          {(['before','after'] as const).map(position=>{const field=position==='before'?'checkpoints_before':'checkpoints_after';return <button key={position} disabled={disabled} aria-pressed={workflow.execution_policy[field].includes(node.id)} onClick={()=>revise(value=>{value.execution_policy[field]=value.execution_policy[field].includes(node.id)?value.execution_policy[field].filter(id=>id!==node.id):[...value.execution_policy[field],node.id];})}>Pause {position} this module</button>;})}
        </>}
      </div>
      {view === 'graph' ? <WorkflowGraph workflow={workflow} layout={frozen ? undefined : document?.layout} selected={selected} disabled={disabled}
        run={run} inputCheck={inputCheck}
        onSelectEdge={frozen?undefined:(from,to)=>{setFrom(from);setTo(to);setConnections(true);select(to);}}
        onSelect={select} onMove={frozen ? undefined : (id, position) => void persist({layout: {...document?.layout, [id]: position}, selected_node_id: id})}/>
        : <PlanPanel workflow={workflow} run={run} inputCheck={inputCheck} selected={selected} onSelect={select}/>}
      {!frozen && document && connections && <section className="workflow-edit-controls">
        <h3>Ordering dependencies</h3>
        <p>This sets execution order, not a new scientific data binding.</p>
        <label>Upstream module<select aria-label="Upstream module" value={from} disabled={disabled} onChange={e => setFrom(e.target.value)}><option value="">Choose upstream</option>{workflow.nodes.map(n => <option key={n.id} value={n.id}>{n.label}</option>)}</select></label>
        <label>Downstream module<select aria-label="Downstream module" value={to} disabled={disabled} onChange={e => setTo(e.target.value)}><option value="">Choose downstream</option>{workflow.nodes.map(n => <option key={n.id} value={n.id}>{n.label}</option>)}</select></label>
        <button disabled={disabled || !from || !to || from === to} onClick={() => revise(w => {const target = w.nodes.find(n => n.id === to)!; if (!target.depends_on.includes(from)) target.depends_on.push(from);})}>Connect modules</button>
        <button disabled={disabled || !from || !to || !workflow.nodes.find(n => n.id === to)?.depends_on.includes(from)} onClick={() => revise(w => {const target = w.nodes.find(n => n.id === to)!; target.depends_on = target.depends_on.filter(id => id !== from);})}>Remove ordering dependency</button>
      </section>}
    </> : <p>No workflow yet. Choose a method in Inputs, create a proposal, or open a saved workflow.</p>}
  </section>;
}
