import { test, expect } from "@playwright/test";
import { readFile, readdir } from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { zipSync } from "fflate";

test("authorized original bytes, offline Plotly exact null/zero and actual Molstar coordinate preview", async ({
  page,
  request,
}, testInfo) => {
  const token = "SOFTWARE_FIXTURE_SESSION_NOT_A_REAL_CREDENTIAL";
  const backend = "http://127.0.0.1:8791/api/platform";
  const headers = { "X-FusionLab-Token": token };
  const files: Record<string, Uint8Array> = {};
  const root = path.resolve(
    import.meta.dirname,
    "../../../../tests/fixtures/workbench_bundle",
  );
  async function collect(relative = "") {
    for (const item of await readdir(path.join(root, relative), {
      withFileTypes: true,
    })) {
      const name = path.posix.join(relative, item.name);
      if (item.isDirectory()) await collect(name);
      else files[name] = await readFile(path.join(root, name));
    }
  }
  await collect();
  const pdb =
    "MODEL        7\nATOM      1  N   ALA B  12A     11.000  12.000  13.000  1.00 99.00           N\nATOM      2  CA  ALA B  12A     12.000  12.000  13.000  1.00 99.00           C\nATOM      3  C   ALA B  12A     13.000  12.000  13.000  1.00 99.00           C\nENDMDL\nEND\n";
  const coordinateSource = pdb.replace(
    "ENDMDL",
    Array.from(
      { length: 119 },
      (_, i) =>
        `ATOM  ${String(i + 4).padStart(5)}  CA  ALA B${String(i + 20).padStart(4)}      11.000  12.000  13.000  1.00 99.00           C`,
    ).join("\n") + "\nENDMDL",
  );
  files["structures/coordinate-sample.pdb"] = Buffer.from(coordinateSource);
  files["structures/reference-overlay-sample.pdb"] = Buffer.from(
    "ATOM      1  CA  GLY C  13       1.000   2.000   3.000  1.00 99.00           C\nEND\n",
  );
  const sourceHash = createHash("sha256")
    .update(coordinateSource)
    .digest("hex");
  files["data/fusion-mapping.fasta"] = Buffer.from(
    ">PARSER_FULL_FUSION\n" + "A".repeat(20) + "\n",
  );
  files["structures/annotations.json"] = Buffer.from(
    JSON.stringify({
      schema_version: "structure-display-annotations-v1",
      target_sha256: sourceHash,
      source_reference: "SOFTWARE_PARSER_SAMPLE_NOT_SCIENCE",
      source_tool: "PARSER_SAMPLE",
      source_tool_version: "1",
      fusion_sequence_id: "PARSER_FULL_FUSION",
      fusion_sequence_file_sha256: createHash("sha256")
        .update(files["data/fusion-mapping.fasta"])
        .digest("hex"),
      confidence_semantics: "plddt",
      overlays: [
        {
          reference_sha256: createHash("sha256")
            .update(files["structures/reference-overlay-sample.pdb"])
            .digest("hex"),
          source_reference: "SOFTWARE_ORIGINAL_TRANSFORM",
          source_tool: "PARSER_SAMPLE",
          source_tool_version: "1",
          direction: "reference_to_target",
          coordinate_unit: "angstrom",
          convention: "row_major_column_vector_xyz1",
          matrix: [
            [0, -1, 0, 5],
            [1, 0, 0, 6],
            [0, 0, 1, 7],
            [0, 0, 0, 1],
          ],
        },
      ],
      rows: [
        {
          residue: {
            model: "7",
            chain: "B",
            residue_number: "12",
            insertion_code: "A",
            residue_name: "ALA",
          },
          full_fusion_position: 17,
          region: "enzyme",
          pocket: true,
          plddt: 42,
        },
        ...Array.from({ length: 119 }, (_, i) => ({
          residue: {
            model: "7",
            chain: "B",
            residue_number: String(i + 20),
            insertion_code: "",
            residue_name: "ALA",
          },
          region: "enzyme",
          plddt: 42,
          pocket: i === 118,
        })),
      ],
    }),
  );
  files["plots/recorded-parser-sample.json"] = Buffer.from(
    JSON.stringify({
      prediction_contract: {
        schema_version: "m4-prediction-v2",
        model_kind: "SOFTWARE_DISPLAY_SAMPLE",
        formula_version: "NOT_SCIENTIFIC",
        time_unit: "h",
        concentration_unit: "uM",
        time: [0, 1, 2],
        concentrations: { dense: { "15": [0, null, 2] } },
      },
    }),
  );
  files["images/pixel-sample.png"] = Buffer.from(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
    "base64",
  );
  const upload = await request.post(
    `${backend}/scientific-projects/upload-binary?config_filename=configs%2Fproject.yaml`,
    {
      headers: { ...headers, "Content-Type": "application/octet-stream" },
      data: Buffer.from(zipSync(files)),
    },
  );
  expect(upload.status()).toBe(200);
  const science = (await upload.json()).scientific_project;
  expect(
    (
      await request.post(`${backend}/projects`, {
        headers,
        data: {
          project: {
            id: "viewer-parser-sample",
            name: "SOFTWARE_VIEWERS_NOT_SCIENCE",
            scientific_project: science,
          },
        },
      })
    ).status(),
  ).toBe(200);
  const external: string[] = [],
    errors: string[] = [],
    csp: string[] = [];
  page.on("request", (r) => {
    if (!new URL(r.url()).hostname.match(/^(127\.0\.0\.1|localhost)$/))
      external.push(r.url());
    expect(r.url()).not.toContain(token);
  });
  page.on("pageerror", (e) => errors.push(e.message));
  await page.addInitScript(
    ({ token }) => {
      localStorage.setItem("fusionlab.project", "viewer-parser-sample");
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
            throw Error("SOFTWARE_BRIDGE_UNSUPPORTED");
          },
        },
      };
      (window as unknown as { cspFailures: string[] }).cspFailures = [];
      document.addEventListener("securitypolicyviolation", (event) =>
        (window as unknown as { cspFailures: string[] }).cspFailures.push(
          event.violatedDirective,
        ),
      );
    },
    { token },
  );
  const config = JSON.parse(
    await readFile(
      path.resolve(import.meta.dirname, "../../src-tauri/tauri.conf.json"),
      "utf8",
    ),
  );
  await page.route("**/", async (route) => {
    const response = await route.fetch();
    await route.fulfill({
      response,
      headers: {
        ...response.headers(),
        "Content-Security-Policy": config.app.security.csp,
      },
    });
  });
  await page.goto("/");
  await expect(page.getByLabel("Current project")).toHaveValue(
    "viewer-parser-sample",
  );
  const checks: string[] = [];
  page.on("response", (response) => {
    if (response.url().endsWith("/precheck")) checks.push(response.url());
  });
  await page
    .getByRole("button", { name: "Check inputs", exact: true })
    .first()
    .click();
  await expect(page.getByLabel("Input check issues")).toHaveCount(2);
  const returnedCheck = await request.get(
    `${backend}/projects/viewer-parser-sample/precheck`,
    { headers },
  );
  expect(returnedCheck.status()).toBe(200);
  const expectedIssues = (await returnedCheck.json()).missing.length;
  expect(expectedIssues).toBeGreaterThan(0);
  for (const issues of await page.getByLabel("Input check issues").all())
    await expect(issues.locator("tbody tr")).toHaveCount(expectedIssues);
  expect(checks).toHaveLength(1);
  await page
    .getByRole("button", { name: "▸ Plots / Images / Structures / Tables" })
    .click();
  await page.getByRole("button", { name: "pixel-sample.png · image" }).click();
  const image = page.locator(".workspace-content img");
  await expect(image).toBeVisible();
  expect(
    await image.evaluate((i: HTMLImageElement) => [
      i.naturalWidth,
      i.naturalHeight,
    ]),
  ).toEqual([1, 1]);
  await page
    .getByRole("button", { name: "recorded-parser-sample.json · series" })
    .click();
  const chart = page
    .getByLabel("Recorded time course")
    .locator(".js-plotly-plot");
  await expect(chart).toBeVisible();
  await expect(
    page.getByRole("tab", { name: "Resources", exact: true }),
  ).toHaveAttribute("aria-selected", "true");
  expect(
    await chart.evaluate((element) =>
      (
        element as unknown as { data: { x: number[]; y: (number | null)[] }[] }
      ).data.map((t) => ({ x: t.x, y: t.y })),
    ),
  ).toEqual([{ x: [0, 1, 2], y: [0, null, 2] }]);
  await expect(
    page
      .getByRole("heading", { name: "Registered artifacts" })
      .locator("..")
      .locator("table"),
  ).toContainText("Not recorded");
  await chart.scrollIntoViewIfNeeded();
  const zoom = await chart.locator(".nsewdrag").boundingBox();
  expect(zoom).not.toBeNull();
  await page.mouse.move(
    zoom!.x + zoom!.width * 0.2,
    zoom!.y + zoom!.height * 0.2,
  );
  await page.mouse.down();
  await page.mouse.move(
    zoom!.x + zoom!.width * 0.75,
    zoom!.y + zoom!.height * 0.75,
    { steps: 12 },
  );
  await page.mouse.up();
  await expect
    .poll(() =>
      chart.evaluate(
        (e) =>
          (e as any)._fullLayout.xaxis.range[1] -
          (e as any)._fullLayout.xaxis.range[0],
      ),
    )
    .toBeLessThan(2);
  const range = await chart.evaluate((e) => (e as any)._fullLayout.xaxis.range);
  expect(range[1] - range[0]).toBeLessThan(2);
  await page.locator(".workspace-content tbody tr").last().click();
  await expect(
    page.locator(".workspace-content tbody tr").last(),
  ).toHaveAttribute("aria-selected", "true");
  await expect
    .poll(() => chart.evaluate((e) => (e as any)._fullLayout.xaxis.range))
    .toEqual(range);
  await page
    .getByRole("button", { name: "coordinate-sample.pdb · structure" })
    .click();
  await expect(page.locator(".structure-canvas canvas")).toBeVisible();
  await expect(
    page
      .getByRole("heading", { name: "Registered artifacts" })
      .locator("..")
      .locator("table"),
  ).toContainText("12A");
  await expect(
    page
      .getByRole("heading", { name: "Registered artifacts" })
      .locator("..")
      .locator("table"),
  ).toContainText("42");
  await expect(page.locator(".workspace-content")).toContainText(sourceHash);
  await page.getByRole("button", { name: "12A", exact: true }).click();
  const selectedAtoms = await page
    .locator(".structure-canvas")
    .evaluate((element) => {
      const node = element as any;
      let fiber =
        node[Object.keys(node).find((key) => key.startsWith("__reactFiber$"))!];
      for (; fiber; fiber = fiber.return) {
        for (let hook = fiber.memoizedState; hook; hook = hook.next) {
          const owned = hook.memoizedState?.current;
          if (owned?.managers?.structure)
            return owned.managers.structure.selection.elementCount();
        }
      }
      throw Error("Actual viewer context missing");
    });
  // Source model 7 is internally numbered 1; selecting must still target only
  // the three atoms of chain B / residue 12 / insertion A, not all 122 atoms.
  expect(selectedAtoms).toBe(3);
  await page
    .getByLabel("Representation", { exact: true })
    .selectOption("ball-and-stick");
  await expect(
    page.getByLabel("Representation", { exact: true }),
  ).toBeEnabled();
  await page
    .getByLabel("Color source", { exact: true })
    .selectOption("confidence");
  await expect(page.getByLabel("Color source", { exact: true })).toBeEnabled();
  const actualColor = await page
    .locator(".structure-canvas")
    .evaluate((element) => {
      const node = element as any;
      let fiber =
        node[Object.keys(node).find((key) => key.startsWith("__reactFiber$"))!];
      for (; fiber; fiber = fiber.return) {
        for (let hook = fiber.memoizedState; hook; hook = hook.next) {
          const owned = hook.memoizedState?.current;
          if (!owned?.managers?.structure) continue;
          const component =
            owned.managers.structure.hierarchy.current.structures[0]
              .components[0];
          const structure = component.cell.obj.data,
            unit = structure.units[0];
          const location = {
            kind: "element-location",
            structure,
            unit,
            element: unit.elements[0],
          };
          return component.representations[0].cell.obj.data.repr.theme.color.color(
            location,
          );
        }
      }
      throw Error("Actual viewer context missing");
    });
  // Independent fixed RGB oracle for the declared 0..100 linear display scale
  // at the registered value 42. Gray or the B-factor 99 cannot pass.
  expect(actualColor).toBe(0x994c62);
  async function allColors() {
    return page.locator(".structure-canvas").evaluate((element) => {
      const node = element as any;
      for (
        let fiber =
          node[Object.keys(node).find((k) => k.startsWith("__reactFiber$"))!];
        fiber;
        fiber = fiber.return
      )
        for (let hook = fiber.memoizedState; hook; hook = hook.next) {
          const owned = hook.memoizedState?.current;
          if (!owned?.managers?.structure) continue;
          return owned.managers.structure.hierarchy.current.structures.flatMap(
            (s: any) =>
              s.components.flatMap((c: any) => {
                const structure = c.cell.obj.data;
                return structure.units.flatMap((unit: any) =>
                  Array.from(unit.elements).map((element) =>
                    c.representations[0].cell.obj.data.repr.theme.color.color({
                      kind: "element-location",
                      structure,
                      unit,
                      element,
                    }),
                  ),
                );
              }),
          );
        }
      throw Error("Actual viewer missing");
    });
  }
  const colorsBefore = await allColors();
  expect(colorsBefore).toHaveLength(122);
  expect(new Set(colorsBefore)).toEqual(new Set([0x994c62]));
  await expect(page.getByRole("alert")).toHaveCount(0);
  await page
    .getByLabel("Representation", { exact: true })
    .selectOption("molecular-surface");
  await expect(
    page.getByLabel("Representation", { exact: true }),
  ).toBeEnabled();
  await expect(page.getByRole("alert")).toHaveCount(0);
  await page.getByRole("button", { name: "Reset structure view" }).click();
  await page.getByRole("button", { name: "Next residues" }).click();
  await expect(
    page.getByRole("button", { name: "Previous residues" }),
  ).toBeEnabled();
  await expect(
    page.getByRole("button", { name: "12A", exact: true }),
  ).toHaveCount(0);
  expect(await allColors()).toEqual(colorsBefore);
  await page.getByRole("button", { name: "Previous residues" }).click();
  await expect(
    page.getByRole("button", { name: "12A", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", {
      name: "Show registered reference overlay 1",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("button", {
      name: "Hide registered reference overlay 1",
      exact: true,
    }),
  ).toBeEnabled();
  const overlayPositions = await page
    .locator(".structure-canvas")
    .evaluate((element) => {
      const node = element as any;
      let fiber =
        node[Object.keys(node).find((key) => key.startsWith("__reactFiber$"))!];
      for (; fiber; fiber = fiber.return)
        for (let hook = fiber.memoizedState; hook; hook = hook.next) {
          const owned = hook.memoizedState?.current;
          if (!owned?.managers?.structure) continue;
          return owned.managers.structure.hierarchy.current.structures.flatMap(
            (s: any) =>
              s.components.flatMap((c: any) => {
                const structure = c.cell.obj.data;
                return structure.units
                  .filter((unit: any) => unit.elements.length === 1)
                  .map((unit: any) =>
                    Array.from(
                      unit.conformation.position(unit.elements[0], [0, 0, 0]),
                    ),
                  );
              }),
          );
        }
      throw Error("Actual viewer context missing");
    });
  expect(overlayPositions).toContainEqual([3, 7, 10]);
  await expect(page.getByRole("alert")).toHaveCount(0);
  await page.screenshot({ path: testInfo.outputPath("offline-structure.png") });
  await page
    .getByRole("button", {
      name: "Hide registered reference overlay 1",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("button", {
      name: "Show registered reference overlay 1",
      exact: true,
    }),
  ).toBeEnabled();
  await page.getByRole("button", { name: "pixel-sample.png · image" }).click();
  await expect(page.locator(".structure-canvas canvas")).toHaveCount(0);
  csp.push(
    ...(await page.evaluate(
      () => (window as unknown as { cspFailures: string[] }).cspFailures,
    )),
  );
  expect(errors).toEqual([]);
  expect(external).toEqual([]);
  expect(csp).toEqual([]);
  const file = science.evidence_files.find(
    (f: { name: string }) => f.name === "pixel-sample.png",
  );
  const original = await request.get(
    `${backend}/files/${file.id}?project_id=viewer-parser-sample`,
    { headers },
  );
  expect(Buffer.from(await original.body())).toEqual(
    Buffer.from(files["images/pixel-sample.png"]),
  );
});
