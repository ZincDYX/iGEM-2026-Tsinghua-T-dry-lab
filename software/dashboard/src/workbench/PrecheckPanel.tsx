import {useEffect,useState} from "react";
import type {ScientificPrecheckView} from "../contracts/generated";
import * as client from "./client";

export function PrecheckPanel({projectId,revision,disabled}:{projectId:string;revision:number;disabled:boolean}) {
  const [request,setRequest]=useState(0);
  const [result,setResult]=useState<ScientificPrecheckView>();
  const [error,setError]=useState("");
  const [pending,setPending]=useState(false);
  useEffect(()=>{
    setResult(undefined);setError("");
    if(!request)return;
    const controller=new AbortController();setPending(true);
    client.precheck(projectId,controller.signal).then(value=>{
      if(controller.signal.aborted)return;
      if(value.project_id!==projectId||value.project_revision!==revision)throw new Error("预检对应输入已改变；请重新保存后检查。");
      setResult(value);
    }).catch(reason=>{if(!controller.signal.aborted)setError(reason instanceof Error?reason.message:"预检未完成。");})
      .finally(()=>{if(!controller.signal.aborted)setPending(false);});
    return()=>controller.abort();
  },[projectId,revision,request]);
  const current=!disabled&&result?.project_id===projectId&&result.project_revision===revision?result:undefined;
  return <section aria-label="已保存科学输入预检"><h3>已知缺项预检</h3>
    <p>仅检查已保存输入与现有参数合同，不运行求解器，不批准证据；最终阶段仍会二次门控。</p>
    <button disabled={disabled||pending} onClick={()=>setRequest(value=>value+1)}>检查已保存输入缺项</button>
    {disabled&&<p>请先应用编辑并保存草稿。</p>}{pending&&<p>正在读取合同缺项…</p>}{error&&<p role="alert">{error}</p>}
    {current&&<><p>revision {current.project_revision} · 输入 SHA-256 {current.input_sha256}</p>
      <table><thead><tr><th>阶段 / 缺项</th><th>字段</th><th>构建 / 条件</th><th>需要的来源 / 原因</th></tr></thead><tbody>
        {current.missing.map((item,index)=><tr key={index}><td>{item.stage} / {item.code}</td><td>{item.field_path}</td><td>{item.construct_id??"未声明"} / {item.condition_id??"未声明"}</td><td>{item.source_kind} / {item.reason_codes.join(", ")}</td></tr>)}
      </tbody></table>{!current.missing.length&&<p>本次未发现已知合同缺项；不代表证据充分或允许预测。</p>}
      {current.limitations.map(text=><p key={text}>{text}</p>)}</>}
  </section>;
}
