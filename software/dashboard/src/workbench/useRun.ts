import {useEffect,useState,useRef} from "react";
import type {EventPage,RunSummaryView} from "../contracts/generated";
import * as client from "./client";
import {pollVersioned} from "./polling";

export function useRun(id:string|undefined,projectId:string|undefined,refresh:number,fail:(reason:unknown)=>void) {
  const[run,setRun]=useState<RunSummaryView>();
  const[events,setEvents]=useState<EventPage["items"]>([]);
  const identity=useRef({id:"",project:"",cursor:0,version:-1});
  useEffect(()=>{
    if(identity.current.id!==id||identity.current.project!==projectId){identity.current={id:id??"",project:projectId??"",cursor:0,version:-1};setRun(undefined);setEvents([]);}
    if(!id||!projectId)return;
    return pollVersioned({initialVersion:identity.current.version,load:async signal=>{
      const summary=await client.summary(id,signal);
      if(summary.project_id!==projectId||summary.id!==id)throw new Error("运行与当前项目身份不匹配。");
      let cursor=Math.max(identity.current.cursor,summary.event_cursor-500);
      const rows:EventPage["items"]=[];
      // Drain this bounded window even at a terminal boundary; otherwise one
      // 200-row page would stop polling before the final events were visible.
      for(let pageNumber=0;pageNumber<3;pageNumber++){
        const page=await client.events(id,cursor,signal);rows.push(...page.items);cursor=page.cursor;
        if(!page.has_more)break;
      }
      return{...summary,newEvents:rows.slice(-500),newCursor:cursor};
    },accept:value=>{identity.current.cursor=value.newCursor;identity.current.version=value.state_version;setRun(value);setEvents(previous=>[...previous,...value.newEvents].slice(-500));localStorage.setItem(`fusionlab.run.${projectId}`,id);},fail});
  },[id,projectId,refresh,fail]);
  const current=run!==undefined&&run.id===id&&run.project_id===projectId;
  return{run:current?run:undefined,events:current?events:[]};
}
