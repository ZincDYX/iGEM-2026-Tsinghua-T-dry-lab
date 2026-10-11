import {test, expect} from '@playwright/test';
import fs from 'node:fs';

// Real authorized coordinate files and actual Molstar/WebGL. This is display
// acceptance, not a scientific geometry/structure-prediction calculation.
const pdb = process.env.FUSIONLAB_STRUCTURE_PDB;
const cif = process.env.FUSIONLAB_STRUCTURE_CIF;
test.skip(!pdb || !cif, 'Provide actual PDB and mmCIF files; no synthetic coordinate substitute.');

async function importStructure(page: import('@playwright/test').Page, filename: string, source: string) {
  await page.getByRole('button',{name:'Inputs',exact:true}).click();
  await page.getByLabel('Import data file').setInputFiles({name:filename,mimeType:'text/plain',buffer:fs.readFileSync(source)});
  await expect(page.getByRole('heading',{name:filename,exact:true})).toBeVisible();
  const duplicate = page.getByLabel(`Duplicate: ${filename}`,{exact:true});
  if (await duplicate.count()) {
    await duplicate.selectOption({label:'Keep as new version'});
    await expect(duplicate).toHaveValue('new_version');
  }
  await page.getByRole('button',{name:'Confirm import',exact:true}).click();
  await expect(page.getByLabel('Import transaction preview')).toHaveCount(0);
}
async function openResources(page: import('@playwright/test').Page) {
  await page.getByText('View',{exact:true}).click();
  await page.getByRole('menuitem',{name:'Artifacts',exact:true}).click();
}

