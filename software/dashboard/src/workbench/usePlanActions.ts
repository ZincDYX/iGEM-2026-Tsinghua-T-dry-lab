import {useCallback,useEffect,useRef,useState} from "react";
import type {ActionView} from "../contracts/generated";
import * as client from "./client";

export function usePlanActions(projectId:string|undefined,version:string,fail:(reason:unknown)=>void){
  const[state,setState]=useState<{project?:string;items:ActionView[];more:boolean;trimmed:boolean}>({items:[],more:false,trimmed:false});
  const cursor=useRef({project:projectId,seq:0});const[refresh,setRefresh]=useState(0);
  useEffect(()=>{
    const controller=new AbortController();if(!projectId)return;
    if(cursor.current.project!==projectId){cursor.current={project:projectId,seq:0};setState({project:projectId,items:[],more:false,trimmed:false});}
    async function drain(){
      let after=cursor.current.seq;const items:ActionView[]=[];let more=false;
      for(let page=0;page<5;page++){
        const values=await client.actions(projectId!,after,controller.signal);if(controller.signal.aborted)return;
        if(values.some(item=>item.seq<=after))throw new Error("行动分页游标不兼容。");
        items.push(...values);if(values.length)after=values.at(-1)!.seq;
        more=values.length===100;if(!more)break;
      }
      if(controller.signal.aborted)return;cursor.current.seq=after;
      setState(previous=>{const same=previous.project===projectId;const all=[...(same?previous.items:[]),...items];
        return {project:projectId,items:all.slice(-500),more,trimmed:(same&&previous.trimmed)||all.length>500};});
    }
    void drain().catch(error=>{if(!controller.signal.aborted)fail(error);});return()=>controller.abort();
  },[projectId,version,refresh,fail]);
  return {items:state.project===projectId?state.items:[],hasMore:state.project===projectId&&state.more,trimmed:state.project===projectId&&state.trimmed,
    loadMore:useCallback(()=>setRefresh(value=>value+1),[])};
}
