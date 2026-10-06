import {useState} from "react";
import type {Workflow} from "../contracts/generated";
import * as client from "./client";

export function WorkflowImporter({busy,enabled,submit,onEdit}:{busy:boolean;enabled:boolean;submit:(create:()=>Promise<Workflow>)=>Promise<void>;onEdit:()=>void}) {
  const[text,setText]=useState("");
  const[error,setError]=useState("");
  return <section><h3>导入自定义 DAG</h3>
    <p>JSON 经过后端结构、工具和正式来源校验，生成待审批提案；不另建执行器，也不直接执行。</p>
    <label>工作流 JSON<textarea aria-label="工作流 JSON" value={text} disabled={busy} onChange={e=>{setText(e.target.value);onEdit();}} rows={5}/></label>
    <label>读取工作流文件<input type="file" accept=".json,application/json" disabled={busy} onChange={e=>{const file=e.target.files?.[0];setError("");onEdit();if(file)void file.text().then(setText).catch(()=>setError("工作流文件读取失败"));}}/></label>
    {error&&<p role="alert">{error}</p>}
    <button disabled={busy||!enabled||!text.trim()} onClick={()=>void submit(()=>client.validate(JSON.parse(text)))}>校验并生成自定义提案</button>
  </section>;
}
