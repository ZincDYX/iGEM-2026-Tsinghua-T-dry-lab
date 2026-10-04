import { test, expect } from "@playwright/test";

test("create, preview, confirm, run, reopen history and inspect provenance", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await page.getByRole("button", { name: "＋ 创建项目" }).click();
  await page.getByLabel("项目名称").fill(`E2E-${Date.now()}`);
  await page.getByRole("button", { name: "保存项目", exact: true }).click();
  await page
    .getByLabel("导入文件")
    .setInputFiles({
      name: "fusion.fasta",
      mimeType: "text/plain",
      buffer: Buffer.from(">fusionA\nMAGSGS\n>fusionB\nMKKGGSS\n"),
    });
  await expect(
    page.getByRole("heading", { name: "导入预览 · fusion.fasta" }),
  ).toBeVisible();
  await expect(page.getByText("fusionA · 6 aa")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "fusionA", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "确认导入", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "fusionA", exact: true }),
  ).toBeVisible();
  await expect(page.getByLabel("实验条件")).toHaveCount(0);
  await page.getByRole("button", { name: /工作台/ }).click();
  await page.getByRole("button", { name: /生成可审阅流程/ }).click();
  await page.getByRole("button", { name: "确认并运行", exact: true }).click();
  await expect(
    page.getByText("2 / 2 步骤完成", { exact: false }),
  ).toBeVisible();
  await page.getByRole("button", { name: "查看结果与错误 →" }).click();
  await expect(
    page.getByRole("heading", { name: "构建序列比较" }),
  ).toBeVisible();
  await page.screenshot({
    path:
      process.env.FUSIONLAB_SCREENSHOT ?? "test-results/fusionlab-results.png",
    fullPage: true,
  });
  await page.reload();
  await page.getByRole("button", { name: /分析历史/ }).click();
  await expect(
    page.getByRole("button", { name: "查看", exact: true }).first(),
  ).toBeVisible();
  await page.getByRole("button", { name: /Scientist Mode/ }).click();
  await page.getByRole("button", { name: /开发者面板/ }).click();
  await expect(
    page.getByText("不可变快照与环境", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Artifact provenance", { exact: true }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});
