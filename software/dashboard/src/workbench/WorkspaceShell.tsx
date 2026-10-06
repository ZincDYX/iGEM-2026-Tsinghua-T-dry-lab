import {useCallback,useEffect,useRef,useState,type CSSProperties} from "react";
import type {ProposalView,RunListView,RuntimeInfoView} from "../contracts/generated";
import type {ExecutionPolicy} from "../contracts/Workflow.generated";
import type {Goal} from "../types";
import {LazyJson} from "../contracts/LazyJson";
import {show} from "../contracts/resultAdapters";
import * as client from "./client";
import {useProject} from "./useProject";
import {useRun} from "./useRun";
import {PlanPanel,dependencies,statusLabel} from "./PlanPanel";
import {AgentPanel} from "./AgentPanel";
import {InputEditor} from "./InputEditor";
import {SelectedResult} from "./SelectedResult";
import {ComparisonPanel} from "./ComparisonPanel";
import {InputDiffPanel} from "./InputDiffPanel";
import {WorkflowImporter} from "./WorkflowImporter";
import {LocalSettings} from "./LocalSettings";
import {PluginPanel} from "./PluginPanel";
import {Splitter} from "./Splitter";
import {useWorkbenchLayout} from "./useWorkbenchLayout";
import {useSelectedResult} from "./useSelectedResult";
import {usePlanActions} from "./usePlanActions";
import "./workbench.css";

