import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

test('installed same-origin Web opens Inputs, authenticates without token entry and preserves GenBank',async({page,context})=>{
  // Software/HTTP import only; numerical computation is tested on a server.
  const errors:string[]=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('tab',{name:'Inputs',exact:true})).toHaveAttribute('aria-selected','true');
  expect(await page.getByRole('tablist',{name:'Workspace documents'}).getByRole('tab').count()).toBe(1);
  await expect(page.getByLabel('Project name')).toBeVisible();
  const cookies=await context.cookies();
  const session=cookies.find(item=>item.name.startsWith('fusionlab_session_'));
  expect(session?.httpOnly).toBe(true);
  expect(await page.evaluate(()=>document.cookie)).not.toContain('fusionlab_session_');
  await page.getByLabel('Project name').fill('Web import acceptance');
  const source=fs.readFileSync(path.resolve(import.meta.dirname,'../../../../tests/fixtures/genbank/software_design.gb'));
  await page.getByLabel('Import data file').setInputFiles({name:'original.gb',mimeType:'text/plain',buffer:source});
  await expect(page.getByText('Missing CDS translations remain explicit gaps;',{exact:false})).toBeVisible();
  await expect(page.getByLabel('Biological data')).toBeVisible();
  await expect(page.getByLabel('Analysis plan and configuration')).toBeVisible();
  await page.getByRole('button',{name:'Confirm import',exact:true}).click();
  await expect(page.getByLabel('Import transaction preview')).toHaveCount(0);
  await page.getByText('File',{exact:true}).click();
  await page.getByRole('menuitem',{name:'Save',exact:true}).click();
  await expect(page.getByText(/Draft synchronized/)).toBeVisible();
  await page.reload();
  await expect(page.getByLabel('Project name')).toHaveValue('Web import acceptance');
  const designs=page.getByLabel('Annotated DNA designs');
  await designs.getByRole('button',{name:'View DNA and features'}).click();
  await expect(designs.locator('.dna-fragment')).toHaveText('ATGGCTGCTTAA');
  const [download]=await Promise.all([page.waitForEvent('download'),designs.getByRole('button',{name:'Export original GenBank'}).click()]);
  expect(fs.readFileSync((await download.path())!)).toEqual(source);
  const missing=await context.request.get('/assets/does-not-exist.js');
  expect(missing.status()).toBe(404);
  expect(errors).toEqual([]);
  await page.screenshot({path:'test-results/local-web-inputs.png',fullPage:false});
});

test('unfinished ambiguous import survives browser restart and requires a molecule decision',async({page,context})=>{
  await page.goto('/');
  await expect(page.getByLabel('Project name')).toBeVisible();
  const projectId=await page.getByLabel('Current project',{exact:true}).inputValue();
  const initial=await (await context.request.get(`/api/platform/projects/${projectId}`)).json();
  await page.getByLabel('Project name').fill('DNA import recovery');
  await page.getByLabel('Import data file').setInputFiles({name:'ambiguous.fa',mimeType:'text/plain',buffer:Buffer.from('>dna-source\nACGTACGT\n')});
  await expect(page.getByRole('button',{name:'Confirm import',exact:true})).toBeDisabled();
  await page.reload();
  await page.getByRole('button',{name:'Resume saved import 1',exact:true}).click();
  await page.getByLabel('Molecule type for ambiguous.fa').selectOption('DNA');
  await page.getByRole('button',{name:'Update preview with confirmed roles'}).click();
  await expect(page.getByRole('button',{name:'Confirm import',exact:true})).toBeEnabled();
  await page.getByRole('button',{name:'Confirm import',exact:true}).click();
  await expect(page.getByLabel('Import transaction preview')).toHaveCount(0);
  const projects=await (await context.request.get('/api/platform/projects')).json();
  const saved=projects.find((p:{name:string})=>p.name==='DNA import recovery');
  expect(saved.sequences).toEqual(initial.sequences);
  expect(saved.sequences.some((sequence:{id:string})=>sequence.id==='dna-source')).toBe(false);
  expect(saved.files.some((file:{name:string})=>file.name==='ambiguous.fa')).toBe(true);
  expect(await (await context.request.get('/api/platform/runs')).json()).toEqual([]);
});

test('missing config dependency can be appended to the saved transaction without reupload',async({page,context})=>{
  await page.goto('/');
  await page.getByLabel('Project name').fill('Dependency import recovery');
  const config={schema_version:'project-config-v1',config:{inputs:{protein_fasta:'study/proteins.faa',enzymes:[],scaffolds:[],linkers:[]},
    execution:{mode:'real',allow_assumptions:false},prepared_through:'m1'}};
  await page.getByLabel('Import data file').setInputFiles({name:'project.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(config))});
  await expect(page.getByText('Add the referenced file to this import:',{exact:false})).toBeVisible();
  await page.getByLabel('Relative filename for one missing file (optional)').fill('study/proteins.faa');
  await page.getByLabel('Add missing import files').setInputFiles({name:'proteins.faa',mimeType:'text/plain',buffer:Buffer.from('>actual-id\nMKWVTFISLLFLFSSAYS\n')});
  await expect(page.getByRole('button',{name:'Confirm import',exact:true})).toBeEnabled();
  await page.getByRole('button',{name:'Confirm import',exact:true}).click();
  await expect(page.getByLabel('Import transaction preview')).toHaveCount(0);
  const projects=await (await context.request.get('/api/platform/projects')).json();
  const saved=projects.find((p:{name:string})=>p.name==='Dependency import recovery');
  expect(saved.scientific_project.config.prepared_through).toBe('m1');
  expect(saved.scientific_project.config.inputs.protein_fasta).toMatch(/^asset:/);
  expect(await (await context.request.get('/api/platform/runs')).json()).toEqual([]);
});
