import { Component, type ReactNode } from "react";
import type { NodeRecord, Run } from "./types";

export function object(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}
function numbers(value: unknown): value is Record<string, number> {
  return object(value) && Object.keys(value).length > 0 && Object.values(value).every(
    (v) => typeof v === "number" && Number.isFinite(v));
}
export function nodeTool(run: Run, node: NodeRecord) {
  return run.snapshot.workflow.nodes.find((item) => item.id === (node.parent_id ?? node.id))?.tool_id;
}
function raw(value: unknown) {
  return <details><summary>原始结果 / artifact 内容</summary><pre>{JSON.stringify(value, null, 2)}</pre></details>;
}
class ResultBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() { return this.state.failed ? <p role="alert">结果展示异常；原始文件仍可在复现信息下载，工作台可继续使用。</p> : this.props.children; }
}

export function adaptSteadyResult(tool: string | undefined, output: unknown) {
  const m4 = tool === "igem.m4.solve_steady_state";
  const data = m4 && object(output) && output.ok === true ? output.result : output;
  if (!object(data)) return null;
  if (m4 ? data.schema_version !== "m4-steady-state-v1" || data.model_kind !== "markdown_steady_state" ||
      !["m4-step0-step8-2026-09-27", "m4-step0-step8-phase-activity-v2-2026-10-04"].includes(String(data.formula_version)) :
      tool !== "pathway.steady_state" || data.schema_version !== "pathway-steady-state-v1" ||
      data.model_kind !== "generic_two_phase_steady_state" || data.rate_law !== "two_phase_competitive_mm_v1") return null;
  if (!["valid", "blocked", "solver_failed", "insufficient_data", "capacity_conflict"].includes(String(data.status))) return null;
  if (data.status !== "valid") return { data, title: m4 ? "M4 原式稳态" : "反应通路稳态", maps: null };
  const keys = [m4 ? "concentrations_cell_average_um" : "concentrations_average_um",
    "concentrations_dense_um", "concentrations_dilute_um", "secretion_flux_um_per_h",
    m4 ? "steady_state_residual_um_per_h" : "residual_um_per_h", "reaction_flux_um_per_h"];
  const maps = keys.map((key) => data[key]);
  if (!maps.every(numbers)) return null;
  const species = Object.keys(maps[0]);
  if (!maps.slice(1, 5).every((map) => Object.keys(map).length === species.length && species.every((s) => s in map))) return null;
  return { data, title: m4 ? "M4 原式稳态" : "反应通路稳态", maps: maps as Record<string, number>[] };
}

function NodeResult({ run, node }: { run: Run; node: NodeRecord }) {
  const tool = nodeTool(run, node);
  const adapted = adaptSteadyResult(tool, node.output);
  const output = node.output;
  if (["project.m1", "project.m2", "project.m3", "project.m4", "project.m5"].includes(tool ?? "") &&
      object(output) && output.schema_version === "scientific-stage-v1" && tool === `project.${output.module}` &&
      Array.isArray(output.records) && output.records.every((row) => object(row) && typeof row.status === "string" &&
        typeof row.evidence_ready === "boolean" && typeof row.numerically_solved === "boolean" && Array.isArray(row.missing_inputs))) {
    return <StageResult output={output} />;
  }
  if (tool === "workflow.gather" || tool === "fusion.sequence_metrics") return null;
  if (tool === "assembly.inventory" && object(output) && numbers(output.subunits) &&
      typeof output.assembly_id === "string" && typeof output.total_subunits === "number" &&
      typeof output.molecular_weight_da === "number" && Number.isFinite(output.molecular_weight_da)) {
    return <section className="card"><h2>自组装组成核验 · {output.assembly_id}</h2>
      <p>{Object.entries(output.subunits).map(([id, count]) => `${id} × ${count}`).join(" + ")}</p>
      <p>总亚基数 {output.total_subunits} · 组装分子量 {output.molecular_weight_da.toFixed(1)} Da</p>
      <p className="muted">这是声明组成核算，不是自组装成功或界面稳定性的预测。</p></section>;
  }
  if (!adapted) return <section className="card"><h2>{tool ?? "未知工具"} · {node.id}</h2>
    <p>未知、旧版本或缺字段的结果格式；未生成有效预测。请检查原始 artifact。</p>{raw(output)}</section>;
  const { data, title, maps } = adapted;
  return <section className="card"><h2>{title}</h2>
    <p>作业状态：{node.status} · 科学状态：{String(data.status)}</p>
    <p>数值求解：{maps ? "满足求解器契约" : "未获得有效预测"} · 证据状态：{data.evidence_ready === true ? "已具备声明的证据" : "未经过正式项目证据审核"}</p>
    <p className="muted">模型 / 公式：{String(data.model_kind)} / {String(data.formula_version ?? data.rate_law)}。数值收敛不代表湿实验验证。</p>
    {maps && <><table><thead><tr><th>物种</th><th>平均浓度 μM</th><th>浓相 μM</th><th>稀相 μM</th><th>外排 μM/h</th><th>残差 μM/h</th></tr></thead>
      <tbody>{Object.keys(maps[0]).map((s) => <tr key={s}><td>{s}</td>{maps.slice(0, 5).map((map, i) => <td key={i}>{map[s].toPrecision(5)}</td>)}</tr>)}</tbody></table>
      <h3>各反应总体通量 μM/h</h3><table><tbody>{Object.entries(maps[5]).sort(([a],[b]) => a.localeCompare(b,undefined,{numeric:true})).map(([r, v]) => <tr key={r}><td>{r}</td><td>{v.toPrecision(5)}</td></tr>)}</tbody></table></>}
    {Array.isArray(data.warnings) && <p>{data.warnings.map(String).join("；")}</p>}
    {object(data.local_stability) && <p>局部稳定性：{String(data.local_stability.classification ?? data.local_stability.status)}；局部结果不证明全局稳定或唯一性。</p>}
    {raw(output)}</section>;
}

