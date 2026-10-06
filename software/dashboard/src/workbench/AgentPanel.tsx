import type {ProposalView,RuntimeInfoView} from "../contracts/generated";
import type {Goal} from "../types";
import {LazyJson} from "../contracts/LazyJson";

export function AgentPanel(props:{proposal?:ProposalView;info?:RuntimeInfoView;goal:Goal;objective:string;mode:"template"|"hybrid";permission:boolean;busy:boolean;canPlan:boolean;
  onGoal:(goal:Goal)=>void;onObjective:(value:string)=>void;onMode:(mode:"template"|"hybrid")=>void;onPermission:(value:boolean)=>void;onPropose:()=>void;onDecision:(action:"accept"|"reject")=>void}) {
  const p=props.proposal;
  return <section aria-label="Agent 计划提案"><h2>Agent / 计划提案</h2>
    <label>研究目标<textarea aria-label="研究目标" value={props.objective} onChange={event=>props.onObjective(event.target.value)} placeholder="描述目标或数据变动，不提供虚构参数"/></label>
    <label>计算入口<select aria-label="计算入口" value={props.goal} onChange={event=>{const value=event.target.value;if(value==="fusion_screen"||value==="assembly_review"||value==="pathway_simulation"||value==="scientific_pipeline")props.onGoal(value);}}>
      <option value="fusion_screen">融合蛋白序列筛查</option><option value="assembly_review">自组装组成核验</option><option value="pathway_simulation">上传通路稳态</option><option value="scientific_pipeline">M1–M5 原式科学管线</option></select></label>
    <label>规划来源<select aria-label="规划来源" value={props.mode} onChange={event=>props.onMode(event.target.value==="hybrid"?"hybrid":"template")}><option value="template">确定性模板（不调用 LLM）</option><option value="hybrid" disabled={props.info?.capabilities.hybrid_planning!=="ready"}>混合语义 / 确定性编译器</option></select></label>
    {props.info?.capabilities.hybrid_planning!=="ready"&&<p className="subtle">混合模型未配置；不读取或展示现有凭据，不声称调用成功。</p>}
    {props.mode==="hybrid"&&<label><input type="checkbox" checked={props.permission} onChange={e=>props.onPermission(e.target.checked)}/>允许向私有配置的模型发送本次目标与公开证据摘要</label>}
    <button disabled={props.busy||!props.canPlan} onClick={props.onPropose}>生成可审阅提案</button>
    {p&&<article className="proposal"><h3>{p.source==="validated_template"?"模板提案":p.source==="hybrid_semantic_compiler"?"混合规划提案":"用户工作流提案"} · {p.status}</h3><p>{p.rationale}</p>
      <p>变动类别：{p.change_types.join(", ")||"模板 / 用户 DAG；没有 LLM 语义分类"}</p>
      <dl><dt>请求阶段</dt><dd>{p.requested_stages.join(" → ")||"无可执行阶段"}</dd><dt>实际范围（含依赖）</dt><dd>{p.execution_stages.join(" → ")||"阻断"}</dd><dt>已核验复用</dt><dd>{p.reused_artifacts.join(", ")||"无；不会自动复用"}</dd><dt>缺项</dt><dd>{p.missing_inputs.join("；")||"无提案自报缺项；科学 stage 仍二次核验"}</dd></dl>
      <h4>证据身份</h4>{p.evidence.length?<ul>{p.evidence.map(hash=><li key={hash}><code>{hash}</code></li>)}</ul>:<p>未引用额外证据。</p>}
      <ul>{p.limitations.map((line,i)=><li key={i}>{line}</li>)}</ul>
      <LazyJson value={p.review_identity} label="本次审阅工具 / 环境身份（不含私有路径与配置）"/>
      {p.previous_review_identity&&<LazyJson value={p.previous_review_identity} label="clone 原运行工具 / 环境身份（核对差异后接受）"/>}
      {p.confirmation&&<p className="subtle">项目 revision {p.confirmation.project_revision} · 输入 {p.confirmation.project_input_sha256.slice(0,12)} · 工作流 {p.confirmation.workflow_sha256.slice(0,12)}</p>}
      <button disabled={props.busy||p.status!=="proposed"} onClick={()=>props.onDecision("accept")}>接受提案（不启动计算）</button><button disabled={props.busy||!["proposed","accepted"].includes(p.status)} onClick={()=>props.onDecision("reject")}>拒绝提案</button>
      <p className="subtle">修改目标、策略或输入会使当前提案失效，需重新生成与接受；这不审批科学参数。</p></article>}
  </section>;
}
