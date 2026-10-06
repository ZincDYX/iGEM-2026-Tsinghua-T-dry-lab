import {test, expect, type Page, type APIRequestContext} from "@playwright/test";

const token = "SOFTWARE_FIXTURE_SESSION_NOT_A_REAL_CREDENTIAL";
const backend = "http://127.0.0.1:8791/api/platform";
const headers = {"X-FusionLab-Token": token};

async function recordedRun(request: APIRequestContext, id: string) {
  const preview = await (await request.post(`${backend}/scientific-projects/upload-preview`, {headers, data: {
    config_filename: "project.yaml", files: [
      {filename: "project.yaml", content: JSON.stringify({run: {id: "SOFTWARE_FIXTURE"}, inputs: {protein_fasta: "fixture.fasta", enzymes: [], scaffolds: [], linkers: []}})},
      {filename: "fixture.fasta", content: ">SOFTWARE_FIXTURE_NOT_BIOLOGICAL\nMAGSGS\n"},
    ],
  }})).json();
  const project = {id, name: "SOFTWARE_FIXTURE_r7_identity", scientific_project: preview.scientific_project};
  expect((await request.post(`${backend}/projects`, {headers, data: {project}})).status()).toBe(200);
  const proposal = await (await request.post(`${backend}/proposals`, {headers, data: {
    project_id: id, goal: "scientific_pipeline", policy: {checkpoints_after: ["m1"]},
  }})).json();
  expect((await request.post(`${backend}/proposals/${proposal.id}/decision`, {headers, data: {action: "accept"}})).status()).toBe(200);
  const run = await (await request.post(`${backend}/runs`, {headers, data: {
    project_id: id, workflow: proposal.workflow, confirmation: proposal.confirmation, proposal_id: proposal.id,
  }})).json();
  return run.id as string;
}

async function open(page: Page, id: string, runId: string) {
  await page.addInitScript(({token, id, runId}) => {
    localStorage.setItem("fusionlab.project", id);
    localStorage.setItem(`fusionlab.run.${id}`, runId);
    window.__TAURI__ = {core: {invoke: async<T>(command: string) => {
      if (command === "backend_info") return {url: "http://127.0.0.1:5191", token, mode: "local"} as T;
      if (command === "desktop_settings") return {mode: "local", ssh_host: "", remote_port: 8780} as T;
      throw new Error("SOFTWARE_FIXTURE unsupported bridge");
    }}};
  }, {token, id, runId});
  await page.goto("/");
  await expect(page.getByLabel("当前项目")).toHaveValue(id);
  await expect(page.locator(".document-status")).toContainText("已暂停");
}

test("checkpoint resume uses the frozen policy and run, not a new plan", async({page, request}) => {
  const id = "r7-checkpoint-identity";
  const runId = await recordedRun(request, id);
  await open(page, id, runId);
  const before = await (await request.get(`${backend}/runs/${runId}/summary`, {headers})).json();
  expect(before.workflow.execution_policy.max_completed_stages).toBeNull();
  expect(before.workflow.execution_policy.checkpoints_after).toEqual(["m1"]);
  expect(before.nodes.find((node: {id: string}) => node.id === "m1").attempts).toBe(1);
  const mutations: {path: string; data: unknown}[] = [];
  page.on("request", request => {
    if (request.method() === "POST") mutations.push({path: new URL(request.url()).pathname, data: request.postDataJSON()});
  });
  await page.getByRole("button", {name: "继续已授权范围", exact: true}).click();
  await expect(page.locator(".document-status")).toContainText("作业完成");
  const after = await (await request.get(`${backend}/runs/${runId}/summary`, {headers})).json();
  expect(after.id).toBe(runId);
  expect(after.snapshot_hash).toBe(before.snapshot_hash);
  expect(after.workflow.execution_policy).toEqual(before.workflow.execution_policy);
  expect(after.nodes.map((node: {attempts: number}) => node.attempts)).toEqual([1, 1, 1, 1, 1]);
  expect(mutations.filter(item => /\/runs$|\/proposals$/.test(item.path))).toEqual([]);
  expect(mutations).toContainEqual({path: `/api/platform/runs/${runId}/control`, data: {action: "resume"}});
  expect(await (await request.get(`${backend}/runs?project_id=${id}`, {headers})).json()).toHaveLength(1);
});

test("same-ID proposal never borrows a historical result or controls its run", async({page, request}) => {
  const id = "r7-proposal-identity";
  const runId = await recordedRun(request, id);
  await open(page, id, runId);
  await page.getByRole("tablist", {name: "检查器标签"}).getByRole("tab", {name: "输入 / 证据"}).click();
  await expect(page.getByLabel("已加载结果身份")).toContainText(`/ ${"m1"} / attempt 1`);
  await page.getByRole("button", {name: "生成 / 审阅计划", exact: true}).click();
  await expect(page.getByLabel("Selection context")).toContainText("Draft proposal");
  await page.getByRole("button", {name: "M1 原式管线与证据门控", exact: true}).click();
  await expect(page.getByLabel("已加载结果身份")).not.toContainText(runId);
  await expect(page.getByRole("button", {name: "继续已授权范围", exact: true})).toBeDisabled();
  await page.getByRole("tablist", {name: "中央工作区"}).getByRole("tab", {name: "阶段结果"}).click();
  await expect(page.getByText("Draft proposals have no results. Explicitly select a frozen run result above.")).toBeVisible();
  await expect(page.getByRole("heading", {name: "M1 · 科学项目结果"})).not.toBeVisible();
  await page.getByLabel("结果对象", {exact: true}).selectOption("m1");
  await expect(page.getByRole("heading", {name: "M1 · 科学项目结果"})).toBeVisible();
  await expect(page.getByLabel("已加载结果身份")).toContainText(runId);
});
