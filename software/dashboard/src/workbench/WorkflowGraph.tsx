import { useRef, useState } from 'react';
import type { Workflow, WorkflowDocument, RunSummaryView, ScientificPrecheckView } from '../contracts/generated';
import { dependencies,statusLabel } from './PlanPanel';
import { matchingRun, ModuleStatus, inputCheckLabel } from './ModuleStatus';

type Position = {x: number; y: number};
export function defaultPositions(workflow: Workflow): Record<string, Position> {
  const depths = new Map<string, number>();
  const depth = (id: string): number => {
    if (depths.has(id)) return depths.get(id)!;
    const node = workflow.nodes.find(n => n.id === id)!;
    const result = Math.max(-1, ...dependencies(node).map(depth)) + 1;
    depths.set(id, result);
    return result;
  };
  const rows = new Map<number, number>();
  return Object.fromEntries(workflow.nodes.map(node => {
    const column = depth(node.id), row = rows.get(column) ?? 0;
    rows.set(column, row + 1);
    return [node.id, {x: 24 + column * 260, y: 24 + row * 240}];
  }));
}

export function WorkflowGraph({workflow, layout, selected, disabled, onSelect, onMove, run, inputCheck,onSelectEdge}: {
  workflow: Workflow; layout?: WorkflowDocument['layout']; selected: string;
  disabled?: boolean; onSelect: (id: string) => void;
  onMove?: (id: string, position: Position) => void;
  run?: RunSummaryView; inputCheck?: ScientificPrecheckView;
  onSelectEdge?:(from:string,to:string)=>void;
}) {
  const snapshot = matchingRun(workflow, run);
  const [drag, setDrag] = useState<{id: string; position: Position}>();
  const pointer = useRef<{id: string; x: number; y: number; start: Position; moved: boolean} | undefined>(undefined);
  const positions = {...defaultPositions(workflow), ...layout, ...(drag ? {[drag.id]: drag.position} : {})};
  const width = Math.max(600, ...Object.values(positions).map(p => p.x + 250));
  const height = Math.max(280, ...Object.values(positions).map(p => p.y + 230));
  return <div className="workflow-graph-scroll" aria-label="Workflow graph">
    <div className="workflow-graph" style={{width, height}}>
      <svg width={width} height={height} aria-label="Module dependencies">
        <defs><marker id="workflow-arrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0,0 L0,8 L8,4 z" fill="currentColor" /></marker></defs>
        {workflow.nodes.flatMap(node => dependencies(node).map(parent => {
          const start = positions[parent], end = positions[node.id];
          const reference = Object.values(node.inputs).some(input => input.kind === 'node' && input.node_id === parent) || (node.map?.items.kind === 'node' && node.map.items.node_id === parent);
          return <path key={`${parent}:${node.id}`} className={reference ? 'data-edge' : 'control-edge'}
            role="button" tabIndex={onSelectEdge?0:-1} aria-label={`Connection ${workflow.nodes.find(n=>n.id===parent)!.label} to ${node.label}`}
            onClick={()=>onSelectEdge?.(parent,node.id)} onKeyDown={event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();onSelectEdge?.(parent,node.id);}}}
            data-from={parent} data-to={node.id} markerEnd="url(#workflow-arrow)"
            d={`M${start.x + 218},${start.y + 38} C${start.x + 250},${start.y + 38} ${end.x - 35},${end.y + 38} ${end.x},${end.y + 38}`}>
            <title>{`${workflow.nodes.find(n => n.id === parent)!.label} → ${node.label}: ${reference ? 'data binding' : 'ordering dependency'}`}</title>
          </path>;
        }))}
      </svg>
      {workflow.nodes.map(node => <button key={node.id} className={`workflow-graph-node ${selected === node.id ? 'selected' : ''}`}
        style={{left: positions[node.id].x, top: positions[node.id].y}} aria-pressed={selected === node.id}
        aria-label={`Module ${node.label}`} disabled={disabled}
        onClick={() => onSelect(node.id)}
        onKeyDown={event => {
          if (!onMove || !['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key)) return;
          event.preventDefault();
          const step = event.shiftKey ? 50 : 10, p = positions[node.id];
          onMove(node.id, {x: Math.max(0, p.x + (event.key === 'ArrowRight' ? step : event.key === 'ArrowLeft' ? -step : 0)),
            y: Math.max(0, p.y + (event.key === 'ArrowDown' ? step : event.key === 'ArrowUp' ? -step : 0))});
        }}
        onPointerDown={event => {
          if (!onMove || event.button !== 0) return;
          event.currentTarget.setPointerCapture(event.pointerId);
          pointer.current = {id: node.id, x: event.clientX, y: event.clientY, start: positions[node.id], moved: false};
        }}
        onPointerMove={event => {
          const p = pointer.current;
          if (!p || p.id !== node.id) return;
          const dx = event.clientX - p.x, dy = event.clientY - p.y;
          if (Math.abs(dx) + Math.abs(dy) > 3) p.moved = true;
          if (p.moved) setDrag({id: node.id, position: {x: Math.max(0, Math.min(100_000, p.start.x + dx)), y: Math.max(0, Math.min(100_000, p.start.y + dy))}});
        }}
        onPointerUp={event => {
          const p = pointer.current;
          pointer.current = undefined;
          if (p?.moved) {
            onMove?.(node.id, {x: Math.max(0, Math.min(100_000, p.start.x + event.clientX - p.x)), y: Math.max(0, Math.min(100_000, p.start.y + event.clientY - p.y))});
          }
          setDrag(undefined);
        }}
        onPointerCancel={() => {pointer.current = undefined; setDrag(undefined);}}
      ><strong>{node.label}</strong><span>{(()=>{const task=snapshot?.nodes.find(value=>value.id===node.id);if(!task)return'Not started';
        if(task.status!=='succeeded')return statusLabel(task.status);const science=task.scientific_summary;
        return science?.missing_input_count?'Completed — missing scientific evidence':science?.numerically_solved_count?'Numerical results recorded':'Completed';})()}</span>
      </button>)}
    </div>
  </div>;
}
