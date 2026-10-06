import { defineConfig } from "@playwright/test";
import path from "node:path";

const repository = path.resolve(import.meta.dirname, "../..");
// Legacy scientific UI suite is not part of software-only local validation.
// Its selectors still need migration; preserve the original numerical oracles.
if(process.platform!=="linux"||process.env.FUSIONLAB_ALLOW_SCIENTIFIC_E2E!=="1")
  throw new Error("Legacy scientific E2E requires an explicitly authorized Linux release environment; do not run local reproduction.");
const testData=process.env.FUSIONLAB_TEST_DATA;
if(!testData)throw new Error("Specify a fresh, owned scientific test workspace.");
const python = process.env.FUSIONLAB_PYTHON ?? path.join(
  repository,
  process.platform === "win32"
    ? ".venv/Scripts/python.exe"
    : ".venv/bin/python",
);
export default defineConfig({
  testDir: "./e2e",
  testIgnore: "**/workbench/**",
  workers: 1,
  timeout: 30000,
  use: {
    baseURL: "http://127.0.0.1:5189",
    channel: process.env.FUSIONLAB_BROWSER_CHANNEL || (process.platform === "win32" ? "msedge" : undefined),
    headless: true,
    locale: "zh-CN",
    timezoneId: "Asia/Shanghai",
    viewport: { width: 1440, height: 1000 },
  },
  webServer: [
    {
      command: `"${python}" -m igem_drylab.cli software serve --port 8789 --dev-anonymous --data-dir "${testData}"`,
      cwd: repository,
      url: "http://127.0.0.1:8789/api/platform/info",
      reuseExistingServer: false,
    },
    {
      command:
        "node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5189 --strictPort",
      url: "http://127.0.0.1:5189",
      env: {
        VITE_DASHBOARD_API_URL: "",
        FUSIONLAB_API_PROXY: "http://127.0.0.1:8789",
      },
      reuseExistingServer: false,
    },
  ],
});
