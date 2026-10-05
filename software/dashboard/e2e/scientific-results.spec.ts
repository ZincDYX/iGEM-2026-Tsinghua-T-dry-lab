import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import path from "node:path";

const repository = path.resolve(import.meta.dirname, "../../..");
const backend = "http://127.0.0.1:8789/api/platform";

test("actual API generic solver and stdio M4 output render; stale approvals and drafts refuse", async ({page, request}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const pathway = JSON.parse(readFileSync(path.join(repository,"examples/workflows/user_pathway.json"),"utf8"));
  const created = await request.post(`${backend}/projects`, {data:{project:{id:`schema-e2e-${Date.now()}`,name:"software_fixture UI contracts",pathway}}});
  const project = await created.json();
  expect(created.ok()).toBeTruthy();
  const planned = await request.post(`${backend}/plans`, {data:{project_id:project.id,goal:"pathway_simulation"}});
  const plan = await planned.json();
  const generic = await request.post(`${backend}/runs`, {data:{project_id:project.id,workflow:plan.workflow,confirmation:plan.confirmation}});
  expect(generic.status()).toBe(202);
  const genericRun = await generic.json();
  await expect.poll(async () => (await (await request.get(`${backend}/runs/${genericRun.id}`)).json()).status).toBe("succeeded");
  await page.addInitScript(({projectId,runId}) => {
    localStorage.setItem("fusionlab.project",projectId); localStorage.setItem("fusionlab.run",runId);
  },{projectId:project.id,runId:genericRun.id});
  await page.goto("/");
  await page.getByRole("button",{name:/分析结果/}).click();
  await expect(page.getByRole("heading",{name:"反应通路稳态",exact:true})).toBeVisible();
  await expect(page.getByText("generic_two_phase_steady_state",{exact:false}).first()).toBeVisible();

  const python = process.env.FUSIONLAB_PYTHON ?? path.join(repository,".venv/bin/python");
  // Only executed in the server release environment. Existing explicitly synthetic
  // scientific fixture supplies INPUTS; actual HTTP -> stdio MCP produces OUTPUTS.
  const args = JSON.parse(execFileSync(python,["-c",
    "import json,sys;sys.path.insert(0,'tests');from test_m4_markdown_contract import _input;print(json.dumps(_input().model_dump(mode='json')))"],{cwd:repository,encoding:"utf8"}));
  const workflow = {id:"m4-e2e",name:"M4 actual MCP software_fixture",version:"1",nodes:[{
    id:"pathway",label:"arbitrary node name",tool_id:"igem.m4.solve_steady_state",
    inputs:{inputs:{kind:"literal",value:args}}}]};
  const reviewed = await (await request.post(`${backend}/plans/custom`,{data:{project_id:project.id,workflow}})).json();
  const m4 = await request.post(`${backend}/runs`,{data:{project_id:project.id,workflow,confirmation:reviewed.confirmation}});
  expect(m4.status()).toBe(202);
  const m4Run = await m4.json();
  await expect.poll(async () => (await (await request.get(`${backend}/runs/${m4Run.id}`)).json()).status).toBe("succeeded");
  await page.evaluate((id) => localStorage.setItem("fusionlab.run",id),m4Run.id);
  // The original addInitScript would overwrite run storage on reload; install the
  // latest run after loading, then open its real persisted history entry.
  await page.getByRole("button",{name:/分析历史/}).click();
  await page.reload();
  await page.getByRole("button",{name:/分析历史/}).click();
  await page.getByRole("button",{name:"查看",exact:true}).first().click();
  await expect(page.getByRole("heading",{name:"M4 原式稳态",exact:true})).toBeVisible();
  await expect(page.getByText(/科学状态：valid/)).toBeVisible();
  await page.screenshot({path:"test-results/m4-real-mcp.png",fullPage:true});
  const saved = await request.post(`${backend}/projects`,{data:{project:{...project,description:"different revision"},expected_revision:project.revision}});
  expect(saved.ok()).toBeTruthy();
  expect((await request.post(`${backend}/runs`,{data:{project_id:project.id,workflow,confirmation:reviewed.confirmation}})).status()).toBe(409);
  await page.reload();
  await page.getByRole("button",{name:/分析流程/}).click();
  await page.getByLabel("选择目标").selectOption("pathway_simulation");
  await page.getByRole("button",{name:"生成流程",exact:true}).click();
  await expect(page.getByRole("button",{name:"确认并运行",exact:true})).toBeEnabled();
  await page.getByRole("button",{name:/项目数据/}).click();
  await page.getByLabel("pH",{exact:true}).fill("5");
  await page.getByRole("button",{name:/分析流程/}).click();
  await expect(page.getByRole("button",{name:"确认并运行",exact:true})).toHaveCount(0);
  expect(errors).toEqual([]);
});
