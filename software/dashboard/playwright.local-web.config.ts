import {defineConfig} from '@playwright/test';
import path from 'node:path';
const data=process.env.FUSIONLAB_TEST_DATA;
const python=process.env.FUSIONLAB_TEST_PYTHON;
if(!data||!python) throw Error('Specify an owned empty test workspace and installed Web-package Python. Do not use user data.');
export default defineConfig({
  testDir:'./e2e/local-web',workers:1,timeout:45000,
  use:{baseURL:'http://127.0.0.1:18881',channel:process.platform==='win32'?'msedge':undefined,
    headless:true,viewport:{width:1280,height:800},locale:'en-US',video:'on',screenshot:'only-on-failure'},
  webServer:{command:`"${python}" -B -m igem_drylab.software.cli --data-dir "${data}" serve --port 18881`,
    cwd:path.resolve(import.meta.dirname,'../../..'),url:'http://127.0.0.1:18881/',reuseExistingServer:false},
});
