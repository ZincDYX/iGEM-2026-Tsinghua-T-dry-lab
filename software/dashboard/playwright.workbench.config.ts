import {defineConfig} from "@playwright/test";
import path from "node:path";
const repository=path.resolve(import.meta.dirname,"../..");
const data=process.env.FUSIONLAB_TEST_DATA;
if(!data)throw new Error("Specify a new, owned SOFTWARE_FIXTURE workspace, not existing user data.");
const python=path.join(repository,process.platform==="win32"?".venv/Scripts/python.exe":".venv/bin/python");
export default defineConfig({testDir:"./e2e/workbench",workers:1,timeout:45000,
  use:{baseURL:"http://127.0.0.1:5191",channel:process.platform==="win32"?"msedge":undefined,headless:true,locale:"zh-CN",timezoneId:"Asia/Shanghai",viewport:{width:1280,height:850}},
  webServer:[{command:`"${python}" tests/serve_workbench_fixture.py --data-dir "${data}" --port 8791`,cwd:repository,url:"http://127.0.0.1:8791/api/platform/info",ignoreHTTPSErrors:false,reuseExistingServer:false,env:{PYTHONDONTWRITEBYTECODE:"1",OPENBLAS_NUM_THREADS:"1"}},
    {command:`node node_modules/vite/bin/vite.js ${process.env.FUSIONLAB_TEST_BUILT==="1"?"preview ":""}--host 127.0.0.1 --port 5191 --strictPort`,url:"http://127.0.0.1:5191",reuseExistingServer:false,env:{VITE_DASHBOARD_API_URL:"",FUSIONLAB_API_PROXY:"http://127.0.0.1:8791"}}]});
