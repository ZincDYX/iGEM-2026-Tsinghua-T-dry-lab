import {test,expect} from '@playwright/test';

test('owned server executes reviewed scalar version and renders frozen unvalidated result',async({page,context})=>{
  // This connected suite is run against an authorized server acceptance
  // workspace, never a workstation calculator or a real user project.
  await page.goto('/');
  await expect(page.getByRole('tab',{name:'Inputs',exact:true})).toBeVisible();
  await page.getByText('File',{exact:true}).click();
  await page.getByRole('menuitem',{name:'New project',exact:true}).click();
  const name='Custom formula server acceptance '+Date.now();
  await page.getByRole('button',{name:'Rename project',exact:true}).click();
  await page.getByLabel('Project name').fill(name);
  await page.getByText('File',{exact:true}).click();
  await page.getByRole('menuitem',{name:'Save',exact:true}).click();
  await expect(page.getByText(/Draft synchronized/)).toBeVisible();
  const projects=await (await context.request.get('/api/platform/projects')).json();
  const project=projects.find((p:{name:string})=>p.name===name);
  expect(project).toBeTruthy();
  const method=(await (await context.request.get('/api/platform/methods')).json()).find((m:{id:string})=>m.id==='m3-s1-e10');
    const saved=await page.evaluate(async({project,method})=>{
      const response=await fetch(`/api/platform/projects/${project.id}/method-drafts`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({base_method_id:method.id,base_version:method.version,formula_id:'E1',title:'Server scalar ratio',latex:'x/(k+x)',reason:'Independent synthetic mathematical oracle, not biological evidence',source_reference:'Exact half ratio with SI conversion',expected_project_revision:project.revision,execution_spec:{expression:'x/(k+x)',output_unit:'1',variables:{x:{value:500,unit:'nM',source:'Synthetic analytic oracle'},k:{value:.5,unit:'uM',source:'Synthetic analytic oracle'}}}})});
      const draft=await response.json();
      const prepared=await fetch(`/api/platform/projects/${project.id}/method-drafts/${draft.id}/workflow`,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
      const workflow=await prepared.json();
      const doc=await fetch(`/api/platform/projects/${project.id}/workflow-documents/formula-display`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expected_project_revision:project.revision,workflow})});
      return {status:doc.status,text:await doc.text()};
    },{project,method});
  expect(saved.status,saved.text).toBe(200);
  await page.getByRole('tab',{name:'Workflow',exact:true}).click();
  await page.getByLabel('Open saved workflow').selectOption('formula-display');
  await expect(page.getByLabel('Workflow graph',{exact:true}).getByRole('button',{name:'Module Server scalar ratio',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Review plan',exact:true}).click();
  await page.getByRole('button',{name:'Accept proposal (does not start computation)',exact:true}).click();
  await expect(page.getByRole('button',{name:'Start run',exact:true})).toBeEnabled();
  await page.getByRole('button',{name:'Start run',exact:true}).click();
  await expect(page.getByText('Job completed',{exact:true}).first()).toBeVisible();
  await page.getByRole('tab',{name:'Results',exact:true}).click();
  await page.getByLabel('Result object',{exact:true}).selectOption('formula');
  await expect(page.getByLabel('Custom formula result')).toContainText('0.5 1');
  await expect(page.getByLabel('Custom formula result')).toContainText('scientifically unvalidated');
  await page.reload();
  await page.getByRole('tab',{name:'Results',exact:true}).click();
  await page.getByLabel('Result object',{exact:true}).selectOption('formula');
  await expect(page.getByLabel('Custom formula result')).toContainText('0.5 1');
});