type Tab="plan"|"inputs"|"results"|"compare"|"settings"|"plugins";
const tabs:{id:Tab;label:string}[]=[{id:"plan",label:"工作流 / 计划"},{id:"inputs",label:"输入 / 证据"},{id:"results",label:"阶段结果"},{id:"compare",label:"版本比较"},{id:"settings",label:"本地设置"},{id:"plugins",label:"受信插件"}];
function Tabs({values,selected,onChange,label}:{values:{id:string;label:string}[];selected:string;onChange:(id:string)=>void;label:string}) {
  return<div role="tablist" aria-label={label} onKeyDown={e=>{if(e.key!=="ArrowRight"&&e.key!=="ArrowLeft")return;const index=values.findIndex(tab=>tab.id===selected);const next=(index+(e.key==="ArrowRight"?1:-1)+values.length)%values.length;onChange(values[next].id);e.preventDefault();const nodes=e.currentTarget.querySelectorAll<HTMLButtonElement>("[role=tab]");nodes[next]?.focus();}}>
    {values.map(tab=><button role="tab" key={tab.id} tabIndex={selected===tab.id?0:-1} aria-selected={selected===tab.id} onClick={()=>onChange(tab.id)}>{tab.label}</button>)}</div>;
}
export function WorkspaceShell() {
  const[error,setError]=useState("");const[pending,setPending]=useState(0);const busy=pending>0;
  const fail=useCallback((reason:unknown)=>setError(reason instanceof Error?reason.message:"操作未完成；请查看安全诊断。"),[]);
  const project=useProject(fail);
  const[runId,setRunId]=useState<string>();const[refresh,setRefresh]=useState(0);
  const{run,events}=useRun(runId,project.draft?.id,refresh,fail);
  const[info,setInfo]=useState<RuntimeInfoView>();const[history,setHistory]=useState<RunListView[]>([]);
  const[proposal,setProposal]=useState<ProposalView>();const[goal,setGoal]=useState<Goal>("fusion_screen");const[objective,setObjective]=useState("");
  const[mode,setMode]=useState<"template"|"hybrid">("template");const[permission,setPermission]=useState(false);
  const[policy,setPolicy]=useState<ExecutionPolicy>(client.defaultPolicy);
  const[tab,setTab]=useState<Tab>("plan");const[inspector,setInspector]=useState("agent");const[bottom,setBottom]=useState("queue");
  const[selected,setSelected]=useState("");const[editing,setEditing]=useState(false);
  const view=useWorkbenchLayout();const{layout,bottomOpen,setBottomOpen,inspectorOpen,setInspectorOpen}=view;
  const[infoRefresh,setInfoRefresh]=useState(0);const goalChosen=useRef(false);
  const planGeneration=useRef(0);const currentProject=project.draft;
  const result=useSelectedResult(run,currentProject?.id,selected);const nodeData=result.data;
  const actionHistory=usePlanActions(currentProject?.id,`${proposal?.id}:${proposal?.status}:${run?.id}:${run?.state_version}`,fail);const actions=actionHistory.items;
  const workflow=proposal?.workflow??run?.workflow;
  const node=workflow?.nodes.find(value=>value.id===selected);
  const stopped=run&&["succeeded","failed","paused","cancelled","interrupted"].includes(run.status);
  const executing=run&&["queued","running"].includes(run.status);

  async function action(job:()=>Promise<unknown>) {setPending(value=>value+1);setError("");try{await job();}catch(reason){fail(reason);}finally{setPending(value=>value-1);}}
  function invalidate(){++planGeneration.current;setProposal(undefined);}
  function updatePolicy(value:ExecutionPolicy){setPolicy(value);invalidate();}
  useEffect(()=>{
    const controller=new AbortController();let timer:ReturnType<typeof setTimeout>;
    async function load(){try{const value=await client.info(controller.signal);if(controller.signal.aborted)return;setInfo(value);
      if(value.capabilities.scientific_mcp==="checking"||executing)timer=setTimeout(load,2500);
    }catch(reason){if(!controller.signal.aborted)fail(reason);}}
    void load();return()=>{controller.abort();clearTimeout(timer);};
  },[!!executing,infoRefresh,fail]);
  useEffect(()=>{invalidate();setSelected("");setEditing(false);setHistory([]);setPolicy(client.defaultPolicy());goalChosen.current=false;
    setRunId(currentProject?localStorage.getItem(`fusionlab.run.${currentProject.id}`)??undefined:undefined);
    setGoal(currentProject?.scientific_project?"scientific_pipeline":"fusion_screen");
  },[currentProject?.id]);
  useEffect(()=>{if(currentProject?.scientific_project&&!goalChosen.current)setGoal("scientific_pipeline");},[currentProject?.id,!!currentProject?.scientific_project]);
  useEffect(()=>{if(!currentProject)return;const controller=new AbortController();
    client.history(currentProject.id,0,controller.signal).then(value=>{if(!controller.signal.aborted)setHistory(value);}).catch(reason=>{if(!controller.signal.aborted)fail(reason)});
    return()=>controller.abort();
  },[currentProject?.id,run?.status,fail]);

  async function propose(scope=policy){await action(async()=>{
    const saved=await project.save();if(!saved)return;
    const stamp=project.generation.current;const planStamp=planGeneration.current;
    const value=await client.propose(saved.id,goal,objective,mode,scope,permission);
    if(stamp!==project.generation.current||planStamp!==planGeneration.current)return;
    setPolicy(scope);setProposal(value);setTab("plan");setSelected(value.workflow?.nodes[0]?.id??"");
  });}
  async function decide(decision:"accept"|"reject"){if(!proposal)return;const stamp=planGeneration.current;await action(async()=>{const value=await client.decide(proposal.id,decision);if(stamp===planGeneration.current)setProposal(value);});}
  async function importWorkflow(create:()=>Promise<import("../contracts/generated").Workflow>){await action(async()=>{
    const saved=await project.save();if(!saved)return;
    const stamp=project.generation.current;const planStamp=planGeneration.current;
    const workflow=await create();const value=await client.proposeCustom(saved.id,workflow,objective);
    if(stamp!==project.generation.current||planStamp!==planGeneration.current)return;
    setProposal(value);setSelected(value.workflow?.nodes[0]?.id??"");
  });}
  async function start(){if(!proposal)return;const stamp=project.generation.current;await action(async()=>{const value=await client.start(proposal);if(stamp===project.generation.current){setRunId(value.id);setRefresh(value=>value+1);setProposal(undefined);setBottom("queue");}});}
  async function control(kind:"pause"|"cancel"|"resume"|"retry"){if(!run)return;const id=run.id;await action(async()=>{await client.control(id,kind,kind==="retry"?selected:undefined);if(runId===id)setRefresh(value=>value+1);});}
  function discardDraft(message:string){return !(project.dirty||editing)||window.confirm(message+"（包括未应用 JSON 编辑）。继续？");}
  function chooseProject(id:string){if(!discardDraft("切换项目将放弃当前未保存草稿"))return;invalidate();setRunId(undefined);void project.choose(id);}
  const style={"--left-width":`${layout.left}px`,"--right-width":`${layout.right}px`,"--bottom-height":`${layout.bottom}px`} as CSSProperties;
  return <div ref={view.root} className={`workbench ${layout.theme} ${layout.density} ${view.narrow?"narrow":""} ${inspectorOpen?"":"inspector-hidden"} ${bottomOpen?"":"bottom-hidden"}`} style={style}>
    <header className="workbench-top"><span className="brand">FusionLab</span><span>融合蛋白与自组装研究工作台</span><span className="workspace-state">{info?`本地/私有工作区 ${info.workspace_id.slice(0,8)}`:"基础服务连接中"}</span><button onClick={()=>setInspectorOpen(value=>!value)}>检查器</button><button onClick={()=>setBottomOpen(value=>!value)}>任务面板</button></header>
    <div className="workbench-toolbar" aria-label="项目与执行控制">
      <button disabled={busy} onClick={()=>{if(!discardDraft("新建项目将放弃当前未保存草稿"))return;project.new();setRunId(undefined);invalidate();setTab("inputs");}}>新建项目</button>
      <button disabled={busy||!currentProject||editing} onClick={()=>void action(()=>project.save())}>保存草稿</button><button disabled={!currentProject} onClick={()=>setTab("inputs")}>导入 / 检查输入</button>
      <button disabled={busy||!currentProject||editing} onClick={()=>void propose()}>生成 / 审阅计划</button>
      <button disabled={busy||!currentProject||editing||info?.capabilities.stage_step!=="ready"||!!executing} onClick={()=>{if(run?.status==="paused"&&run.workflow.execution_policy.max_completed_stages===1)void control("resume");else{const value={...client.defaultPolicy(),...policy,max_completed_stages:1,target_node_id:null};invalidate();void propose(value);}}}>运行下一阶段</button>
      <button disabled={busy||!currentProject||!node||editing||!!executing} onClick={()=>{const value={...policy,target_node_id:selected,max_completed_stages:null};invalidate();void propose(value);}}>运行至选中（先重审范围）</button>
      <button disabled={busy||proposal?.status!=="accepted"||project.dirty||editing} onClick={()=>void start()}>确认并运行</button>
      <button disabled={busy||!executing||!!run?.control} onClick={()=>void control("pause")}>请求暂停</button><button disabled={busy||!run||!["queued","running","paused","interrupted"].includes(run.status)||run?.control==="cancel"} onClick={()=>void control("cancel")}>取消运行</button>
      <button disabled={busy||!run||!["paused","interrupted"].includes(run.status)} onClick={()=>void control("resume")}>继续已授权范围</button>
      <button disabled={busy||!run||!selected||!["failed","interrupted"].includes(run.nodes.find(value=>value.id===selected)?.status??"")} onClick={()=>void control("retry")}>重试选中节点</button>
      <button disabled={busy||!run} onClick={()=>{if(!discardDraft("创建迭代将放弃当前未保存草稿"))return;void action(async()=>{const value=await client.iteration(run!.id);project.adopt(value.project);setRunId(undefined);invalidate();setTab("inputs");});}}>创建输入迭代</button>
    </div>
    <aside id="project-tree" className="project-tree" aria-label="项目与运行树"><h2>项目资源</h2><select aria-label="当前项目" disabled={busy} value={currentProject?.id??""} onChange={e=>chooseProject(e.target.value)}><option value="" disabled>选择或创建项目</option>{currentProject&&!project.summaries.some(row=>row.id===currentProject.id)&&<option value={currentProject.id}>{currentProject.name}（草稿）</option>}{project.summaries.map(row=><option key={row.id} value={row.id}>{row.name} · r{row.revision}</option>)}</select>
      {currentProject&&<><p>{currentProject.sequences.length} 条蛋白序列</p><button onClick={()=>setTab("inputs")}>▸ 科学配置 / 条件</button><button onClick={()=>setTab("inputs")}>▸ 部件 / 构建 / 组成</button><button onClick={()=>{setTab("inputs");setInspector("evidence");}}>▸ 参数来源 / 测量</button><h3>运行（最近 50 条 / 页）</h3>
        {history.map(value=><button className={runId===value.id?"tree-selected":""} key={value.id} title={value.id} onClick={()=>{invalidate();setRunId(value.id);setRefresh(n=>n+1);setTab("plan");}}>{value.name} · r{value.project_revision}<small>{statusLabel(value.status)}</small></button>)}
        {history.length>=50&&<button disabled={busy} onClick={()=>void action(async()=>{const values=await client.history(currentProject.id,history.length);setHistory(previous=>[...previous,...values.filter(value=>!previous.some(row=>row.id===value.id))]);})}>加载下一页运行</button>}
        <h3>科学产物</h3>{run?.artifacts.map(value=><button key={value.id} onClick={()=>{setSelected(value.node_id);setTab("results");}}>{value.node_id} · {value.hash.slice(0,10)}</button>)}
      </>}
    </aside>
    <Splitter dimension="left" value={layout.left} {...view.bounds.left} defaultValue={view.defaults.left} onChange={(value,save)=>view.resize("left",value,save)}/>
    <main className="workspace-center"><Tabs values={tabs} selected={tab} label="中央工作区" onChange={id=>{const value=tabs.find(t=>t.id===id);if(value)setTab(value.id);}}/>
      <div className="workspace-content" role="tabpanel"><div className="document-status"><span>{currentProject?.name??"未载入项目"} · {project.dirty?"有未保存修改":"草稿已同步"}{editing?" · 有未应用编辑":""}</span><span>{run?`${statusLabel(run.status)} / 输入 r${run.project_revision}`:"无已启动运行"}</span></div>
        {error&&<div className="error-strip" role="alert">{error}<button onClick={()=>setError("")}>关闭提示</button></div>}
        {executing&&run?.control&&<p className="control-notice">已请求{run.control==="pause"?"暂停":"取消"}，等待当前实际步骤结束；不修改或截断科学求解。</p>}
        {project.loading?<p>读取项目…</p>:currentProject?<div hidden={tab!=="inputs"}><InputEditor key={currentProject.id} project={currentProject} busy={busy} dirty={project.dirty} onEditing={value=>{setEditing(value);invalidate();}} onChange={value=>{project.edit(value);invalidate();}} action={action}/></div>:tab==="inputs"?<p>先创建或选择项目。</p>:null}
        {tab==="plan"&&<><PlanPanel workflow={workflow??undefined} run={proposal?undefined:run} selected={selected} onSelect={setSelected}/><section className="policy-editor"><h3>执行授权与停止条件（软件策略）</h3><label><input type="checkbox" checked={policy.max_completed_stages===1} onChange={e=>updatePolicy({...policy,max_completed_stages:e.target.checked?1:null})}/>每次完成一个阶段后暂停</label>
          <label>工具调用预算<input type="number" min="1" value={policy.max_tool_calls} onChange={e=>{const value=Number(e.target.value);if(Number.isInteger(value)&&value>0)updatePolicy({...policy,max_tool_calls:value});}}/></label>
          <label>派发截止秒数（空值不限；不强杀求解器）<input type="number" min="1" value={policy.stop_after_seconds??""} onChange={e=>{const value=e.target.value===""?null:Number(e.target.value);if(value===null||value>0)updatePolicy({...policy,stop_after_seconds:value});}}/></label>
          {node&&<><button onClick={()=>updatePolicy({...policy,checkpoints_before:policy.checkpoints_before.includes(selected)?policy.checkpoints_before.filter(id=>id!==selected):[...policy.checkpoints_before,selected]})}>切换选中阶段前检查点</button><button onClick={()=>updatePolicy({...policy,checkpoints_after:policy.checkpoints_after.includes(selected)?policy.checkpoints_after.filter(id=>id!==selected):[...policy.checkpoints_after,selected]})}>切换选中阶段后检查点</button><p>草稿检查点：前 [{policy.checkpoints_before.join(", ")}] / 后 [{policy.checkpoints_after.join(", ")}]；修改后必须重新生成与接受提案，不能改当前运行快照。</p></>}
          <p>工具内部单步、内存硬限制和跨运行科学结果复用：不支持。停止 Agent 提案不会自动取消已授权数值任务。</p></section><WorkflowImporter key={currentProject?.id} busy={busy} enabled={!!currentProject&&!editing} submit={importWorkflow} onEdit={invalidate}/></>}
        {tab==="results"&&(run?<><label>结果对象<select aria-label="结果对象" value={selected} onChange={e=>setSelected(e.target.value)}><option value="">选择阶段 / 分支对象</option>{run.nodes.map(value=><option key={value.id} value={value.id}>{value.id} · {statusLabel(value.status)}</option>)}</select></label><SelectedResult run={run} selected={selected} data={nodeData} error={result.error} offset={result.offset} onOffset={result.setOffset} action={action}/></>:<p>尚无当前项目的运行；不会生成示例结果。</p>)}
        {tab==="compare"&&<ComparisonPanel history={history} current={run}/>}
        {tab==="settings"&&<LocalSettings layout={layout} onLayout={view.update} info={info} onRefresh={()=>setInfoRefresh(value=>value+1)}/>}
        {tab==="plugins"&&<PluginPanel busy={busy} action={action}/>}
      </div>
    </main>
    {inspectorOpen&&!view.narrow&&<Splitter dimension="right" value={layout.right} {...view.bounds.right} defaultValue={view.defaults.right} onChange={(value,save)=>view.resize("right",value,save)}/>}
    <aside id="workspace-inspector" className="workspace-inspector" aria-label="研究检查器"><div className="inspector-heading"><span>{view.narrow?"检查器抽屉；执行控制保留在顶部":"研究检查器"}</span><button onClick={()=>setInspectorOpen(false)}>关闭检查器</button></div><Tabs label="检查器标签" values={[{id:"agent",label:"Agent"},{id:"evidence",label:"输入 / 证据"},{id:"diagnostics",label:"诊断"}]} selected={inspector} onChange={setInspector}/><div className="inspector-content">
      {inspector==="agent"&&<AgentPanel proposal={proposal} info={info} goal={goal} objective={objective} mode={mode} permission={permission} busy={busy} canPlan={!!currentProject&&!editing} onGoal={value=>{goalChosen.current=true;setGoal(value);invalidate();}} onObjective={value=>{setObjective(value);invalidate();}} onMode={value=>{setMode(value);invalidate();}} onPermission={value=>{setPermission(value);invalidate();}} onPropose={()=>void propose()} onDecision={value=>void decide(value)}/>}
      {inspector==="evidence"&&<section><h2>选中对象 / 来源</h2><p>{node?.label??"尚未选中阶段"}</p>{node&&<><p>工具：{node.tool_id} · 前置：{dependencies(node).join(", ")||"无"}</p><LazyJson value={node.inputs} label="输入绑定（不是客户端科学标志）"/><LazyJson value={run?.tools[node.tool_id]} label="实际工具版本 / 实现 hash"/></>}
        <p>当前草稿 r{currentProject?.revision??"未提供"} · 选中运行原输入 r{run?.project_revision??"未提供"}；修改草稿不会覆盖冻结运行。</p>{currentProject&&<InputDiffPanel project={currentProject} runId={run?.id} dirty={project.dirty}/>}<LazyJson value={currentProject?.scientific_project?.config.experimental_context} label="权威科学条件"/><p aria-label="已加载结果身份">{nodeData?`已加载：${run?.id} / ${nodeData.node.id} / attempt ${nodeData.node.attempts} / ${nodeData.artifact?.hash??"尚无产物"} / page ${nodeData.offset}`:"选中结果尚未加载；不展示其他阶段原值。"}</p><LazyJson value={nodeData?.node.output} label="当前结果页的原值 / 单位 / 来源"/>
        <button onClick={()=>setTab("inputs")}>定位输入与源文件</button><button disabled={!run||!selected} onClick={()=>setTab("results")}>定位阶段结果</button></section>}
      {inspector==="diagnostics"&&<section><h2>计算诊断</h2><p>作业、数值、证据、实验验证是独立状态；没有记录不视为 0 或通过。</p><LazyJson value={nodeData?.node.error} label="安全错误 / diagnostic_id"/><LazyJson value={nodeData?.node.output} label="选中科学记录 / 原 warning code"/><p>非幂等中断须外部作业对账；工具版本变化需新迭代，不能强制续跑。</p></section>}
    </div></aside>
    {bottomOpen&&<Splitter dimension="bottom" value={layout.bottom} {...view.bounds.bottom} defaultValue={view.defaults.bottom} onChange={(value,save)=>view.resize("bottom",value,save)}/>}
    <section id="workspace-bottom" className="workspace-bottom" aria-label="任务与动作面板"><Tabs label="底部面板标签" values={[{id:"queue",label:"任务队列"},{id:"events",label:"工具 / 阶段事件"},{id:"agent",label:"Agent 行动"},{id:"problems",label:"问题 / 审批"}]} selected={bottom} onChange={setBottom}/><div className="bottom-content">
      {bottom==="queue"&&<><p>全局任务：{show(info?.resources.active_tasks)} 执行 / {show(info?.resources.queued_tasks)} 排队 · CPU 池 {info?.max_workers??"未提供"} · GPU 槽 {show(info?.resources.gpu_slots)} · 内存硬限制不支持</p><table><thead><tr><th>任务 / 原输入</th><th>实际状态</th><th>控制请求</th><th>范围</th></tr></thead><tbody>{run&&<tr><td>{run.id} / r{run.project_revision}</td><td>{statusLabel(run.status)}</td><td>{run.control??"无"}</td><td>{run.workflow.execution_policy.target_node_id??"授权计划"}</td></tr>}</tbody></table></>}
      {bottom==="events"&&<table><thead><tr><th>序号</th><th>节点</th><th>实际事件</th><th>公开状态 / 原因</th></tr></thead><tbody>{events.map(event=><tr key={event.seq}><td>{event.seq}</td><td>{event.node_id??"运行"}</td><td>{event.event}</td><td>{show(event.payload)}</td></tr>)}</tbody></table>}
      {bottom==="agent"&&<><p>行动账本窗口最多 500 条；{actionHistory.trimmed?"较早行已截断，请查询服务端账本。":"当前窗口未截断。"}</p><table><thead><tr><th>身份</th><th>主体</th><th>动作</th><th>关联运行</th></tr></thead><tbody>{actions.map(event=><tr key={event.seq}><td>{event.proposal_id}</td><td>{event.actor}</td><td>{event.action}</td><td>{event.run_id??"仅提案，尚未运行"}</td></tr>)}</tbody></table>{actionHistory.hasMore&&<button onClick={actionHistory.loadMore}>加载后续行动页（有界窗口）</button>}</>}
      {bottom==="problems"&&<><p>{error||"无当前公开 API 错误；不代表科学证据完整。"}</p><p>提案：{proposal?.status??"未生成"} · 科学参数/测量审批：仅原有明确记录有效，接受提案不代替审批。</p>{proposal?.missing_inputs.map(item=><p key={item}>{item}</p>)}<button disabled={!proposal||proposal.status!=="proposed"} onClick={()=>void decide("reject")}>停止 / 拒绝当前 Agent 提案</button><p>数值任务取消需使用顶部“取消运行”，两者作用对象不同。</p></>}
    </div></section>
    <footer className="workbench-footer"><span>{busy?"操作中":stopped?"阶段边界 / 终态":executing?"后台实际执行中":"就绪"}</span><span>科学原式与证据审批不因界面改变 · 未提供值不补零 · 事件有界显示</span></footer>
  </div>;
}
