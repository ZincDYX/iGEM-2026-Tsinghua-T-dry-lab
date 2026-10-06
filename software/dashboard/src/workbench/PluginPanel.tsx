import {useState} from "react";
import type {PluginInspectionView} from "../contracts/generated";
import {LazyJson} from "../contracts/LazyJson";
import * as client from "./client";

export function PluginPanel({busy,action}:{busy:boolean;action:(job:()=>Promise<unknown>)=>Promise<void>}){
  const[url,setUrl]=useState("");const[commit,setCommit]=useState("");const[inspection,setInspection]=useState<PluginInspectionView>();const[trusted,setTrusted]=useState(false);
  return <section><h2>受信任插件管理</h2><p>此操作使用当前工作区授权；venv 仅隔离依赖，不是文件或网络安全沙箱。固定源码 hash 不等于源码无害。</p>
    <label>公开 GitHub 仓库<input disabled={busy} value={url} onChange={e=>{setUrl(e.target.value);setInspection(undefined);setTrusted(false);}}/></label>
    <label>固定 commit<input disabled={busy} value={commit} onChange={e=>{setCommit(e.target.value);setInspection(undefined);setTrusted(false);}}/></label>
    <button disabled={busy||!url||!commit} onClick={()=>void action(async()=>{const value=await client.fetchPlugin(url,commit);if(!value.source_path)throw new Error("缺少已登记源码身份。");setInspection(value);setTrusted(false);})}>抓取固定源码并检查</button>
    {inspection&&<><LazyJson value={inspection} label="许可、能力声明与源码 hash"/><label><input type="checkbox" disabled={busy} checked={trusted} onChange={e=>setTrusted(e.target.checked)}/>我信任该源码；能力/秘密仍须维护者逐项授权</label><button disabled={busy||!trusted||!inspection.source_path} onClick={()=>void action(()=>client.installPlugin(inspection.source_path!,inspection.hash))}>安装已核验插件</button></>}
  </section>;
}
