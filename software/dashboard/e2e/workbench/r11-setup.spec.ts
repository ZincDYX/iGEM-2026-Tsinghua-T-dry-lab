import { test, expect } from "@playwright/test";
test("empty project creates bound scientific configuration through real forms, no YAML and no approved values", async ({
  page,
  request,
}) => {
  const headers = {
      "X-FusionLab-Token": "SOFTWARE_FIXTURE_SESSION_NOT_A_REAL_CREDENTIAL",
    },
    u = "http://127.0.0.1:8791/api/platform";
  const project = await (
    await request.post(u + "/projects", {
      headers,
      data: { project: { id: "r11-form", name: "SOFTWARE_FORM_NOT_BIOLOGY" } },
    })
  ).json();
  await page.addInitScript(
    ({ token }) => {
      localStorage.setItem("fusionlab.project", "r11-form");
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
            throw Error("UNSUPPORTED_SOFTWARE_BRIDGE");
          },
        },
      };
    },
    { token: headers["X-FusionLab-Token"] },
  );
  await page.goto("/");
  await page.getByLabel("Current project").selectOption(project.id);
  await page.getByRole("button", { name: "Import", exact: true }).click();
  const original = Buffer.from(">EXPLICIT_SOFTWARE_SEQUENCE\nMAGSGS\n");
  await page.getByLabel("Import data file").setInputFiles({
    name: "explicit-original.fasta",
    mimeType: "text/plain",
    buffer: original,
  });
  await page
    .getByRole("button", { name: "Confirm import into draft", exact: true })
    .click();
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await page.getByText(/Draft synchronized/).waitFor();
  const creator = page.locator("#input-scientific-setup");
  // Import navigation already opens this section; do not toggle it closed.
  if (!(await creator.evaluate((node) => (node as HTMLDetailsElement).open)))
    await creator.locator("summary").first().click();
  const root = "scientific_project.config";
  await expect(
    page.getByLabel(root + ".execution.mode", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByLabel(root + ".execution.mode", { exact: true }),
  ).toHaveValue("");
  // New projects prepare M1 only. This test explicitly prepares M1–M4;
  // later-stage controls must not be forced into the default M1 form.
  await expect(page.getByLabel(root + ".prepared_through", { exact: true })).toHaveValue("m1");
  await page.getByLabel(root + ".prepared_through", { exact: true }).selectOption("m4");
  await expect(
    page.getByLabel(root + ".stages.m4_reaction.t_end", { exact: true }),
  ).toHaveValue("");
  await page
    .getByLabel(root + ".execution.mode", { exact: true })
    .selectOption("real");
  await page
    .getByLabel(root + ".execution.allow_assumptions", { exact: true })
    .selectOption("false");
  const source = (
    await (await request.get(u + "/projects/r11-form", { headers })).json()
  ).files[0];
  await page
    .getByLabel(root + ".inputs.protein_fasta", { exact: true })
    .selectOption(source.path);
  const m3 = root + ".stages.m3_concentration",
    m4 = root + ".stages.m4_reaction";
  for (const [key, value] of Object.entries({
    phi_source: "measured",
    binding_model: "independent",
    recruitment_mode: "finite_site",
    ptr_pt_phase_handling: "dilute_only",
  }))
    await page.getByLabel(m3 + "." + key, { exact: true }).selectOption(value);
  await page
    .getByLabel(m3 + ".recruitment_bias_oc_vs_dmt", { exact: true })
    .fill("1");
  for (const [key, value] of Object.entries({
    network_mode: "markdown_steady_state",
    scenario_mode: "homogeneous_constitutive",
    unit_mode: "physical",
    activity_mode: "sensitivity_parameters",
  }))
    await page.getByLabel(m4 + "." + key, { exact: true }).selectOption(value);
  for (const [key, value] of Object.entries({
    target_product: "USER_TARGET_SOFTWARE",
    t_end: "1",
    max_side_product_fraction_13: ".1",
    min_13_reduction: ".2",
    min_15_improvement: "0",
    min_productivity: "0",
  }))
    await page.getByLabel(m4 + "." + key, { exact: true }).fill(value);
  await page
    .getByRole("button", {
      name: "Validate scientific configuration",
      exact: true,
    })
    .click();
  await page
    .getByRole("button", {
      name: "Confirm scientific inputs into draft",
      exact: true,
    })
    .click();
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await page.getByText(/Draft synchronized/).waitFor();
  const saved = await (
    await request.get(u + "/projects/r11-form", { headers })
  ).json();
  expect(saved.scientific_project.config.prepared_through).toBe("m4");
  expect(saved.scientific_project.config.parameters).toEqual([]);
  expect(
    Object.values(saved.scientific_project.config.experimental_context).every(
      (v) => v === null,
    ),
  ).toBe(true);
  expect(
    saved.scientific_project.config.stages.m4_reaction.initial_state,
  ).toBeNull();
  expect(
    saved.scientific_project.config.stages.m4_reaction.target_product,
  ).toBe("USER_TARGET_SOFTWARE");
  expect(saved.scientific_project.sequence_index.count).toBe(1);
  const downloaded = await request.get(
    u + "/files/" + source.id + "?project_id=r11-form",
    { headers },
  );
  expect(await downloaded.body()).toEqual(original);
  await page
    .getByRole("button", { name: "Check inputs", exact: true })
    .first()
    .click();
  const missing = page.getByLabel("Input check issues").first();
  await expect(missing).toContainText("phi");
  const phi = missing
    .locator("tbody tr")
    .filter({ has: page.getByText("m3 / phi", { exact: true }) });
  await phi.getByRole("button", { name: "Open input", exact: true }).click();
  await expect(page.getByLabel("Parameter name", { exact: true })).toHaveValue(
    "phi",
  );
  await expect(
    page.getByLabel("Numeric parameter value", { exact: true }),
  ).toHaveValue("");
  await expect(
    page.getByLabel("Explicit parameter unit", { exact: true }),
  ).toHaveValue("");
  expect(
    await (
      await request.get(u + "/runs?project_id=r11-form", { headers })
    ).json(),
  ).toEqual([]);
});
