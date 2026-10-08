import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";
const token = "SOFTWARE_FIXTURE_SESSION_NOT_A_REAL_CREDENTIAL";
const backend = "http://127.0.0.1:8791/api/platform";

test("authenticated real HTTP compiler/ledger/handlers, staged control, provenance, export and frozen iteration", async ({
  page,
  request,
}, testInfo) => {
  const errors: string[] = [];
  const requests: { url: string; headers: Record<string, string> }[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("request", (value) => {
    if (value.url().includes("/api/platform/"))
      requests.push({ url: value.url(), headers: value.headers() });
  });
  expect((await request.get(`${backend}/info`)).status()).toBe(401);
  if (process.env.FUSIONLAB_TEST_BUILT === "1")
    await page.route("**/", async (route) => {
      const response = await route.fetch();
      await route.fulfill({
        response,
        headers: {
          ...response.headers(),
          "Content-Security-Policy":
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' http://127.0.0.1:*; img-src 'self' data: blob:; worker-src 'self'; font-src 'self' data:; object-src 'none'; frame-src 'none'",
        },
      });
    });
  await page.addInitScript(
    ({ token }) => {
      if (!localStorage.getItem("fusionlab.project"))
        localStorage.setItem("fusionlab.project", "software-fixture");
      window.__TAURI__ = {
        core: {
          invoke: async <T>(command: string) => {
            if (command === "backend_info")
              return {
                url: "http://127.0.0.1:5191",
                token,
                mode: "local",
              } as T;
            if (command === "desktop_settings")
              return { mode: "local", api_url: "", ca_file: "", has_access_token: false } as T;
            throw new Error("SOFTWARE_FIXTURE: unsupported native command");
          },
        },
      };
    },
    { token },
  );
  await page.goto("/");
  await expect(page.getByLabel("Current project")).toHaveValue(
    "software-fixture",
  );
  await page
    .getByLabel("Research objective")
    .fill("SOFTWARE_FIXTURE design; not biological computation");
  await page.getByLabel("Planner source").selectOption("hybrid");
  await page
    .getByLabel(/Allow this objective and public evidence summary/)
    .check();
  await page.getByLabel("Pause after each stage").check();
  await page.getByRole("button", { name: "Generate proposal" }).click();
  await expect(
    page.getByRole("heading", { name: /Hybrid proposal/ }),
  ).toBeVisible();
  const rows = page.locator(".plan-table tbody tr");
  await expect(rows).toHaveCount(4);
  const before = await request.get(
    `${backend}/runs?project_id=software-fixture`,
    { headers: { "X-FusionLab-Token": token } },
  );
  expect(await before.json()).toEqual([]);
  await page
    .getByRole("button", {
      name: "Accept proposal (does not start computation)",
    })
    .click();
  await expect(page.getByRole("button", { name: "Start run" })).toBeEnabled();
  expect(
    await (
      await request.get(`${backend}/runs?project_id=software-fixture`, {
        headers: { "X-FusionLab-Token": token },
      })
    ).json(),
  ).toEqual([]);
  await page.getByRole("button", { name: "Start run" }).click();
  await expect(rows.nth(0)).toContainText("Job completed");
  await expect(rows.nth(1)).toContainText("Pending");
  await expect(page.locator(".document-status")).toContainText("Paused");
  const runs = await (
    await request.get(`${backend}/runs?project_id=software-fixture`, {
      headers: { "X-FusionLab-Token": token },
    })
  ).json();
  expect(runs).toHaveLength(1);
  const runId = runs[0].id;
  const initial = await (
    await request.get(`${backend}/runs/${runId}/summary`, {
      headers: { "X-FusionLab-Token": token },
    })
  ).json();
  for (let stage = 1; stage < 4; stage++) {
    await page.getByRole("button", { name: "Resume run", exact: true }).click();
    await expect(rows.nth(stage)).toContainText("Job completed");
    if (stage < 3) {
      await expect(page.locator(".document-status")).toContainText("Paused");
      await expect(rows.nth(stage + 1)).toContainText("Pending");
    }
  }
  await expect(page.locator(".document-status")).toContainText("Job completed");
  await page
    .getByRole("tabpanel")
    .getByRole("button", {
      name: "M4 original-formula pipeline and evidence gates",
      exact: true,
    })
    .click();
  await page
    .getByRole("tablist", { name: "Workspace documents" })
    .getByRole("tab", { name: "Results" })
    .click();
  await expect(
    page.getByRole("heading", { name: "M4 · Scientific project results" }),
  ).toBeVisible();
  await expect(
    page.getByText(/Endpoint compound 15 Not recorded/),
  ).toBeVisible();
  await expect(page.getByLabel("Four independent statuses")).toContainText(
    "software_fixture_not_prediction",
  );
  expect(await page.locator(".workspace-content pre").count()).toBe(0);
  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: /Authorized scientific export/ })
    .click();
  const result = await download;
  const destination = testInfo.outputPath("scientific-public-export.json");
  await result.saveAs(destination);
  const raw = await readFile(destination, "utf8");
  const exported = JSON.parse(raw);
  expect(exported.export_schema).toBe("scientific-public-export-v1");
  expect(exported.result.records[0].numerically_solved).toBe(false);
  expect(raw).not.toContain(token);
  expect(raw).not.toMatch(/[A-Z]:\\/);
  await page.screenshot({
    path: testInfo.outputPath("workbench-1280x850.png"),
  });
  await page
    .getByRole("tablist", { name: "Bottom panel tabs" })
    .getByRole("tab", { name: "Agent actions" })
    .click();
  await expect(page.locator(".bottom-content")).toContainText(
    "execution_requested",
  );
  await page.getByText("File", { exact: true }).click();
  await page.getByRole("menuitem", { name: "Create iteration" }).click();
  await expect(page.getByLabel("Current project")).not.toHaveValue(
    "software-fixture",
  );
  await page
    .getByLabel("Project name")
    .fill("SOFTWARE_FIXTURE iteration draft");
  await expect(page.getByRole("button", { name: "Start run" })).toHaveCount(0);
  await page.getByRole("button", { name: "Save" }).click();
  await page
    .getByRole("tablist", { name: "Inspector tabs" })
    .getByRole("tab", { name: "Inputs / Evidence" })
    .click();
  await expect(page.getByLabel("Frozen input differences")).toContainText(
    "name",
  );
  await expect(page.getByLabel("Frozen input differences")).toContainText(
    "No bound scientific input changes",
  );
  expect(
    (
      await (
        await request.get(`${backend}/runs/${runId}/summary`, {
          headers: { "X-FusionLab-Token": token },
        })
      ).json()
    ).snapshot_hash,
  ).toBe(initial.snapshot_hash);
  await page.reload();
  await expect(page.getByLabel("Current project")).not.toHaveValue(
    "software-fixture",
  );
  await page.setViewportSize({ width: 800, height: 650 });
  await page.getByText("View", { exact: true }).click();
  await page.getByRole("menuitem", { name: "Inspector", exact: true }).click();
  await expect(page.locator(".workspace-center")).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("workbench-800x650.png") });
  expect(errors).toEqual([]);
  expect(requests.every((value) => !value.url.includes(token))).toBe(true);
  expect(
    requests
      .filter((value) => !value.url.includes("/files/"))
      .every((value) => value.headers["x-fusionlab-token"] === token),
  ).toBe(true);
});