test('real PDB/mmCIF rotate, image export, file switch and twenty GPU lifecycle cycles',async({page,context},testInfo)=>{
  test.setTimeout(300000);
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    const seen = new WeakSet<object>();
    const ledger: {created: number; deleted: number; releasedByContext: number; kind: string}[] = [];
    Object.assign(window,{fusionlabGlLedger:ledger});
    HTMLCanvasElement.prototype.getContext = function(...args: Parameters<typeof original>) {
      const ctx = original.apply(this,args) as unknown as Record<string, (...args: unknown[]) => unknown> | null;
      if (ctx && String(args[0]).includes('webgl') && !seen.has(ctx)) {
        seen.add(ctx);
        for (const kind of ['Buffer','Texture','Program','Shader','Framebuffer','Renderbuffer']) {
          const row = {created:0,deleted:0,releasedByContext:0,kind}; ledger.push(row);
          const handles = new Set<unknown>();
          // A native context-loss event invalidates remaining handles even
          // when the library does not call delete on every transient resource.
          this.addEventListener('webglcontextlost', () => {
            row.releasedByContext += handles.size; handles.clear();
          });
          const create = ctx['create'+kind], remove = ctx['delete'+kind];
          ctx['create'+kind] = function(...values) {const value=create.apply(ctx,values); if (value) {handles.add(value); row.created++;} return value;};
          ctx['delete'+kind] = function(...values) {if (handles.delete(values[0])) row.deleted++; return remove.apply(ctx,values);};
        }
      }
      return ctx as ReturnType<typeof original>;
    } as typeof original;
  });
  const errors: string[] = [];
  page.on('pageerror',error => errors.push(error.message));
  const started = Date.now();
  await page.goto('/');
  await expect(page.getByRole('button',{name:'Rename project',exact:true})).toBeVisible();
  await importStructure(page,'actual.pdb',pdb!);
  await importStructure(page,'actual.cif',cif!);
  await openResources(page);
  await page.getByRole('button',{name:'actual.pdb · structure',exact:true}).click();
  const viewport = page.locator('.structure-canvas');
  await expect(viewport).toHaveAttribute('data-state','ready',{timeout:30000});
  await expect(page.getByLabel('Chain',{exact:true})).toHaveValue('A');
  await expect(page.getByText('B-factor is not pLDDT.',{exact:false})).toBeVisible();
  const before = await viewport.screenshot();
  const box = (await viewport.boundingBox())!;
  await page.mouse.move(box.x+box.width*.4,box.y+box.height*.5);
  await page.mouse.down(); await page.mouse.move(box.x+box.width*.7,box.y+box.height*.65,{steps:12}); await page.mouse.up();
  await expect.poll(async()=> (await viewport.screenshot()).equals(before)).toBe(false);
  await page.mouse.wheel(0,-150);
  await page.getByRole('button',{name:'Reset structure view'}).click();
  const [download] = await Promise.all([page.waitForEvent('download'),page.getByRole('button',{name:'Export structure image'}).click()]);
  const png = fs.readFileSync((await download.path())!);
  expect(png.subarray(0,8).toString('hex')).toBe('89504e470d0a1a0a');
  expect(png.length).toBeGreaterThan(1000);
  await page.getByRole('button',{name:'actual.cif · structure',exact:true}).click();
  await expect(viewport).toHaveAttribute('data-state','ready',{timeout:30000});
  await expect(page.getByRole('heading',{name:'actual.cif',exact:true})).toBeVisible();
  const cdp = await context.newCDPSession(page);
  await cdp.send('HeapProfiler.collectGarbage');
  const baseline = (await cdp.send('Runtime.getHeapUsage')).usedSize;
  const cycles: {cycle:number; heap:number; gpuLive:number}[] = [];
  for (let cycle=1;cycle<=20;cycle++) {
    await page.getByRole('button',{name:'Inputs',exact:true}).click();
    await expect(viewport).toHaveCount(0);
    const liveHandles = () => page.evaluate(() => (window as unknown as {fusionlabGlLedger:{created:number;deleted:number;releasedByContext:number}[]}).fusionlabGlLedger.reduce((sum,row)=>sum+row.created-row.deleted-row.releasedByContext,0));
    await expect.poll(liveHandles,{message:`GPU resource handles after closing cycle ${cycle}`}).toBe(0);
    const live = await liveHandles();
    await page.getByRole('tab',{name:'Resources',exact:true}).click();
    await expect(viewport).toHaveAttribute('data-state','ready',{timeout:30000});
    expect(await viewport.count()).toBe(1);
    await cdp.send('HeapProfiler.collectGarbage');
    cycles.push({cycle,heap:(await cdp.send('Runtime.getHeapUsage')).usedSize,gpuLive:live});
  }
  // No invented universal heap threshold. Save observed samples and exact
  // resource-release assertions for comparison with the same-machine baseline.
  await testInfo.attach('actual-3d-lifecycle.json',{body:JSON.stringify({started,elapsed_ms:Date.now()-started,baseline_heap:baseline,cycles,errors},null,2),contentType:'application/json'});
  await viewport.scrollIntoViewIfNeeded();
  await page.screenshot({path:'test-results/real-structure-viewer.png'});
  expect(errors).toEqual([]);
  const projectId = await page.getByLabel('Current project',{exact:true}).inputValue();
  expect(await (await context.request.get(`/api/platform/runs?project_id=${projectId}`)).json()).toEqual([]);
});

test('real coordinate metadata survives actual WebGL-unavailable fallback',async({page})=>{
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(...args: Parameters<typeof original>) {
      return String(args[0]).includes('webgl') ? null : original.apply(this,args);
    } as typeof original;
  });
  await page.goto('/');
  await expect(page.getByRole('button',{name:'Rename project',exact:true})).toBeVisible();
  await importStructure(page,'fallback.pdb',pdb!);
  await openResources(page);
  await page.getByRole('button',{name:'fallback.pdb · structure',exact:true}).click();
  await expect(page.getByRole('alert').filter({hasText:'WebGL is required'})).toBeVisible({timeout:30000});
  await expect(page.getByLabel('Chain',{exact:true})).toHaveValue('A');
  await expect(page.getByRole('button',{name:'Download authorized original'})).toBeEnabled();
  await expect(page.getByRole('button',{name:'Export structure image'})).toBeDisabled();
});
