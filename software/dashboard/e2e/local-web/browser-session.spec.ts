import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import {ready,rename,commitImport} from './helpers';

test('installed same-origin Web opens Inputs, authenticates without token entry and preserves GenBank',async({page,context})=>{
  // Software/HTTP import only; numerical computation is tested on a server.
  const errors:string[]=[];
  const importStatuses:number[]=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('response',response=>{if(/\/projects\/[^/]+\/imports$/.test(new URL(response.url()).pathname))importStatuses.push(response.status());});
  await page.goto('/');
  await expect(page.getByRole('tab',{name:'Inputs',exact:true})).toHaveAttribute('aria-selected','true');
  expect(await page.getByRole('tablist',{name:'Workspace documents'}).getByRole('tab').count()).toBe(3);
  await ready(page);
  const cookies=await context.cookies();
  const session=cookies.find(item=>item.name.startsWith('fusionlab_session_'));
  expect(session?.httpOnly).toBe(true);
  expect(await page.evaluate(()=>document.cookie)).not.toContain('fusionlab_session_');
  await rename(page,'Web import acceptance');
  const source=fs.readFileSync(path.resolve(import.meta.dirname,'../../../../tests/fixtures/genbank/software_design.gb'));
  await page.getByLabel('Import data file').setInputFiles({name:'original.gb',mimeType:'text/plain',buffer:source});
  await expect(page.getByText('Missing CDS translations remain explicit gaps;',{exact:false})).toBeVisible();
  await expect(page.getByRole('button',{name:'Import',exact:true})).toBeVisible();

  await commitImport(page);
  await expect(page.getByLabel('Import transaction preview')).toHaveCount(0);
  await page.getByText('File',{exact:true}).click();
  await page.getByRole('menuitem',{name:'Save',exact:true}).click();
  await expect(page.locator('.workbench-footer')).not.toContainText('Unsaved');
  await page.reload();
  await page.getByText('File',{exact:true}).click();await page.getByRole('menuitem',{name:'Rename project',exact:true}).click();
  await expect(page.getByLabel('Project name')).toHaveValue('Web import acceptance');
  await page.getByRole('button',{name:'Cancel',exact:true}).click();
  await page.getByRole('button',{name:'original.gb',exact:true}).click();
  const designs=page.getByLabel('Annotated DNA designs');
  await designs.getByRole('button',{name:'View DNA and features'}).click();
  await expect(designs.locator('.dna-fragment')).toHaveText('ATGGCTGCTTAA');
  const [download]=await Promise.all([page.waitForEvent('download'),designs.getByRole('button',{name:'Export original GenBank'}).click()]);
  expect(fs.readFileSync((await download.path())!)).toEqual(source);
  const missing=await context.request.get('/assets/does-not-exist.js');
  expect(missing.status()).toBe(404);
  expect(errors).toEqual([]);
  expect(importStatuses.length).toBeGreaterThan(0);
  expect(importStatuses.every(status=>status>=200&&status<300)).toBe(true);
  await expect(page.getByText('Saved import previews could not be loaded.',{exact:false})).toHaveCount(0);
  await page.screenshot({path:'test-results/local-web-inputs.png',fullPage:false});
});

test('unfinished ambiguous import survives browser restart and requires a molecule decision',async({page,context})=>{
  await page.goto('/');
  await ready(page);
  const projectId=await page.getByLabel('Current project',{exact:true}).inputValue();
  const initial=await (await context.request.get(`/api/platform/projects/${projectId}`)).json();
  await rename(page,'DNA import recovery');
  await page.getByLabel('Import data file').setInputFiles({name:'ambiguous.fa',mimeType:'text/plain',buffer:Buffer.from('>dna-source\nACGTACGT\n')});
  await expect(page.getByRole('button',{name:'Import objects',exact:true})).toBeDisabled();
  await page.reload();
  await page.getByRole('button',{name:'Resume saved import 1',exact:true}).click();
  await page.getByLabel('Molecule type for ambiguous.fa').selectOption('DNA');
  await expect(page.getByRole('button',{name:'Import objects',exact:true})).toBeEnabled();
  await commitImport(page);
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
  await rename(page,'Dependency import recovery');
  const config={schema_version:'project-config-v1',config:{inputs:{protein_fasta:'study/proteins.faa',enzymes:[],scaffolds:[],linkers:[]},
    execution:{mode:'real',allow_assumptions:false},prepared_through:'m1',run:{output_dir:'outputs'}}};
  await page.getByLabel('Import data file').setInputFiles({name:'project.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(config))});
  await expect(page.getByText('Add the referenced file to this import:',{exact:false})).toBeVisible();
  await page.getByRole('button',{name:'Add file: study/proteins.faa',exact:true}).click();
  await page.getByLabel('Add missing import files').setInputFiles({name:'proteins.faa',mimeType:'text/plain',buffer:Buffer.from('>actual-id\nMKWVTFISLLFLFSSAYS\n')});
  await expect(page.getByRole('button',{name:'Import objects',exact:true})).toBeEnabled();
  await commitImport(page);
  await expect(page.getByLabel('Import transaction preview')).toHaveCount(0);
  const projects=await (await context.request.get('/api/platform/projects')).json();
  const saved=projects.find((p:{name:string})=>p.name==='Dependency import recovery');
  expect(saved.scientific_project.config.prepared_through).toBe('m1');
  expect(saved.scientific_project.config.inputs.protein_fasta).toMatch(/^asset:/);
  expect(await (await context.request.get('/api/platform/runs')).json()).toEqual([]);
});
