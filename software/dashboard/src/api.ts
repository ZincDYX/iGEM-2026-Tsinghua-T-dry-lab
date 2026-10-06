export let baseUrl=import.meta.env.VITE_DASHBOARD_API_URL??"http://127.0.0.1:8780";
let sessionToken="";
export let backendMode:"local"|"ssh"="local";
declare global {
  interface Window {
    __TAURI__?:{core:{invoke<T>(command:string,args?:Record<string,unknown>):Promise<T>}};
  }
}
const connection=window.__TAURI__
  ?window.__TAURI__.core.invoke<{url:string;token:string;mode:"local"|"ssh"}>("backend_info").then(info=>{
    baseUrl=info.url;sessionToken=info.token;backendMode=info.mode;
  }).catch(()=>{throw new Error("桌面后台连接失败；请查看私有运维诊断。");})
  :Promise.resolve();
export interface DesktopSettings{mode:"local"|"ssh";ssh_host:string;remote_port:number}
export const isDesktop=()=>Boolean(window.__TAURI__);
export const getDesktopSettings=()=>window.__TAURI__!.core.invoke<DesktopSettings>("desktop_settings");
export const saveDesktopSettings=(settings:DesktopSettings)=>window.__TAURI__!.core.invoke<void>("save_desktop_settings",{settings});
export class PublicApiError extends Error {
  constructor(public readonly detail:{code:string;message:string;diagnostic_id:string;field_paths:string[];logical_files:string[];actions:string[]}) {
    super([detail.message,...detail.field_paths.map(value=>`字段：${value}`),...detail.logical_files.map(value=>`文件：${value}`),...detail.actions,`诊断 ID：${detail.diagnostic_id}`].join("\n"));
  }
}
export async function requestJson(path:string,body?:unknown,signal?:AbortSignal):Promise<unknown>{
  await connection;
  const response=await fetch(`${baseUrl}/api/platform${path}`,{
    method:body===undefined?"GET":"POST",headers:{"Content-Type":"application/json",...(sessionToken?{"X-FusionLab-Token":sessionToken}:{})},
    body:body===undefined?undefined:JSON.stringify(body),signal,cache:"no-store",
  });
  if(!response.ok){
    const error=await response.json().catch(()=>null), detail=error?.detail;
    if(detail&&typeof detail.code==="string"&&typeof detail.message==="string"&&typeof detail.diagnostic_id==="string"&&[detail.field_paths,detail.logical_files,detail.actions].every(value=>Array.isArray(value)&&value.every(item=>typeof item==="string")))throw new PublicApiError(detail);
    throw new Error(`请求失败 (${response.status})；请查看安全诊断。`);
  }
  return response.json();
}
export const downloadArtifact=(id:string,projectId:string)=>downloadResource(`/artifacts/${encodeURIComponent(id)}/science-export?project_id=${encodeURIComponent(projectId)}`,"scientific-public-export.json");
export async function downloadResource(path:string,filename:string){
  await connection;
  const response=await fetch(`${baseUrl}/api/platform${path}`,{headers:sessionToken?{"X-FusionLab-Token":sessionToken}:{}});
  if(!response.ok)throw new Error(`下载被拒绝 (${response.status})；请核对授权或安全诊断。`);
  const blob=await response.blob();const url=URL.createObjectURL(blob);const link=document.createElement("a");
  link.href=url;link.download=filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
