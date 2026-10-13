import type {Workflow,RunSummaryView,ScientificPrecheckView} from '../contracts/generated';
import type {WorkflowNode} from '../contracts/Workflow.generated';
import {jobLabels} from './messages.en';
import {matchingRun} from './ModuleStatus';
export const statusLabel=(value:string)=>jobLabels[value]??value;
export function dependencies(node:WorkflowNode){const values=[...Object.values(node.inputs),...(node.map?[node.map.items]:[])];return[...new Set([...node.depends_on,...values.flatMap(value=>value.kind==='node'?[value.node_id]:[])])];}
export function PlanPanel({workflow,run,selected,onSelect}:{workflow?:Workflow;run?:RunSummaryView;selected:string;onSelect:(id:string)=>void;inputCheck?:ScientificPrecheckView}){
  if(!workflow)return <p>No workflow selected.</p>;
  const snapshot=matchingRun(workflow,run);
  return <table className="plan-table"><thead><tr><th>Module</th><th>Depends on</th><th>Status</th></tr></thead><tbody>{workflow.nodes.map(node=>{
    const task=snapshot?.nodes.find(value=>value.id===node.id);
    return <tr key={node.id}><td><button aria-pressed={node.id===selected} onClick={()=>onSelect(node.id)}>{node.label}</button></td>
      <td>{dependencies(node).map(id=>workflow.nodes.find(value=>value.id===id)?.label??'Unavailable module').join(', ')||'None'}</td>
      <td>{task?task.status==='succeeded'&&task.scientific_summary?.missing_input_count?'Completed — missing scientific evidence':statusLabel(task.status):'Not started'}</td></tr>;
  })}</tbody></table>;
}
