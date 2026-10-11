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
import type { ProjectView, ProposalView } from "./contracts/generated";

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
    decide: vi.fn(),
    start: vi.fn(),
    workflowDocuments: vi.fn(),
    saveWorkflowDocument: vi.fn(),
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
    vi.mocked(client.decide).mockResolvedValue({
      ...proposal,
      status: "accepted",
    });
  });
  afterEach(cleanup);
  it("loads a real project into simultaneous panes without a global private developer mode", async () => {
    render(<App />);
    expect(
      await screen.findByText("Standalone sequences: 1", { exact: true }),
    ).toBeTruthy();
    expect(screen.getByLabelText("Project and run tree")).toBeTruthy();
    expect(screen.getByLabelText("Inspector")).toBeTruthy();
    expect(screen.getByLabelText("Jobs and actions")).toBeTruthy();
    expect(screen.queryByText(/Scientist Mode/)).toBeNull();
    expect(screen.queryByText(/Developer Mode/)).toBeNull();
  });
  it("an accepted plan is separate from calculation and binds the saved revision", async () => {
    render(<App />);
    await screen.findByText("Standalone sequences: 1", { exact: true });
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
      await screen.findByText("Standalone sequences: 1", { exact: true }),
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
    await screen.findByText('Standalone sequences: 1',{exact:true});
    expect(screen.queryByLabelText('Workflow run controls')).toBeNull();
    expect(screen.queryByRole('button',{name:/^Import$/})).toBeNull();
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
    fireEvent.change(screen.getByLabelText('Tool call budget'),{target:{value:'50'}});
    await vi.waitFor(()=>expect(screen.getByLabelText('Tool call budget')).toHaveProperty('value','50'));
    const policySave=vi.mocked(client.saveWorkflowDocument).mock.calls.at(-1)![2];
    expect(policySave.workflow?.nodes.find(n=>n.id==='c')?.depends_on).toEqual(['a','b']);
    expect(policySave.workflow?.execution_policy.max_tool_calls).toBe(50);
    expect(screen.getByRole('button',{name:'Start run'})).toHaveProperty('disabled',true);
    fireEvent.click(screen.getByRole('button',{name:/^Inputs$/}));
    expect(screen.queryByLabelText('Workflow run controls')).toBeNull();
  });
  it("editing facts invalidates acceptance and cannot start an obsolete workflow", async () => {
    render(<App />);
    await screen.findByText("Standalone sequences: 1", { exact: true });
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
    fireEvent.change(screen.getByLabelText("Project name"), {
      target: { value: "changed fixture" },
    });
    expect(screen.getByText(/Unsaved changes/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Start run" })).toBeNull();
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
    await screen.findByText("Standalone sequences: 1", { exact: true });
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
    await screen.findByText("Standalone sequences: 1", { exact: true });
    fireEvent.click(screen.getByRole("button", { name: "Inputs" }));
    fireEvent.change(screen.getByLabelText("Project name"), {
      target: { value: "edited fixture" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Generate proposal" }));
    await vi.waitFor(() => expect(client.save).toHaveBeenCalled());
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
