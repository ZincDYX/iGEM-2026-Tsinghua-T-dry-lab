import {useEffect,useState} from "react";
import type {RunListView,RunSummaryView} from "../contracts/generated";
import {ResultComparison,type ResultRun} from "../ScientificResults";
import * as client from "./client";

export function ComparisonPanel({history,current}:{history:RunListView[];current?:RunSummaryView}) {
  const[other,setOther]=useState("");const[pair,setPair]=useState<ResultRun[]>([]);const[error,setError]=useState("");
  useEffect(()=>{const controller=new AbortController();setPair([]);setError("");if(!current||!other)return;
    async function load(){const second=await client.summary(other,controller.signal);if(second.project_id!==current!.project_id)throw new Error("比较对象不属于当前项目。");
      const values:ResultRun[]=[];for(const run of[current!,second]){
        const nodes=[];for(const node of run.nodes.filter(value=>value.tool_id==="fusion.sequence_metrics"&&value.parent_id&&value.status==="succeeded").slice(0,100)){nodes.push((await client.node(run.id,node.id,0,controller.signal)).node);}
        values.push({id:run.id,snapshot:{workflow:run.workflow,project:{revision:run.project_revision}},nodes});
      }if(!controller.signal.aborted)setPair(values);
    }void load().catch(reason=>{if(!controller.signal.aborted)setError(reason instanceof Error?reason.message:"比较加载失败")});return()=>controller.abort();
  },[current?.id,other]);
  return<section><h2>冻结版本比较</h2><p>仅在打开本标签后加载已完成序列对象，最多 100 条；未实现正式 F3 自动排名，不复用相同文本 ID 冒充科学身份。</p><label>前次运行<select value={other} onChange={e=>setOther(e.target.value)}><option value="">选择比较运行</option>{history.filter(run=>run.id!==current?.id).map(run=><option key={run.id} value={run.id}>{run.name} · revision {run.project_revision} · {run.status}</option>)}</select></label>
    {error&&<p role="alert">{error}</p>}{pair.length===2&&<ResultComparison runs={pair}/>}</section>;
}
