// Read-only Web/HTTP measurements. No scientific job/tool is invoked.
import {chromium} from '@playwright/test';
import {spawn,execFileSync} from 'node:child_process';
import {readFileSync,writeFileSync} from 'node:fs';
import {gzipSync} from 'node:zlib';
import os from 'node:os';
const args=Object.fromEntries(process.argv.slice(2).reduce((pairs,value,index,array)=>index%2?pairs:[...pairs,[value,array[index+1]]],[]));
for(const key of ['--python','--package','--data','--output'])if(!args[key])throw Error('Required '+key);
const port=18887,url=`http://127.0.0.1:${port}`;
const child=spawn(args['--python'],['-B','-m','igem_drylab.software.cli','--data-dir',args['--data'],'serve','--port',String(port)],
  {windowsHide:true,stdio:['ignore','pipe','pipe'],env:{...process.env,PYTHONPATH:args['--package'],PYTHONDONTWRITEBYTECODE:'1',OPENBLAS_NUM_THREADS:'1',OMP_NUM_THREADS:'1'}});
let output='';child.stdout.on('data',value=>{output+=value;});child.stderr.on('data',value=>{output+=value;});
function processUsage() {
  if(process.platform==='win32')return JSON.parse(execFileSync('powershell',['-NoProfile','-Command',`Get-Process -Id ${child.pid} | Select-Object CPU,WorkingSet64 | ConvertTo-Json -Compress`],{encoding:'utf8',windowsHide:true}));
  return {stat:readFileSync(`/proc/${child.pid}/stat`,'utf8'),status:readFileSync(`/proc/${child.pid}/status`,'utf8').split('\n').filter(line=>line.startsWith('VmRSS:'))};
}
let browser;
try {
  const start=performance.now();
  for(let attempt=0;attempt<120;attempt++) {
    if(child.exitCode!==null)throw Error('Owned measurement server failed to start: '+output);
    try{if((await fetch(url)).ok)break;}catch{/* Retry readiness, not computation. */}
    if(attempt===119)throw Error('Owned server readiness timed out.');
    await new Promise(resolve=>setTimeout(resolve,250));
  }
  const backendReady=performance.now()-start;
  browser=await chromium.launch({channel:process.platform==='win32'?'msedge':undefined,headless:true});
  const page=await browser.newPage({viewport:{width:1280,height:800}});
  const assets=new Map(),pending=[];
  let requests=0;page.on('request',()=>requests++);
  page.on('response',response=>{if(response.url().includes('/assets/'))pending.push((async()=>{
    const body=await response.body();assets.set(response.url().split('/').at(-1),{bytes:body.length,gzip_bytes:gzipSync(body).length});
  })());});
  const visibleStart=performance.now();await page.goto(url);
  await page.getByLabel('Project name').waitFor({state:'visible'});
  const inputsVisible=performance.now()-visibleStart;
  // Wait for actual tool registration, not a GPU/model computation.
  for(let attempt=0;attempt<120;attempt++){
    const info=await page.evaluate(async()=> (await fetch('/api/platform/info')).json());
    if(info.capabilities.scientific_mcp!=='checking')break;
    await new Promise(resolve=>setTimeout(resolve,250));
  }
  await Promise.all(pending);
  const cdp=await page.context().newCDPSession(page);await cdp.send('HeapProfiler.collectGarbage');
  const heap=(await cdp.send('Runtime.getHeapUsage')).usedSize;
  const latency=[];
  for(let index=0;index<50;index++)latency.push(await page.evaluate(async()=>{
    const started=performance.now();const response=await fetch('/api/platform/info');if(!response.ok)throw Error('Read-only API failed');await response.json();return performance.now()-started;
  }));
  latency.sort((a,b)=>a-b);
  const beforeUsage=processUsage(),beforeRequests=requests;
  await new Promise(resolve=>setTimeout(resolve,10000));
  const afterUsage=processUsage();
  const report={scope:'Software-only, cold empty local workspace, one sequential sample; not a scientific benchmark or a clean release-build verification.',
    label:args['--label']??'Measured installed package',machine:{platform:process.platform,os:os.release(),cpu:os.cpus()[0]?.model,ram_bytes:os.totalmem(),node:process.version,browser:browser.version()},
    backend_ready_ms:backendReady,inputs_visible_ms:inputsVisible,post_gc_heap_bytes:heap,loaded_assets:Object.fromEntries(assets),
    loaded_js_bytes:[...assets].filter(([name])=>name.endsWith('.js')).reduce((sum,[,value])=>sum+value.bytes,0),
    loaded_js_gzip_bytes:[...assets].filter(([name])=>name.endsWith('.js')).reduce((sum,[,value])=>sum+value.gzip_bytes,0),
    api_samples:50,api_info_p50_ms:latency[24],api_info_p95_ms:latency[47],idle_10s_extra_requests:requests-beforeRequests,backend_idle_before:beforeUsage,backend_idle_after:afterUsage};
  writeFileSync(args['--output'],JSON.stringify(report,null,2));
  console.log(JSON.stringify({label:report.label,loaded_js_bytes:report.loaded_js_bytes,loaded_js_gzip_bytes:report.loaded_js_gzip_bytes,post_gc_heap_bytes:heap,api_p95_ms:latency[47],idle_extra_requests:report.idle_10s_extra_requests}));
} finally {
  await browser?.close();
  // Only this child PID is terminated; no process-name or port-wide killing.
  child.kill();
}
