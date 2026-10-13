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
import type {
  ProjectView,
  ProposalView,
  RunSummaryView,
} from "./contracts/generated";

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
    if (path === "/projects/test/imports") return { transaction_ids: [] };
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
    { id: "fixture", sequence: "ACDEFGHIK", role: "software_fixture", localization_context: "cytosolic" },
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
    sessionStorage.clear();
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
    vi.mocked(client.assistantHistory).mockResolvedValue({
      project_id: project.id,
      messages: [],
      has_more: false,
    });
    vi.mocked(client.proposalDiff).mockResolvedValue({
      proposal_id: proposal.id,
      previous_proposal_id: null,
      changes: [],
      missing_inputs: [],
      evidence: [],
      limitations: [],
    });
    vi.mocked(client.saveWorkflowDocument).mockImplementation(
      async (projectId, id, value, revision) => ({
        ...value,
        workflow: value.workflow ?? proposal.workflow!,
        id,
        project_id: projectId,
        project_revision: revision,
        revision: 1,
        semantic_revision: 1,
        layout_revision: 1,
      }),
    );
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

  async function ready() {
    render(<App />);
    await vi.waitFor(() =>
      expect(screen.getByLabelText("Current project")).toHaveProperty(
        "value",
        "test",
      ),
    );
  }
  function assistant() {
    fireEvent.click(screen.getByText("View", { exact: true }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Assistant" }));
  }
  async function proposalReady() {
    assistant();
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    await screen.findByLabelText("Current proposal");
  }
  async function approve() {
    fireEvent.click(screen.getByRole("button", { name: "Accept changes" }));
    await screen.findByRole("button", { name: "Run approved task" });
  }
  it("defaults to file-level inputs with no resource catalogue or duplicate panes", async () => {
    await ready();
    expect(
      screen.getByRole("button", { name: "Project sequences" }),
    ).toBeTruthy();
    expect(screen.queryByRole("button", { name: "fixture" })).toBeNull();
    expect(document.querySelector(".inspector-hidden")).not.toBeNull();
    expect(screen.queryByLabelText("Project and run tree")).toBeNull();
    expect(
      screen.queryByRole("tab", { name: /Artifacts|Resources|Terminal/ }),
    ).toBeNull();
    expect(
      screen.queryByRole("button", { name: /^Assistant$|^Jobs$/ }),
    ).toBeNull();
  });
  it("one acceptance saves the exact workflow; no calculation starts until Run", async () => {
    await ready();
    await proposalReady();
    expect(client.start).not.toHaveBeenCalled();
    await approve();
    expect(client.start).not.toHaveBeenCalled();
    expect(client.saveWorkflowDocument).toHaveBeenCalledWith(
      "test",
      "proposal",
      expect.objectContaining({ workflow: proposal.workflow }),
      1,
      undefined,
    );
    expect(client.propose).toHaveBeenCalledWith(
      "test",
      "fusion_screen",
      "",
      "template",
      expect.any(Object),
      false,
    );
    expect(screen.getAllByLabelText("Current proposal")).toHaveLength(1);
    expect(screen.getAllByLabelText("Assistant message")).toHaveLength(1);
  });
  it("unsent chat and Modify intent survive closing while the selected workflow and approval remain", async () => {
    await ready();
    await proposalReady();
    await approve();
    fireEvent.click(screen.getByRole("tab", { name: "Workflow" }));
    await screen.findByRole("button", { name: "Module 受控夹具Node" });
    fireEvent.click(screen.getByRole("button", { name: "Modify" }));
    fireEvent.change(screen.getByLabelText("Assistant message"), {
      target: { value: "unsent revision" },
    });
    const writes = vi.mocked(client.saveWorkflowDocument).mock.calls.length;
    fireEvent.click(screen.getByRole("button", { name: "Close Assistant" }));
    assistant();
    expect(screen.getByLabelText("Assistant message")).toHaveProperty(
      "value",
      "unsent revision",
    );
    expect(screen.getByText("Modify this proposal")).toBeTruthy();
    expect(
      screen
        .getByRole("button", { name: "Module 受控夹具Node" })
        .getAttribute("aria-pressed"),
    ).toBe("true");
    expect(
      screen.getByRole("button", { name: "Run approved task" }),
    ).toBeTruthy();
    expect(client.saveWorkflowDocument).toHaveBeenCalledTimes(writes);
    expect(client.start).not.toHaveBeenCalled();
  });
  it("a renamed scientific draft retires approval without deleting its workflow", async () => {
    await ready();
    await proposalReady();
    await approve();
    fireEvent.click(screen.getByText("File", { exact: true }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Rename project" }));
    fireEvent.change(screen.getByLabelText("Project name"), {
      target: { value: "changed fixture" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /^Rename$/ }),
    );
    expect(
      screen.queryByRole("button", { name: "Run approved task" }),
    ).toBeNull();
    fireEvent.click(screen.getByRole("tab", { name: "Workflow" }));
    expect(
      await screen.findByRole("button", { name: "Module 受控夹具Node" }),
    ).toBeTruthy();
    expect(screen.getByRole("button", { name: "Review changes" })).toBeTruthy();
    expect(client.start).not.toHaveBeenCalled();
  });
  it("graph edits cannot start an old approval and Review preserves the edited definition", async () => {
    const candidate = {
      ...proposal,
      workflow: {
        ...proposal.workflow!,
        nodes: [
          proposal.workflow!.nodes[0],
          {
            ...proposal.workflow!.nodes[0],
            id: "other",
            label: "Other module",
            depends_on: [],
            inputs: {},
          },
        ],
      },
    } as ProposalView;
    vi.mocked(client.propose).mockResolvedValue(candidate);
    vi.mocked(client.decide).mockResolvedValue({
      ...candidate,
      status: "accepted",
    });
    let active = candidate.workflow!;
    vi.mocked(client.saveWorkflowDocument).mockImplementation(
      async (p, id, value, revision) => {
        active = value.workflow ?? active;
        return {
          ...value,
          workflow: active,
          id,
          project_id: p,
          project_revision: revision,
          revision: 2,
          semantic_revision: 2,
          layout_revision: 1,
        };
      },
    );
    await ready();
    await proposalReady();
    await approve();
    fireEvent.click(screen.getByRole("tab", { name: "Workflow" }));
    await screen.findByRole("button", { name: "Module Other module" });
    fireEvent.click(screen.getByRole("button", { name: "Connections" }));
    fireEvent.change(screen.getByLabelText("Upstream module"), {
      target: { value: "fixture" },
    });
    fireEvent.change(screen.getByLabelText("Downstream module"), {
      target: { value: "other" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Connect modules" }));
    await vi.waitFor(() =>
      expect(
        screen.queryByRole("button", { name: "Run approved task" }),
      ).toBeNull(),
    );
    expect(active.nodes[1].depends_on).toEqual(["fixture"]);
    fireEvent.click(screen.getByRole("button", { name: "Review changes" }));
    await vi.waitFor(() =>
      expect(client.proposeCustom).toHaveBeenCalledWith("test", active, ""),
    );
    expect(client.start).not.toHaveBeenCalled();
  });
  it("capability failures do not invent data or block viewing actual inputs", async () => {
    vi.mocked(client.info).mockRejectedValue(
      new Error("capability unavailable"),
    );
    await ready();
    expect(
      screen.getByRole("button", { name: "Project sequences" }),
    ).toBeTruthy();
    expect((await screen.findByRole("alert")).textContent).toContain(
      "capability unavailable",
    );
    expect(client.start).not.toHaveBeenCalled();
  });
  it("Help has one clear destination, not a mirrored Inspector", async () => {
    await ready();
    fireEvent.click(screen.getByText("Help", { exact: true }));
    fireEvent.click(
      screen.getByRole("menuitem", { name: "Scientific boundaries" }),
    );
    expect(
      screen.getByRole("tab", { name: "Help" }).getAttribute("aria-selected"),
    ).toBe("true");
    expect(
      screen.getByRole("heading", { name: "Scientific boundaries" }),
    ).toBeTruthy();
    expect(screen.queryByLabelText("Inspector tabs")).toBeNull();
  });
  it("a previous projects delayed proposal cannot replace the newly selected project", async () => {
    const other = { ...project, id: "other", name: "Other project" };
    vi.mocked(client.projectSummaries).mockResolvedValue(
      [project, other].map((value) => ({
        id: value.id,
        name: value.name,
        revision: 1,
        scientific: false,
        sequence_count: 1,
        scientific_sequence_count: null,
        scientific_sequence_index_status: "not_attached",
      })),
    );
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
    await ready();
    assistant();
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    await vi.waitFor(() => expect(client.propose).toHaveBeenCalled());
    fireEvent.change(screen.getByLabelText("Current project"), {
      target: { value: "other" },
    });
    await vi.waitFor(() =>
      expect(screen.getByLabelText("Current project")).toHaveProperty(
        "value",
        "other",
      ),
    );
    resolve(proposal);
    await vi.waitFor(() =>
      expect(screen.getByRole("button", { name: "Send" })).toHaveProperty(
        "disabled",
        false,
      ),
    );
    expect(screen.queryByLabelText("Current proposal")).toBeNull();
  });
});
