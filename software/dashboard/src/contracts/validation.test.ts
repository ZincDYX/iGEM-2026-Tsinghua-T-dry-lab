import {expect,it} from "vitest";
import {parsePublic} from "./validation";

it("rejects unknown protocol, missing states and string numbers without defaults or coercion",()=>{
  const info={name:"fixture",protocol_version:"2",authentication:"session_required",workspace_id:"fixture",storage:"SQLite WAL",max_workers:2,plugin_sandbox:false,agent_backend:"validated_workflow_templates",capabilities:{},resources:{active_tasks:0},remote_desktop_authenticated_session:false,supported_rate_laws:[]};
  expect(parsePublic("RuntimeInfoView",info)).toEqual(info);
  expect(()=>parsePublic("RuntimeInfoView",{...info,protocol_version:"future"})).toThrow();expect(()=>parsePublic("RuntimeInfoView",{...info,max_workers:"2"})).toThrow();
  const missing={...info};delete (missing as Partial<typeof info>).resources;expect(()=>parsePublic("RuntimeInfoView",missing)).toThrow();
  expect(()=>parsePublic("RuntimeInfoView",{...info,private_profile:{api_key:"SOFTWARE_FIXTURE_NOT_A_SECRET"}})).toThrow();
});

it('workflow literal inputs retain JSON arrays, primitives and null rather than object-only inference',()=>{
  for (const value of [[], [1,'record'], 3, 'name', false, null, {record:'source'}]) {
    const workflow={id:'literal-contract',name:'Software protocol fixture',description:'',version:'1',nodes:[{
      id:'module',label:'Module',tool_id:'fixture.contract',inputs:{item:{kind:'literal',value}},depends_on:[],map:null,
    }],execution_policy:{target_node_id:null,max_completed_stages:null,checkpoints_before:[],checkpoints_after:[],allowed_tools:['fixture.contract'],max_tool_calls:1,stop_after_seconds:null,memory_limit_mb:null}};
    const parsed=parsePublic('Workflow',workflow);
    expect(parsed.nodes[0].inputs.item).toEqual({kind:'literal',value});
  }
});
