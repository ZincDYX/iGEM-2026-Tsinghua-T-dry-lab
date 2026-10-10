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
  await page.getByRole('button',{name:'Confirm import into draft',exact:true}).click();
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
