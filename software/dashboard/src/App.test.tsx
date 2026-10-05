import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import * as api from "./api";
import type { Project } from "./types";

vi.mock("./api", () => ({
  getProjects: vi.fn(),
  getTools: vi.fn(),
  getInfo: vi.fn(),
  getRuns: vi.fn(),
  getRun: vi.fn(),
  saveProject: vi.fn(),
  createPlan: vi.fn(),
  startRun: vi.fn(),
}));
const project: Project = {
  id: "test",
  name: "融合蛋白测试",
  revision: 1,
  description: "",
  sequences: [{ id: "protein", sequence: "ACDEFGHIK", role: "fusion" }],
  assemblies: [],
  conditions: {},
  pathway: null,
  files: [],
  datasets: [],
};

describe("FusionLab", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    vi.mocked(api.getProjects).mockResolvedValue([project]);
    vi.mocked(api.getTools).mockResolvedValue([]);
    vi.mocked(api.getRuns).mockResolvedValue([]);
    vi.mocked(api.getInfo).mockResolvedValue({
      name: "FusionLab",
      data_dir: "local",
      storage: "SQLite WAL",
      max_workers: 4,
      plugin_sandbox: false,
      agent_backend: "validated_workflow_templates",
      supported_rate_laws: ["two_phase_competitive_mm_v1"],
    });
    vi.mocked(api.saveProject).mockResolvedValue({ ...project, revision: 2 });
    vi.mocked(api.createPlan).mockResolvedValue({
      workflow: {
        id: "screen",
        version: "1",
        name: "可审阅分析",
        description: "真实序列分析",
        nodes: [],
      },
      source: "validated_template",
      requires_confirmation: true,
      confirmation: { project_id: "test", project_revision: 2, project_input_sha256: "a".repeat(64), workflow_sha256: "b".repeat(64) },
    });
  });
  afterEach(cleanup);
  it("loads a real project and keeps developer details opt-in", async () => {
    render(<App />);
    expect(await screen.findByText("1 条蛋白序列")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /开发者面板/ })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /Scientist Mode/ }));
    expect(screen.getByRole("button", { name: /开发者面板/ })).toBeTruthy();
    expect(localStorage.getItem("fusionlab.mode")).toBe("developer");
  });
  it("saves the current revision before producing a plan for confirmation", async () => {
    render(<App />);
    await screen.findByText("1 条蛋白序列");
    fireEvent.click(screen.getByRole("button", { name: /生成可审阅流程/ }));
    expect(await screen.findByText("可审阅分析")).toBeTruthy();
    expect(api.saveProject).toHaveBeenCalledWith(project, 1);
    expect(api.createPlan).toHaveBeenCalledWith("test", "fusion_screen", "");
  });
  it("shows connection errors without fabricated project data", async () => {
    vi.mocked(api.getProjects).mockRejectedValue(
      new Error("backend unavailable"),
    );
    render(<App />);
    expect(await screen.findByRole("alert")).toHaveProperty(
      "textContent",
      expect.stringContaining("backend unavailable"),
    );
    expect(
      screen.getByRole("button", { name: /生成可审阅流程/ }),
    ).toHaveProperty("disabled", true);
  });
  it("editing draft facts invalidates the reviewed plan and blocks its confirmation", async () => {
    render(<App />);
    await screen.findByText("1 条蛋白序列");
    fireEvent.click(screen.getByRole("button", {name:/生成可审阅流程/}));
    await screen.findByText("可审阅分析");
    expect(screen.getByRole("button", {name:"确认并运行"})).toHaveProperty("disabled", false);
    fireEvent.click(screen.getByRole("button", {name:/项目数据/}));
    fireEvent.change(screen.getByLabelText("pH"), {target:{value:"5"}});
    expect(screen.getByText(/有未保存修改/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", {name:/分析流程/}));
    expect(screen.queryByRole("button", {name:"确认并运行"})).toBeNull();
    expect(api.startRun).not.toHaveBeenCalled();
  });
  it("a plan response for the previous project cannot replace the current project", async () => {
    vi.mocked(api.getProjects).mockResolvedValue([project, {...project,id:"other",name:"另一个项目"}]);
    let resolve!: (value: Awaited<ReturnType<typeof api.createPlan>>) => void;
    vi.mocked(api.createPlan).mockImplementation(() => new Promise((done) => { resolve = done; }));
    render(<App />);
    await screen.findByText("1 条蛋白序列");
    fireEvent.click(screen.getByRole("button", {name:/生成可审阅流程/}));
    await vi.waitFor(() => expect(api.createPlan).toHaveBeenCalled());
    fireEvent.change(screen.getByLabelText("当前项目"), {target:{value:"other"}});
    resolve({workflow:{id:"obsolete",name:"过期方案",version:"1",description:"",nodes:[]},
      confirmation:{project_id:"test",project_revision:2,project_input_sha256:"a".repeat(64),workflow_sha256:"b".repeat(64)},
      source:"validated_template",requires_confirmation:true});
    await vi.waitFor(() => expect(screen.getByLabelText("当前项目")).toHaveProperty("value","other"));
    expect(screen.queryByText("过期方案")).toBeNull();
  });
});
