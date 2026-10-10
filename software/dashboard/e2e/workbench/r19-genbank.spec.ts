import {test, expect} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

test('annotated DNA import, saved design browser and unchanged export through real HTTP', async ({page, request}) => {
  const token = 'SOFTWARE_FIXTURE_SESSION_NOT_A_REAL_CREDENTIAL';
  const headers = {'X-FusionLab-Token':token};
  const api = 'http://127.0.0.1:8791/api/platform';
  const id = 'r19-genbank-software';
  const created = await request.post(api+'/projects',{headers,data:{project:{id,name:'SOFTWARE_ONLY_DNA_DESIGN'}}});
  expect(created.status()).toBe(200);
  await page.addInitScript(({token,id}) => {
    localStorage.setItem('fusionlab.project',id);
    window.__TAURI__ = {core:{invoke: async <T>(command:string) => {
      if(command === 'backend_info') return {url:'http://127.0.0.1:5191',token,mode:'local'} as T;
      if(command === 'desktop_settings') return {mode:'local',api_url:'',ca_file:'',has_access_token:false} as T;
      throw Error('UNSUPPORTED_SOFTWARE_BRIDGE');
    }}};
  }, {token,id});
  await page.goto('/');
  await page.getByLabel('Current project').selectOption(id);
  await page.getByRole('button',{name:'Import',exact:true}).click();
  const source = fs.readFileSync(path.resolve(import.meta.dirname,'../../../../tests/fixtures/genbank/software_design.gb'));
  await page.getByLabel('Import data file').setInputFiles({name:'design.gb',mimeType:'text/plain',buffer:source});
  await expect(page.getByText('Missing CDS translations remain explicit gaps;', {exact:false})).toBeVisible();
  await page.getByRole('button',{name:'Confirm import into draft',exact:true}).click();
  const designs = page.getByLabel('Annotated DNA designs');
  await expect(designs.getByRole('button',{name:'View DNA and features'})).toBeDisabled();
  await page.getByRole('button',{name:'Save',exact:true}).click();
  await page.getByText(/Draft synchronized/).waitFor();
  await designs.getByRole('button',{name:'View DNA and features'}).click();
  await expect(designs.locator('.dna-fragment')).toHaveText('ATGGCTGCTTAA');
  await expect(designs.getByRole('table')).toContainText('missing source translation');
  await expect(designs.getByRole('table')).toContainText('<0:9');
  const [download] = await Promise.all([page.waitForEvent('download'), designs.getByRole('button',{name:'Export original GenBank'}).click()]);
  expect(fs.readFileSync((await download.path())!)).toEqual(source);
  await page.reload();
  await page.getByRole('button',{name:'Import',exact:true}).click();
  await designs.getByRole('button',{name:'View DNA and features'}).click();
  await expect(designs.locator('.dna-fragment')).toHaveText('ATGGCTGCTTAA');
  expect((await(await request.get(api+'/runs?project_id='+id,{headers})).json())).toEqual([]);
});
