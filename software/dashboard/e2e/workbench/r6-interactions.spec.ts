import {test,expect,type Page} from "@playwright/test";
import path from "node:path";
const token="SOFTWARE_FIXTURE_SESSION_NOT_A_REAL_CREDENTIAL";
const backend="http://127.0.0.1:8791/api/platform";
const headers={"X-FusionLab-Token":token};
async function open(page:Page,id="software-fixture"){
  await page.addInitScript(({token,id})=>{localStorage.setItem("fusionlab.project",id);window.__TAURI__={core:{invoke:async<T>(command:string)=>{
    if(command==="backend_info")return {url:"http://127.0.0.1:5191",token,mode:"local"} as T;
    if(command==="desktop_settings")return {mode:"local",ssh_host:"",remote_port:8780} as T;
    throw new Error("SOFTWARE_FIXTURE unsupported bridge");
  }}};},{token,id});
  await page.goto("/");await expect(page.getByLabel("当前项目")).toHaveValue(id);
}
test("JSON draft survives tabs, invalid apply and project-switch cancellation",async({page})=>{
  await open(page);await page.getByRole("button",{name:"导入 / 检查输入"}).click();
  await page.getByRole("button",{name:"编辑完整公开输入 JSON"}).click();
  const editor=page.getByLabel("公开输入 JSON");const draft=JSON.parse(await editor.inputValue());draft.name="SOFTWARE_FIXTURE_UNAPPLIED";
  const text=JSON.stringify(draft,null,2);await editor.fill(text);
  for(const tab of ["工作流 / 计划","阶段结果","输入 / 证据"]){await page.getByRole("tablist",{name:"中央工作区"}).getByRole("tab",{name:tab,exact:true}).click();}
  await expect(editor).toHaveValue(text);await expect(page.getByRole("button",{name:"保存草稿"})).toBeDisabled();
  await editor.fill("{invalid fixture JSON");await page.getByRole("button",{name:"应用已校验草稿"}).click();
  await expect(page.getByRole("alert")).toBeVisible();await expect(editor).toHaveValue("{invalid fixture JSON");
  page.once("dialog",dialog=>dialog.dismiss());await page.getByRole("button",{name:"新建项目"}).click();await expect(editor).toHaveValue("{invalid fixture JSON");
  await editor.fill(text);await page.getByRole("button",{name:"应用已校验草稿"}).click();await expect(page.getByLabel("项目名称")).toHaveValue(draft.name);
  await page.getByRole("button",{name:"保存草稿"}).click();await expect(page.locator(".document-status")).toContainText("草稿已同步");
  page.once("dialog",dialog=>dialog.accept());await page.getByRole("button",{name:"新建项目"}).click();
  await page.getByRole("button",{name:"编辑完整公开输入 JSON"}).click();expect(await editor.inputValue()).not.toContain("SOFTWARE_FIXTURE_UNAPPLIED");
});
test("three pointer/keyboard splitters persist view only and narrow drawer leaves controls reachable",async({page,request})=>{
  await open(page);const before=await(await request.get(`${backend}/projects/software-fixture`,{headers})).json();
  for(const[name,dx,dy]of [["项目栏",50,0],["检查器",-50,0],["底部面板",0,-40]] as const){
    const splitter=page.getByRole("separator",{name,exact:true});const original=Number(await splitter.getAttribute("aria-valuenow"));const box=(await splitter.boundingBox())!;
    await page.mouse.move(box.x+box.width/2,box.y+box.height/2);await page.mouse.down();await page.mouse.move(box.x+box.width/2+dx,box.y+box.height/2+dy,{steps:5});
    expect(await page.evaluate(()=>localStorage.getItem("fusionlab.layout"))).toBeNull(); // pointermove never persists
    await page.mouse.up();expect(Number(await splitter.getAttribute("aria-valuenow"))).toBeGreaterThan(original);
    await splitter.focus();const key=name==="底部面板"?"ArrowUp":name==="检查器"?"ArrowLeft":"ArrowRight";
    const current=Number(await splitter.getAttribute("aria-valuenow"));await page.keyboard.press(key);expect(Number(await splitter.getAttribute("aria-valuenow"))).toBeGreaterThan(current);
    // The next drag must not assert empty storage: clear only optional view state.
    await page.evaluate(()=>localStorage.removeItem("fusionlab.layout"));
  }
  await page.getByRole("separator",{name:"项目栏",exact:true}).focus();await page.keyboard.press("ArrowLeft");
  const saved=await page.evaluate(()=>localStorage.getItem("fusionlab.layout"));await page.reload();await expect(page.getByLabel("当前项目")).toHaveValue("software-fixture");
  expect(await page.evaluate(()=>localStorage.getItem("fusionlab.layout"))).toBe(saved);
  expect(await(await request.get(`${backend}/projects/software-fixture`,{headers})).json()).toEqual(before);
  await page.setViewportSize({width:800,height:600});await expect(page.getByLabel("研究检查器")).not.toBeVisible();
  await page.getByRole("button",{name:"检查器",exact:true}).click();await expect(page.getByRole("button",{name:"关闭检查器"})).toBeVisible();
  const drawer=(await page.getByLabel("研究检查器").boundingBox())!,toolbar=(await page.getByLabel("项目与执行控制").boundingBox())!;
  expect(drawer.y).toBeGreaterThanOrEqual(toolbar.y+toolbar.height);await page.getByRole("button",{name:"关闭检查器"}).click();
  expect((await page.locator(".workspace-center").boundingBox())!.width).toBeGreaterThanOrEqual(300);
});
test("paused UI cancel is terminal and inspector result stays with selected stage off the result tab",async({page,request})=>{
  const id="software-fixture-r6-execution";
  const preview=await(await request.post(`${backend}/scientific-projects/upload-preview`,{headers,data:{config_filename:"project.yaml",files:[
    {filename:"project.yaml",content:JSON.stringify({run:{id:"SOFTWARE_FIXTURE"},inputs:{protein_fasta:"fixture.fasta",enzymes:[],scaffolds:[],linkers:[]}})},
    {filename:"fixture.fasta",content:">SOFTWARE_FIXTURE_NOT_BIOLOGICAL\nMAGSGS\n"}]} })).json();
  expect((await request.post(`${backend}/projects`,{headers,data:{project:{id,name:"SOFTWARE_FIXTURE_r6",scientific_project:preview.scientific_project}}})).status()).toBe(200);
  await open(page,id);await page.getByLabel("研究目标").fill("SOFTWARE_FIXTURE_ONLY");
  await page.getByLabel("每次完成一个阶段后暂停").check();await page.getByRole("button",{name:"生成可审阅提案"}).click();
  await page.getByRole("button",{name:"接受提案（不启动计算）"}).click();await page.getByRole("button",{name:"确认并运行"}).click();
  await expect(page.locator(".document-status")).toContainText("已暂停");await expect(page.getByRole("button",{name:"取消运行",exact:true})).toBeEnabled();
  await page.getByRole("button",{name:"取消运行",exact:true}).click();await expect(page.locator(".document-status")).toContainText("已取消");
  await expect(page.getByRole("button",{name:"继续已授权范围"})).toBeDisabled();
  const value=await(await request.post(`${backend}/proposals`,{headers,data:{project_id:id,goal:"scientific_pipeline"}})).json();
  await request.post(`${backend}/proposals/${value.id}/decision`,{headers,data:{action:"accept"}});
  await request.post(`${backend}/runs`,{headers,data:{project_id:value.project_id,workflow:value.workflow,confirmation:value.confirmation,proposal_id:value.id}});
  await page.reload();await expect(page.getByRole("button",{name:/M1–M5 科学项目管线 · r/}).first()).toBeVisible();
  await page.getByRole("button",{name:/M1–M5 科学项目管线 · r/}).first().click();
  await expect(page.locator(".document-status")).toContainText("作业完成");
  await page.getByRole("button",{name:"M4 原式管线与证据门控",exact:true}).click();
  await page.getByRole("tablist",{name:"中央工作区"}).getByRole("tab",{name:"阶段结果"}).click();await expect(page.getByRole("heading",{name:"M4 · 科学项目结果"})).toBeVisible();
  await page.getByRole("tablist",{name:"中央工作区"}).getByRole("tab",{name:"工作流 / 计划"}).click();
  await page.getByRole("button",{name:"M1 原式管线与证据门控",exact:true}).click();
  await page.getByRole("tablist",{name:"检查器标签"}).getByRole("tab",{name:"输入 / 证据"}).click();
  await expect(page.getByLabel("已加载结果身份")).toContainText("/ m1 / attempt 1");
  await page.locator(".workspace-inspector").getByText("当前结果页的原值 / 单位 / 来源",{exact:true}).click();
  await expect(page.locator(".workspace-inspector pre").last()).toContainText('"module": "m1"');
  await expect(page.locator(".workspace-inspector pre").last()).not.toContainText('"module": "m4"');
});
test("real folder upload retains configs/data siblings and synchronizes only an unchosen science entry",async({page})=>{
  await open(page);await page.getByRole("button",{name:"新建项目"}).click();
  await expect(page.getByLabel("计算入口",{exact:true})).toHaveValue("fusion_screen");
  const directory=path.resolve(import.meta.dirname,"../../../../tests/fixtures/workbench_bundle");
  await page.getByLabel("科学项目文件夹").setInputFiles(directory);
  await page.getByLabel("科学项目入口").selectOption("configs/project.yaml");
  await page.getByRole("button",{name:"检查科学输入"}).click();await expect(page.getByText(/已校验 typed 配置，绑定/)).toBeVisible();
  await page.getByRole("button",{name:"确认科学配置到草稿"}).click();await expect(page.getByLabel("计算入口",{exact:true})).toHaveValue("scientific_pipeline");
  await page.getByLabel("计算入口",{exact:true}).selectOption("fusion_screen");
  await page.getByRole("button",{name:"保存草稿"}).click();await expect(page.locator(".document-status")).toContainText("草稿已同步");
  await expect(page.getByLabel("计算入口",{exact:true})).toHaveValue("fusion_screen");
  await page.getByRole("button",{name:"检查已保存输入缺项"}).click();
  const precheck=page.getByLabel("已保存科学输入预检");
  await expect(precheck).toContainText("explicit_construct_definitions");
  await expect(precheck).toContainText("wetlab_results_file");
  await expect(precheck).toContainText("不是完整候选门控或运行许可");
});
