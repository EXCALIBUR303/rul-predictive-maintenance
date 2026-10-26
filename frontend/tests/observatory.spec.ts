import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
for (const width of [360, 768, 1440]) {
  test(`fleet, replay, arena and explorer at ${width}px`, async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("console", (m) => {
      if (m.type() === "error") errors.push(m.text());
    });
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/");
    await expect(page.getByRole("button", { name: /Open ENG-/ })).toHaveCount(
      12,
    );
    await expect(
      page.getByRole("heading", { name: "Every engine. One clear picture." }),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBeTruthy();
    await page.waitForTimeout(600);
    const a11y = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    expect(
      a11y.violations.map((v) => ({
        id: v.id,
        nodes: v.nodes.map((n) => ({
          target: n.target,
          summary: n.failureSummary,
        })),
      })),
    ).toEqual([]);
    await page.screenshot({ path: `qa/fleet-${width}.png`, fullPage: true });
    await page
      .getByRole("searchbox", { name: "Search engines" })
      .fill("nonexistent");
    await expect(
      page.getByRole("heading", { name: "No matching engines" }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Clear filters" }).click();
    await page.getByRole("button", { name: "Explore an engine" }).click();
    await expect(page.getByRole("slider", { name: /Cycle / })).toBeVisible();
    await page.getByRole("slider", { name: /Cycle / }).fill("150");
    await expect(
      page.getByText("Cycle 150 of", { exact: false }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Run what-if" }).click();
    await expect(page.getByRole("status")).toContainText(
      "XGBoost checkpoint what-if",
    );
    await page.getByRole("slider", { name: "Sensor 2 adjustment" }).fill("5");
    await expect(
      page.getByText("Inputs changed.", { exact: false }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Play replay" }).click();
    await page.waitForTimeout(1200);
    await page.getByRole("button", { name: "Pause replay" }).click();
    expect(
      Number(await page.getByRole("slider", { name: /Cycle / }).inputValue()),
    ).toBeGreaterThan(150);
    await page.screenshot({ path: `qa/engine-${width}.png`, fullPage: true });
    expect(
      (
        await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
          .analyze()
      ).violations,
    ).toEqual([]);
    await page
      .getByRole("button", { name: "Model arena", exact: true })
      .click();
    await expect(page.getByText("Best RMSE")).toBeVisible();
    await page
      .getByRole("combobox", { name: "Benchmark dataset" })
      .selectOption("FD002");
    await expect(
      page.getByText("FD002 · Reduced-budget checkpoints", { exact: false }),
    ).toBeVisible();
    await page
      .getByRole("combobox", { name: "Benchmark dataset" })
      .selectOption("FD004");
    await page.screenshot({ path: `qa/arena-${width}.png`, fullPage: true });
    await page
      .getByRole("button", { name: "Dataset explorer", exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "Sensor correlation" }),
    ).toBeVisible();
    await page.screenshot({ path: `qa/explorer-${width}.png`, fullPage: true });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBeTruthy();
    expect(
      (
        await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
          .analyze()
      ).violations,
    ).toEqual([]);
    await page.getByRole("button", { name: "Switch to light theme" }).click();
    await page.waitForTimeout(300);
    expect(
      (
        await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
          .analyze()
      ).violations,
    ).toEqual([]);
    await page.screenshot({ path: `qa/light-${width}.png`, fullPage: true });
    const dataset = await (await page.request.get("/demo.json")).json();
    const engineName = dataset.engines[0].name;
    await page.keyboard.press("Control+k");
    await expect(page.getByRole("dialog")).toBeVisible();
    await page
      .getByRole("searchbox", { name: "Search commands" })
      .fill(engineName);
    await page
      .getByRole("button", { name: `${engineName} Engine detail` })
      .click();
    await expect(
      page.getByRole("heading", { name: `${engineName} / digital workspace` }),
    ).toBeVisible();
    expect(errors).toEqual([]);
  });
}
test("dataset failure, retry and loading", async ({ page }) => {
  let fail = true;
  await page.route("**/demo.json", async (route) => {
    if (fail) await route.fulfill({ status: 503, body: "unavailable" });
    else await route.continue();
  });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Couldn’t load the workspace" }),
  ).toBeVisible();
  fail = false;
  await page.getByRole("button", { name: "Retry dataset" }).click();
  await expect(page.getByRole("button", { name: /Open ENG-/ })).toHaveCount(12);
});
test("reduced motion and keyboard dialog", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await page.getByRole("button", { name: "Open command palette" }).click();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await expect(
    page.getByRole("button", { name: "Open command palette" }),
  ).toBeFocused();
});

test("risk filtering and replay threshold alert", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("button", { name: /Open ENG-/ })).toHaveCount(12);
  await page
    .getByRole("combobox", { name: "Filter health" })
    .selectOption("critical");
  const d = await (await page.request.get("/demo.json")).json();
  const critical = d.engines.filter(
    (e: { current: number; points: { xgboost: number }[] }) =>
      e.points[e.current - 1].xgboost <= 30,
  ).length;
  await expect(page.getByRole("button", { name: /Open ENG-/ })).toHaveCount(
    critical,
  );
  await page.getByRole("button", { name: "Explore an engine" }).click();
  const dataset = await (await page.request.get("/demo.json")).json();
  const target = dataset.engines.find((e: { points: { xgboost: number }[] }) =>
    e.points.some(
      (p, i, a) => i > 0 && a[i - 1].xgboost > 30 && p.xgboost <= 30,
    ),
  );
  expect(target).toBeTruthy();
  await page
    .getByRole("combobox", { name: "Selected engine" })
    .selectOption(String(target.id));
  const points = target.points as {
    cycle: number;
    xgboost: number;
  }[];
  const crossing = points.findIndex(
    (p, i) => i > 0 && points[i - 1].xgboost > 30 && p.xgboost <= 30,
  );
  expect(crossing).toBeGreaterThan(0);
  await page.getByRole("slider", { name: /Cycle / }).fill(String(crossing));
  await page.getByRole("combobox", { name: "Replay speed" }).selectOption("10");
  await page.getByRole("button", { name: "Play replay" }).click();
  await expect(page.getByRole("status")).toContainText(
    "critical threshold crossed",
  );
  await page.getByRole("button", { name: "Pause replay" }).click();
  await page.getByRole("button", { name: "Reset replay" }).click();
  await expect(page.getByRole("slider", { name: /Cycle / })).toHaveValue("1");
});

test("all four real datasets and model-based what-if", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("button", { name: /Open ENG-/ })).toHaveCount(12);
  for (const subset of ["FD001", "FD002", "FD003", "FD004"]) {
    await page
      .getByRole("button", { name: "Fleet overview", exact: true })
      .click();
    await page
      .getByRole("combobox", { name: "Workspace dataset" })
      .selectOption(subset);
    await expect(page.getByRole("button", { name: /Open ENG-/ })).toHaveCount(
      12,
    );
    await expect(
      page.getByText(`C-MAPSS ${subset} held-out validation engines`, {
        exact: false,
      }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Explore an engine" }).click();
    const dataset = await (
      await page.request.get(`/demo-${subset}.json`)
    ).json();
    const engine = dataset.engines[0];
    await page.getByRole("slider", { name: /Cycle / }).fill("100");
    await page
      .getByRole("combobox", { name: "Importance / what-if model" })
      .selectOption("transformer");
    await page.getByRole("slider", { name: "Sensor 4 adjustment" }).fill("10");
    await page.getByRole("button", { name: "Run what-if" }).click();
    await expect(page.getByRole("status")).toContainText(
      `Transformer checkpoint what-if: ${engine.points[99].whatIf.transformer["4"]["10"].toFixed(1)}`,
    );
    await expect(
      page.getByText("Permutation Δ MAE", { exact: false }),
    ).toBeVisible();
  }
});
