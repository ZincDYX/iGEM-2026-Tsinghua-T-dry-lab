import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import * as client from "./workbench/client";
import type { ProjectView, ProposalView, RunSummaryView } from "./contracts/generated";

// jsdom has no layout/scroll API; browser/native tests exercise actual scrolling.
Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
  configurable: true,
  value: vi.fn(),
});

vi.mock("./api", () => ({
  isDesktop: () => false,
  backendMode: "local",
  requestJson: vi.fn(async (path: string) => {
    // Navigation-only stub. Real schema/setup validation is covered via HTTP
    // and the production browser, not this empty-project App fixture.
    if (path.split("?")[0] === "/scientific-projects/form-schema")
      return { $defs: {}, properties: {} };
    if (path === '/projects/test/imports') return {transaction_ids:[]};
    throw Error("Unexpected App fixture request: " + path);
  }),
}));
vi.mock("./workbench/client", async (importOriginal) => {
  const original = await importOriginal<typeof import("./workbench/client")>();
  return {
    ...original,
    projectSummaries: vi.fn(),
    project: vi.fn(),
    info: vi.fn(),
    history: vi.fn(),
    actions: vi.fn(),
    save: vi.fn(),
    propose: vi.fn(),
    proposeCustom: vi.fn(),
    decide: vi.fn(),
    start: vi.fn(),
    summary: vi.fn(),
    events: vi.fn(),
    node: vi.fn(),
    workflowDocuments: vi.fn(),
    saveWorkflowDocument: vi.fn(),
    assistantHistory: vi.fn(),
    proposalDiff: vi.fn(),
    revise: vi.fn(),
  };
});
const project: ProjectView = {
  id: "test",
  name: "SOFTWARE_FIXTURE",
  revision: 1,
  description: "",
  sequences: [
    { id: "fixture", sequence: "ACDEFGHIK", role: "software_fixture" },
  ],
  assemblies: [],
  conditions: {},
  pathway: null,
  files: [],
  datasets: [],
  scientific_project: null,
  runtime_profile_ref: null,
  parent_run_id: null,
  parent_snapshot_sha256: null,
};
const proposal: ProposalView = {
  review_identity: null,
  observation: null,
  scientific_actions: [],
  reviewed_tool_labels: [],
  previous_review_identity: null,
  id: "proposal",
  task_id: "proposal",
  project_id: "test",
  source: "validated_template",
  status: "proposed",
  objective: "",
  rationale: "软件夹具，不调用Model",
  change_types: [],
  evidence: [],
  requested_stages: ["fixture"],
  execution_stages: ["fixture"],
  reused_artifacts: [],
  missing_inputs: [],
  limitations: [],
  created_at: "fixture",
  workflow: {
    id: "fixture",
    name: "可审阅分析",
    version: "1",
    description: "软件夹具",
    execution_policy: {
      target_node_id: null,
      max_completed_stages: null,
      checkpoints_before: [],
      checkpoints_after: [],
      allowed_tools: ["fusion.sequence_metrics"],
      max_tool_calls: 1000,
      stop_after_seconds: null,
      memory_limit_mb: null,
    },
    nodes: [
      {
        id: "fixture",
        label: "受控夹具Node",
        tool_id: "fusion.sequence_metrics",
        inputs: {},
        map: null,
        depends_on: [],
      },
    ],
  },
  confirmation: {
    project_id: "test",
    project_revision: 1,
    project_input_sha256: "a".repeat(64),
    workflow_sha256: "b".repeat(64),
  },
};
describe("FusionLab scientific workbench", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    vi.stubGlobal(
      "ResizeObserver",
      class {
        observe() {}
        disconnect() {}
      },
    );
    vi.mocked(client.projectSummaries).mockResolvedValue([
      {
        id: project.id,
        name: project.name,
        revision: 1,
        scientific: false,
        sequence_count: 1,
        scientific_sequence_count: null,
        scientific_sequence_index_status: "not_attached",
      },
    ]);
    vi.mocked(client.project).mockResolvedValue(project);
    vi.mocked(client.history).mockResolvedValue([]);
    vi.mocked(client.actions).mockResolvedValue([]);
    vi.mocked(client.workflowDocuments).mockResolvedValue([]);
    vi.mocked(client.assistantHistory).mockResolvedValue({project_id:project.id,messages:[],has_more:false});
    vi.mocked(client.proposalDiff).mockResolvedValue({proposal_id:proposal.id,previous_proposal_id:null,changes:[],missing_inputs:[],evidence:[],limitations:[]});
    vi.mocked(client.saveWorkflowDocument).mockImplementation(async (projectId, id, value, revision) => ({
      ...value, workflow: value.workflow ?? proposal.workflow!, id, project_id: projectId, project_revision: revision, revision: 1, semantic_revision: 1, layout_revision: 1,
    }));
    vi.mocked(client.info).mockResolvedValue({
      name: "FusionLab",
      workspace_id: "w".repeat(64),
      protocol_version: "2",
      authentication: "session_required",
      storage: "SQLite WAL",
      max_workers: 4,
      plugin_sandbox: false,
      agent_backend: "validated_workflow_templates",
      capabilities: {
        stage_step: "ready",
        hybrid_planning: "unavailable",
        scientific_mcp: "unavailable",
      },
      resources: { active_tasks: 0, queued_tasks: 0, gpu_slots: 1 },
      remote_desktop_authenticated_session: false,
      supported_rate_laws: [],
    });
    vi.mocked(client.save).mockResolvedValue({ ...project, revision: 2 });
    vi.mocked(client.propose).mockResolvedValue(proposal);
    vi.mocked(client.proposeCustom).mockResolvedValue(proposal);
    vi.mocked(client.decide).mockResolvedValue({
      ...proposal,
      status: "accepted",
    });
  });
  afterEach(cleanup);
  it("loads a real project into simultaneous panes without a global private developer mode", async () => {
    render(<App />);
    expect(
      await screen.findByRole("button", {name: "fixture"}),
    ).toBeTruthy();
    expect(screen.queryByLabelText("Project and run tree")).toBeNull();
    expect(document.querySelector(".inspector-hidden")).not.toBeNull();
    expect(screen.queryByRole("button",{name:"Jobs"})).toBeNull();
    expect(screen.queryByRole("button",{name:"Assistant"})).toBeNull();
    expect(screen.queryByRole("tab",{name:"Terminal"})).toBeNull();
    expect(screen.queryByText(/Scientist Mode/)).toBeNull();
    expect(screen.queryByText(/Developer Mode/)).toBeNull();
  });
  it("an accepted plan is separate from calculation and binds the saved revision", async () => {
    render(<App />);
    await screen.findByRole("button", {name: "fixture"});
    fireEvent.click(screen.getByText('View',{exact:true}));fireEvent.click(screen.getByRole('menuitem',{name:'Assistant'}));
    fireEvent.click(screen.getByRole("button", { name: "Generate proposal" }));
    expect(await screen.findByText("可审阅分析")).toBeTruthy();
    expect(client.start).not.toHaveBeenCalled();
    expect(screen.queryByRole("button", { name: "Start run" })).toBeNull();
    fireEvent.click(
      screen.getByRole("button", {
        name: "Accept proposal (does not start computation)",
      }),
    );
    await vi.waitFor(() =>
      expect(screen.getByRole("button", { name: "Start run" })).toHaveProperty(
        "disabled",
        false,
      ),
    );
    expect(client.start).not.toHaveBeenCalled();
    expect(client.propose).toHaveBeenCalledWith(
      "test",
      "fusion_screen",
      "",
      "template",
      expect.any(Object),
      false,
    );
  });
  it("connection errors have no fabricated projects and independent capability failure does not block viewing", async () => {
    vi.mocked(client.info).mockRejectedValue(
      new Error("capability unavailable"),
    );
    render(<App />);
    expect(
      await screen.findByRole("button", {name: "fixture"}),
    ).toBeTruthy();
    expect(await screen.findByRole("alert")).toHaveProperty(
      "textContent",
      expect.stringContaining("capability unavailable"),
    );
    cleanup();
    vi.mocked(client.projectSummaries).mockRejectedValue(
      new Error("backend unavailable"),
    );
    render(<App />);
    expect(await screen.findByRole("alert")).toHaveProperty(
      "textContent",
      expect.stringContaining("backend unavailable"),
    );
    expect(
      screen.getByRole("button", { name: "Generate proposal" }),
    ).toHaveProperty("disabled", true);
  });
  it('an edited graph cannot start an old accepted proposal; run controls appear only in Workflow',async()=>{
    const candidate: ProposalView={...proposal,workflow:{...proposal.workflow!,name:'Reviewed graph',execution_policy:{...proposal.workflow!.execution_policy,allowed_tools:['workflow.gather']},nodes:[
      {id:'a',label:'Inputs',tool_id:'workflow.gather',inputs:{results:{kind:'literal',value:[]}},map:null,depends_on:[]},
      {id:'b',label:'First branch',tool_id:'workflow.gather',inputs:{results:{kind:'literal',value:[]}},map:null,depends_on:['a']},
      {id:'c',label:'Second branch',tool_id:'workflow.gather',inputs:{results:{kind:'literal',value:[]}},map:null,depends_on:['a']},
    ]}};
    vi.mocked(client.propose).mockResolvedValue(candidate);
    vi.mocked(client.decide).mockResolvedValue({...candidate,status:'accepted'});
    let current=candidate.workflow!;
    vi.mocked(client.saveWorkflowDocument).mockImplementation(async (projectId,id,value,projectRevision)=>{
      current=value.workflow??current;
      return {...value,workflow:current,id,project_id:projectId,project_revision:projectRevision,revision:2,semantic_revision:2,layout_revision:1};
    });
    render(<App/>);
    await screen.findByRole("button", {name: "fixture"});
    expect(screen.queryByLabelText('Workflow run controls')).toBeNull();
    expect(screen.queryByRole('button',{name:/^Import$/})).toBeNull();
    fireEvent.click(screen.getByText('View',{exact:true}));fireEvent.click(screen.getByRole('menuitem',{name:'Assistant'}));
    fireEvent.click(screen.getByRole('button',{name:'Generate proposal'}));
    await screen.findByText('Reviewed graph');
    fireEvent.click(screen.getByRole('button',{name:'Accept proposal (does not start computation)'}));
    await vi.waitFor(()=>expect(screen.getByRole('button',{name:'Start run'})).toHaveProperty('disabled',false));
    fireEvent.change(screen.getByLabelText('Upstream module'),{target:{value:'b'}});
    fireEvent.change(screen.getByLabelText('Downstream module'),{target:{value:'c'}});
    fireEvent.click(screen.getByRole('button',{name:'Connect modules'}));
    await vi.waitFor(()=>expect(screen.getByRole('button',{name:'Start run'})).toHaveProperty('disabled',true));
    expect(screen.getByText('Workflow changes are saved but not authorized. Review and accept a new proposal before running.')).toBeTruthy();
    expect(client.start).not.toHaveBeenCalled();
    expect(screen.queryByLabelText('Tool call budget')).toBeNull();
    expect(screen.getByRole('button',{name:'Start run'})).toHaveProperty('disabled',true);
    fireEvent.change(screen.getByLabelText('Run through module'),{target:{value:'c'}});
    await vi.waitFor(()=>expect(screen.getByLabelText('Run through module')).toHaveProperty('value','c'));
    expect(vi.mocked(client.saveWorkflowDocument).mock.calls.at(-1)![2].workflow?.execution_policy.target_node_id).toBe('c');
    expect(screen.queryByRole('button',{name:'Review stage-by-stage plan'})).toBeNull();
    expect(screen.queryByRole('button',{name:'Review run to selected stage'})).toBeNull();
    expect(screen.getAllByRole('button',{name:'Review plan'})).toHaveLength(1);
    fireEvent.click(screen.getByRole('button',{name:'Review plan'}));
    await vi.waitFor(()=>expect(client.proposeCustom).toHaveBeenCalledWith('test',expect.objectContaining({
      nodes:current.nodes,execution_policy:expect.objectContaining({target_node_id:'c',max_tool_calls:1000}),
    }),''));
    expect(client.propose).toHaveBeenCalledTimes(1); // No template replacement of the edited graph.
    expect(client.start).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('tab',{name:/^Inputs$/}));
    expect(screen.queryByLabelText('Workflow run controls')).toBeNull();
  });
  it('execution settings wait for the first durable document instead of dropping its proposal',async()=>{
    let release!:()=>void;
    const pending=new Promise<void>(resolve=>{release=resolve;});
    vi.mocked(client.saveWorkflowDocument).mockImplementationOnce(async(projectId,id,value,revision)=>{
      await pending;
      return {...value,workflow:value.workflow??proposal.workflow!,id,project_id:projectId,project_revision:revision,
        revision:1,semantic_revision:1,layout_revision:1};
    });
    render(<App/>);
    await screen.findByRole("button", {name: "fixture"});
    fireEvent.click(screen.getByText('View',{exact:true}));fireEvent.click(screen.getByRole('menuitem',{name:'Assistant'}));
    fireEvent.click(screen.getByRole('button',{name:'Generate proposal'}));
    await screen.findByText('可审阅分析');
    expect(screen.getByLabelText('Run through module').matches(':disabled')).toBe(true);
    release();
    await vi.waitFor(()=>expect(screen.getByLabelText('Run through module').matches(':disabled')).toBe(false));
    expect(screen.getByLabelText('Run through module').querySelector('option[value="fixture"]')).not.toBeNull();
    expect(screen.getByText('可审阅分析')).toBeTruthy();
    expect(client.start).not.toHaveBeenCalled();
  });
  it('opening a recorded run displays its frozen execution scope instead of the draft policy',async()=>{
    const recorded: RunSummaryView={id:'recorded',name:'Recorded software run',project_id:project.id,status:'succeeded',snapshot_hash:'fixture',
      created_at:'fixture',updated_at:'fixture',project_revision:1,control:null,heartbeat:null,state_version:1,event_cursor:0,
      workflow:{...proposal.workflow!,execution_policy:{...proposal.workflow!.execution_policy,max_tool_calls:7,target_node_id:'fixture',checkpoints_after:['fixture']}},
      tools:{},artifacts:[],scientific_assessment:{experimental_validation:'not_established'},nodes:[{
        id:'fixture',parent_id:null,status:'succeeded',attempts:1,tool_id:'fusion.sequence_metrics',label:'Recorded module',scientific_summary:null,
      }]};
    vi.mocked(client.history).mockResolvedValue([recorded]);
    vi.mocked(client.summary).mockResolvedValue(recorded);
    vi.mocked(client.events).mockResolvedValue({items:[],cursor:0,has_more:false});
    vi.mocked(client.node).mockResolvedValue({node:{id:'fixture',parent_id:null,status:'succeeded',attempts:1,output:null,error:null,inputs:null},offset:0,limit:20,total_records:0,artifact:null,sequence_map:null});
    render(<App/>);
    await screen.findByRole("button", {name: "fixture"});
    fireEvent.click(screen.getByRole('tab',{name:'Results'}));
    fireEvent.change(await screen.findByLabelText("Run version"),{target:{value:"recorded"}});
    await vi.waitFor(()=>expect(client.summary).toHaveBeenCalled());
    fireEvent.click(screen.getByRole('tab',{name:'Workflow'}));
    await vi.waitFor(()=>expect(screen.getByLabelText('Run through module')).toHaveProperty('value','fixture'));
    expect(screen.queryByLabelText('Tool call budget')).toBeNull();
    expect(screen.getByLabelText('Run through module')).toHaveProperty('value','fixture');
    expect(screen.getByRole('checkbox',{name:'Pause after 受控夹具Node'})).toHaveProperty('checked',true);
    expect(screen.queryByRole('button',{name:'Review plan'})).toBeNull();
    expect(screen.queryByRole('button',{name:'Start run'})).toBeNull();
    expect(client.saveWorkflowDocument).not.toHaveBeenCalled();
  });
  it("editing facts invalidates acceptance and cannot start an obsolete workflow", async () => {
    render(<App />);
    await screen.findByRole("button", {name: "fixture"});
    fireEvent.click(screen.getByText('View',{exact:true}));fireEvent.click(screen.getByRole('menuitem',{name:'Assistant'}));
    fireEvent.click(screen.getByRole("button", { name: "Generate proposal" }));
    await screen.findByText("可审阅分析");
    fireEvent.click(
      screen.getByRole("button", {
        name: "Accept proposal (does not start computation)",
      }),
    );
    await vi.waitFor(() =>
      expect(screen.getByRole("button", { name: "Start run" })).toHaveProperty(
        "disabled",
        false,
      ),
    );
    fireEvent.click(
      within(
        screen.getByRole("tablist", { name: "Workspace documents" }),
      ).getByRole("tab", { name: "Inputs" }),
    );
    fireEvent.click(screen.getByRole("button",{name:"Rename project"}));
    fireEvent.change(screen.getByLabelText("Project name"), {
      target: { value: "changed fixture" },
    });
    expect(screen.getByText(/Unsaved changes/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Start run" })).toBeNull();
    expect(client.start).not.toHaveBeenCalled();
  });
  it('scientific boundaries open the Workflow source context without a second Diagnostic tab',async()=>{
    render(<App/>);
    await screen.findByRole("button", {name: "fixture"});
    expect(screen.queryByRole("tab",{name:"Diagnostic"})).toBeNull();
    fireEvent.click(screen.getByText('Help',{exact:true}));
    fireEvent.click(screen.getByRole('menuitem',{name:'Scientific boundaries'}));
    expect(screen.getByRole('tab',{name:'Workflow'}).getAttribute('aria-selected')).toBe('true');
    expect(within(screen.getByRole('tablist',{name:'Inspector tabs'})).getByRole('tab',{name:'Inputs / Evidence'}).getAttribute('aria-selected')).toBe('true');
    expect(screen.queryByRole('heading',{name:'Computation diagnostics'})).toBeNull();
    expect(client.start).not.toHaveBeenCalled();
  });
  it("a previous project's slow proposal cannot replace the current project", async () => {
    const other = { ...project, id: "other", name: "另一 Project" };
    vi.mocked(client.projectSummaries).mockResolvedValue([
      {
        id: "test",
        name: project.name,
        revision: 1,
        scientific: false,
        sequence_count: 1,
        scientific_sequence_count: null,
        scientific_sequence_index_status: "not_attached",
      },
      {
        id: "other",
        name: other.name,
        revision: 1,
        scientific: false,
        sequence_count: 1,
        scientific_sequence_count: null,
        scientific_sequence_index_status: "not_attached",
      },
    ]);
    vi.mocked(client.project).mockImplementation(async (id) =>
      id === "other" ? other : project,
    );
    let resolve!: (value: ProposalView) => void;
    vi.mocked(client.propose).mockImplementation(
      () =>
        new Promise((done) => {
          resolve = done;
        }),
    );
    render(<App />);
    await screen.findByRole("button", {name: "fixture"});
    fireEvent.click(screen.getByText('View',{exact:true}));fireEvent.click(screen.getByRole('menuitem',{name:'Assistant'}));
    fireEvent.click(screen.getByRole("button", { name: "Generate proposal" }));
    await vi.waitFor(() => expect(client.propose).toHaveBeenCalled());
    fireEvent.change(screen.getByLabelText("Current project"), {
      target: { value: "other" },
    });
    resolve(proposal);
    await vi.waitFor(() =>
      expect(screen.getByLabelText("Current project")).toHaveProperty(
        "value",
        "other",
      ),
    );
    expect(screen.queryByText("可审阅分析")).toBeNull();
  });
  it("changing intent during save never submits the old goal after save resolves", async () => {
    let resolve!: (value: ProjectView) => void;
    vi.mocked(client.save).mockImplementation(
      () =>
        new Promise((done) => {
          resolve = done;
        }),
    );
    render(<App />);
    await screen.findByRole("button", {name: "fixture"});
    fireEvent.click(screen.getByRole("tab", { name: "Inputs" }));
    fireEvent.click(screen.getByRole("button",{name:"Rename project"}));
    fireEvent.change(screen.getByLabelText("Project name"), {
      target: { value: "edited fixture" },
    });
    fireEvent.click(screen.getByText('View',{exact:true}));fireEvent.click(screen.getByRole('menuitem',{name:'Assistant'}));
    fireEvent.click(screen.getByRole("button", { name: "Generate proposal" }));
    await vi.waitFor(() => expect(client.save).toHaveBeenCalled());
    fireEvent.click(screen.getByText("Tools",{exact:true}));
    fireEvent.click(screen.getByRole("menuitem",{name:"Settings"}));
    fireEvent.change(
      screen.getByLabelText("Analysis entry point", { selector: "select" }),
      { target: { value: "assembly_review" } },
    );
    resolve({ ...project, name: "edited fixture", revision: 2 });
    await vi.waitFor(() =>
      expect(
        screen.getByLabelText("Analysis entry point", { selector: "select" }),
      ).toHaveProperty("value", "assembly_review"),
    );
    await vi.waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Generate proposal" }),
      ).toHaveProperty("disabled", false),
    );
    expect(client.propose).not.toHaveBeenCalled();
    expect(screen.queryByText("可审阅分析")).toBeNull();
  });
});
