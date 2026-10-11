import {test, expect} from '@playwright/test';

test('real persisted workflow Graph/List, fan-out, rejected edits and reopened selection',async({page,context})=>{
  // Only software graph/approval metadata. No numerical/scientific tool is run.
  await page.goto('/');
  await expect(page.getByLabel('Project name')).toBeVisible();
  const projects=await (await context.request.get('/api/platform/projects')).json();
  const project=projects[0];
  const workflow={id:'browser-graph',name:'Browser workflow acceptance',nodes:[
    {id:'a',label:'Original inputs',tool_id:'workflow.gather',inputs:{results:{kind:'literal',value:[]}}},
    {id:'b',label:'First branch',tool_id:'workflow.gather',inputs:{results:{kind:'node',node_id:'a',path:['results']}}},
    {id:'c',label:'Second branch',tool_id:'workflow.gather',inputs:{results:{kind:'node',node_id:'a',path:['results']}}},
  ]};
  const endpoint=`/api/platform/projects/${project.id}/workflow-documents/browser-acceptance`;
  const created=await page.evaluate(async ({url,data})=>{
    const response=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    return {status:response.status,body:await response.text()};
  },{url:endpoint,data:{workflow,expected_project_revision:project.revision}});
  expect(created.status,created.body).toBe(200);
  await page.getByRole('button',{name:'Workflow',exact:true}).click();
  await page.getByLabel('Open saved workflow').selectOption('browser-acceptance');
  const graph=page.getByLabel('Workflow graph', {exact:true});
  await expect(graph.locator('path[data-from="a"]')).toHaveCount(2);
  await graph.getByRole('button',{name:'Module Second branch'}).click();
  await expect(page.getByRole('button',{name:'List',exact:true})).toBeEnabled();
  await page.getByRole('button',{name:'List',exact:true}).click();
  await expect(page.getByRole('button',{name:'Second branch',exact:true})).toHaveAttribute('aria-pressed','true');
  let saved=await (await context.request.get(endpoint)).json();
  expect(saved.selected_node_id).toBe('c'); expect(saved.view).toBe('list'); expect(saved.semantic_revision).toBe(1);
  await page.reload();
  await page.getByLabel('Open saved workflow').selectOption('browser-acceptance');
  await expect(page.getByRole('button',{name:'Second branch',exact:true})).toHaveAttribute('aria-pressed','true');
  await page.getByRole('button',{name:'Graph',exact:true}).click();
  await expect(graph.getByRole('button',{name:'Module Second branch'})).toBeEnabled();
  await graph.getByRole('button',{name:'Module Second branch'}).focus();
  await page.keyboard.press('ArrowRight');
  await expect.poll(async()=> (await (await context.request.get(endpoint)).json()).layout.c?.x).toBe(294);
  const moved=graph.getByRole('button',{name:'Module Second branch'});
  const box=(await moved.boundingBox())!;
  await page.mouse.move(box.x+40,box.y+20); await page.mouse.down();
  await page.mouse.move(box.x+10,box.y+30,{steps:5}); await page.mouse.up();
  await expect.poll(async()=> (await (await context.request.get(endpoint)).json()).layout.c?.x).toBe(264);
  expect((await (await context.request.get(endpoint)).json()).semantic_revision).toBe(1);
  await page.getByLabel('Upstream module').selectOption('c');
  await page.getByLabel('Downstream module').selectOption('a');
  await page.getByRole('button',{name:'Connect modules'}).click();
  await expect(page.getByRole('alert')).toContainText('circular dependency');
  saved=await (await context.request.get(endpoint)).json(); expect(saved.semantic_revision).toBe(1);
  await expect(graph.getByRole('button',{name:'Module Original inputs'})).toBeEnabled();
  await graph.getByRole('button',{name:'Module Original inputs'}).click();
  await expect(page.getByRole('button',{name:'Delete selected module'})).toBeEnabled();
  await expect(page.getByText(/Removing it affects:/)).toContainText('First branch, Second branch');
  await page.getByRole('button',{name:'Delete selected module'}).click();
  await expect(page.getByRole('alert')).toContainText('removed or unknown upstream');
  await expect(graph.getByRole('button',{name:'Module Original inputs'})).toBeVisible();
  await graph.getByRole('button',{name:'Module Second branch'}).click();
  await expect(page.getByRole('button',{name:'Delete selected module'})).toBeEnabled();
  await page.getByRole('button',{name:'Delete selected module'}).click();
  await expect(graph.getByRole('button',{name:'Module Second branch'})).toHaveCount(0);
  saved=await (await context.request.get(endpoint)).json(); expect(saved.semantic_revision).toBe(2);
  expect(saved.workflow.nodes.map((n:{id:string})=>n.id)).toEqual(['a','b']);
  expect(await (await context.request.get('/api/platform/runs')).json()).toEqual([]);
  await page.locator('.workspace-content').evaluate(element=>element.scrollTop=0);
  await expect(page.getByLabel('Workflow run controls').getByRole('button').first()).toBeVisible();
  await page.screenshot({path:'test-results/workflow-persisted-graph.png',fullPage:true});
});
