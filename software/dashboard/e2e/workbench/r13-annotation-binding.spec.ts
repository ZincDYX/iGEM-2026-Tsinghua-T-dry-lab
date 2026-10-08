import { test, expect } from "@playwright/test";
test("annotation source file choices generate backend bindings and keep original measurements and bytes", async ({
  page,
  request,
}) => {
  const headers = {
    "X-FusionLab-Token": "SOFTWARE_FIXTURE_SESSION_NOT_A_REAL_CREDENTIAL",
  };
  const u = "http://127.0.0.1:8791/api/platform";
  const pdb =
    "MODEL        7\nATOM      1  CA  ALA B  12A     11.000  12.000  13.000  1.00 99.00           C\nENDMDL\n";
  const source = JSON.stringify({
    source_reference: "SOFTWARE_SOURCE_NOT_SCIENCE",
    source_tool: "PARSER_FIXTURE",
    source_tool_version: "1",
    confidence_semantics: "plddt",
    rows: [
      {
        residue: {
          model: "7",
          chain: "B",
          residue_number: "12",
          insertion_code: "A",
          residue_name: "ALA",
        },
        plddt: 0,
        pocket: true,
      },
    ],
  });
  const structure = await request.post(
    u + "/imports/display-file?filename=target.pdb",
    {
      headers: { ...headers, "Content-Type": "application/octet-stream" },
      data: Buffer.from(pdb),
    },
  );
  expect(structure.status()).toBe(200);
  const imported = await request.post(u + "/imports/preview", {
    headers,
    data: { filename: "source.json", content: source },
  });
  expect(imported.status()).toBe(200);
  const files = [(await structure.json()).file, (await imported.json()).file];
  const saved = await request.post(u + "/projects", {
    headers,
    data: {
      project: { id: "r13-link", name: "SOFTWARE_ANNOTATION_LINKING", files },
    },
  });
  expect(saved.status()).toBe(200);
  await page.addInitScript(
    ({ token }) => {
      localStorage.setItem("fusionlab.project", "r13-link");
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
  await page.getByRole("tablist", { name: "Workspace documents" }).getByRole("tab", { name: "Inputs", exact: true }).click();
  await page
    .getByText("Link structure annotation source", { exact: true })
    .click();
  await page
    .getByLabel("Annotation JSON source", { exact: true })
    .selectOption(files[1].id);
  await page
    .getByLabel("Annotation target structure", { exact: true })
    .selectOption(files[0].id);
  await page
    .getByRole("button", { name: "Check annotation file links", exact: true })
    .click();
  await expect(
    page.getByText("Preview: structure_annotations · source.linked.json"),
  ).toBeVisible();
  expect(
    (await (await request.get(u + "/projects/r13-link", { headers })).json())
      .files,
  ).toHaveLength(2);
  await page
    .getByRole("button", { name: "Confirm import into draft", exact: true })
    .click();
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await page.getByText(/Draft synchronized/).waitFor();
  const meta = await request.get(
    u + "/files/" + files[0].id + "/structure-annotations?project_id=r13-link",
    { headers },
  );
  expect(meta.status()).toBe(200);
  const result = await meta.json();
  expect(result.annotations[0].plddt).toBe(0);
  expect(result.annotations[0].residue.insertion_code).toBe("A");
  expect(result.confidence_status).toBe(
    "source_registered_not_scientific_approval",
  );
  expect(
    await (
      await request.get(u + "/files/" + files[1].id + "?project_id=r13-link", {
        headers,
      })
    ).text(),
  ).toBe(source);
  const text = await page.locator("body").innerText();
  for (const file of files) expect(text).not.toContain(file.sha256);
  expect(text).not.toContain("target_sha256");
  expect(text).not.toContain("scientific_project.config");
});
