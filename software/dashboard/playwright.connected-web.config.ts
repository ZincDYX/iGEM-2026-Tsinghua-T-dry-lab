import {defineConfig} from '@playwright/test';
const baseURL=process.env.FUSIONLAB_ACCEPTANCE_WEB_URL;
if(!baseURL) throw Error('Specify an authorized, isolated acceptance workspace URL. Never use user or production project data.');
export default defineConfig({
  testDir:'./e2e/connected-web',workers:1,timeout:90000,
  use:{baseURL,channel:process.platform==='win32'?'msedge':undefined,
    headless:true,viewport:{width:1440,height:1000},locale:'en-US',video:'on',screenshot:'only-on-failure'},
});
