import {DesktopConnectionPanel} from "../DesktopConnectionPanel";
import type {RuntimeInfoView} from "../contracts/generated";
import {LazyJson} from "../contracts/LazyJson";
import {defaultLayout,type Layout} from "./layout";

export function LocalSettings({layout,onLayout,info,onRefresh}:{layout:Layout;onLayout:(value:Layout)=>void;info?:RuntimeInfoView;onRefresh:()=>void}) {
  return<section><h2>本地布局与能力</h2><p>拖动栏边缘调整尺寸，箭头微调，双击恢复该栏默认尺寸。布局只存本机，不进入科学输入或审批 hash。</p>
    <label>表格密度<select value={layout.density} onChange={e=>onLayout({...layout,density:e.target.value==="comfortable"?"comfortable":"compact"})}><option value="compact">紧凑</option><option value="comfortable">宽松</option></select></label>
    <label>主题<select value={layout.theme} onChange={e=>onLayout({...layout,theme:e.target.value==="dark"?"dark":"light"})}><option value="light">浅色</option><option value="dark">深色</option></select></label><button onClick={()=>onLayout(defaultLayout())}>恢复默认布局</button>
    <DesktopConnectionPanel/><button onClick={onRefresh}>刷新连接与工具能力</button>{info&&<LazyJson value={info} label="公开协议、工具能力与资源状态"/>}
  </section>;
}
