import type {Workflow,RunSummaryView} from "../contracts/generated";
import type {WorkflowNode} from "../contracts/Workflow.generated";

export const statusLabel=(value:string)=>({pending:"待执行",queued:"排队",running:"执行中",succeeded:"作业完成",failed:"失败",paused:"已暂停",cancelled:"已取消",interrupted:"已中断",blocked:"阻断"}[value]??value);
export function dependencies(node:WorkflowNode) {
  const values=[...Object.values(node.inputs),...(node.map?[node.map.items]:[])];
  return [...new Set([...node.depends_on,...values.flatMap(value=>value.kind==="node"?[value.node_id]:[])])];
}
export function PlanPanel({workflow,run,selected,onSelect}:{workflow?:Workflow;run?:RunSummaryView;selected:string;onSelect:(id:string)=>void}) {
  if(!workflow)return <div className="empty-panel"><h2>计算计划</h2><p>选择项目并检查输入，再生成固定管线或受控 Agent 提案。这里不填示例科学数值。</p></div>;
  return <section><header className="panel-heading"><h2>{workflow.name}</h2><span>{workflow.nodes.length} 个阶段</span></header>
    <p>{workflow.description}</p><table className="plan-table"><thead><tr><th>阶段</th><th>实际工具</th><th>前置依赖</th><th>作业状态</th><th>检查点</th></tr></thead><tbody>
      {workflow.nodes.map(node=>{const state=run?.nodes.find(value=>value.id===node.id);const policy=workflow.execution_policy;return <tr key={node.id} className={selected===node.id?"selected-row":""}>
        <td><button aria-pressed={selected===node.id} onClick={()=>onSelect(node.id)}>{node.label}</button></td><td>{node.tool_id}</td><td>{dependencies(node).join(" → ")||"无前置节点"}</td><td>{statusLabel(state?.status??"pending")}</td>
        <td>{[policy.checkpoints_before.includes(node.id)?"之前":null,policy.checkpoints_after.includes(node.id)?"之后":null].filter(Boolean).join(" / ")||"—"}</td></tr>;})}</tbody></table>
    <p className="subtle">范围：{workflow.execution_policy.target_node_id??"计划内全部阶段"} · 每次阶段数：{workflow.execution_policy.max_completed_stages??"授权范围内连续执行"} · 工具调用预算：{workflow.execution_policy.max_tool_calls} · 内存硬限制：不支持。</p>
    <p className="subtle">缺证据由原科学门控阻断。作业完成不等于数值有效、证据已批准或实验验证。</p>
  </section>;
}
