import { defineConfig } from "@playwright/test";
import path from "node:path";

const repository = path.resolve(import.meta.dirname, "../..");
const testData =
  process.env.FUSIONLAB_TEST_DATA ??
  path.join(repository, "outputs/platform-e2e");
const python = path.join(
  repository,
  process.platform === "win32"
    ? ".venv/Scripts/python.exe"
    : ".venv/bin/python",
);
export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  timeout: 30000,
  use: {
    baseURL: "http://127.0.0.1:5189",
    channel: process.env.FUSIONLAB_BROWSER_CHANNEL ?? "msedge",
    headless: true,
    locale: "zh-CN",
    timezoneId: "Asia/Shanghai",
    viewport: { width: 1440, height: 1000 },
  },
  webServer: [
    {
      command: `"${python}" -m igem_drylab.cli software serve --port 8789 --data-dir "${testData}"`,
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
