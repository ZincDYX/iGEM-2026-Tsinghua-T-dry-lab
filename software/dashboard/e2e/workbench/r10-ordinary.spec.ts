import { test, expect } from "@playwright/test";

test("empty project ordinary TSV mapping, full range and explicit compatible overlays", async ({
  page,
  request,
}, testInfo) => {
  const token = "SOFTWARE_FIXTURE_SESSION_NOT_A_REAL_CREDENTIAL";
  const headers = { "X-FusionLab-Token": token };
  const created = await request.post(
    "http://127.0.0.1:8791/api/platform/projects",
    {
      headers,
      data: {
        project: {
          id: "ordinary-route-sample",
          name: "SOFTWARE_ORDINARY_NOT_BIOLOGY",
        },
      },
    },
  );
  expect(created.status()).toBe(200);
  await page.addInitScript(
    ({ token }) => {
      localStorage.setItem("fusionlab.project", "ordinary-route-sample");
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
            throw Error("UNSUPPORTED_SOFTWARE_BRIDGE");
          },
        },
      };
    },
    { token },
  );
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(page.getByLabel("Current project")).toHaveValue(
    "ordinary-route-sample",
  );
  await page.getByRole("tab", { name: "Inputs", exact: true }).click();
  const content =
    "minutes\ta\tb\tc\n" +
    Array.from({ length: 1201 }, (_, i) =>
      [i, i === 513 ? "" : i * 2, i * 3, i * 4].join("\t"),
    ).join("\n") +
    "\n";
  await page.getByLabel("Import data file").setInputFiles({
    name: "ordinary.tsv",
    mimeType: "text/tab-separated-values",
    buffer: Buffer.from(content),
  });
  await page.getByRole("button", { name: "Confirm import into draft" }).click();
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await page.getByText(/Draft synchronized/).waitFor();
  await page
    .getByRole("button", { name: "Open resource", exact: true })
    .click();
  await expect(
    page.getByRole("tab", { name: "Resources", exact: true }),
  ).toHaveAttribute("aria-selected", "true");
  await expect(page.getByText(/Original strings.*1201 rows/)).toBeVisible();
  await page.getByText("Declare time-course columns", { exact: true }).click();
  await page.getByLabel("Time column", { exact: true }).selectOption("minutes");
  await page.getByLabel("Time unit", { exact: true }).fill("min");
  await page
    .getByLabel("Source reference", { exact: true })
    .fill("SOFTWARE_RECORDED_SOURCE_NOT_PREDICTION");
  for (const [key, species, unit] of [
    ["a", "A", "mM"],
    ["b", "B", "mM"],
    ["c", "C", "uM"],
  ]) {
    await page.getByRole("checkbox", { name: key, exact: true }).check();
    await page.getByLabel(`${key} species`, { exact: true }).fill(species);
    await page
      .getByLabel(`${key} compartment`, { exact: true })
      .fill("recorded_dense");
    await page.getByLabel(`${key} unit`, { exact: true }).fill(unit);
  }
  await page.getByRole("button", { name: "Register declared series" }).click();
  const chart = page
    .getByLabel("Recorded time course")
    .locator(".js-plotly-plot");
  await expect(chart).toBeVisible();
  await expect(page.getByText(/Complete recorded range: 1–1201/)).toBeVisible();
  expect(
    await chart.evaluate((element: any) => [
      element.data[0].x.length,
      element.data[0].x.at(-1),
      element.data[0].y[0],
      element.data[0].y[513],
      element.data[0].y.at(-1),
    ]),
  ).toEqual([1201, 1200, 0, null, 2400]);
  const identity = await chart.evaluate(
    (element: any) => element.layout.uirevision,
  );
  await page.getByRole("button", { name: "Next series page" }).click();
  await expect(page.getByText(/Exact contiguous page, 501–1000/)).toBeVisible();
  expect(
    await chart.evaluate((element: any) => [
      element.data[0].x.length,
      element.layout.uirevision,
    ]),
  ).toEqual([1201, identity]);
  await page.getByText("Overlay recorded series", { exact: true }).click();
  await page
    .getByRole("checkbox", { name: "recorded_dense / B (mM)", exact: true })
    .check();
  await expect
    .poll(() => chart.evaluate((element: any) => element.data.length))
    .toBe(2);
  await page
    .getByRole("checkbox", { name: "recorded_dense / C (uM)", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText(
    "Incompatible declared units",
  );
  expect(await chart.evaluate((element: any) => element.data.length)).toBe(2);
  await page.getByRole("button", { name: "Return to source" }).click();
  await expect(
    page.getByRole("tab", { name: "Inputs", exact: true }),
  ).toHaveAttribute("aria-selected", "true");
  const actual = await request.get(
    "http://127.0.0.1:8791/api/platform/projects/ordinary-route-sample",
    { headers },
  );
  const project = await actual.json();
  expect(project.scientific_project).toBeNull();
  expect(project.pathway).toBeNull();
  expect(project.datasets).toEqual([]);
  const original = await request.get(
    `http://127.0.0.1:8791/api/platform/files/${project.files[0].id}?project_id=ordinary-route-sample`,
    { headers },
  );
  expect((await original.body()).toString()).toBe(content);
  expect(errors).toEqual([]);
  await page.screenshot({
    path: testInfo.outputPath("ordinary-import-return.png"),
  });
});

