import { test, expect } from "@playwright/test";
import path from "node:path";

test("typed scientific project page runs real stages without inventing missing evidence", async ({page}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await page.getByRole("button",{name:"＋ 创建项目"}).click();
  await page.getByLabel("科学配置路径").fill(path.resolve(import.meta.dirname,"../../../configs/m1_m4_real_scoring_example.yaml"));
  await page.getByRole("button",{name:"检查科学配置",exact:true}).click();
  await page.getByRole("button",{name:"确认科学配置（待保存）",exact:true}).click();
  await page.getByRole("button",{name:"保存项目",exact:true}).click();
  await page.getByRole("button",{name:/分析流程/}).click();
  await page.getByLabel("选择目标").selectOption("scientific_pipeline");
  await page.getByRole("button",{name:"生成流程",exact:true}).click();
  await page.getByRole("button",{name:"确认并运行",exact:true}).click();
  await expect(page.getByText("5 / 5 步骤完成",{exact:false})).toBeVisible();
  await page.getByRole("button",{name:"查看结果与错误 →"}).click();
  await expect(page.getByRole("heading",{name:"M4 · 科学项目结果",exact:true})).toBeVisible();
  await expect(page.getByText(/科学状态：insufficient_data/).first()).toBeVisible();
  await expect(page.getByText(/产物 15：未提供/).first()).toBeVisible();
  await page.screenshot({path:"test-results/scientific-project-missing-evidence.png",fullPage:true});
  expect(errors).toEqual([]);
});
