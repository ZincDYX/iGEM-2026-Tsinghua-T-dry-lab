import {test,expect} from '@playwright/test';

test('actual original M1–M4 formulas render, custom version is unvalidated and settings/Skills persist',async({page,context},testInfo)=>{
  test.setTimeout(120000);
  const loaded:string[]=[];
  page.on('response',response=>{if(response.url().includes('/assets/'))loaded.push(response.url().split('/').at(-1)!);});
  await page.goto('/');
  await expect(page.getByLabel('Project name')).toBeVisible();
  const projects=await (await context.request.get('/api/platform/projects')).json();
  const project=projects.find((value:{name:string})=>value.name==='Dependency import recovery');
  expect(project,'Run the actual dependency-import browser task first').toBeTruthy();
  await page.getByLabel('Current project',{exact:true}).selectOption(project.id);
  const workflow={id:'original-method-display',name:'Original method display only',nodes:['m1','m2','m3','m4'].map((stage,index)=>({
    id:stage,label:stage.toUpperCase(),tool_id:'project.'+stage,inputs:{project:{kind:'project',path:['scientific_project']},
      ...(index?{upstream_result:{kind:'node',node_id:'m'+index,path:['result_identity']}}:{})},depends_on:[],map:null}))};
  const response=await page.evaluate(async({project,workflow})=>{
    const response=await fetch(`/api/platform/projects/${project.id}/workflow-documents/method-display`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({workflow,expected_project_revision:project.revision})});
    return {status:response.status,text:await response.text()};
  },{project,workflow});
  expect(response.status,response.text).toBe(200);
  await page.getByRole('button',{name:'Workflow',exact:true}).click();
  await page.getByLabel('Open saved workflow').selectOption('method-display');
  const metadata=await (await context.request.get('/api/platform/methods')).json();
  const rendered:{module:string;formulas:number}[]=[];
  for(const stage of ['M1','M2','M3','M4']) {
    await page.getByLabel('Workflow graph',{exact:true}).getByRole('button',{name:'Module '+stage,exact:true}).click();
    const panel=page.getByLabel('Module method',{exact:true});
    await panel.getByRole('tab',{name:'Formulas',exact:true}).click();
    const method=metadata.find((value:{id:string})=>value.id.startsWith(stage.toLowerCase()+'-'));
    await expect(panel.getByRole('heading',{name:method.title,exact:true})).toBeVisible();
    for(const formula of method.formulas) {
      await panel.locator('summary').filter({hasText:formula.id+' · '+formula.title+' · '}).click();
    }
    await expect(panel.locator('.method-formula math')).toHaveCount(method.formulas.length);
    await expect(panel.getByRole('alert')).toHaveCount(0);
    rendered.push({module:stage,formulas:method.formulas.length});
  }
  const panel=page.getByLabel('Module method',{exact:true});
  await panel.getByLabel('Formula base method').selectOption('m4-step0-step8');
  await panel.getByLabel('Formula to revise').selectOption(metadata.find((value:{id:string})=>value.id==='m4-step0-step8').formulas[0].id);
  await panel.getByLabel('Custom formula title').fill('Browser instruction draft');
  await panel.getByLabel('Custom formula source').fill('User-authored software test, not scientific evidence');
  await panel.getByLabel('Custom formula reason').fill('Document a proposed version only, no execution');
  await panel.getByRole('button',{name:'Save separate unvalidated version',exact:true}).click();
  await expect(panel.locator('summary').filter({hasText:'Browser instruction draft — version 1, unvalidated / not executable'})).toBeVisible();
  await panel.getByLabel('Custom formula title').fill('Browser executable scalar draft');
  await panel.getByLabel('Proposed formula LaTeX').fill('x/(k+x)');
  await panel.getByLabel('Custom formula reason').fill('Independent synthetic scalar test, not an original M4 result');
  await panel.getByLabel('Executable scalar expression').fill('x/(k+x)');
  await panel.getByLabel('Formula result unit').fill('1');
  for(const [index,name,value,unit] of [[1,'x','500','nM'],[2,'k','0.5','uM']] as const){
    await panel.getByRole('button',{name:'Add formula input',exact:true}).click();
    await panel.getByLabel(`Formula input ${index} name`).fill(name);
    await panel.getByLabel(`Formula input ${index} value`).fill(value);
    await panel.getByLabel(`Formula input ${index} unit`).fill(unit);
    await panel.getByLabel(`Formula input ${index} source`).fill('Synthetic admission fixture, no workstation evaluation');
  }
  await panel.getByRole('button',{name:'Save separate unvalidated version',exact:true}).click();
  await expect(panel.locator('summary').filter({hasText:'Browser executable scalar draft — version 2, unvalidated / exploratory execution available'})).toBeVisible();
  await panel.locator('summary').filter({hasText:'Browser executable scalar draft — version 2,'}).click();
  await panel.getByRole('button',{name:'Prepare exploratory workflow',exact:true}).click();
  await expect(page.getByRole('button',{name:'Accept proposal (does not start computation)',exact:true})).toBeVisible();
  expect(await (await context.request.get('/api/platform/runs')).json()).toEqual([]);
  await page.getByRole('navigation',{name:'Workbench menus'}).getByText('Tools',{exact:true}).click();
  await page.getByRole('menuitem',{name:'Assistant Settings',exact:true}).click();
  await expect(page.getByLabel('Assistant provider')).toHaveValue('none');
  await page.getByLabel('Assistant response style').fill('Use short explanations; never approve missing evidence.');
  await page.getByRole('button',{name:'Save Assistant profile',exact:true}).click();
  await expect(page.getByText('Model disabled or not configured.',{exact:false})).toBeVisible();
  await page.getByRole('navigation',{name:'Workbench menus'}).getByText('Tools',{exact:true}).click();
  await page.getByRole('menuitem',{name:'Tools & extensions',exact:true}).click();
  await expect(page.getByRole('heading',{name:'All registered capabilities',exact:true})).toBeVisible();
  await page.getByRole('tab',{name:'Skills',exact:true}).click();
  await page.getByLabel('Import SKILL.md').setInputFiles({name:'SKILL.md',mimeType:'text/markdown',buffer:Buffer.from('---\nname: Browser instruction\ndescription: Read-only explanation\ntrigger: Review missing input\nversion: "1"\nsource: User-authored software test\nlicense: Apache-2.0\n---\nDo not invent data or grant permissions.\n')});
  await page.getByLabel('Enable instruction guidance').check();
  await page.getByRole('button',{name:'Save Skill revision',exact:true}).click();
  await expect(page.getByRole('button',{name:'Browser instruction — Enabled',exact:true})).toBeVisible();
  await page.reload();
  await page.getByRole('tab',{name:'Skills',exact:true}).click();
  await expect(page.getByRole('button',{name:'Browser instruction — Enabled',exact:true})).toBeVisible();
  expect(await (await context.request.get('/api/platform/runs')).json()).toEqual([]);
  await testInfo.attach('actual-formula-and-lazy-load-observation.json',{body:JSON.stringify({rendered,loaded:[...new Set(loaded)]},null,2),contentType:'application/json'});
});