test("large synthetic coordinate display uses full annotation index and indexed batch selection", async ({
  page,
  request,
}, testInfo) => {
  test.setTimeout(90000);
  const token = "SOFTWARE_FIXTURE_SESSION_NOT_A_REAL_CREDENTIAL",
    headers = { "X-FusionLab-Token": token };
  const count = 6000;
  const pdb =
    Array.from(
      { length: count },
      (_, i) =>
        `ATOM  ${String(i + 1).padStart(5)}  CA  ALA B${String(i + 1).padStart(4)}    ${((i % 100) * 2).toFixed(3).padStart(8)}${(Math.floor(i / 100) * 2).toFixed(3).padStart(8)}${"0.000".padStart(8)}  1.00 99.00           C`,
    ).join("\n") + "\nEND\n";
  const { createHash } = await import("node:crypto");
  const pdbPreview = await request.post(
    "http://127.0.0.1:8791/api/platform/imports/display-file?filename=large-software.pdb",
    { headers, data: Buffer.from(pdb) },
  );
  expect(pdbPreview.status()).toBe(200);
  const annotation = {
    schema_version: "structure-display-annotations-v1",
    target_sha256: createHash("sha256").update(pdb).digest("hex"),
    source_reference: "SYNTHETIC_PARSER_LOAD_NOT_FTH1_OR_BIOLOGY",
    source_tool: "SOFTWARE_FIXTURE",
    source_tool_version: "1",
    confidence_semantics: "plddt",
    rows: Array.from({ length: count }, (_, i) => ({
      residue: {
        model: "1",
        chain: "B",
        residue_number: String(i + 1),
        insertion_code: "",
        residue_name: "ALA",
      },
      plddt: 42,
      pocket: i % 2 === 0,
      clash: i === count - 1,
    })),
  };
  const annotationPreview = await request.post(
    "http://127.0.0.1:8791/api/platform/imports/preview",
    {
      headers,
      data: {
        filename: "large-annotations.json",
        content: JSON.stringify(annotation),
      },
    },
  );
  expect(annotationPreview.status()).toBe(200);
  expect(
    (
      await request.post("http://127.0.0.1:8791/api/platform/projects", {
        headers,
        data: {
          project: {
            id: "large-software-sample",
            name: "SYNTHETIC_COORDINATE_LOAD_NOT_BIOLOGY",
            files: [
              (await pdbPreview.json()).file,
              (await annotationPreview.json()).file,
            ],
          },
        },
      })
    ).status(),
  ).toBe(200);
  await page.addInitScript(
    ({ token }) => {
      localStorage.setItem("fusionlab.project", "large-software-sample");
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
            throw Error("UNSUPPORTED_SOFTWARE_BRIDGE");
          },
        },
      };
    },
    { token },
  );
  await page.goto("/");
  await page.getByRole("tab", { name: "Resources", exact: true }).click();
  const started = Date.now();
  await page
    .getByRole("button", {
      name: "large-software.pdb · structure",
      exact: true,
    })
    .click();
  await expect(page.getByLabel("Color source", { exact: true })).toBeEnabled({
    timeout: 60000,
  });
  const loadMs = Date.now() - started;
  await page
    .getByLabel("Color source", { exact: true })
    .selectOption("confidence");
  await expect(page.getByLabel("Color source", { exact: true })).toBeEnabled();
  const batchStarted = Date.now();
  await page
    .getByRole("button", {
      name: "Select all registered pocket residues (full model)",
      exact: true,
    })
    .click();
  const actual = await page
    .locator(".structure-canvas")
    .evaluate((element: any) => {
      for (
        let fiber =
          element[
            Object.keys(element).find((k) => k.startsWith("__reactFiber$"))!
          ];
        fiber;
        fiber = fiber.return
      )
        for (let hook = fiber.memoizedState; hook; hook = hook.next) {
          const owned = hook.memoizedState?.current;
          if (!owned?.managers?.structure) continue;
          const atoms =
            owned.managers.structure.hierarchy.current.structures.flatMap(
              (s: any) =>
                s.components.flatMap((c: any) =>
                  c.cell.obj.data.units.flatMap((unit: any) =>
                    Array.from(unit.elements).map((atom: any) =>
                      c.representations[0].cell.obj.data.repr.theme.color.color(
                        {
                          kind: "element-location",
                          structure: c.cell.obj.data,
                          unit,
                          element: atom,
                        },
                      ),
                    ),
                  ),
                ),
            );
          return {
            atoms: atoms.length,
            colors: [...new Set(atoms)],
            selected: owned.managers.structure.selection.stats.elementCount,
          };
        }
      throw Error("Actual large viewer missing");
    });
  expect(actual).toEqual({
    atoms: count,
    colors: [0x994c62],
    selected: count / 2,
  });
  await page
    .getByRole("button", {
      name: "Select all registered clash residues (full model)",
      exact: true,
    })
    .click();
  await expect(page.getByRole("alert")).toHaveCount(0);
  await testInfo.attach("software-load-measurement", {
    body: JSON.stringify({
      count,
      load_ms: loadMs,
      batch_ms: Date.now() - batchStarted,
      scientific_validation: false,
      scope:
        "6000_synthetic_CA_coordinates_not_arbitrary_structure_performance",
    }),
    contentType: "application/json",
  });
});
