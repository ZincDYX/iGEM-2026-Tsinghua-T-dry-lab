import {useState} from "react";
import {DesktopConnectionPanel} from "../DesktopConnectionPanel";
import type {RuntimeInfoView} from "../contracts/generated";
import * as client from "./client";
import {LazyJson} from "../contracts/LazyJson";
import type {PluginInspectionView} from "../contracts/generated";

export interface Layout {left:number;right:number;bottom:number;density:"compact"|"comfortable";theme:"light"|"dark"}
export const defaultLayout=():Layout=>({left:225,right:310,bottom:165,density:"compact",theme:"light"});
export function loadLayout():Layout {
  try{const value:unknown=JSON.parse(localStorage.getItem("fusionlab.layout")??"null");if(value&&typeof value==="object"&&"left"in value&&"right"in value&&"bottom"in value&&typeof value.left==="number"&&typeof value.right==="number"&&typeof value.bottom==="number"&&value.left>=180&&value.left<=300&&value.right>=260&&value.right<=400&&value.bottom>=100&&value.bottom<=300)return{left:value.left,right:value.right,bottom:value.bottom,density:"density"in value&&value.density==="comfortable"?"comfortable":"compact",theme:"theme"in value&&value.theme==="dark"?"dark":"light"};}catch{/* Invalid local layout is not scientific state. */}return defaultLayout();
}
export function LocalSettings({layout,onLayout,info,action}:{layout:Layout;onLayout:(value:Layout)=>void;info?:RuntimeInfoView;action:(job:()=>Promise<unknown>)=>Promise<void>}) {
  const[url,setUrl]=useState("");const[commit,setCommit]=useState("");const[source,setSource]=useState("");const[inspection,setInspection]=useState<PluginInspectionView>();const[trusted,setTrusted]=useState(false);
  return<section><h2>本地布局与能力</h2><p>布局只存本机，不进入科学输入或审批 hash。私有运行 profile 由维护者配置，不在这里编辑 endpoint/凭据。</p>
    {(["left","right","bottom"]as const).map(key=><label key={key}>{key==="left"?"项目栏宽度":key==="right"?"检查器宽度":"底部面板高度"}<input type="range" min={key==="left"?180:key==="right"?260:100} max={key==="left"?300:key==="right"?400:300} value={layout[key]} onChange={e=>onLayout({...layout,[key]:Number(e.target.value)})}/></label>)}
    <label>表格密度<select value={layout.density} onChange={e=>onLayout({...layout,density:e.target.value==="comfortable"?"comfortable":"compact"})}><option value="compact">紧凑</option><option value="comfortable">宽松</option></select></label>
    <label>主题<select value={layout.theme} onChange={e=>onLayout({...layout,theme:e.target.value==="dark"?"dark":"light"})}><option value="light">浅色</option><option value="dark">深色</option></select></label><button onClick={()=>onLayout(defaultLayout())}>恢复默认布局</button>
    <DesktopConnectionPanel/>{info&&<LazyJson value={info} label="公开协议、工具能力与资源状态"/>}
    <h3>受信任插件（不是安全沙箱）</h3><label>公开 GitHub 仓库<input value={url} onChange={e=>{setUrl(e.target.value);setInspection(undefined);}}/></label><label>固定 commit<input value={commit} onChange={e=>{setCommit(e.target.value);setInspection(undefined);}}/></label>
    <button disabled={!url||!commit} onClick={()=>void action(async()=>{const value=await client.fetchPlugin(url,commit);if(!value.source_path)throw new Error("缺少已登记插件源码身份。");setSource(value.source_path);setInspection(value);setTrusted(false);})}>抓取固定源码并检查</button>
    {inspection&&<><LazyJson value={inspection} label="插件许可、能力声明与源码 hash"/><label><input type="checkbox" checked={trusted} onChange={e=>setTrusted(e.target.checked)}/>我信任该源码；能力/秘密仍须维护者逐项授权</label><button disabled={!trusted} onClick={()=>void action(()=>client.installPlugin(source,inspection.hash))}>安装已核验插件</button></>}
  </section>;
}
