import type {NodePage,RunSummaryView} from "../contracts/generated";
import {ScientificResults} from "../ScientificResults";
import {downloadArtifact} from "../api";
import {show} from "../contracts/resultAdapters";

export function SelectedResult({run,selected,data,error,offset,onOffset,action}:{run:RunSummaryView;selected:string;data?:NodePage;error?:string;offset:number;onOffset:(value:number)=>void;action:(job:()=>Promise<unknown>)=>Promise<void>}) {
  if(error)return<p role="alert">{error}</p>;if(!selected)return<p>在计划图或结果对象列表选择阶段。</p>;if(!data)return<p>读取选中阶段…</p>;
  return<section><p>运行 {run.id} · 原输入 revision {run.project_revision} · artifact SHA-256 {show(data.artifact?.hash)}</p>
    {data.node.error&&<p role="alert">{show(data.node.error.code)} · {show(data.node.error.message)} · 诊断 {show(data.node.error.diagnostic_id)}</p>}
    {data.node.status!=="succeeded"?<p>该节点尚未完整成功；不发布为有效预测。</p>:<ScientificResults projectId={run.project_id} run={{id:run.id,snapshot:{workflow:run.workflow,project:{revision:run.project_revision}},nodes:[data.node]}}/>}
    {data.total_records>0&&<p><button disabled={!offset} onClick={()=>onOffset(Math.max(0,offset-20))}>候选上一页</button><button disabled={offset+20>=data.total_records} onClick={()=>onOffset(offset+20)}>候选下一页</button> {offset+1}–{Math.min(offset+20,data.total_records)} / {data.total_records}</p>}
    {data.artifact&&<button onClick={()=>void action(()=>downloadArtifact(data.artifact!.id,run.project_id))}>授权科学导出（非原 artifact 字节）</button>}
  </section>;
}
