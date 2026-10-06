import {expect,it} from "vitest";
import {parsePublic} from "./validation";

it("rejects unknown protocol, missing states and string numbers without defaults or coercion",()=>{
  const info={name:"fixture",protocol_version:"2",authentication:"session_required",workspace_id:"fixture",storage:"SQLite WAL",max_workers:2,plugin_sandbox:false,agent_backend:"validated_workflow_templates",capabilities:{},resources:{active_tasks:0},remote_desktop_authenticated_session:false,supported_rate_laws:[]};
  expect(parsePublic("RuntimeInfoView",info)).toEqual(info);
  expect(()=>parsePublic("RuntimeInfoView",{...info,protocol_version:"future"})).toThrow();expect(()=>parsePublic("RuntimeInfoView",{...info,max_workers:"2"})).toThrow();
  const missing={...info};delete (missing as Partial<typeof info>).resources;expect(()=>parsePublic("RuntimeInfoView",missing)).toThrow();
  expect(()=>parsePublic("RuntimeInfoView",{...info,private_profile:{api_key:"SOFTWARE_FIXTURE_NOT_A_SECRET"}})).toThrow();
});
