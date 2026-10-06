import {Component,useEffect,useState,type ReactNode} from "react";
import {object} from "./contracts/validation";
import {adaptSteadyResult,numbers,sequenceOutput,show,stageRecords} from "./contracts/resultAdapters";
import {LazyJson} from "./contracts/LazyJson";
import {requestJson} from "./api";
import {M1Matrix,M2Metrics} from "./workbench/ScreenResultTables";
import {MissingEvidence} from "./workbench/MissingEvidence";
export {object,adaptSteadyResult,sequenceOutput};

export interface ResultRun {
  id:string;
  nodes:{id:string;parent_id:string|null;status:string;output:unknown}[];
  snapshot:{workflow:{nodes:{id:string;tool_id:string}[]};project?:{revision:number}};
}
export function nodeTool(run:ResultRun,node:ResultRun["nodes"][number]) {
  return run.snapshot.workflow.nodes.find(item=>item.id===(node.parent_id??node.id))?.tool_id;
}
class ResultBoundary extends Component<{children:ReactNode},{failed:boolean}> {
  state={failed:false};static getDerivedStateFromError(){return{failed:true};}
  render(){return this.state.failed?<p role="alert">结果展示异常；授权原始文件仍保留，工作台可继续使用。</p>:this.props.children;}
}
function TrajectoryPage({fileId,projectId}:{fileId:string;projectId:string}) {
  const[offset,setOffset]=useState(0);const[data,setData]=useState<Record<string,unknown>>();const[error,setError]=useState("");
  useEffect(()=>{const controller=new AbortController();setData(undefined);setError("");
    requestJson(`/files/${encodeURIComponent(fileId)}/data?project_id=${encodeURIComponent(projectId)}&offset=${offset}&limit=100`,undefined,controller.signal).then(value=>{
      if(controller.signal.aborted)return;
      if(!object(value)||value.file_id!==fileId||typeof value.total!=="number"||!object(value.prediction_contract)||value.prediction_contract.schema_version!=="m4-prediction-v2")throw new Error("未知时间序列协议；未补零或生成曲线。");
      setData(value);
    }).catch(reason=>{if(!controller.signal.aborted)setError(reason instanceof Error?reason.message:"时间序列读取失败。")});return()=>controller.abort();
  },[fileId,projectId,offset]);
  if(error)return<p role="alert">{error}</p>;if(!data||!object(data.prediction_contract))return<p>按需读取已登记原始轨迹…</p>;
  const contract=data.prediction_contract;const time=contract.time;
  if(!Array.isArray(time)||!time.every(v=>typeof v==="number"&&Number.isFinite(v))||!object(contract.concentrations))return<p>轨迹缺项；不生成预测。</p>;
  if(!time.length)return<p>未提供时间序列；稳态不伪装时间曲线。</p>;
  const columns:{label:string;values:number[]}[]=[];
  for(const[compartment,species]of Object.entries(contract.concentrations)) {
    if(!object(species))return<p>区室数据不完整。</p>;
    for(const[name,values]of Object.entries(species)) {
      if(!Array.isArray(values)||values.length!==time.length||!values.every(v=>typeof v==="number"&&Number.isFinite(v)))return<p>时间/浓度长度不匹配；不补零。</p>;
      columns.push({label:`${compartment} / ${name}`,values});
    }
  }
  return <div className="trajectory"><p>模型 {show(contract.model_kind)} · 原式 {show(contract.formula_version)} · 原文件 SHA-256 {show(data.sha256)}</p><p>仅展示当前分页；不改变积分、拟合或原始导出。</p>
    <div className="table-scroll"><table><thead><tr><th>时间 ({show(contract.time_unit)})</th>{columns.map(column=><th key={column.label}>{column.label} ({show(contract.concentration_unit)})</th>)}</tr></thead><tbody>{time.map((t,i)=><tr key={i}><td>{t}</td>{columns.map(column=><td key={column.label}>{column.values[i]}</td>)}</tr>)}</tbody></table></div>
    <button disabled={!offset} onClick={()=>setOffset(Math.max(0,offset-100))}>轨迹上一页</button><button disabled={typeof data.total!=="number"||offset+100>=data.total} onClick={()=>setOffset(offset+100)}>轨迹下一页</button><span>{offset+1}–{offset+time.length} / {show(data.total)}</span></div>;
}
function TrajectoryReference({reference,projectId}:{reference:unknown;projectId?:string}) {
  const[open,setOpen]=useState(false);const path=object(reference)?reference.path:reference;
  if(typeof path!=="string"||!path.startsWith("asset:")||!projectId)return<p>没有可授权的已登记轨迹引用；未生成曲线。</p>;
  return<details onToggle={e=>setOpen(e.currentTarget.open)}><summary>读取时间序列（分页原值）</summary>{open&&<TrajectoryPage fileId={path.slice(6)} projectId={projectId}/>}</details>;
}
function StageResult({output,records,projectId}:{output:Record<string,unknown>;records:Record<string,unknown>[];projectId?:string}) {
  const[selected,setSelected]=useState(0);const record=records[selected]??records[0];const module=String(output.module).toUpperCase();
  if(!record)return<section><h2>{module} · 科学项目结果</h2><p>无候选记录；不视为有效预测。</p></section>;
  const id=String(record.candidate_id??record.experiment_id??selected);
  return<section><h2>{module} · 科学项目结果</h2><label>当前候选<select aria-label="当前候选" value={selected} onChange={e=>setSelected(Number(e.target.value))}>{records.map((row,i)=><option key={i} value={i}>{show(row.candidate_id??row.experiment_id??i)}</option>)}</select></label>
    <table className="science-status" aria-label="四类独立状态"><thead><tr><th>作业状态</th><th>数值状态</th><th>证据 / 审批状态</th><th>实验验证状态</th></tr></thead><tbody><tr><td>执行完成{record.status==="insufficient_data"?"，科学数据不足":""}</td><td>{record.numerically_solved===true?"已求解（不等于证据充分）":record.numerically_solved===false?"未获得数值预测":"未提供"}</td><td>{record.evidence_ready===true?"后端声明证据就绪；参数审批仍按原记录":"未声明证据充分"} · {show(record.status)}</td><td>未提供独立实验验证结论；不能由作业状态推断</td></tr></tbody></table><p>声明范围：{show(record.claim_scope)}</p>
    <MissingEvidence module={module} missing={record.missing_inputs} status={record.status}/>
    <p>原式 {show(record.formula_version)} · 参数身份 {show(record.parameter_ids)} · 来源分级 {show(record.provenance_summary)}；作业完成不升级实验验证状态。</p>
    {["M1","M2"].includes(module)&&<p>序列/静态结构负筛与几何指标，不代表酶活或自组装已经由实验确认。</p>}
    {module==="M1"&&<><M1Matrix records={records}/><LazyJson value={record.part_screens} label="部件原特征、规则与否决原因"/><LazyJson value={record.full_fusion_screen} label="完整融合序列筛查与规则来源"/></>}
    {module==="M2"&&<><M2Metrics record={record}/><LazyJson value={record.construct_definition} label="构建 / 残基映射来源"/></>}
    {module==="M3"&&<><p>OC:DMT 浓相比：{show(record.dense_oc_dmt_ratio)} · 全细胞比：{show(record.whole_cell_oc_dmt_ratio)}</p><table><thead><tr><th>物理量（原字段/单位）</th><th>后端原值</th></tr></thead><tbody>{["free_dense_concentration","bound_dense_concentration","free_dilute_concentration","bound_fraction_of_whole_cell_total","fraction_in_dense","site_occupancy","capacity_status","capacity_excess_um","mass_balance_residual_um"].map(key=><tr key={key}><td>{key==="fraction_in_dense"?"dense_phase_fraction_of_whole_cell_total":key}</td><td>{show(record[key])}</td></tr>)}</tbody></table><p>位点计量基准：{show(object(record.m4_candidate_context)?record.m4_candidate_context.site_count_basis:null)}；占位比例和浓相总体比例不是同一物理量。</p></>}
    {module==="M4"&&<><p>产物 15：{show(record.final_15)} · 支产物 13：{show(record.final_13)} · yield_abs：{show(record.yield_abs)}（缺失不记为 0）</p>
      <TrajectoryReference projectId={projectId} reference={object(output.trajectory_refs)?output.trajectory_refs[id]:record.trajectory_artifact}/>
      <LazyJson label="运输/外排、稳态残差、局部稳定性" value={{transport:record.transport_report,residuals:record.steady_state_residuals,analysis:record.analysis_result}}/>
      <LazyJson label="F2：敏感性与稳健性（原分析结果）" value={{robustness:record.robustness,sensitivity:record.sensitivity}}/><LazyJson label="F3：设计比较契约（未提供则不排名）" value={record.design_comparison??record.analysis_result}/></>}
    {module==="M5"&&<><p>QC：{show(record.qc_flags)} · 拟合候选（未自动批准）：{show(record.fitted_parameter_candidate)} · 拟合警告：{show(record.fit_warnings)}</p><LazyJson value={record} label="条件匹配、测量来源、残差与冻结留出记录"/></>}
    <LazyJson value={record} label="当前候选全部原值、来源与适用边界"/>
  </section>;
}
function NodeResult({run,node,projectId}:{run:ResultRun;node:ResultRun["nodes"][number];projectId?:string}) {
  const tool=nodeTool(run,node);const output=node.output;const records=stageRecords(tool,output);
  if(records&&object(output))return<StageResult output={output} records={records} projectId={projectId}/>;
  const sequence=sequenceOutput(output);
  if(tool==="fusion.sequence_metrics"&&sequence)return<section><h2>序列理化指标 · {String(sequence.id)}</h2><p>长度 {show(sequence.features.length)} · 分子量 {show(sequence.protparam.molecular_weight_da)} Da · 理论 pI {show(sequence.protparam.theoretical_pi)}</p><p>序列 SHA-256 {show(sequence.features.sequence_sha256)}；这是计算指标，不是酶活/组装实验证据。</p><LazyJson value={output}/></section>;
  if(tool==="assembly.inventory"&&object(output)&&numbers(output.subunits)&&typeof output.assembly_id==="string"&&typeof output.total_subunits==="number"&&typeof output.molecular_weight_da==="number"&&Number.isFinite(output.molecular_weight_da))return<section><h2>自组装组成核验 · {output.assembly_id}</h2><p>{Object.entries(output.subunits).map(([id,count])=>`${id} × ${count}`).join(" + ")}</p><p>总亚基数 {output.total_subunits} · 组装分子量 {output.molecular_weight_da} Da</p><p>声明组成核算，不是自组装成功或界面稳定性预测。</p><LazyJson value={output}/></section>;
  const adapted=adaptSteadyResult(tool,output);
  if(!adapted)return<section><h2>{tool??"未知工具"} · {node.id}</h2><p>未知、旧版本或缺字段的结果格式；未生成有效预测。请检查授权原始 artifact。</p><LazyJson value={output}/></section>;
  const{data,title,maps}=adapted;
  return<section><h2>{title}</h2><p>作业状态：{node.status} · 科学状态：{String(data.status)}</p><p>数值求解：{maps?"满足求解器契约":"未获得有效预测"} · 证据状态：{data.evidence_ready===true?"已具备声明的证据":"未经过正式项目证据审核"}</p><p>模型 / 公式：{String(data.model_kind)} / {String(data.formula_version??data.rate_law)}</p>
    {maps&&<><table><thead><tr><th>物种</th><th>全细胞平均 μM</th><th>浓相 μM</th><th>稀相 μM</th><th>外排 μM/h</th><th>残差 μM/h</th></tr></thead><tbody>{Object.keys(maps[0]).map(s=><tr key={s}><td>{s}</td>{maps.slice(0,5).map((map,i)=><td key={i}>{map[s]}</td>)}</tr>)}</tbody></table><h3>反应通量 μM/h</h3><table><tbody>{Object.entries(maps[5]).map(([r,v])=><tr key={r}><td>{r}</td><td>{v}</td></tr>)}</tbody></table></>}
    {Array.isArray(data.warnings)&&<p>{data.warnings.map(String).join("；")}</p>}{object(data.local_stability)&&<p>局部稳定性：{show(data.local_stability.classification??data.local_stability.status)}；不证明全局稳定或唯一性。</p>}<LazyJson value={output}/></section>;
}
export function ScientificResults({run,projectId}:{run:ResultRun;projectId?:string}) {
  return<>{run.nodes.filter(node=>node.status==="succeeded").map(node=><ResultBoundary key={`${run.id}:${node.id}`}><NodeResult run={run} node={node} projectId={projectId}/></ResultBoundary>)}</>;
}
export function ResultComparison({runs}:{runs:ResultRun[]}) {
  if(runs.length!==2)return null;
  const metrics=runs.map(run=>new Map(run.nodes.filter(node=>nodeTool(run,node)==="fusion.sequence_metrics"&&node.status==="succeeded").flatMap(node=>{const output=sequenceOutput(node.output);return output?[[String(output.id),output]as const]:[];})));
  const shared=[...metrics[0].keys()].filter(id=>metrics[1].has(id));
  return<section><h3>输入/结果身份对比（不是正式 F3 排名）</h3><p>revision {show(runs[0].snapshot.project?.revision)} → {show(runs[1].snapshot.project?.revision)}；相同 ID 不等于同一构建/条件。</p>{!shared.length?<p>无共同可识别序列结果；不能生成有效比较或补零。</p>:<table><thead><tr><th>记录</th><th>前次序列 SHA-256</th><th>后次序列 SHA-256</th><th>差异</th><th>分子量 Da</th></tr></thead><tbody>{shared.map(id=>{const a=metrics[0].get(id)!;const b=metrics[1].get(id)!;const ah=String(a.features.sequence_sha256);const bh=String(b.features.sequence_sha256);return<tr key={id}><td>{id}</td><td>{ah}</td><td>{bh}</td><td>{ah===bh?"序列相同；仍需核对条件":"序列改变，非相同构建"}</td><td>{show(a.protparam.molecular_weight_da)} → {show(b.protparam.molecular_weight_da)}</td></tr>;})}</tbody></table>}<p>科学阶段比较必须先通过后端正式可比性门控；本视图不按数值大小升级证据。</p></section>;
}
