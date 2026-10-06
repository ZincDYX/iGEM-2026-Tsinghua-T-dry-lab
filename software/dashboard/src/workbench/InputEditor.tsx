import {useEffect,useRef,useState} from "react";
import type {ProjectView,ImportView,ScientificPreviewView} from "../contracts/generated";
import {object,parsePublic} from "../contracts/validation";
import * as client from "./client";
import {downloadResource} from "../api";
import {LazyJson} from "../contracts/LazyJson";
import {PrecheckPanel} from "./PrecheckPanel";

export function InputEditor({project,busy,dirty,onChange,onEditing,action}:{project:ProjectView;busy:boolean;dirty:boolean;onChange:(value:ProjectView)=>void;onEditing:(value:boolean)=>void;action:(job:()=>Promise<unknown>)=>Promise<void>}) {
  const[kind,setKind]=useState("auto");
  const[preview,setPreview]=useState<ImportView>();
  const[bundle,setBundle]=useState<File[]>([]);
  const[configFile,setConfigFile]=useState("");
  const[scientific,setScientific]=useState<ScientificPreviewView>();
  const[editing,setEditing]=useState(false);
  const[text,setText]=useState("");
  const mounted=useRef(true);
  const epoch=useRef(0);
  useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;++epoch.current;};},[]);
  function change(value:ProjectView){++epoch.current;onChange(value);}
  function startEditor(){setText(JSON.stringify(project,null,2));setEditing(true);onEditing(true);}
  function relativeName(file:File){const raw=file.webkitRelativePath||file.name;return file.webkitRelativePath?raw.split("/").slice(1).join("/"):raw;}
  const scope=project.scientific_project;
  return <section aria-label="项目输入与证据"><header className="panel-heading"><h2>输入与证据</h2><span>revision {project.revision}</span></header>
    <fieldset className="input-fields" disabled={busy||editing}>
    <label>项目名称<input aria-label="项目名称" value={project.name} onChange={e=>change({...project,name:e.target.value})}/></label>
    <label>项目备注（不替代科学条件）<textarea value={project.description} onChange={e=>change({...project,description:e.target.value})}/></label>
    <section className="input-section"><h3>文件导入</h3><label>数据类型<select value={kind} onChange={e=>{++epoch.current;setKind(e.target.value);setPreview(undefined);}}><option value="auto">序列 / 数据表 / 通路 JSON</option><option value="pathway">通路 JSON</option><option value="wetlab">WetLabResult 测量 JSON</option></select></label>
      <input aria-label="导入数据文件" type="file" accept=".fasta,.fa,.faa,.gb,.gbk,.json,.csv,.tsv" disabled={busy} onChange={e=>{const file=e.target.files?.[0];if(!file)return;const stamp=epoch.current;void action(async()=>{const value=await client.importFile(file,kind);if(mounted.current&&stamp===epoch.current)setPreview(value);});}}/>
      {preview&&<div><p>预览：{preview.kind} · {preview.file.name} · SHA-256 {preview.file.sha256}</p><LazyJson value={preview.patch}/>
        <button disabled={busy} onClick={()=>{const patch=preview.patch;const draft=parsePublic("ProjectView",{...project,...patch,files:[...project.files,preview.file],datasets:Array.isArray(patch.datasets)?[...project.datasets,...patch.datasets]:project.datasets});change(draft);setPreview(undefined);}}>确认导入到草稿</button><button onClick={()=>setPreview(undefined)}>放弃导入</button></div>}
    </section>
    <section className="input-section"><h3>科学项目与依赖</h3><p>选择 YAML 与依赖文件或整个项目文件夹，保留相对目录；不填写后台绝对路径。工具配置由维护者私有 profile 提供。</p>
      <input aria-label="科学项目文件" type="file" multiple disabled={busy||editing} onChange={e=>{++epoch.current;const files=Array.from(e.target.files??[]);setBundle(files);setConfigFile("");setScientific(undefined);}}/>
      <label>或选择文件夹<input aria-label="科学项目文件夹" type="file" multiple disabled={busy||editing} ref={el=>{if(el)el.setAttribute("webkitdirectory","");}} onChange={e=>{++epoch.current;setBundle(Array.from(e.target.files??[]));setConfigFile("");setScientific(undefined);}}/></label>
      {!!bundle.length&&<><label>入口 YAML<select aria-label="科学项目入口" disabled={busy||editing} value={configFile} onChange={e=>{++epoch.current;setScientific(undefined);setConfigFile(e.target.value);}}><option value="">选择配置</option>{bundle.filter(file=>/\.ya?ml$/i.test(file.name)).map(file=><option key={relativeName(file)} value={relativeName(file)}>{relativeName(file)}</option>)}</select></label>
        <p>{bundle.length} 个文件；上限 256 个 / 20 MB。缺失依赖或运维 tools 字段会被拒绝。</p><button disabled={busy||!configFile} onClick={()=>{const stamp=epoch.current;void action(async()=>{const files=await Promise.all(bundle.map(async file=>({filename:relativeName(file),content:await file.text()})));const value=await client.uploadScientific(configFile,files);if(mounted.current&&stamp===epoch.current)setScientific(value);});}}>检查科学输入</button></>}
      {scientific&&<div><p>已校验 typed 配置，绑定 {scientific.scientific_project.evidence_files.length} 个原文件；导入不审批证据。</p><LazyJson value={scientific.scientific_project}/><button disabled={busy} onClick={()=>{change({...project,scientific_project:scientific.scientific_project});setScientific(undefined);}}>确认科学配置到草稿</button></div>}
      {scope?<><p>执行模式：{scope.config.execution.mode} · 条件入口唯一：下方科学条件。普通项目备注不参与计算。</p>
        <div className="field-grid">{(["host","strain","assay_system"] as const).map(key=><label key={key}>{key}<input value={scope.config.experimental_context[key]??""} onChange={e=>change({...project,scientific_project:{...scope,config:{...scope.config,experimental_context:{...scope.config.experimental_context,[key]:e.target.value||null}}}})}/></label>)}
          {(["temperature_c","pH"] as const).map(key=><label key={key}>{key}<input aria-label={key} type="number" step="any" value={scope.config.experimental_context[key]??""} onChange={e=>change({...project,scientific_project:{...scope,config:{...scope.config,experimental_context:{...scope.config.experimental_context,[key]:e.target.value===""?null:Number(e.target.value)}}}})}/></label>)}</div>
        <p>网络 {scope.config.stages.m4_reaction.network_variant} · 单位 {scope.config.stages.m4_reaction.unit_mode} · 缺少值保持未提供。</p><LazyJson value={scope.config.parameters} label="参数来源与原有审批记录（只读）"/></>:<p>尚未接入完整科学管线；普通序列分析不等同于 M1–M5 正式项目。</p>}
    </section>
    <h3>登记的输入文件</h3><table><thead><tr><th>逻辑文件</th><th>SHA-256</th><th>授权下载</th></tr></thead><tbody>{[...project.files,...(scope?.evidence_files??[])].map((file,i)=><tr key={`${file.id}-${i}`}><td>{file.name}</td><td><code>{file.sha256}</code></td><td><button onClick={()=>void action(()=>downloadResource(`/files/${encodeURIComponent(file.id)}?project_id=${encodeURIComponent(project.id)}`,file.name))}>原文件</button></td></tr>)}</tbody></table>
    <h3>测量与 M5</h3>{dirty&&<p>请先保存当前草稿，再预览后端 M5 绑定，避免覆盖未保存修改。</p>}{project.datasets.filter(row=>row.kind==="wetlab").map((row,i)=><article key={i}><p>{String(row.name)} · 导入 / QC 不等于拟合参数已批准。</p><LazyJson value={row}/>{scope&&typeof row.file_id==="string"&&<button disabled={busy||dirty} onClick={()=>{const fileId=row.file_id;if(typeof fileId!=="string")return;const stamp=epoch.current;void action(async()=>{const value=await client.bindMeasurement(project.id,project.revision,fileId);if(mounted.current&&stamp===epoch.current)change(value.project);});}}>预览 M5 测量绑定（需保存与重审）</button>}</article>)}
    <p>{project.sequences.length} 条蛋白序列 · {project.assemblies.length} 份组成声明</p><LazyJson value={project.sequences} label="序列与角色"/><LazyJson value={project.assemblies} label="自组装声明（不是实验确认）"/>
    </fieldset>
    <PrecheckPanel key={`${project.id}:${project.revision}`} projectId={project.id} revision={project.revision} disabled={busy||dirty||editing}/>
    <button disabled={busy||editing} onClick={startEditor}>编辑完整公开输入 JSON</button>
    {editing&&<section><p>编辑的是科学草稿，不含运维 profile；未应用时禁止启动新计划。后台仍二次核验。</p><textarea aria-label="公开输入 JSON" className="json-editor" value={text} onChange={e=>{setText(e.target.value);++epoch.current;}}/>
      <button disabled={busy} onClick={()=>void action(async()=>{const value=parsePublic("ProjectView",JSON.parse(text));if(value.id!==project.id||value.revision!==project.revision)throw new Error("不能在输入编辑器改项目 ID/revision；请创建迭代。");change(value);setEditing(false);onEditing(false);})}>应用已校验草稿</button><button disabled={busy} onClick={()=>{setEditing(false);onEditing(false);}}>撤销未应用编辑</button></section>}
  </section>;
}
