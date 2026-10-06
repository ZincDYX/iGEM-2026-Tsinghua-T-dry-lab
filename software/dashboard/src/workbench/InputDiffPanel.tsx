import {useEffect,useState} from "react";
import type {InputDiffView,ProjectView} from "../contracts/generated";
import {diff} from "./client";

export function InputDiffPanel({project,runId,dirty}:{project:ProjectView;runId?:string;dirty:boolean}) {
  const[value,setValue]=useState<InputDiffView>();
  const[error,setError]=useState("");
  const baseline=project.parent_run_id??runId;
  useEffect(()=>{
    setValue(undefined);setError("");if(!baseline)return;
    const controller=new AbortController();
    diff(project.id,baseline,controller.signal).then(result=>{if(!controller.signal.aborted)setValue(result);})
      .catch(reason=>{if(!controller.signal.aborted)setError(reason instanceof Error?reason.message:"差异读取失败");});
    return()=>controller.abort();
  },[project.id,project.revision,baseline]);
  if(!baseline)return null;
  return <section aria-label="冻结输入差异"><h3>保存输入与冻结运行的差异</h3>
    {dirty&&<p>有未保存编辑；以下仅比较最近保存版本，不含未保存草稿。</p>}
    {error?<p role="alert">{error}</p>:value?<>
      <p>基线 {value.baseline_run_id} · 保存版本 r{value.project_revision} · {value.total_changed_fields} 个字段变化</p>
      <ul>{value.changed_fields.map(field=><li key={field}><code>{field}</code></li>)}</ul>
      <p>受影响节点：{value.affected_nodes.join(" → ")||"无已绑定科学输入变化"}</p>
      <p className="subtle">{value.explanation} 未复用旧科学结果。</p>
    </>:<p>核对保存输入…</p>}
  </section>;
}
