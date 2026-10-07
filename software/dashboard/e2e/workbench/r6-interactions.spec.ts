import { test, expect, type Page } from "@playwright/test";
import path from "node:path";
const token = "SOFTWARE_FIXTURE_SESSION_NOT_A_REAL_CREDENTIAL";
const backend = "http://127.0.0.1:8791/api/platform";
const headers = { "X-FusionLab-Token": token };
async function open(page: Page, id = "software-fixture") {
  await page.addInitScript(
    ({ token, id }) => {
      localStorage.setItem("fusionlab.project", id);
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
              return { mode: "local", ssh_host: "", remote_port: 8780 } as T;
            throw new Error("SOFTWARE_FIXTURE unsupported bridge");
          },
        },
      };
    },
    { token, id },
  );
  await page.goto("/");
  await expect(page.getByLabel("Current project")).toHaveValue(id);
}
test("JSON draft survives tabs, invalid apply and project-switch cancellation", async ({
  page,
}) => {
  await open(page);
  await page.getByRole("button", { name: "Import" }).click();
  await page
    .getByRole("button", { name: "Advanced: Edit public project JSON" })
    .click();
  const editor = page.getByLabel("Public inputs JSON");
  const draft = JSON.parse(await editor.inputValue());
  draft.name = "SOFTWARE_FIXTURE_UNAPPLIED";
  const text = JSON.stringify(draft, null, 2);
  await editor.fill(text);
  for (const tab of ["Workflow", "Results", "Inputs"]) {
    await page
      .getByRole("tablist", { name: "Workspace documents" })
      .getByRole("tab", { name: tab, exact: true })
      .click();
  }
  await expect(editor).toHaveValue(text);
  await expect(page.getByRole("button", { name: "Save" })).toBeDisabled();
  await editor.fill("{invalid fixture JSON");
  await page.getByRole("button", { name: "Apply validated draft" }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(editor).toHaveValue("{invalid fixture JSON");
  page.once("dialog", (dialog) => dialog.dismiss());
  await page.getByText("File", { exact: true }).click();
  await page.getByRole("menuitem", { name: "New project" }).click();
  await expect(editor).toHaveValue("{invalid fixture JSON");
  await editor.fill(text);
  await page.getByRole("button", { name: "Apply validated draft" }).click();
  await expect(page.getByLabel("Project name")).toHaveValue(draft.name);
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.locator(".document-status")).toContainText(
    "Draft synchronized",
  );
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByText("File", { exact: true }).click();
  await page.getByRole("menuitem", { name: "New project" }).click();
  await page
    .getByRole("button", { name: "Advanced: Edit public project JSON" })
    .click();
  expect(await editor.inputValue()).not.toContain("SOFTWARE_FIXTURE_UNAPPLIED");
});
test("three pointer/keyboard splitters persist view only and narrow drawer leaves controls reachable", async ({
  page,
  request,
}) => {
  await open(page);
  const before = await (
    await request.get(`${backend}/projects/software-fixture`, { headers })
  ).json();
  for (const [name, dx, dy] of [
    ["Project pane", 50, 0],
    ["Inspector", -50, 0],
    ["Bottom pane", 0, -40],
  ] as const) {
    const splitter = page.getByRole("separator", { name, exact: true });
    const original = Number(await splitter.getAttribute("aria-valuenow"));
    const box = (await splitter.boundingBox())!;
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await page.mouse.move(
      box.x + box.width / 2 + dx,
      box.y + box.height / 2 + dy,
      { steps: 5 },
    );
    expect(
      await page.evaluate(() => localStorage.getItem("fusionlab.layout")),
    ).toBeNull(); // pointermove never persists
    await page.mouse.up();
    expect(
      Number(await splitter.getAttribute("aria-valuenow")),
    ).toBeGreaterThan(original);
    await splitter.focus();
    const key =
      name === "Bottom pane"
        ? "ArrowUp"
        : name === "Inspector"
          ? "ArrowLeft"
          : "ArrowRight";
    const current = Number(await splitter.getAttribute("aria-valuenow"));
    await page.keyboard.press(key);
    expect(
      Number(await splitter.getAttribute("aria-valuenow")),
    ).toBeGreaterThan(current);
    // The next drag must not assert empty storage: clear only optional view state.
    await page.evaluate(() => localStorage.removeItem("fusionlab.layout"));
  }
  await page
    .getByRole("separator", { name: "Project pane", exact: true })
    .focus();
  await page.keyboard.press("ArrowLeft");
  const saved = await page.evaluate(() =>
    localStorage.getItem("fusionlab.layout"),
  );
  await page.reload();
  await expect(page.getByLabel("Current project")).toHaveValue(
    "software-fixture",
  );
  expect(
    await page.evaluate(() => localStorage.getItem("fusionlab.layout")),
  ).toBe(saved);
  expect(
    await (
      await request.get(`${backend}/projects/software-fixture`, { headers })
    ).json(),
  ).toEqual(before);
  await page.setViewportSize({ width: 800, height: 600 });
  await expect(
    page.getByRole("complementary", { name: "Inspector", exact: true }),
  ).not.toBeVisible();
  await page.getByText("View", { exact: true }).click();
  await page.getByRole("menuitem", { name: "Inspector", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Close inspector" }),
  ).toBeVisible();
  const drawer = (await page
      .getByRole("complementary", { name: "Inspector", exact: true })
      .boundingBox())!,
    toolbar = (await page
      .getByLabel("Project and run controls")
      .boundingBox())!;
  expect(drawer.y).toBeGreaterThanOrEqual(toolbar.y + toolbar.height);
  await page.getByRole("button", { name: "Close inspector" }).click();
  expect(
    (await page.locator(".workspace-center").boundingBox())!.width,
  ).toBeGreaterThanOrEqual(300);
});
test("paused UI cancel is terminal and inspector result stays with selected stage off the result tab", async ({
  page,
  request,
}) => {
  const id = "software-fixture-r6-execution";
  const preview = await (
    await request.post(`${backend}/scientific-projects/upload-preview`, {
      headers,
      data: {
        config_filename: "project.yaml",
        files: [
          {
            filename: "project.yaml",
            content: JSON.stringify({
              run: { id: "SOFTWARE_FIXTURE" },
              inputs: {
                protein_fasta: "fixture.fasta",
                enzymes: [],
                scaffolds: [],
                linkers: [],
              },
            }),
          },
          {
            filename: "fixture.fasta",
            content: ">SOFTWARE_FIXTURE_NOT_BIOLOGICAL\nMAGSGS\n",
          },
        ],
      },
    })
  ).json();
  expect(
    (
      await request.post(`${backend}/projects`, {
        headers,
        data: {
          project: {
            id,
            name: "SOFTWARE_FIXTURE_r6",
            scientific_project: preview.scientific_project,
          },
        },
      })
    ).status(),
  ).toBe(200);
  await open(page, id);
  await page.getByLabel("Research objective").fill("SOFTWARE_FIXTURE_ONLY");
  await page.getByLabel("Pause after each stage").check();
  await page.getByRole("button", { name: "Generate proposal" }).click();
  await page
    .getByRole("button", {
      name: "Accept proposal (does not start computation)",
    })
    .click();
  await page.getByRole("button", { name: "Start run" }).click();
  await expect(page.locator(".document-status")).toContainText("Paused");
  await expect(
    page.getByRole("button", { name: "Cancel run", exact: true }),
  ).toBeEnabled();
  await page.getByRole("button", { name: "Cancel run", exact: true }).click();
  await expect(page.locator(".document-status")).toContainText("Cancelled");
  await expect(page.getByRole("button", { name: "Resume run" })).toHaveCount(0);
  const value = await (
    await request.post(`${backend}/proposals`, {
      headers,
      data: { project_id: id, goal: "scientific_pipeline" },
    })
  ).json();
  await request.post(`${backend}/proposals/${value.id}/decision`, {
    headers,
    data: { action: "accept" },
  });
  await request.post(`${backend}/runs`, {
    headers,
    data: {
      project_id: value.project_id,
      workflow: value.workflow,
      confirmation: value.confirmation,
      proposal_id: value.id,
    },
  });
  await page.reload();
  await expect(
    page.getByRole("button", { name: /M1–M5 scientific pipeline · r/ }).first(),
  ).toBeVisible();
  await page
    .getByRole("button", { name: /M1–M5 scientific pipeline · r/ })
    .first()
    .click();
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
  await page
    .getByRole("tablist", { name: "Workspace documents" })
    .getByRole("tab", { name: "Workflow" })
    .click();
  await page
    .getByRole("tabpanel")
    .getByRole("button", {
      name: "M1 original-formula pipeline and evidence gates",
      exact: true,
    })
    .click();
  await page
    .getByRole("tablist", { name: "Inspector tabs" })
    .getByRole("tab", { name: "Inputs / Evidence" })
    .click();
  await expect(page.getByLabel("Loaded result identity")).toContainText(
    "M1 original-formula pipeline and evidence gates · attempt 1",
  );
  await page
    .locator(".workspace-inspector")
    .getByText("Current result page values / Unit / Source", { exact: true })
    .click();
  await expect(page.locator(".workspace-inspector pre").last()).toContainText(
    '"module": "m1"',
  );
  await expect(
    page.locator(".workspace-inspector pre").last(),
  ).not.toContainText('"module": "m4"');
});
test("real folder upload retains configs/data siblings and synchronizes only an unchosen science entry", async ({
  page,
}) => {
  await open(page);
  await page.getByText("File", { exact: true }).click();
  await page.getByRole("menuitem", { name: "New project" }).click();
  await expect(
    page.getByLabel("Analysis entry point", { exact: true }),
  ).toHaveValue("fusion_screen");
  const directory = path.resolve(
    import.meta.dirname,
    "../../../../tests/fixtures/workbench_bundle",
  );
  await page.getByLabel("Scientific project folder").setInputFiles(directory);
  await page
    .getByLabel("Scientific project entry")
    .selectOption("configs/project.yaml");
  await page.getByRole("button", { name: "Check scientific inputs" }).click();
  await expect(
    page.getByText(/Validated typed configuration, binding /),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Confirm scientific inputs into draft" })
    .click();
  await expect(
    page.getByLabel("Analysis entry point", { exact: true }),
  ).toHaveValue("scientific_pipeline");
  await page
    .getByLabel("Analysis entry point", { exact: true })
    .selectOption("fusion_screen");
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.locator(".document-status")).toContainText(
    "Draft synchronized",
  );
  await expect(
    page.getByLabel("Analysis entry point", { exact: true }),
  ).toHaveValue("fusion_screen");
  await page
    .getByLabel("Saved scientific input check")
    .getByRole("button", { name: "Check inputs" })
    .click();
  const precheck = page.getByLabel("Saved scientific input check");
  await expect(precheck).toContainText("explicit_construct_definitions");
  await expect(precheck).toContainText("wetlab_results_file");
  await expect(precheck).toContainText("Final stage gates still apply.");
});
