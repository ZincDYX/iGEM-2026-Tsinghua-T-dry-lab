import { useEffect, useRef, useState } from "react";
import * as api from "./api";
import type { Json, Project, ScientificProject } from "./types";
import { object } from "./ScientificResults";

function fact(value: unknown) { return value === null || value === undefined || value === "" ? "未提供" : String(value); }
export function ScientificProjectPanel({project, busy, action, onChange}: {
  project: Project; busy: boolean; action: (job: () => Promise<unknown>) => Promise<void>;
  onChange: (project: Project) => void;
}) {
  const [path, setPath] = useState("");
  const [preview, setPreview] = useState<ScientificProject>();
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  const scientific = project.scientific_project;
  const context = scientific?.config.experimental_context;
  const stages = scientific?.config.stages;
  const m4 = object(stages) && object(stages.m4_reaction) ? stages.m4_reaction : {};
  const execution = scientific?.config.execution;
  const inputs = scientific?.config.inputs;
  return <section className="card"><h2>科学项目输入与证据</h2>
    <p>绑定已有 ProjectConfig 和服务器上的真实输入文件。缺项保留；载入不代表证据已批准或模型已验证。</p>
    <label>服务器配置文件路径<input aria-label="科学配置路径" placeholder="air-lab 上已有项目 YAML 的绝对路径" value={path} onChange={(e) => setPath(e.target.value)} /></label>
    <button disabled={busy || !path} onClick={() => action(async () => {
      const result = await api.previewScientificProject(path);
      if (mounted.current) setPreview(result.scientific_project);
    })}>检查科学配置</button>
    {preview && <div className="import-preview"><p>已通过 typed 配置校验；{preview.evidence_files.length} 个输入文件绑定 SHA-256。</p>
      <details><summary>审阅配置、参数与来源</summary><pre>{JSON.stringify(preview, null, 2)}</pre></details>
      <button disabled={busy} onClick={() => { onChange({...project, scientific_project:preview}); setPreview(undefined); }}>确认科学配置（待保存）</button></div>}
    {scientific ? <><p>执行模式：{fact(object(execution) ? execution.mode : null)} · 网络：{fact(m4.network_variant)} · 单位模式：{fact(m4.unit_mode)}</p>
      <dl className="science-facts">{["host","strain","temperature_c","pH","assay_system"].map((key) => <div key={key}><dt>{key}</dt><dd>{fact(object(context) ? context[key] : null)}</dd></div>)}</dl>
      <p>协议：{fact(m4.assay_mode)} · 表达：{fact(m4.expression_mode)} · 投喂：{fact(m4.feed_mode)} / {fact(m4.feed_compound_id)} · 观测区室：{fact(m4.measurement_compartment)}</p>
      <h3>酶序列身份（缺少 hash 不等于已核验）</h3><table><thead><tr><th>酶 / 蛋白 ID</th><th>sequence SHA-256</th></tr></thead><tbody>
        {object(inputs) && Array.isArray(inputs.enzymes) && inputs.enzymes.map((enzyme,i) => object(enzyme) ? <tr key={i}><td>{fact(enzyme.id)} / {fact(enzyme.protein_id)}</td><td>{fact(enzyme.sequence_sha256)}</td></tr> : null)}</tbody></table>
      <h3>参数审批记录（不自动审批）</h3><table><thead><tr><th>参数</th><th>来源</th><th>审批</th><th>条件/构建</th></tr></thead><tbody>
        {Array.isArray(scientific.config.parameters) && scientific.config.parameters.map((row, i) => object(row) ? <tr key={i}><td>{fact(row.name)} · {fact(row.unit)}</td><td>{fact(row.source_reference ?? row.doi)}</td><td>{fact(row.review_status)} / {fact(row.approved_by)}</td><td>{fact(row.construct_id)} / {fact(row.condition_id)}</td></tr> : null)}</tbody></table>
      <details><summary>输入文件与 SHA-256 / 原始 typed 配置</summary><pre>{JSON.stringify(scientific,null,2)}</pre></details>
      <p className="muted">{scientific.dependency_scope}。科学字段来自该配置，不使用上方普通背景记录替代；修改需重载并重新审阅运行方案。</p>
    </> : <p>尚未接入科学项目。普通序列/组成分析与裸通路计算器不是完整 M1–M5 管线。</p>}
    {project.datasets.filter((row) => row.kind === "wetlab").map((row) => <div key={String(row.id)}><h3>测量数据：{String(row.name)}</h3>
      <details><summary>WetLabResult 条件、来源与 QC</summary><pre>{JSON.stringify(row,null,2)}</pre></details>
      {scientific && <button disabled={busy} onClick={() => {
        const file = project.files.find((file) => file.id === row.id);
        if (!file || !object(stages)) return;
        const currentM5 = object(stages.m5_feedback) ? stages.m5_feedback : {};
        const config = {...scientific.config, stages:{...stages,m5_feedback:{...currentM5,wetlab_results_file:file.path}}} as Record<string, Json>;
        onChange({...project,scientific_project:{...scientific,config,evidence_files:[...scientific.evidence_files.filter((item) => item.path !== file.path),{path:file.path,sha256:file.sha256}]}});
      }}>将这份测量用于 M5（待保存和重新审阅）</button>}</div>)}
  </section>;
}