function show(value: unknown) { return value === null || value === undefined ? "未提供 / 不适用" : typeof value === "object" ? JSON.stringify(value) : String(value); }
function Trajectory({value}: {value:unknown}) {
  if (!object(value) || !object(value.prediction_contract)) return <p>无可识别轨迹；不生成曲线或补零。</p>;
  const contract = value.prediction_contract;
  if (!Array.isArray(contract.time) || !contract.time.every((v) => typeof v === "number" && Number.isFinite(v)) || !object(contract.concentrations)) return <p>轨迹格式不完整；请看原始 artifact。</p>;
  const time = contract.time;
  return <><p>模型：{show(contract.model_kind)} · 公式：{show(contract.formula_version)} · 时间：{show(contract.time_unit)} · 浓度：{show(contract.concentration_unit)}</p>
    {Object.entries(contract.concentrations).map(([compartment,species]) => {
      if (!object(species)) return null;
      const names = ["10","11","13","14","15"];
      if (!names.every((name) => Array.isArray(species[name]) && (species[name] as unknown[]).length === (time.length || 1) &&
          (species[name] as unknown[]).every((v) => typeof v === "number" && Number.isFinite(v)))) return <p key={compartment}>区室 {compartment} 的序列缺失；不补零。</p>;
      return <details key={compartment}><summary>{compartment} · 10/11/13/14/15 时间序列</summary><table><thead><tr><th>时间 {show(contract.time_unit)}</th>{names.map((name) => <th key={name}>{name} ({show(contract.concentration_unit)})</th>)}</tr></thead><tbody>
        {(time.length ? time : [null]).map((t,i) => <tr key={i}><td>{t === null ? "稳态（无时间曲线）" : String(t)}</td>{names.map((name) => <td key={name}>{show((species[name] as unknown[])[i])}</td>)}</tr>)}</tbody></table></details>;
    })}</>;
}
function StageResult({output}: {output:Record<string, unknown>}) {
  const module = String(output.module).toUpperCase();
  const records = output.records as Record<string, unknown>[];
  return <section className="card"><h2>{module} · 科学项目结果</h2><p>执行模式：{show(output.execution_mode)}；模块作业完成不等于科学有效或实验验证。</p>
    {["M1","M2"].includes(module) && <p className="muted">序列/静态结构负筛与几何指标，不代表酶活或自组装已经由实验确认。实际工具版本、原始文件与 hash 见模块来源记录。</p>}
    {!records.length && <p>没有候选记录；检查上游、配置和缺失项，不视为有效预测。</p>}
    {records.map((record,i) => <article key={i}><h3>{show(record.candidate_id ?? record.experiment_id)}</h3>
      <p>科学状态：{show(record.status)} · numerically_solved：{show(record.numerically_solved)} · evidence_ready：{show(record.evidence_ready)} · claim_scope：{show(record.claim_scope)}</p>
      <p>缺失项：{(record.missing_inputs as unknown[]).length ? (record.missing_inputs as unknown[]).map(show).join("；") : "无自报缺项（不等于实验验证）"}</p>
      {module === "M3" && <><p>OC:DMT 浓相比：{show(record.dense_oc_dmt_ratio)} · 全细胞比：{show(record.whole_cell_oc_dmt_ratio)}</p>
        <dl>{["free_dense_concentration","bound_dense_concentration","free_dilute_concentration","bound_fraction_of_whole_cell_total","fraction_in_dense","site_occupancy","capacity_status","capacity_excess_um","mass_balance_residual_um"].map((key) => <div key={key}><dt>{key === "fraction_in_dense" ? "dense_phase_fraction_of_whole_cell_total" : key}</dt><dd>{show(record[key])}</dd></div>)}</dl>
        <p>位点计量基准：{show(object(record.m4_candidate_context) ? record.m4_candidate_context.site_count_basis : null)}；占位比例和浓相比例不是同一量。</p></>}
      {module === "M4" && <><p>产物 15：{show(record.final_15)} · 支产物 13：{show(record.final_13)} · yield_abs：{show(record.yield_abs)}（缺失值不记为 0）</p>
        {object(output.trajectories) && <Trajectory value={output.trajectories[String(record.candidate_id)]} />}
        <details><summary>运输、稳态残差、局部稳定性及 F2/F3 分析</summary><pre>{JSON.stringify({transport:record.transport_report,residuals:record.steady_state_residuals,analysis:record.analysis_result,robustness:record.robustness,sensitivity:record.sensitivity},null,2)}</pre></details></>}
      {module === "M5" && <p>QC：{show(record.qc_flags)} · 拟合候选（未自动批准）：{show(record.fitted_parameter_candidate)} · 拟合警告：{show(record.fit_warnings)}</p>}
      <details><summary>模块原始记录、来源和适用边界</summary><pre>{JSON.stringify(record,null,2)}</pre></details>
    </article>)}{raw(output)}</section>;
}

