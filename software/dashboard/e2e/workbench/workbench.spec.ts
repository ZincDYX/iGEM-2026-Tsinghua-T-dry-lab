import {test,expect} from "@playwright/test";
import {readFile} from "node:fs/promises";
const token="SOFTWARE_FIXTURE_SESSION_NOT_A_REAL_CREDENTIAL";
const backend="http://127.0.0.1:8791/api/platform";

test("authenticated real HTTP compiler/ledger/handlers, staged control, provenance, export and frozen iteration",async({page,request},testInfo)=>{
  const errors:string[]=[];const requests:{url:string;headers:Record<string,string>}[]=[];
  page.on("pageerror",error=>errors.push(error.message));page.on("request",value=>{if(value.url().includes("/api/platform/"))requests.push({url:value.url(),headers:value.headers()});});
  expect((await request.get(`${backend}/info`)).status()).toBe(401);
  if(process.env.FUSIONLAB_TEST_BUILT==="1")await page.route("**/",async route=>{
    const response=await route.fetch();
    await route.fulfill({response,headers:{...response.headers(),"Content-Security-Policy":"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' http://127.0.0.1:*; img-src 'self' data:; object-src 'none'"}});
  });
  await page.addInitScript(({token})=>{if(!localStorage.getItem("fusionlab.project"))localStorage.setItem("fusionlab.project","software-fixture");window.__TAURI__={core:{invoke:async<T>(command:string)=>{
    if(command==="backend_info")return {url:"http://127.0.0.1:5191",token,mode:"local"} as T;
    if(command==="desktop_settings")return {mode:"local",ssh_host:"",remote_port:8780} as T;
    throw new Error("SOFTWARE_FIXTURE: unsupported native command");
  }}};},{token});
  await page.goto("/");await expect(page.getByLabel("当前项目")).toHaveValue("software-fixture");
  await page.getByLabel("研究目标").fill("SOFTWARE_FIXTURE design; not biological computation");
  await page.getByLabel("规划来源").selectOption("hybrid");
  await page.getByLabel(/允许向私有配置的模型/).check();
  await page.getByLabel("每次完成一个阶段后暂停").check();
  await page.getByRole("button",{name:"生成可审阅提案"}).click();
  await expect(page.getByRole("heading",{name:/混合规划提案/})).toBeVisible();
  const rows=page.locator(".plan-table tbody tr");await expect(rows).toHaveCount(4);
  const before=await request.get(`${backend}/runs?project_id=software-fixture`,{headers:{"X-FusionLab-Token":token}});expect(await before.json()).toEqual([]);
  await page.getByRole("button",{name:"接受提案（不启动计算）"}).click();
  await expect(page.getByRole("button",{name:"确认并运行"})).toBeEnabled();
  expect(await (await request.get(`${backend}/runs?project_id=software-fixture`,{headers:{"X-FusionLab-Token":token}})).json()).toEqual([]);
  await page.getByRole("button",{name:"确认并运行"}).click();
  await expect(rows.nth(0)).toContainText("作业完成");await expect(rows.nth(1)).toContainText("待执行");
  await expect(page.locator(".document-status")).toContainText("已暂停");
  const runs=await(await request.get(`${backend}/runs?project_id=software-fixture`,{headers:{"X-FusionLab-Token":token}})).json();expect(runs).toHaveLength(1);const runId=runs[0].id;
  const initial=await(await request.get(`${backend}/runs/${runId}/summary`,{headers:{"X-FusionLab-Token":token}})).json();
  for(let stage=1;stage<4;stage++){await page.getByRole("button",{name:"运行下一阶段",exact:true}).click();await expect(rows.nth(stage)).toContainText("作业完成");if(stage<3){await expect(page.locator(".document-status")).toContainText("已暂停");await expect(rows.nth(stage+1)).toContainText("待执行");}}
  await expect(page.locator(".document-status")).toContainText("作业完成");
  await page.getByRole("button",{name:"M4 原式管线与证据门控",exact:true}).click();
  await page.getByRole("tablist",{name:"中央工作区"}).getByRole("tab",{name:"阶段结果"}).click();
  await expect(page.getByRole("heading",{name:"M4 · 科学项目结果"})).toBeVisible();
  await expect(page.getByText(/产物 15：未提供/)).toBeVisible();await expect(page.getByLabel("四类独立状态")).toContainText("software_fixture_not_prediction");
  expect(await page.locator(".workspace-content pre").count()).toBe(0);
  const download=page.waitForEvent("download");await page.getByRole("button",{name:/授权科学导出/}).click();const result=await download;const destination=testInfo.outputPath("scientific-public-export.json");await result.saveAs(destination);
  const raw=await readFile(destination,"utf8");const exported=JSON.parse(raw);expect(exported.export_schema).toBe("scientific-public-export-v1");expect(exported.result.records[0].numerically_solved).toBe(false);expect(raw).not.toContain(token);expect(raw).not.toMatch(/[A-Z]:\\/);
  await page.screenshot({path:testInfo.outputPath("workbench-1280x850.png")});
  await page.getByRole("tablist",{name:"底部面板标签"}).getByRole("tab",{name:"Agent 行动"}).click();await expect(page.locator(".bottom-content")).toContainText("execution_requested");
  await page.getByRole("button",{name:"创建输入迭代"}).click();await expect(page.getByLabel("当前项目")).not.toHaveValue("software-fixture");
  await page.getByLabel("项目名称").fill("SOFTWARE_FIXTURE iteration draft");await expect(page.getByRole("button",{name:"确认并运行"})).toBeDisabled();
  await page.getByRole("button",{name:"保存草稿"}).click();
  await page.getByRole("tablist",{name:"检查器标签"}).getByRole("tab",{name:"输入 / 证据"}).click();
  await expect(page.getByLabel("冻结输入差异")).toContainText("name");
  await expect(page.getByLabel("冻结输入差异")).toContainText("无已绑定科学输入变化");
  expect((await(await request.get(`${backend}/runs/${runId}/summary`,{headers:{"X-FusionLab-Token":token}})).json()).snapshot_hash).toBe(initial.snapshot_hash);
  await page.reload();await expect(page.getByLabel("当前项目")).not.toHaveValue("software-fixture");
  await page.setViewportSize({width:800,height:650});await page.getByRole("button",{name:"检查器",exact:true}).click();await expect(page.locator(".workspace-center")).toBeVisible();await page.screenshot({path:testInfo.outputPath("workbench-800x650.png")});
  expect(errors).toEqual([]);expect(requests.every(value=>!value.url.includes(token))).toBe(true);expect(requests.filter(value=>!value.url.includes("/files/")).every(value=>value.headers["x-fusionlab-token"]===token)).toBe(true);
});