export function ScientificResults({ run }: { run: Run }) {
  return <>{run.nodes.filter((node) => node.status === "succeeded").map((node) =>
    <ResultBoundary key={`${run.id}:${node.id}`}><NodeResult run={run} node={node} /></ResultBoundary>)}</>;
}

export function sequenceOutput(value: unknown) {
  if (!object(value) || typeof value.id !== "string" || !object(value.features) ||
      typeof value.features.sequence_sha256 !== "string" || typeof value.features.length !== "number" ||
      !object(value.protparam)) return null;
  const properties = value.protparam;
  return ["molecular_weight_da", "theoretical_pi"].every((key) =>
    typeof properties[key] === "number" && Number.isFinite(properties[key])) ? value : null;
}
export function ResultComparison({ runs }: { runs: Run[] }) {
  if (runs.length !== 2) return null;
  const metrics = runs.map((run) => new Map(run.nodes.filter((node) => nodeTool(run, node) === "fusion.sequence_metrics" && node.status === "succeeded")
    .flatMap((node) => { const output = sequenceOutput(node.output); return output ? [[String(output.id), output] as const] : []; })));
  const shared = [...metrics[0].keys()].filter((id) => metrics[1].has(id));
  if (!shared.length) return null;
  return <><h3>同名记录的版本对比（ID 不等于构建身份）</h3>
    <p>revision {runs[0].snapshot.project.revision} → {runs[1].snapshot.project.revision}；正式设计排名另需 F3 比较契约。</p>
    <table><thead><tr><th>记录 ID</th><th>前次序列 SHA-256</th><th>后次序列 SHA-256</th><th>实际差异</th><th>分子量 Da</th></tr></thead>
    <tbody>{shared.map((id) => { const a = metrics[0].get(id)!; const b = metrics[1].get(id)!;
      const ah = String((a.features as Record<string, unknown>).sequence_sha256); const bh = String((b.features as Record<string, unknown>).sequence_sha256);
      return <tr key={id}><td>{id}</td><td title={ah}>{ah.slice(0, 16)}</td><td title={bh}>{bh.slice(0, 16)}</td><td>{ah === bh ? "序列相同；条件仍需核对" : "序列已改变，非相同构建"}</td>
        <td>{String((a.protparam as Record<string, unknown>).molecular_weight_da)} → {String((b.protparam as Record<string, unknown>).molecular_weight_da)}</td></tr>; })}</tbody></table></>;
}
